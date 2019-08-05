from django import forms
from django.utils.translation import gettext as _

TYPE_CHOICES = [('or', 'or'), ('and', 'and')]

class DateInput(forms.DateInput):
	# Creating a custom widget because default DateInput doesn't use
	# input type="date"
	input_type = 'date'

class SearchForm(forms.Form):
	query = forms.CharField(label=_("Hashtag"),
		widget=forms.TextInput(attrs={'placeholder': _('Enter a hashtag'),
			'style': 'width:100%'}))

	project = forms.CharField(required=False,label= _("Project"),
		widget=forms.TextInput(attrs={'placeholder': 'en.wikisource.org',
			'style': 'width:100%'}))

	search_type = forms.CharField(required=False, label= _("Type:"),
		widget=forms.Select(choices=TYPE_CHOICES))

	user = forms.CharField(required=False, label= _("User:"),
		widget=forms.TextInput(attrs={'placeholder': _('Enter username')}))

	startdate = forms.DateField(required=False, label= _("Start date:"),
		widget=DateInput())
	enddate = forms.DateField(required=False, label= _("End date:"),
		widget=DateInput())