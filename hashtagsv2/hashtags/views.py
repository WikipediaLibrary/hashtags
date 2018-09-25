import csv
from datetime import datetime, timedelta

from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.db.models import Count
from django.shortcuts import render
from django.views.generic import FormView, ListView

from .forms import SearchForm
from .models import Hashtag

def hashtag_queryset(request_dict):
    queryset = Hashtag.objects.filter(hashtag=request_dict['query'])

    if request_dict['project']:
        queryset = queryset.filter(
            domain=request_dict['project'])
    if request_dict['startdate']:
        queryset = queryset.filter(
            timestamp__gt=request_dict['startdate'])
    if request_dict['enddate']:
        queryset = queryset.filter(
            timestamp__lt=request_dict['enddate'])

    ordered_queryset = queryset.order_by('-timestamp')

    return ordered_queryset

class Index(ListView):
    model = Hashtag
    template_name = 'hashtags/index.html'
    form_class = SearchForm
    context_object_name = 'hashtags'
    paginate_by = 20

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        top_tags = Hashtag.objects.filter(
                timestamp__gt = datetime.now() - timedelta(days=100)
            ).values_list('hashtag').annotate(
            count=Count('hashtag')).order_by('-count')[:10]
        context['top_tags'] = [x[0] for x in top_tags]

        # Make sure we're setting initial values if user has
        # already submitted something.
        context['form'] = self.form_class(self.request.GET)

        hashtags = self.object_list
        if hashtags:
            context['hashtag_query'] = self.request.GET.get('query')

            context['oldest'] = hashtags.order_by('timestamp')[0].timestamp.date()
            context['newest'] = hashtags.latest('timestamp').timestamp.date()
            context['revisions'] = hashtags.count()
            context['pages'] = hashtags.values('page_title', 'domain').distinct().count()
            context['users'] = hashtags.values('username').distinct().count()
            context['projects'] = hashtags.values('domain').distinct().count()

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
    response['Content-Disposition'] = 'attachment; filename="{filename}.csv"'.format(
        filename=request_dict['query'])

    hashtags = hashtag_queryset(request_dict)

    writer = csv.writer(response)
    writer.writerow(['Domain', 'Timestamp', 'Username',
        'Page title', 'Edit summary', 'Diff ID'])
    for hashtag in hashtags:
        writer.writerow([hashtag.domain, hashtag.timestamp, hashtag.username,
            hashtag.page_title, hashtag.edit_summary, hashtag.diff_id])

    return response