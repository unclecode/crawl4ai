import os

from crawl4ai.utils import get_home_folder, normalize_url


def test_get_home_folder(monkeypatch, tmp_path):
    base_dir = tmp_path / "custom_base"
    monkeypatch.setenv("CRAWL4_AI_BASE_DIRECTORY", str(base_dir))

    home_folder = get_home_folder()
    assert home_folder == f"{base_dir}/.crawl4ai"
    assert os.path.exists(home_folder)
    assert os.path.exists(f"{home_folder}/cache")
    assert os.path.exists(f"{home_folder}/models")

class TestNormalizeUrl:
    def test_relative_path_href(self):
        assert normalize_url("path/to/page.html", "http://example.com/base/") == "http://example.com/base/path/to/page.html"

    def test_base_url_without_trailing_slash(self):
        assert normalize_url("page.html", "http://example.com/base") == "http://example.com/page.html"

    def test_absolute_url_as_href(self):
        assert normalize_url("http://another.com/page.html", "http://example.com/") == "http://another.com/page.html"

    def test_leading_trailing_spaces(self):
        assert normalize_url("  page.html  ", "http://example.com/") == "http://example.com/page.html"

    def test_href_with_query_parameters(self):
        assert normalize_url("page.html?query=test", "http://example.com/") == "http://example.com/page.html?query=test"

    def test_parent_directory_in_href(self):
        assert normalize_url("../otherpage.html", "http://example.com/base/current/") == "http://example.com/base/otherpage.html"

    def test_root_relative_href(self):
        assert normalize_url("/otherpage.html", "http://example.com/base/current/") == "http://example.com/otherpage.html"

    def test_href_is_only_query(self):
        assert normalize_url("?query=true", "http://example.com/page.html") == "http://example.com/page.html?query=true"

    def test_href_with_special_characters(self):
        assert normalize_url("path with spaces/file.html", "http://example.com/") == "http://example.com/path%20with%20spaces/file.html"