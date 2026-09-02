from datetime import datetime
from mock import patch
from json import loads

import requests

from django.urls import reverse
from django.test import TestCase, RequestFactory

from .factories import HashtagFactory
from .models import Hashtag
from .helpers import split_hashtags
from . import views


def all_revisions_visible(domain, rev_ids):
    """Stand in for the API, reporting every revision asked about as public."""
    return {
        "query": {
            "pages": [
                {"revisions": [{"revid": rev_id} for rev_id in rev_ids]},
            ]
        }
    }


class HomepageTest(TestCase):
    @classmethod
    def setUp(cls):
        pass

    def tearDown(self):
        super(HomepageTest, self).tearDown()

    def test_homepage_no_data(self):
        """
        Test that the Hashtags homepage loads successfully
        when there is no data in the database.
        """
        url = reverse("index")
        factory = RequestFactory()

        request = factory.get(url)
        response = views.Index.as_view()(request)

        self.assertEqual(response.status_code, 200)


class HashtagSearchTest(TestCase):
    @classmethod
    def setUp(cls):
        # Create two sets of 5 hashtag entries
        for hashtag_text in ["hashtag1", "hashtag2"]:
            for i in range(5):
                _ = HashtagFactory(hashtag=hashtag_text)

        cls.project_hashtag = HashtagFactory(
            hashtag="hashtag3", domain="fr.wikipedia.org"
        )

        cls.date_hashtag = HashtagFactory(
            hashtag="hashtag4",
            domain="ja.wikipedia.org",
            timestamp=datetime(2017, 6, 1),
        )

        cls.user_hashtag = HashtagFactory(
            hashtag="hashtag5", domain="en.wikipedia.org", username="xyz"
        )

        cls.message_patcher = patch("hashtagsv2.hashtags.views.messages.add_message")
        cls.message_patcher.start()

        # Results are checked against the wiki before they are displayed, so
        # stop the tests from calling out to the API. See T277832.
        cls.visibility_patcher = patch(
            "hashtagsv2.hashtags.visibility._query_wiki",
            side_effect=all_revisions_visible,
        )
        cls.visibility_patcher.start()

    @classmethod
    def setUpClass(cls):
        super(HashtagSearchTest, cls).setUpClass()
        cls.url = reverse("index")
        cls.download_url = reverse("csv_download")

    def tearDown(self):
        super(HashtagSearchTest, self).tearDown()
        self.message_patcher.stop()
        self.visibility_patcher.stop()

    def test_split_hashtags1(self):
        """
        Test that split_hashtags method gives correct results
        """
        input_string = "hashtag1, hashtag2"
        expected_list = ["hashtag1", "hashtag2"]
        ans_list = split_hashtags(input_string)
        self.assertEqual(expected_list, ans_list)

    def test_split_hashtags2(self):
        """
        Test that split_hashtags method gives correct results when hashtags contains octothorpe.
        """
        input_string = "#hashtag1, #hashtag2"
        expected_list = ["hashtag1", "hashtag2"]
        ans_list = split_hashtags(input_string)
        self.assertEqual(expected_list, ans_list)

    def test_hashtags_search(self):
        """
        Make sure we can simply use the search.
        """
        factory = RequestFactory()

        data = {"query": "hashtag1"}

        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)

        self.assertEqual(response.status_code, 200)

    def test_hashtags_results(self):
        """
        Test that we receive the correct object list when
        searching with only a hashtag.
        """
        factory = RequestFactory()

        data = {"query": "hashtag1"}

        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)

        object_list = response.context_data["object_list"]

        self.assertEqual(len(object_list), 5)

    def test_hashtags_results_2(self):
        """
        Test that we receive the correct object list when
        searching with a hashtag and a project.
        """
        factory = RequestFactory()

        data = {"query": "hashtag3", "project": "fr.wikipedia.org"}

        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)

        object_list = response.context_data["object_list"]

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
            "query": "hashtag4",
            "project": "ja.wikipedia.org",
            "startdate": "2017-01-01",
            "enddate": "2018-01-01",
        }

        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)

        object_list = response.context_data["object_list"]

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

        data = {"query": "#hashtag4"}

        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)

        object_list = response.context_data["object_list"]

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
            "query": "hashtag4, hashtag3",
        }

        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)

        object_list = response.context_data["object_list"]

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

        data = {"query": "hashtag1"}

        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)
        page_content = response.render().content

        # We expect 10 table rows in total. 4 for the statistics at the
        # top of the page, 1 for the table header, and 5 entries.
        # This is a crappy way to test the page content but it works
        # for now.
        self.assertEqual(page_content.decode().count("<tr>"), 10)

    def test_hashtags_download_csv(self):
        """
        Make sure the CSV download works with just a hashtag
        """
        factory = RequestFactory()

        data = {"query": "hashtag1"}

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
            "query": "hashtag4",
            "project": "ja.wikipedia.org",
            "startdate": "2017-01-01",
            "enddate": "2018-01-01",
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

        data = {"query": "hashtag1"}

        request = factory.get(self.download_url, data)
        response = views.json_download(request)

        # decode and transform response back to JSON
        page_content = response.content.decode("utf-8")
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
            "query": "hashtag4",
            "project": "ja.wikipedia.org",
            "startdate": "2017-01-01",
            "enddate": "2018-01-01",
        }

        request = factory.get(self.download_url, data)
        response = views.json_download(request)

        # decode and transform response back to JSON
        page_content = response.content.decode("utf-8")
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

    def test_user_search(self):
        """
        Test that we receive the correct object list when
        searching with a hashtag and user.
        """
        factory = RequestFactory()

        data = {
            "query": "hashtag5",
            "user": "xyz",
        }

        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)

        object_list = response.context_data["object_list"]

        # We only get one result
        self.assertEqual(len(object_list), 1)
        # And it's the specific entry we're looking for
        self.assertEqual(object_list[0], self.user_hashtag.get_values_list())

    def test_and_or_search(self):
        """
        Test that we get the correct object list when search_type
        'and' is provided by user
        """
        # Two hashtags on one edit, so both rows share the edit's IDs.
        HashtagFactory(
            hashtag="hashtag_and_1",
            timestamp=datetime(2016, 1, 3),
            username="xyz",
            page_title="test",
            edit_summary="test_summary",
            rc_id=1234,
            rev_id=5678,
        )
        HashtagFactory(
            hashtag="hashtag_and_2",
            timestamp=datetime(2016, 1, 3),
            username="xyz",
            page_title="test",
            edit_summary="test_summary",
            rc_id=1234,
            rev_id=5678,
        )

        factory = RequestFactory()

        data = {"query": "hashtag_and_1, hashtag_and_2", "search_type": "and"}
        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)

        object_list = response.context_data["object_list"]

        # We get one result
        self.assertEqual(len(object_list), 1)
        # And it is the correct edit
        self.assertEqual(object_list[0].rc_id, 1234)

    def test_image_filter(self):
        """
        Test that we can filter by edits that introduce images.
        """
        HashtagFactory(hashtag="hashtag1", has_image=True, rc_id=1234)

        factory = RequestFactory()
        data = {
            "query": "hashtag1",
            "image": "on",
        }
        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)
        object_list = response.context_data["object_list"]

        # We get one result
        self.assertEqual(len(object_list), 1)
        # And it is the correct edit
        self.assertEqual(object_list[0].rc_id, 1234)

    def test_video_filter(self):
        """
        Same as above, for video.
        """
        HashtagFactory(hashtag="hashtag1", has_video=True, rc_id=1234)

        factory = RequestFactory()
        data = {
            "query": "hashtag1",
            "video": "on",
        }
        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)
        object_list = response.context_data["object_list"]

        # We get one result
        self.assertEqual(len(object_list), 1)
        # And it is the correct edit
        self.assertEqual(object_list[0].rc_id, 1234)

    def test_audio_filter(self):
        """
        Same as above, for audio.
        """
        HashtagFactory(hashtag="hashtag1", has_audio=True, rc_id=1234)

        factory = RequestFactory()
        data = {
            "query": "hashtag1",
            "audio": "on",
        }
        request = factory.get(self.url, data)
        response = views.Index.as_view()(request)
        object_list = response.context_data["object_list"]

        # We get one result
        self.assertEqual(len(object_list), 1)
        # And it is the correct edit
        self.assertEqual(object_list[0].rc_id, 1234)


