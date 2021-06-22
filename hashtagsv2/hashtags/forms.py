from django import forms
from django.utils.translation import gettext as _

TYPE_CHOICES = [('or', 'or'), ('and', 'and')]

class DateInput(forms.DateInput):
	# Creating a custom widget because default DateInput doesn't use
	# input type="date"
	input_type = 'date'

class SearchForm(forms.Form):
	query = forms.CharField(label=_("Hashtag"),
		# Translators: Placeholder for the section of form where we ask user to specify a hashtag.
		widget=forms.TextInput(attrs={'placeholder': _('Enter a hashtag'),
			'style': 'width:100%'}))

	project = forms.CharField(required=False,
		# Translators: Label for the section of form where we ask user to specify a project.
		label= _("Project"),
		widget=forms.TextInput(attrs={'placeholder': 'en.wikisource.org',
			'style': 'width:100%'}))

	search_type = forms.CharField(required=False,
		# Translators: Label for the section of form where we ask user to specify the type of search.
		label= _("Type:"),
		widget=forms.Select(choices=TYPE_CHOICES))

	user = forms.CharField(required=False,
		# Translators: Label for the section of form where we ask user to enter a username.
		label= _("User:"),
		# Translators: Placeholder for the section of the form where we ask user to enter a username.
		widget=forms.TextInput(attrs={'placeholder': _('Enter username')}))

	startdate = forms.DateField(required=False,
		# Translators: Label for the section of form where we ask user to specify a initial date for search results.
		label= _("Start date:"),
		widget=DateInput())

	enddate = forms.DateField(required=False,
		# Translators: Label for the section of form where we ask user to specify the last date for search results.
		label= _("End date:"),
		widget=DateInput())

	image = forms.BooleanField(required=False,
		# Translators: Label for the section of form where we ask user whether to filter edits that introduce images.
		label= _("Edit adds image:"))

	video = forms.BooleanField(required=False,
		# Translators: Label for the section of form where we ask user whether to filter edits that introduce videos.
                label= _("Edit adds video:"))

	audio = forms.BooleanField(required=False,
		# Translators: Label for the section of form where we ask user whether to filter edits that introduce audio.
                label= _("Edit adds audio:"))
