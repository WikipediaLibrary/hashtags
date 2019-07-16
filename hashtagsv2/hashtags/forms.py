from django import forms

class DateInput(forms.DateInput):
	# Creating a custom widget because default DateInput doesn't use
	# input type="date"
	input_type = 'date'

class SearchForm(forms.Form):
	query = forms.CharField(label="Hashtag",
		widget=forms.TextInput(attrs={'placeholder': 'Enter a hashtag',
			'style': 'width:100%'}))

	project = forms.CharField(required=False,label="Project",
		widget=forms.TextInput(attrs={'placeholder': 'en.wikisource.org',
			'style': 'width:100%'}))

	user = forms.CharField(required=False, label="User",
		widget=forms.TextInput(attrs={'placeholder': 'Enter username'}))

	startdate = forms.DateField(required=False, label="Start date:",
		widget=DateInput())
	enddate = forms.DateField(required=False, label="End date:",
		widget=DateInput())