class RevisionVisibilityTest(TestCase):
    """
    The wiki can hide an edit summary or a username after we record it, so
    results are checked before they are displayed. See T277832.
    """

    def setUp(self):
        self.url = reverse("index")
        self.factory = RequestFactory()
        self.message_patcher = patch("hashtagsv2.hashtags.views.messages.add_message")
        self.message_patcher.start()

    def tearDown(self):
        super(RevisionVisibilityTest, self).tearDown()
        self.message_patcher.stop()

    def _results(self, api_response):
        """Search for one hashtag, with the API replaced by a fixed answer."""
        with patch(
            "hashtagsv2.hashtags.visibility._query_wiki", return_value=api_response
        ):
            request = self.factory.get(self.url, {"query": "hashtag1"})
            response = views.Index.as_view()(request)
            return response.context_data["object_list"]

    def test_hidden_summary_removes_row(self):
        HashtagFactory(hashtag="hashtag1", rev_id=1, domain="en.wikipedia.org")
        object_list = self._results(
            {"query": {"pages": [{"revisions": [{"revid": 1, "commenthidden": True}]}]}}
        )
        self.assertEqual(len(object_list), 0)

    def test_suppressed_revision_removes_row(self):
        HashtagFactory(hashtag="hashtag1", rev_id=1, domain="en.wikipedia.org")
        object_list = self._results(
            {"query": {"pages": [{"revisions": [{"revid": 1, "suppressed": True}]}]}}
        )
        self.assertEqual(len(object_list), 0)

    def test_deleted_page_removes_row(self):
        HashtagFactory(hashtag="hashtag1", rev_id=1, domain="en.wikipedia.org")
        object_list = self._results({"query": {"badrevids": {"1": {"revid": 1}}}})
        self.assertEqual(len(object_list), 0)

    def test_hidden_username_removes_row(self):
        # We drop the row rather than blank the name, because the user search
        # filter still matches on the stored username.
        HashtagFactory(
            hashtag="hashtag1", rev_id=1, domain="en.wikipedia.org", username="xyz"
        )
        object_list = self._results(
            {"query": {"pages": [{"revisions": [{"revid": 1, "userhidden": True}]}]}}
        )
        self.assertEqual(len(object_list), 0)

    def test_api_error_response_removes_rows(self):
        # MediaWiki reports some errors with HTTP 200 and an error object.
        HashtagFactory(hashtag="hashtag1", rev_id=1, domain="en.wikipedia.org")
        object_list = self._results({"error": {"code": "badvalue"}})
        self.assertEqual(len(object_list), 0)

    def test_malformed_response_removes_rows(self):
        HashtagFactory(hashtag="hashtag1", rev_id=1, domain="en.wikipedia.org")
        object_list = self._results({"query": {"pages": "not a list"}})
        self.assertEqual(len(object_list), 0)

    def test_visible_revision_is_shown(self):
        HashtagFactory(
            hashtag="hashtag1", rev_id=1, domain="en.wikipedia.org", username="xyz"
        )
        object_list = self._results(
            {"query": {"pages": [{"revisions": [{"revid": 1}]}]}}
        )
        self.assertEqual(len(object_list), 1)
        self.assertEqual(object_list[0].username, "xyz")

    def test_row_with_no_revision_id_is_removed(self):
        # Log actions such as uploads have no revision ID, so we cannot check
        # them and must not show them.
        HashtagFactory(hashtag="hashtag1", rev_id=None, domain="en.wikipedia.org")
        object_list = self._results({"query": {"pages": []}})
        self.assertEqual(len(object_list), 0)

    def test_api_failure_removes_rows(self):
        HashtagFactory(hashtag="hashtag1", rev_id=1, domain="en.wikipedia.org")
        with patch(
            "hashtagsv2.hashtags.visibility._query_wiki",
            side_effect=requests.RequestException("boom"),
        ):
            request = self.factory.get(self.url, {"query": "hashtag1"})
            response = views.Index.as_view()(request)
            self.assertEqual(len(response.context_data["object_list"]), 0)

    def test_time_budget_stops_further_api_calls(self):
        # Results can span many wikis. We must stop before the gunicorn
        # worker times out, and not show what we did not check.
        HashtagFactory(hashtag="hashtag1", rev_id=1, domain="en.wikipedia.org")
        with patch("hashtagsv2.hashtags.visibility.API_TOTAL_BUDGET_S", -1):
            with patch("hashtagsv2.hashtags.visibility._query_wiki") as query:
                request = self.factory.get(self.url, {"query": "hashtag1"})
                response = views.Index.as_view()(request)
                self.assertEqual(len(response.context_data["object_list"]), 0)
                query.assert_not_called()
