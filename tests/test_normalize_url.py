import unittest
from crawl4ai.utils import normalize_url

class TestNormalizeUrl(unittest.TestCase):

    def test_basic_relative_path(self):
        self.assertEqual(normalize_url("path/to/page.html", "http://example.com/base/"), "http://example.com/base/path/to/page.html")

    def test_base_url_with_trailing_slash(self):
        self.assertEqual(normalize_url("page.html", "http://example.com/base/"), "http://example.com/base/page.html")

    def test_base_url_without_trailing_slash(self):
        # If normalize_url correctly uses urljoin, "base" is treated as a file.
        self.assertEqual(normalize_url("page.html", "http://example.com/base"), "http://example.com/page.html")

    def test_absolute_url_as_href(self):
        self.assertEqual(normalize_url("http://another.com/page.html", "http://example.com/"), "http://another.com/page.html")

    def test_href_with_leading_trailing_spaces(self):
        self.assertEqual(normalize_url("  page.html  ", "http://example.com/"), "http://example.com/page.html")

    def test_empty_href(self):
        # urljoin with an empty href and base ending in '/' returns the base.
        self.assertEqual(normalize_url("", "http://example.com/base/"), "http://example.com/base/")
        # urljoin with an empty href and base not ending in '/' also returns base.
        self.assertEqual(normalize_url("", "http://example.com/base"), "http://example.com/base")

    def test_href_with_query_parameters(self):
        self.assertEqual(normalize_url("page.html?query=test", "http://example.com/"), "http://example.com/page.html?query=test")

    def test_href_with_fragment(self):
        self.assertEqual(normalize_url("page.html#section", "http://example.com/"), "http://example.com/page.html#section")

    def test_different_scheme_in_href(self):
        self.assertEqual(normalize_url("https://secure.example.com/page.html", "http://example.com/"), "https://secure.example.com/page.html")

    def test_parent_directory_in_href(self):
        self.assertEqual(normalize_url("../otherpage.html", "http://example.com/base/current/"), "http://example.com/base/otherpage.html")

    def test_root_relative_href(self):
        self.assertEqual(normalize_url("/otherpage.html", "http://example.com/base/current/"), "http://example.com/otherpage.html")

    def test_base_url_with_path_and_no_trailing_slash(self):
        # If normalize_url correctly uses urljoin, "path" is treated as a file.
        self.assertEqual(normalize_url("file.html", "http://example.com/path"), "http://example.com/file.html")

    def test_base_url_is_just_domain(self):
        self.assertEqual(normalize_url("page.html", "http://example.com"), "http://example.com/page.html")

    def test_href_is_only_query(self):
        self.assertEqual(normalize_url("?query=true", "http://example.com/page.html"), "http://example.com/page.html?query=true")

    def test_href_is_only_fragment(self):
        self.assertEqual(normalize_url("#fragment", "http://example.com/page.html"), "http://example.com/page.html#fragment")

    def test_relative_link_from_base_file_url(self):
        """
        Tests the specific bug report: relative links from a base URL that is a file.
        Example:
        Page URL: http://example.com/path/to/document.html
        Link on page: <a href="./file.xlsx">
        Expected: http://example.com/path/to/file.xlsx
        """
        base_url_file = "http://example.com/zwgk/fdzdgk/zdxx/spaq/t19360680.shtml"
        href_relative_current_dir = "./P020241203375994691134.xlsx"
        expected_url1 = "http://example.com/zwgk/fdzdgk/zdxx/spaq/P020241203375994691134.xlsx"
        self.assertEqual(normalize_url(href_relative_current_dir, base_url_file), expected_url1)

        # Test with a relative link that doesn't start with "./"
        href_relative_no_dot_slash = "another.doc"
        expected_url2 = "http://example.com/zwgk/fdzdgk/zdxx/spaq/another.doc"
        self.assertEqual(normalize_url(href_relative_no_dot_slash, base_url_file), expected_url2)

    def test_invalid_base_url_scheme(self):
        with self.assertRaises(ValueError) as context:
            normalize_url("page.html", "ftp://example.com/")
        self.assertIn("Invalid base URL format", str(context.exception))

    def test_invalid_base_url_netloc(self):
        with self.assertRaises(ValueError) as context:
            normalize_url("page.html", "http:///path/")
        self.assertIn("Invalid base URL format", str(context.exception))
        
    def test_base_url_with_port(self):
        self.assertEqual(normalize_url("path/file.html", "http://example.com:8080/base/"), "http://example.com:8080/base/path/file.html")

    def test_href_with_special_characters(self):
        self.assertEqual(normalize_url("path%20with%20spaces/file.html", "http://example.com/"), "http://example.com/path%20with%20spaces/file.html")

if __name__ == '__main__':
    unittest.main()