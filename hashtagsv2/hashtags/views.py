import csv
from datetime import datetime, timedelta, timezone

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count
from django.views.generic import ListView, TemplateView
from django.utils.translation import gettext as _

from .forms import SearchForm
from .helpers import hashtag_queryset, get_hashtags_context
from .models import Hashtag


class Index(ListView):
    model = Hashtag
    template_name = 'hashtags/index.html'
    form_class = SearchForm
    context_object_name = 'hashtags'
    paginate_by = 20

    def get_context_data(self, *args, **kwargs):
        # If we have any hashtags in the database, check if we appear
        # to be up-to-date.
        try:
            latest_datetime = Hashtag.objects.all().latest('timestamp').timestamp
        except Hashtag.DoesNotExist:
            latest_datetime = datetime.now(timezone.utc)
        diff = datetime.now(timezone.utc) - latest_datetime
        if diff.seconds > 3600:
            messages.add_message(self.request, messages.INFO,
            # Translators: Message to be displayed when the latest edits are not in the database.
            _('Note that the latest edits may not currently be reflected in the tool.'))

        context = super().get_context_data(**kwargs)

        # Make sure we're setting initial values in case user has
        # already submitted something.
        context['form'] = self.form_class(self.request.GET)

        # If we have any paginated data to display, compute statistics for
        # the overall, non paginated queryset. `if queryset:` actually evaluates
        # the queryset and queries the database. We want to make sure to only
        # evaluate the paginated queryset we are displaying.
        if context['page_obj']:
            context = get_hashtags_context(
                self.request, self.object_list, context)
        elif self.request.GET.get('query'):
            messages.add_message(self.request, messages.INFO,
                # Translators: Message to be displayed when there are no
                # results for the search.
                _('No results found.'))
        else:
            # We're just displaying the home page with no query.
            top_tags = Hashtag.objects.filter(
                timestamp__gt=datetime.now() - timedelta(days=30)
            ).values_list('hashtag').annotate(
                count=Count('hashtag')).order_by('-count')[:10]
            context['top_tags'] = [x[0] for x in top_tags]

        return context

    def get_queryset(self):
        form = self.form_class(self.request.GET)
        if form.is_valid():
            form_data = form.cleaned_data
            if 'wikidata.org' in form_data['project']:
                hashtag_qs = []
                messages.add_message(self.request, messages.INFO,
                # Translators: Message to be displayed when a user specify 'wikidata' in the project field.
                _('Unfortunately Wikidata searching is not currently supported.'))
            else:
                hashtag_qs = hashtag_queryset(form_data)

            return hashtag_qs

        # We're mixing forms and listview; paginate_by expects to always
        # have *something* to paginate, so we send back an empty list
        # if the form hasn't been filled yet.
        return []


def csv_download(request):
    # If this fails for large files we should consider
    # https://docs.djangoproject.com/en/2.1/howto/outputting-csv/#streaming-large-csv-files
    request_dict = request.GET.dict()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hashtags.csv"'

    hashtags = hashtag_queryset(request_dict)

    writer = csv.writer(response)
    writer.writerow([
        # Translators: Domain of a wikimedia project.
        _('Domain'),
        # Translators: Time at which edit is done.
        _('Timestamp'),
        # Translators: Username of the editor.
        _('Username'),
        # Translations: Title of the page to which edit belongs.
        _('Page_title'),
        # Translations: Summary of the edit done on Wikimedia project.
        _('Edit_summary'),
        # Translations: Revision ID of the edit.
        _('Revision_id')])
    for hashtag in hashtags:
        writer.writerow([hashtag.domain, hashtag.timestamp.strftime("%Y-%m-%d %H:%M:%S"), hashtag.username,
            hashtag.page_title, hashtag.edit_summary, hashtag.rev_id])

    return response


def json_download(request):
    request_dict = request.GET.dict()

    hashtags = hashtag_queryset(request_dict)

    row_list = []
    for hashtag in hashtags:
        row_list.append({
            "Domain": hashtag.domain,
            "Timestamp": hashtag.timestamp,
            "Username": hashtag.username,
            "Page_title": hashtag.page_title,
            "Edit_summary": hashtag.edit_summary,
            "Revision_ID": hashtag.rev_id
        })

    return JsonResponse({"Rows": row_list})


class Docs(TemplateView):
    template_name = 'hashtags/docs.html'
