import csv
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncDay, TruncYear
from django.views.generic import FormView, ListView, TemplateView, View
from django.shortcuts import render

from .forms import SearchForm
from .helpers import split_hashtags, hashtag_queryset, get_hashtags_context
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
        all_hashtags = Hashtag.objects.all().count()
        if all_hashtags > 0:
            latest_datetime = Hashtag.objects.all().latest('timestamp').timestamp
            diff = datetime.now(timezone.utc) - latest_datetime
            if diff.seconds > 3600:
                messages.add_message(self.request, messages.INFO,
                'Note that the latest edits may not currently be reflected in the tool.')

        context = super().get_context_data(**kwargs)

        # Make sure we're setting initial values in case user has
        # already submitted something.
        context['form'] = self.form_class(self.request.GET)

        hashtags = self.object_list
        if hashtags:
            context = get_hashtags_context(self.request, hashtags, context)
        else:
            # We don't need top tags if we're showing results
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
                    'Unfortunately Wikidata searching is not currently supported.')
            else:    
                hashtag_qs = hashtag_queryset(form_data)

                if not hashtag_qs:
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

def top_project_statistics_data(request):
    # Returns top 10 projects in decreasing order of number of edits.
    # We will need this info as x-axis and y-axis when rendering chart.
    request_dict = request.GET.dict()

    projects = []
    edits_per_project = []

    hashtags = hashtag_queryset(request_dict)
    qs = hashtags.values('domain').annotate(edits = Count('rc_id')).order_by('-edits')[:10]
    for item in qs:
        projects.append(item['domain'])
        edits_per_project.append(item['edits'])

    data = {
        'projects': projects,
        'edits_per_project': edits_per_project
    }
    return JsonResponse(data)

def top_user_statistics_data(request):
    # Returns top 10 projects in decreasing order of number of edits.
    request_dict = request.GET.dict()

    usernames = []
    edits_per_user = []

    hashtags = hashtag_queryset(request_dict)
    qs = hashtags.values('username').annotate(edits = Count('rc_id')).order_by('-edits')[:10]
    for item in qs:
        usernames.append(item['username'])
        edits_per_user.append(item['edits'])

    data = {
        'usernames': usernames,
        'edits_per_user': edits_per_user
    }
    return JsonResponse(data)

def time_statistics_data(request):
    request_dict = request.GET.dict()

    edits_array = []
    time_array = []

    hashtags = hashtag_queryset(request_dict)
    earliest_date = hashtags[len(hashtags)-1].timestamp.date()
    latest_date = hashtags.first().timestamp.date()

    date_range = latest_date - earliest_date
    # key value pairs of date unit and number of edits
    time_dic = {}

    # Split by days
    if date_range.days < 90:
        qs = hashtags.annotate(day = TruncDay('timestamp')).values('day').annotate(edits = Count('rc_id')).order_by()
        
        for item in qs:
            time_dic[item['day'].date()] = item['edits']
        while earliest_date <= latest_date:
            time_array.append(earliest_date.strftime("%Y-%m-%d"))
            #If there are edits on a day, append number of edits else append 0
            if earliest_date in time_dic:
                temp = time_dic.pop(earliest_date)
                edits_array.append(temp)
            else:
                edits_array.append(0)
            earliest_date = earliest_date + timedelta(days=1)
    # Split by months
    elif date_range.days >=90 and date_range.days <1095:
        qs = hashtags.annotate(month = TruncMonth('timestamp')).values('month').annotate(edits = Count('rc_id')).order_by()
        for item in qs:
            time_dic[item['month'].date()] = item['edits']
        
        earliest_date = earliest_date.replace(day=1)
        latest_date = latest_date.replace(day=1)
        while earliest_date <= latest_date:
            time_array.append(earliest_date.strftime("%b-%Y"))
            if earliest_date in time_dic:
                temp = time_dic.pop(earliest_date)
                edits_array.append(temp)
            else:
                edits_array.append(0)
            earliest_date = earliest_date + relativedelta(months= +1)
    # Split by years
    else:
        qs = hashtags.annotate(year = TruncYear('timestamp')).values('year').annotate(edits = Count('rc_id')).order_by()       
        for item in qs:
            time_dic[item['year'].date()] = item['edits']
          
        earliest_date = earliest_date.replace(day=1,month=1)
        latest_date = latest_date.replace(day=1,month=1)
        while earliest_date <= latest_date:
            time_array.append(earliest_date.strftime("%Y"))
            if earliest_date in time_dic:
                temp = time_dic.pop(earliest_date)
                edits_array.append(temp)
            else:
                edits_array.append(0)
            earliest_date = earliest_date + relativedelta(years= +1)

    data = {
        'edits_array': edits_array,
        'time_array': time_array
    }
    return JsonResponse(data)

