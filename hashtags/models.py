from django.db import models
from django.utils.translation import ugettext_lazy as _

class Hashtag(models.Model):
	"""
	Hashtags model, based on the db schema for the original hashtags tool.
	We should always be gathering every piece of the model - edit summary
	is optional, but we shouldn't be logging anything with no summary.
	"""
	hashtag = models.CharField(max_length=128)

	# Hashtags v1 only recorded language Wikipedia project. Recording
	# the entire domain allows us to track edits to other projects too.
	domain = models.CharField(max_length=32)

	timestamp = models.DateTimeField()
	username = models.CharField(max_length=255)
	page_title = models.CharField(max_length=255)

	# Per https://meta.wikimedia.org/wiki/Help:Edit_summary, summaries
	# have a maximum possible length of 800 characters.
	edit_summary = models.CharField(max_length=800)
	diff_id = models.PositiveIntegerField()