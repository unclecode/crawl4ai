from crawl4ai.utils import normalize_url_for_deep_crawl, quick_extract_links

BASE = "https://example.com/"


def test_blank_valued_param_is_kept():
    assert normalize_url_for_deep_crawl("/report?download=", BASE) == "https://example.com/report?download="


def test_bare_param_is_kept():
    assert normalize_url_for_deep_crawl("/report?download", BASE) == "https://example.com/report?download="


def test_blank_param_not_collapsed_into_bare_path():
    assert normalize_url_for_deep_crawl("/report?download=", BASE) != normalize_url_for_deep_crawl("/report", BASE)


def test_repeated_param_keeps_blank_value():
    out = normalize_url_for_deep_crawl("/s?tag=&tag=python", BASE)
    assert out == "https://example.com/s?tag=&tag=python"


def test_tracking_params_still_removed():
    out = normalize_url_for_deep_crawl("/s?utm_source=x&ref=&q=", BASE)
    assert out == "https://example.com/s?q="


def test_quick_extract_links_keeps_distinct_links():
    html = '<a href="/report?download=">a</a><a href="/report">b</a>'
    hrefs = [l["href"] for l in quick_extract_links(html, BASE)["internal"]]
    assert hrefs == ["https://example.com/report?download=", "https://example.com/report"]
