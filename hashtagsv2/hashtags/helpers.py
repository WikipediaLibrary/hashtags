from datetime import datetime
from datetime import timedelta

from .models import Hashtag

from django.db.models import Count
from urllib.parse import urlencode

def split_hashtags(hashtag_list):
    split_hashtags_list = hashtag_list.split(",")
    stripped_hashtags = [x.strip() for x in split_hashtags_list]

    # Strip # from hashtags if entered
    final_hashtags = [x[1:] if x.startswith("#") else x for x in stripped_hashtags]

    return final_hashtags

def hashtag_queryset(request_dict):
    """
    This function parses a request dictionary and filters a hashtag
    queryset accordingly, sorted by most recent.
    """

    hashtag_list = split_hashtags(request_dict['query'])

    queryset = Hashtag.objects.filter(
        hashtag__in=hashtag_list
            )

    if 'project' in request_dict:
        if request_dict['project']:
            queryset = queryset.filter(
                domain=request_dict['project'])

    if 'user' in request_dict:
        if request_dict['user']:
            queryset = queryset.filter(
                username=request_dict['user'])

    if 'startdate' in request_dict:
        if request_dict['startdate']:
            queryset = queryset.filter(
                timestamp__gt=request_dict['startdate'])

    if 'enddate' in request_dict:
        if request_dict['enddate']:
            # Convert enddate to a datetime directly to ensure timedelta
            # works if the date comes in as a string.
            if type(request_dict['enddate']) == str:
                end_date = datetime.strptime(request_dict['enddate'], '%Y-%m-%d')
            else:
                end_date = request_dict['enddate']
            enddate_plus_one = end_date + timedelta(days=1)
            queryset = queryset.filter(
                timestamp__lt=enddate_plus_one)

    # We're using MySQL, which doesn't support DISTINCT ON, but we
    # want to allow multiple hashtags to be queried simultaneously while
    # not displaying the same edit more than once. We can achieve this
    # by using values_list() for every field except hashtag - each
    # other field is identical for the same edit, so we can use
    # distinct() successfully.
    # Note that this returns a Queryset of Rows, not Objects.
    ordered_queryset = queryset.order_by(
        '-timestamp').values_list(
            'domain', 'timestamp', 'username', 'page_title', 'edit_summary',
            'rc_id', 'rev_id',
                named=True
                ).distinct()

    return ordered_queryset

def get_hashtags_context(request, hashtags, context):
    # Context data for StatisticsView and Index view
    
    hashtag_query = request.GET.get('query')
    context['hashtag_query_list'] = split_hashtags(hashtag_query)

    # Context for the stats section
    context['revisions'] = len(hashtags)
    context['oldest'] = hashtags[len(hashtags)-1].timestamp.date()
    context['newest'] = hashtags.first().timestamp.date()
    context['pages'] = hashtags.values('page_title', 'domain').distinct().count()
    context['users'] = hashtags.values('username').distinct().count()
    context['projects'] = hashtags.values('domain').distinct().count()

    request_dict = request.GET.dict()

    # The GET parameters from the URL, for formatting links
    # We don't require page parameter so removing it from request_dict
    if 'page' in request_dict:
        request_dict.pop('page')
    context['query_string'] = urlencode(request_dict)
    return context

def results_count(qs, field, sort_param):
    # Return edits count for a particular field (for eg. users) sorted by sort_param (for eg. edits)
    return qs.values(field).annotate(edits = Count('rc_id')).order_by(sort_param)