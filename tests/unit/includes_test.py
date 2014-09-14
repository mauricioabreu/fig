import os.path

import mock
from .. import unittest

from fig.includes import (
    fetch_external_config,
    get_project_from_file,
    normalize_url,
)
from fig.service import ConfigError


class NormalizeUrlTest(unittest.TestCase):

    def test_normalize_url_with_scheme(self):
        url = normalize_url('HTTPS://example.com')
        self.assertEqual(url.scheme, 'https')

    def test_normalize_url_without_scheme(self):
        url = normalize_url('./path/to/somewhere')
        self.assertEqual(url.scheme, 'file')


class FetchExternalConfigTest(unittest.TestCase):

    def test_unsupported_scheme(self):
        with self.assertRaises(ConfigError) as exc:
            fetch_external_config(normalize_url("bogus://something"), None)
        self.assertIn("bogus", str(exc.exception))            

    def test_fetch_from_file(self):
        url = "./tests/fixtures/external-includes-figfile/fig.yml"
        config = fetch_external_config(normalize_url(url), None)
        self.assertEqual(
            set(config.keys()),
            set(['db', 'webapp', 'project-config']))


class GetProjectFromFileWithNormalizeUrlTest(unittest.TestCase):

    def setUp(self):
        self.expected = set(['db', 'webapp', 'project-config'])
        self.path = "tests/fixtures/external-includes-figfile/fig.yml"

    def test_fetch_from_file_relative_no_context(self):
        config = get_project_from_file(normalize_url(self.path))
        self.assertEqual(set(config.keys()), self.expected)

    def test_fetch_from_file_relative_with_context(self):
        url = './' + self.path
        config = get_project_from_file(normalize_url(url))
        self.assertEqual(set(config.keys()), self.expected)

    def test_fetch_from_file_absolute_path(self):
        url = os.path.abspath(self.path)
        config = get_project_from_file(normalize_url(url))
        self.assertEqual(set(config.keys()), self.expected)

    def test_fetch_from_file_relative_with_scheme(self):
        url = 'file://./' + self.path
        config = get_project_from_file(normalize_url(url))
        self.assertEqual(set(config.keys()), self.expected)

    def test_fetch_from_file_absolute_with_scheme(self):
        url = 'file://' + os.path.abspath(self.path)
        config = get_project_from_file(normalize_url(url))
        self.assertEqual(set(config.keys()), self.expected)

