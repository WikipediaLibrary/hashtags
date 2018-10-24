import csv
from datetime import datetime, timedelta

from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count
from django.views.generic import FormView, ListView, TemplateView

from .forms import SearchForm
from .models import Hashtag

def hashtag_queryset(request_dict):
    """
    This function parses a request dictionary and filters a hashtag
    queryset accordingly, sorted by most recent.
    """

    split_hashtags_query = request_dict['query'].split(",")
    split_hashtags = [x.strip() for x in split_hashtags_query]
    queryset = Hashtag.objects.filter(
        hashtag__in=split_hashtags
            )

    if 'project' in request_dict:
        if request_dict['project']:
            queryset = queryset.filter(
                domain=request_dict['project'])

    if 'startdate' in request_dict:
        if request_dict['startdate']:
            queryset = queryset.filter(
                timestamp__gt=request_dict['startdate'])

    if 'enddate' in request_dict:
        if request_dict['enddate']:
            queryset = queryset.filter(
                timestamp__lt=request_dict['enddate'])

    # We're using MySQL, which doesn't support DISTINCT ON, but we
    # want to allow multiple hashtags to be queried simultaneously while
    # not displaying the same edit more than once. We can achieve this
    # by using values_list() for every field except hashtag - each
    # other field is identical for the same edit, so we can use
    # distinct() successfully.
    # Note that this returns a Queryset of Rows, not Objects.
    ordered_queryset = queryset.order_by(
        '-timestamp').values_list(
            'domain', 'timestamp', 'username', 'page_title', 'edit_summary', 'rc_id', named=True
                ).distinct()

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

        # Make sure we're setting initial values in case user has
        # already submitted something.
        context['form'] = self.form_class(self.request.GET)

        hashtags = self.object_list
        if hashtags:

            hashtag_query = self.request.GET.get('query')
            context['hashtag_query_list'] = [x.strip() for x in hashtag_query.split(",")]

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

class Docs(TemplateView):
    template_name = 'hashtags/docs.html'