from datetime import datetime
from mock import patch
from json import loads

from django.urls import reverse
from django.test import TestCase, RequestFactory

from .factories import HashtagFactory
from .models import Hashtag
from . import views

class HashtagSearchTest(TestCase):
	@classmethod
	def setUp(self):
		# Create two sets of 5 hashtag entries
		for hashtag_text in ['hashtag1', 'hashtag2']:
			for i in range(5):
				_ = HashtagFactory(hashtag=hashtag_text)

		self.project_hashtag = HashtagFactory(
			hashtag='hashtag3',
			domain='fr.wikipedia.org')

		self.date_hashtag = HashtagFactory(
			hashtag='hashtag4',
			domain='ja.wikipedia.org',
			timestamp=datetime(2017,6,1))

		self.message_patcher = patch('hashtagsv2.hashtags.views.messages.add_message')
		self.message_patcher.start()

	@classmethod
	def setUpClass(cls):
		super(HashtagSearchTest, cls).setUpClass()
		cls.url = reverse('index')
		cls.download_url = reverse('csv_download')

	def tearDown(self):
		super(HashtagSearchTest, self).tearDown()
		self.message_patcher.stop()

	def test_hashtags_search(self):
		"""
		Make sure we can simply use the search.
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag1'
		}

		request = factory.get(self.url, data)
		response = views.Index.as_view()(request)

		self.assertEqual(response.status_code, 200)

	def test_hashtags_results(self):
		"""
		Test that we receive the correct object list when
		searching with only a hashtag.
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag1'
		}

		request = factory.get(self.url, data)
		response = views.Index.as_view()(request)

		object_list = response.context_data['object_list']

		self.assertEqual(object_list.count(), 5)

	def test_hashtags_results_2(self):
		"""
		Test that we receive the correct object list when
		searching with a hashtag and a project.
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag3',
			'project': 'fr.wikipedia.org'
		}

		request = factory.get(self.url, data)
		response = views.Index.as_view()(request)

		object_list = response.context_data['object_list']

		# We only get one result
		self.assertEqual(object_list.count(), 1)
		# And it's the specific entry we're looking for
		self.assertEqual(object_list[0], self.project_hashtag.get_values_list())

	def test_hashtags_results_3(self):
		"""
		Test that we receive the correct object list when
		searching with a hashtag, a project, and a date range.
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag4',
			'project': 'ja.wikipedia.org',
			'startdate': '2017-01-01',
			'enddate': '2018-01-01'
		}

		request = factory.get(self.url, data)
		response = views.Index.as_view()(request)

		object_list = response.context_data['object_list']

		# We only get one result
		self.assertEqual(object_list.count(), 1)
		# And it's the specific entry we're looking for
		self.assertEqual(object_list[0], self.date_hashtag.get_values_list())

	def test_hashtags_results_4(self):
		"""
		Test that we receive the correct object list when
		searching with a query that contains an octothorpe
		"""
		factory = RequestFactory()

		data = {
			'query': '#hashtag4'
		}

		request = factory.get(self.url, data)
		response = views.Index.as_view()(request)

		object_list = response.context_data['object_list']

		# We only get one result
		self.assertEqual(object_list.count(), 1)
		# And it's the specific entry we're looking for
		self.assertEqual(object_list[0], self.date_hashtag.get_values_list())

	def test_hashtags_results_5(self):
		"""
		Test that we receive the correct object list when
		searching for multiple hashtags
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag4, hashtag3',
		}

		request = factory.get(self.url, data)
		response = views.Index.as_view()(request)

		object_list = response.context_data['object_list']

		# We get two results
		self.assertEqual(object_list.count(), 2)
		# and they're the correct objects
		self.assertIn(self.date_hashtag.get_values_list(), object_list)
		self.assertIn(self.project_hashtag.get_values_list(), object_list)

	def test_hashtags_results_template(self):
		"""
		Test that only the hashtags we expect are listed in the
		results table.
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag1'
		}

		request = factory.get(self.url, data)
		response = views.Index.as_view()(request)
		page_content = response.render().content

		# We expect 10 table rows in total. 4 for the statistics at the
		# top of the page, 1 for the table header, and 5 entries.
		# This is a crappy way to test the page content but it works
		# for now.
		self.assertEqual(page_content.decode().count('<tr>'), 10)

	def test_hashtags_download_csv(self):
		"""
		Make sure the CSV download works with just a hashtag
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag1'
		}

		request = factory.get(self.download_url, data)
		response = views.csv_download(request)

		page_content = response.content

		# CSV should be presented successfully, and should contain
		# 6 lines - header plus 5 entries
		self.assertEqual(len(page_content.splitlines()), 6)

	def test_hashtags_download_json(self):
		"""
		Make sure the JSON download works with just a hashtag
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag1'
		}

		request = factory.get(self.download_url, data)
		response = views.json_download(request)

		#decode and transform response back to JSON
		page_content = response.content.decode('utf-8')
		json_content = loads(page_content)

		# JSON should contain 5 rows. Not sure though if this test
		# tests enough.
		self.assertEqual(len(json_content["Rows"]), 5)