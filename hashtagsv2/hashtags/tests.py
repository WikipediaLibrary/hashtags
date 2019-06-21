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

		self.assertEqual(len(object_list), 5)

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
		self.assertEqual(len(object_list), 1)
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
		self.assertEqual(len(object_list), 1)
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
		self.assertEqual(len(object_list), 1)
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
		self.assertEqual(len(object_list), 2)
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

	def test_hashtags_download_csv_full_query(self):
		"""
		Make sure the CSV download works with a full query
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag4',
			'project': 'ja.wikipedia.org',
			'startdate': '2017-01-01',
			'enddate': '2018-01-01'
		}

		request = factory.get(self.download_url, data)
		response = views.csv_download(request)

		page_content = response.content

		# CSV should be presented successfully, and should contain
		# 2 lines - header plus 1 entry
		self.assertEqual(len(page_content.splitlines()), 2)

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

	def test_hashtags_download_json_full_query(self):
		"""
		Make sure the JSON download works with a full query
		"""
		factory = RequestFactory()

		data = {
			'query': 'hashtag4',
			'project': 'ja.wikipedia.org',
			'startdate': '2017-01-01',
			'enddate': '2018-01-01'
		}

		request = factory.get(self.download_url, data)
		response = views.json_download(request)

		#decode and transform response back to JSON
		page_content = response.content.decode('utf-8')
		json_content = loads(page_content)

		# JSON should contain 1 row. Not sure though if this test
		# tests enough.
		self.assertEqual(len(json_content["Rows"]), 1)

	def test_no_hashtags(self):
		"""
		On first setup, the tool has nothing in the database.
		This shouldn't result in a homepage server error.
		"""

		# Clear the database of hashtag objects
		Hashtag.objects.all().delete()

		factory = RequestFactory()

		request = factory.get(self.url)
		response = views.Index.as_view()(request)

		self.assertEqual(response.status_code, 200)

class StatisticsTest(TestCase):
	def setUp(self):
		# 5 edits for project: 'en.wikipedia.org' and username: 'a'
		for i in range(1,6):
			HashtagFactory(hashtag='test_hashtag', domain='en.wikipedia.org', username='a', rc_id=i)

		# 3 edits for project: 'fr.wikipedia.org' and username: 'b'
		for i in range(6,9):
			HashtagFactory(hashtag='test_hashtag', domain='fr.wikipedia.org', username='b', rc_id=i)

		# 2 edits for project: 'es.wikipedia.org' and username: 'c'
		for i in range(9,11):
			HashtagFactory(hashtag='test_hashtag', domain='es.wikipedia.org', username='c', rc_id=i)
	
	def test_top_project_statistics(self):
		# Test if top projects stats view is giving correct results
		factory = RequestFactory()

		data = {
			'query': 'test_hashtag'
		}
		request = factory.get('/api/top_project_stats', data)
		response = views.top_project_statistics_data(request)
		page_content = response.content.decode('utf-8')
		dict = loads(page_content)
		self.assertEqual(dict['projects'], ['en.wikipedia.org', 'fr.wikipedia.org', 'es.wikipedia.org'])
		self.assertEqual(dict['edits_per_project'], [5, 3, 2])

	def test_top_user_statistics(self):
		# Test if top user stats view is giving correct results
		factory = RequestFactory()

		data = {
			'query': 'test_hashtag'
		}

		request = factory.get('/api/top_user_stats', data)
		response = views.top_user_statistics_data(request)
		page_content = response.content.decode('utf-8')
		dict = loads(page_content)
		self.assertEqual(dict['usernames'], ['a', 'b', 'c'])
		self.assertEqual(dict['edits_per_user'], [5, 3, 2])