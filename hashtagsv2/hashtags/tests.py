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
			HashtagFactory(hashtag='test_hashtag1', domain='en.wikipedia.org', username='a', rc_id=i, timestamp=datetime(2016,2,1))

		# 3 edits for project: 'fr.wikipedia.org' and username: 'b'
		for i in range(6,9):
			HashtagFactory(hashtag='test_hashtag1', domain='fr.wikipedia.org', username='b', rc_id=i, timestamp=datetime(2016,2,2))

		# 2 edits for project: 'es.wikipedia.org' and username: 'c'
		for i in range(9,11):
			HashtagFactory(hashtag='test_hashtag1', domain='es.wikipedia.org', username='c', rc_id=i, timestamp=datetime(2016,2,4))
	
	def test_top_project_statistics(self):
		# Test if top projects stats view is giving correct results
		factory = RequestFactory()

		data = {
			'query': 'test_hashtag1'
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
			'query': 'test_hashtag1'
		}
		request = factory.get('/api/top_user_stats', data)
		response = views.top_user_statistics_data(request)
		page_content = response.content.decode('utf-8')
		dict = loads(page_content)
		self.assertEqual(dict['usernames'], ['a', 'b', 'c'])
		self.assertEqual(dict['edits_per_user'], [5, 3, 2])

	def test_edits_over_days(self):
		# Test edits over days
		factory =  RequestFactory()
		
		data = {
			'query': 'test_hashtag1'
		}
		request = factory.get('/api/time_stats', data)
		response = views.time_statistics_data(request)
		page_content = response.content.decode('utf-8')
		dict = loads(page_content)
		self.assertEqual(dict['time_array'], ['2016-02-01', '2016-02-02', '2016-02-03', '2016-02-04'])
		self.assertEqual(dict['edits_array'], [5, 3, 0, 2])

	def test_edits_over_months(self):
		# Test edits over month
		for i in range(1,5):
			HashtagFactory(hashtag='test_hashtag2', rc_id=20+i, timestamp=datetime(2016,i,1))
		# Some more edits in same month
		HashtagFactory(hashtag='test_hashtag2', rc_id=1234, timestamp=datetime(2016,1,3))
		HashtagFactory(hashtag='test_hashtag2', rc_id=12345, timestamp=datetime(2016,1,3))
		HashtagFactory(hashtag='test_hashtag2', rc_id=123, timestamp=datetime(2016,3,7))

		factory =  RequestFactory()
		
		data = {
			'query': 'test_hashtag2'
		}
		request = factory.get('/api/time_stats', data)
		response = views.time_statistics_data(request)
		page_content = response.content.decode('utf-8')
		dict = loads(page_content)
		self.assertEqual(dict['time_array'], ['Jan-2016', 'Feb-2016', 'Mar-2016', 'Apr-2016'])
		self.assertEqual(dict['edits_array'], [3, 1, 2, 1])

	def test_edits_over_years(self):
		# Test edits over years
		for i in range(1,5):
			HashtagFactory(hashtag='test_hashtag3', rc_id=20+i, timestamp=datetime(2015+i,2,1))
		# More edits in same year
		HashtagFactory(hashtag='test_hashtag3', rc_id=1234, timestamp=datetime(2016,1,3))
		HashtagFactory(hashtag='test_hashtag3', rc_id=12345, timestamp=datetime(2017,5,3))
		HashtagFactory(hashtag='test_hashtag3', rc_id=123, timestamp=datetime(2017,5,3))

		factory =  RequestFactory()
		
		data = {
			'query': 'test_hashtag3'
		}
		request = factory.get('/api/time_stats', data)
		response = views.time_statistics_data(request)
		page_content = response.content.decode('utf-8')
		dict = loads(page_content)
		self.assertEqual(dict['time_array'], ['2016', '2017', '2018', '2019'])
		self.assertEqual(dict['edits_array'], [2, 3, 1, 1])

	def test_users_csv_view(self):
		factory = RequestFactory()
		
		data = {
			'query': 'test_hashtag1'
		}
		request = factory.get('/users_csv', data)
		response = views.users_csv(request)
		page_content = response.content

		# CSV should contain 4 lines - header plus 3 entries
		self.assertEqual(len(page_content.splitlines()), 4)

	def test_projects_csv_view(self):
		factory = RequestFactory()
		
		data = {
			'query': 'test_hashtag1'
		}
		request = factory.get('/projects_csv', data)
		response = views.projects_csv(request)
		page_content = response.content

		# CSV should contain 4 lines - header plus 3 entries
		self.assertEqual(len(page_content.splitlines()), 4)

	def test_time_csv_view(self):
		factory = RequestFactory()
		
		data = {
			'query': 'test_hashtag1'
		}
		request = factory.get('/time_csv', data)
		response = views.time_csv(request)
		page_content = response.content

		# CSV should contain 5 lines - header plus 4 entries
		self.assertEqual(len(page_content.splitlines()), 5)

	def test_all_users(self):
		# Test if All_users_view is giving correct results
		factory = RequestFactory()

		data = {
			'query': 'test_hashtag1'
		}
		request = factory.get('/all_users', data)
		response = views.All_users_view.as_view()(request)
		user_list = list(response.context_data['users_list'])
		test_users_list = [
			{'edits': 5, 'username': 'a'},
			{'edits': 3, 'username': 'b'},
			{'edits': 2, 'username': 'c'}
		]
		self.assertEqual(user_list, test_users_list)

	def test_all_projects(self):
		# Test if All_projects_view is giving correct results
		factory = RequestFactory()

		data = {
			'query': 'test_hashtag1'
		}
		request = factory.get('/all_projects', data)
		response = views.All_projects_view.as_view()(request)
		project_list = list(response.context_data['projects_list'])
		test_projects_list = [
			{'edits': 5, 'domain': 'en.wikipedia.org'},
			{'edits': 3, 'domain': 'fr.wikipedia.org'},
			{'edits': 2, 'domain': 'es.wikipedia.org'}
		]
		self.assertEqual(project_list, test_projects_list)