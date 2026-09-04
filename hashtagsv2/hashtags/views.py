import csv
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, TemplateView
from django.utils.cache import add_never_cache_headers
from django.utils.translation import gettext as _

from .forms import SearchForm
from .helpers import hashtag_queryset, get_hashtags_context
from .models import Hashtag
from .visibility import (
    EXPORT_MAX_BATCHES,
    EXPORT_TOTAL_BUDGET_S,
    EXPORT_VERIFY_LIMIT,
    redact,
)


class Index(ListView):
    model = Hashtag
    template_name = "hashtags/index.html"
    form_class = SearchForm
    context_object_name = "hashtags"
    paginate_by = 20

    def get_context_data(self, *args, **kwargs):
        # If we have any hashtags in the database, check if we appear
        # to be up-to-date.
        try:
            latest_datetime = Hashtag.objects.all().latest("timestamp").timestamp
        except Hashtag.DoesNotExist:
            latest_datetime = datetime.now(timezone.utc)
        diff = datetime.now(timezone.utc) - latest_datetime
        if diff.seconds > 3600:
            messages.add_message(
                self.request,
                messages.INFO,
                # Translators: Message to be displayed when the latest edits are not in the database.
                _(
                    "Note that the latest edits may not currently be reflected in the tool."
                ),
            )

        context = super().get_context_data(**kwargs)

        # Make sure we're setting initial values in case user has
        # already submitted something.
        context["form"] = self.form_class(self.request.GET)

        # If we have any paginated data to display, compute statistics for
        # the overall, non paginated queryset. `if queryset:` actually evaluates
        # the queryset and queries the database. We want to make sure to only
        # evaluate the paginated queryset we are displaying.
        if context["page_obj"]:
            context = get_hashtags_context(self.request, self.object_list, context)

            # The wiki can hide an edit summary or a username after we record
            # it, so check this page of results before we show it. T277832
            #
            # We ignore whether the check reached every row. A page holds 20
            # rows, so it needs 20 API calls at most, and the message below
            # tells the user that some results are missing.
            context["hashtags"], removed, _complete = redact(context["hashtags"])
            context["object_list"] = context["hashtags"]
            if removed:
                messages.add_message(
                    self.request,
                    messages.INFO,
                    # Translators: Message to be displayed when some results
                    # were removed because the wiki no longer shows them.
                    _(
                        "Some results are not shown. The wiki has hidden them, "
                        "or we could not confirm that they are still public."
                    ),
                )
        elif self.request.GET.get("query"):
            messages.add_message(
                self.request,
                messages.INFO,
                # Translators: Message to be displayed when there are no
                # results for the search.
                _("No results found."),
            )
        else:
            # We're just displaying the home page with no query.
            top_tags = (
                Hashtag.objects.filter(
                    timestamp__gt=datetime.now() - timedelta(days=30)
                )
                .values_list("hashtag")
                .annotate(count=Count("hashtag"))
                .order_by("-count")[:10]
            )
            context["top_tags"] = [x[0] for x in top_tags]

        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.GET.get("query"):
            # We checked these results against the wiki as we rendered them.
            # A cache must not keep serving them after the wiki hides an
            # edit. T277832
            add_never_cache_headers(response)
        return response

    def get_queryset(self):
        form = self.form_class(self.request.GET)
        if form.is_valid():
            form_data = form.cleaned_data
            if "wikidata.org" in form_data["project"]:
                hashtag_qs = []
                messages.add_message(
                    self.request,
                    messages.INFO,
                    # Translators: Message to be displayed when a user specify 'wikidata' in the project field.
                    _("Unfortunately Wikidata searching is not currently supported."),
                )
            else:
                hashtag_qs = hashtag_queryset(form_data)

            return hashtag_qs

        # We're mixing forms and listview; paginate_by expects to always
        # have *something* to paginate, so we send back an empty list
        # if the form hasn't been filled yet.
        return []


def refuse_download(request, request_dict):
    """Send the user back to the search page, and say why."""
    messages.add_message(
        request,
        messages.INFO,
        # Translators: Message to be displayed when we cannot check all of
        # the results of a search, so we cannot make a file of them.
        _(
            "We cannot check all of the results of this search, so we cannot "
            "make the file. Make the search smaller, or try again later."
        ),
    )
    return redirect(
        "{path}?{query}".format(path=reverse("index"), query=urlencode(request_dict))
    )


def rows_for_download(request):
    """
    Get the rows for a download, after a check against the wikis.

    Returns (rows, refusal). If we cannot check all of the results, `rows` is
    None and `refusal` is a response that sends the user back to the search
    page. A file that is short for a reason that the user cannot see is worse
    than no file. See T277832.
    """
    request_dict = request.GET.dict()
    hashtags = hashtag_queryset(request_dict)

    # A download sends all of the results, not one page of them. A large
    # search needs more API calls than we can make before the request times
    # out, so we refuse it before we read the rows.
    if hashtags.count() > EXPORT_VERIFY_LIMIT:
        return None, refuse_download(request, request_dict)

    rows, _removed, complete = redact(
        hashtags, budget=EXPORT_TOTAL_BUDGET_S, max_batches=EXPORT_MAX_BATCHES
    )

    # The check needs too many calls, or it ran out of time, or a call
    # failed. We do not know about every row, so we send no file.
    if not complete:
        return None, refuse_download(request, request_dict)

    return rows, None


def csv_download(request):
    # If this fails for large files we should consider
    # https://docs.djangoproject.com/en/2.1/howto/outputting-csv/#streaming-large-csv-files
    hashtags, refusal = rows_for_download(request)
    if refusal is not None:
        return refusal

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="hashtags.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            # Translators: Domain of a wikimedia project.
            _("Domain"),
            # Translators: Time at which edit is done.
            _("Timestamp"),
            # Translators: Username of the editor.
            _("Username"),
            # Translations: Title of the page to which edit belongs.
            _("Page_title"),
            # Translations: Summary of the edit done on Wikimedia project.
            _("Edit_summary"),
            # Translations: Revision ID of the edit.
            _("Revision_id"),
        ]
    )
    for hashtag in hashtags:
        writer.writerow(
            [
                hashtag.domain,
                hashtag.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                hashtag.username,
                hashtag.page_title,
                hashtag.edit_summary,
                hashtag.rev_id,
            ]
        )

    # We checked these rows against the wikis as we made the file. A cache
    # must not send them again after the wiki hides an edit. T277832
    add_never_cache_headers(response)

    return response


def json_download(request):
    hashtags, refusal = rows_for_download(request)
    if refusal is not None:
        return refusal

    row_list = []
    for hashtag in hashtags:
        row_list.append(
            {
                "Domain": hashtag.domain,
                "Timestamp": hashtag.timestamp,
                "Username": hashtag.username,
                "Page_title": hashtag.page_title,
                "Edit_summary": hashtag.edit_summary,
                "Revision_ID": hashtag.rev_id,
            }
        )

    response = JsonResponse({"Rows": row_list})

    # We checked these rows against the wikis as we made the file. A cache
    # must not send them again after the wiki hides an edit. T277832
    add_never_cache_headers(response)

    return response


class Docs(TemplateView):
    template_name = "hashtags/docs.html"
