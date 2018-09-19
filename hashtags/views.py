from datetime import datetime, timedelta

from django.urls import reverse_lazy
from django.db.models import Count
from django.shortcuts import render
from django.views.generic import FormView, ListView

from .forms import SearchForm
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

		return context

	def get_queryset(self):
		form = self.form_class(self.request.GET)
		if form.is_valid():
			form_data = form.cleaned_data
			search_queryset = Hashtag.objects.filter(hashtag=form_data['query'])

			if form_data['project']:
				search_queryset = search_queryset.filter(
					domain=form_data['project'])
			if form_data['startdate']:
				search_queryset = search_queryset.filter(
					timestamp__gt=form_data['startdate'])
			if form_data['enddate']:
				search_queryset = search_queryset.filter(
					timestamp__lt=form_data['enddate'])

			return search_queryset.order_by('-timestamp')

		# We're mixing forms and listview; paginate_by expects to always
		# have *something* to paginate, so we have to send back a list
		# if the form hasn't been filled yet.
		return []
