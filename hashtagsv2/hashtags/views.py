import csv
from datetime import datetime, timedelta, timezone

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count
from django.views.generic import FormView, ListView, TemplateView
from haystack.generic_views import SearchView

from .forms import HashtagSearchForm
from .helpers import split_hashtags
from .models import Hashtag

from logging import getLogger

logger = getLogger('django')

class Index(SearchView):
    model = Hashtag
    template_name = 'hashtags/index.html'
    form_class = HashtagSearchForm

    def get_context_data(self, *args, **kwargs):
        latest_datetime = Hashtag.objects.latest('timestamp').timestamp
        diff = datetime.now(timezone.utc) - latest_datetime
        if diff.seconds > 3600:
            messages.add_message(self.request, messages.INFO,
            'Note that the latest edits may not currently be reflected in the tool.')

        context = super().get_context_data(**kwargs)

        # Make sure we're setting initial values in case user has
        # already submitted something.
        context['form'] = self.form_class(self.request.GET)

        hashtags = self.get_queryset()
        if hashtags:
            hashtag_query = self.request.GET.get('q')
            context['hashtag_query_list'] = split_hashtags(hashtag_query)

            # Context for the stats section
            num_edits = hashtags.count()
            context['revisions'] = num_edits
            context['oldest'] = hashtags[num_edits-1].timestamp.date()
            context['newest'] = hashtags[0].timestamp.date()
            # TODO: Reinstate - haystack queryset doesn't understand .values().distinct()
            #context['pages'] = hashtags.values('page_title', 'domain').distinct().count()
            #context['users'] = hashtags.values('username').distinct().count()
            #context['projects'] = hashtags.values('domain').distinct().count()

            # The GET parameters from the URL, for formatting links
            context['query_string'] = self.request.META['QUERY_STRING']
        else:
            # We don't need top tags if we're showing results
            top_tags = Hashtag.objects.filter(
                timestamp__gt=datetime.now() - timedelta(days=30)
            ).values_list('hashtag').annotate(
                count=Count('hashtag')).order_by('-count')[:10]
            context['top_tags'] = [x[0] for x in top_tags]

        return context


def csv_download(request):
    # If this fails for large files we should consider
    # https://docs.djangoproject.com/en/2.1/howto/outputting-csv/#streaming-large-csv-files
    request_dict = request.GET.dict()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hashtags.csv"'

    hashtags = hashtag_queryset(request_dict)

    writer = csv.writer(response)
    writer.writerow(['Domain', 'Timestamp', 'Username',
        'Page_title', 'Edit_summary', 'Revision_id'])
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