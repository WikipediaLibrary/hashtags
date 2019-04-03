from django import forms
from haystack.forms import SearchForm

from datetime import datetime
from datetime import timedelta

from logging import getLogger

logger = getLogger('django')


class DateInput(forms.DateInput):
	# Creating a custom widget because default DateInput doesn't use
	# input type="date"
	input_type = 'date'


class HashtagSearchForm(SearchForm):
	q = forms.CharField(label="Hashtag",
		widget=forms.TextInput(attrs={'placeholder': 'Enter a hashtag',
			'style': 'width:100%'}))

	project = forms.CharField(required=False,label="Project",
		widget=forms.TextInput(attrs={'placeholder': 'en.wikisource.org',
			'style': 'width:100%'}))

	startdate = forms.DateField(required=False, label="Start date:",
		widget=DateInput())
	enddate = forms.DateField(required=False, label="End date:",
		widget=DateInput())

	def search(self):
		sqs = super(HashtagSearchForm, self).search()

		if not self.is_valid():
			return self.no_query_found()

		if 'project' in self.cleaned_data:
			if self.cleaned_data['project']:
				sqs = sqs.filter(
					domain=self.cleaned_data['project'])

		if 'startdate' in self.cleaned_data:
			if self.cleaned_data['startdate']:
				sqs = sqs.filter(
					timestamp__gt=self.cleaned_data['startdate'])

		if 'enddate' in self.cleaned_data:
			if self.cleaned_data['enddate']:
				# Convert enddate to a datetime directly to ensure timedelta
				# works if the date comes in as a string.
				if type(self.cleaned_data['enddate']) == str:
					end_date = datetime.strptime(self.cleaned_data['enddate'], '%Y-%m-%d')
				else:
					end_date = self.cleaned_data['enddate']
				enddate_plus_one = end_date + timedelta(days=1)
				sqs = sqs.filter(
					timestamp__lt=enddate_plus_one)

		# We're using MySQL, which doesn't support DISTINCT ON, but we
		# want to allow multiple hashtags to be queried simultaneously while
		# not displaying the same edit more than once. We can achieve this
		# by using values_list() for every field except hashtag - each
		# other field is identical for the same edit, so we can use
		# distinct() successfully.
		# Note that this returns a Queryset of Rows, not Objects.
		# ordered_queryset = sqs.order_by(
		# 	'-timestamp').values_list(
		# 	'domain', 'timestamp', 'username', 'page_title', 'edit_summary',
		# 	'rc_id', 'rev_id',
		# 	named=True
		# ).distinct()

		# return ordered_queryset

		return sqs
