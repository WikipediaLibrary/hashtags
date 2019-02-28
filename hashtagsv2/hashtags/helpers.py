from datetime import datetime
from datetime import timedelta

from .models import Hashtag

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

    # If search_type is provided by the user
    if 'search_type' in request_dict:
        if request_dict['search_type'] == 'and':
            rcids_for_hashtag=[]
            #Collect rc_ids for each individual tag
            for hashtag in hashtag_list:
                qs=Hashtag.objects.filter(hashtag=hashtag).values_list('rc_id', flat=True).distinct()
                rcids_for_hashtag.append(set(qs))
            #Find common rc_ids by taking intersection of above obtained rc_ids 
            final_rcids = rcids_for_hashtag[0].intersection(*rcids_for_hashtag)
            queryset = Hashtag.objects.filter(rc_id__in=list(final_rcids))
 
        else:
            queryset = Hashtag.objects.filter(
            hashtag__in=hashtag_list
            )

    # If user didn't provide search_type
    else:
        queryset = Hashtag.objects.filter(
        hashtag__in=hashtag_list
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
