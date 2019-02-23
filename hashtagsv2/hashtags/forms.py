from django import forms

TYPE_CHOICES = [('or', 'or'), ('and', 'and')]

class DateInput(forms.DateInput):
	# Creating a custom widget because default DateInput doesn't use
	# input type="date"
	input_type = 'date'

class SearchForm(forms.Form):
	query = forms.CharField(label="Hashtag",
		widget=forms.TextInput(attrs={'placeholder': 'Enter a hashtag',
			'style': 'width:100%'}))

	type = forms.CharField(label="Type",
		widget=forms.Select(choices=TYPE_CHOICES))

	project = forms.CharField(required=False,label="Project",
		widget=forms.TextInput(attrs={'placeholder': 'en.wikisource.org',
			'style': 'width:100%'}))

	startdate = forms.DateField(required=False, label="Start date:",
		widget=DateInput())
	enddate = forms.DateField(required=False, label="End date:",
		widget=DateInput())