from datetime import datetime
from json import loads

from django.test import TestCase, RequestFactory

from hashtagsv2.hashtags.factories import HashtagFactory
from hashtagsv2.hashtags.models import Hashtag
from . import views

# Create your tests here.
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

	def test_time_csv_daily_view(self):
		factory = RequestFactory()
		data = {
			'query': 'test_hashtag1',
			'view_type': 'dailyTimeChart'
		}
		request = factory.get('/time_csv',data)
		response = views.time_csv(request)
		page_content = response.content
		
		# CSV should contain 5 lines - header plus 4 entries
		self.assertEqual(len(page_content.splitlines()), 5)

	def test_time_csv_monthly_view(self):
		for i in range(1,5):
			HashtagFactory(hashtag='test_hashtag4', rc_id=120+i, timestamp=datetime(2016,i,1+i))

		factory = RequestFactory()
		data = {
			'query': 'test_hashtag4',
			'view_type': 'monthlyTimeChart'
		}
		request = factory.get('/time_csv',data)
		response = views.time_csv(request)
		page_content = response.content
		
		# CSV should contain 5 lines - header plus 4 entries
		self.assertEqual(len(page_content.splitlines()), 5)

	def test_time_csv_yearly_view(self):
		for i in range(1,5):
			HashtagFactory(hashtag='test_hashtag5', rc_id=120+i, timestamp=datetime(2011+i,i,i+3))

		factory = RequestFactory()
		data = {
			'query': 'test_hashtag5',
			'view_type': 'yearlyTimeChart'
		}
		request = factory.get('/time_csv',data)
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
