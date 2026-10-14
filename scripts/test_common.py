import unittest

from common import is_canary


class IsCanaryTest(unittest.TestCase):
    def test_canary_event(self):
        self.assertTrue(is_canary({"meta": {"domain": "canary"}}))

    def test_normal_event(self):
        self.assertFalse(is_canary({"meta": {"domain": "en.wikipedia.org"}}))

    def test_missing_meta(self):
        self.assertFalse(is_canary({}))


if __name__ == "__main__":
    unittest.main()
