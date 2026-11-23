"""URLPatternFilter must keep its stats and its cache independent.

``apply()`` was wrapped in a module-level ``lru_cache``, so a repeated URL returned
the memoised verdict without touching the counters: after filtering 10 000 URLs a
filter could report ``total_urls == 1``. The same cache also held a strong reference
to ``self`` as part of the key, so filter instances created per crawl were never
released.
"""

import pytest

from crawl4ai.deep_crawling.filters import URLPatternFilter


@pytest.mark.parametrize(
    "patterns,url,expected",
    [
        ("*/blog/*", "https://example.com/blog/post", True),
        ("*/blog/*", "https://example.com/about", False),
        ("*.html", "https://example.com/a.html", True),
        ("/docs/*", "https://example.com/docs/intro", True),
        # A prefix pattern also matches the bare prefix: "/docs/*" -> "/docs".
        ("/docs/*", "https://example.com/docs", True),
    ],
)
def test_verdicts_are_unchanged(patterns, url, expected):
    assert URLPatternFilter(patterns).apply(url) is expected


def test_repeated_urls_are_counted_every_time():
    filter_ = URLPatternFilter("*/blog/*")

    for _ in range(3):
        assert filter_.apply("https://example.com/blog/a") is True

    assert filter_.stats.total_urls == 3
    assert filter_.stats.passed_urls == 3
    assert filter_.stats.rejected_urls == 0


def test_reverse_still_flips_the_verdict_and_is_counted():
    filter_ = URLPatternFilter("*/blog/*", reverse=True)

    assert filter_.apply("https://example.com/blog/a") is False
    assert filter_.apply("https://example.com/blog/a") is False
    assert filter_.apply("https://example.com/about") is True

    assert filter_.stats.total_urls == 3
    assert filter_.stats.rejected_urls == 2
    assert filter_.stats.passed_urls == 1


def test_cache_is_per_instance():
    blocked = URLPatternFilter("*/blog/*")
    other = URLPatternFilter("*/docs/*")

    blocked.apply("https://example.com/blog/a")

    assert other.apply("https://example.com/blog/a") is False
    assert other.stats.total_urls == 1