class StatisticsView(View):
    template_name = 'hashtags/graph.html'
    form_class = SearchForm
    def get(self, request):
        request_dict = request.GET.dict()
        hashtags = hashtag_queryset(request_dict)
        context = {'form': self.form_class(request.GET)}
        context['hashtags'] = hashtags
        if hashtags:
            context = get_hashtags_context(request, hashtags, context)
        return render(request, self.template_name, context=context)

class All_users_view(ListView):
    template_name = 'hashtags/all_users.html'
    context_object_name = 'users_list'
    paginate_by = 30

    def get_context_data(self, *args, **kwargs):
        context = super(All_users_view, self).get_context_data(**kwargs)
        request_dict = self.request.GET.dict()
        hashtags = hashtag_queryset(request_dict)
        # Context data for stats box
        context = get_hashtags_context(self.request, hashtags, context)
        return context

    def get_queryset(self):
        request_dict = self.request.GET.dict()
        hashtags = hashtag_queryset(request_dict)
        users_qs = hashtags.values('username').annotate(edits = Count('rc_id')).order_by('username')
        return users_qs

class All_projects_view(ListView):
    template_name = 'hashtags/all_projects.html'
    context_object_name = 'projects_list'

    def get_context_data(self, *args, **kwargs):
        context = super(All_projects_view, self).get_context_data(**kwargs)
        request_dict = self.request.GET.dict()
        hashtags = hashtag_queryset(request_dict)
        # Context data for stats box
        context = get_hashtags_context(self.request, hashtags, context)
        return context

    def get_queryset(self):
        request_dict = self.request.GET.dict()
        hashtags = hashtag_queryset(request_dict)
        projects_qs = hashtags.values('domain').annotate(edits = Count('rc_id')).order_by('-edits')
        return projects_qs

def users_csv(request):
    request_dict = request.GET.dict()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hashtags_users.csv"'

    hashtags = hashtag_queryset(request_dict)
    users_qs = hashtags.values('username').annotate(edits = Count('rc_id')).order_by('-edits')
    writer = csv.writer(response)
    writer.writerow(['User', 'Edits'])
    for user in users_qs:
        writer.writerow([user['username'], user['edits']])
    return response

def projects_csv(request):
    request_dict = request.GET.dict()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hashtags_projects.csv"'

    hashtags = hashtag_queryset(request_dict)
    projects_qs = hashtags.values('domain').annotate(edits = Count('rc_id')).order_by('-edits')
    writer = csv.writer(response)
    writer.writerow(['Project','Edits'])
    for project in projects_qs:
        writer.writerow([project['domain'], project['edits']])
    return response

def time_csv(request):
    request_dict = request.GET.dict()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hashtags_dates.csv"'

    hashtags = hashtag_queryset(request_dict)
    earliest_date = hashtags[len(hashtags)-1].timestamp.date()
    latest_date = hashtags.first().timestamp.date()

    time_dic = {}
    qs = hashtags.annotate(day = TruncDay('timestamp')).values('day').annotate(edits = Count('rc_id')).order_by()
    for item in qs:
        time_dic[item['day'].date()] = item['edits']
    writer = csv.writer(response)
    writer.writerow(['Date','Edits'])
    while earliest_date <= latest_date:
        if earliest_date in time_dic:
            temp = time_dic.pop(earliest_date)
            writer.writerow([earliest_date.strftime("%Y-%m-%d"), temp])
        else:
            writer.writerow([earliest_date.strftime("%Y-%m-%d"), 0])
        earliest_date = earliest_date + timedelta(days=1)
    
    return response