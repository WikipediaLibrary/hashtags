import csv
from datetime import datetime, timedelta

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count
from django.views.generic import FormView, ListView, TemplateView

from .forms import SearchForm
from .helpers import split_hashtags, hashtag_queryset
from .models import Hashtag

class Index(ListView):
    model = Hashtag
    template_name = 'hashtags/index.html'
    form_class = SearchForm
    context_object_name = 'hashtags'
    paginate_by = 20

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        top_tags = Hashtag.objects.filter(
                timestamp__gt = datetime.now() - timedelta(days=30)
            ).values_list('hashtag').annotate(
            count=Count('hashtag')).order_by('-count')[:10]
        context['top_tags'] = [x[0] for x in top_tags]

        # Make sure we're setting initial values in case user has
        # already submitted something.
        context['form'] = self.form_class(self.request.GET)

        hashtags = self.object_list
        if hashtags:

            hashtag_query = self.request.GET.get('query')
            context['hashtag_query_list'] = split_hashtags(hashtag_query)

            # Context for the stats section
            context['oldest'] = hashtags.order_by('timestamp')[0].timestamp.date()
            context['newest'] = hashtags.latest('timestamp').timestamp.date()
            context['revisions'] = hashtags.count()
            context['pages'] = hashtags.values('page_title', 'domain').distinct().count()
            context['users'] = hashtags.values('username').distinct().count()
            context['projects'] = hashtags.values('domain').distinct().count()

            # The GET parameters from the URL, for formatting links
            context['query_string'] = self.request.META['QUERY_STRING']

        return context

    def get_queryset(self):
        form = self.form_class(self.request.GET)
        if form.is_valid():
            form_data = form.cleaned_data

            hashtag_qs = hashtag_queryset(form_data)

            if hashtag_qs.count() == 0:
                messages.add_message(self.request, messages.INFO,
                    'No results found.')

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
    writer.writerow(['Domain', 'Timestamp', 'Username',
        'Page title', 'Edit summary'])
    for hashtag in hashtags:
        writer.writerow([hashtag.domain, hashtag.timestamp, hashtag.username,
            hashtag.page_title, hashtag.edit_summary])

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
            "Page title": hashtag.page_title,
            "Edit summary": hashtag.edit_summary
        })

    return JsonResponse({"Rows": row_list})

class Docs(TemplateView):
    template_name = 'hashtags/docs.html'