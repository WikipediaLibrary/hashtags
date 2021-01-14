from django.utils import timezone
import factory
import random

from .models import Hashtag

class HashtagFactory(factory.django.DjangoModelFactory):

	class Meta:
		model = Hashtag
		strategy = factory.CREATE_STRATEGY

	hashtag = factory.Faker('word')
	domain = 'en.wikipedia.org'
	timestamp = timezone.now()
	username = factory.Faker('word')
	page_title = factory.Faker('word')
	edit_summary = factory.Faker('sentence')
	rc_id = random.randint(1,100000)
	has_image = False
	has_video = False
