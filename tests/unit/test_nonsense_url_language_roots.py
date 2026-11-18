"""Regression test for ``AsyncUrlSeeder._is_nonsense_url`` language roots.

The "very short path" filter measured length on the slash-stripped path but
matched the *un-stripped* path against the language-root whitelist, so the
canonical trailing-slash form (e.g. ``/en/``) was dropped as nonsense even
though ``/en`` was kept.
"""
import sys
from types import SimpleNamespace

import pytest

# Avoid the optional rank_bm25 dependency at import time (mirrors the sibling
# unit test); _is_nonsense_url itself does not use BM25.
sys.modules.setdefault("rank_bm25", SimpleNamespace(BM25Okapi=object))

from crawl4ai.async_url_seeder import AsyncUrlSeeder


@pytest.fixture
def seeder():
    # _is_nonsense_url only uses its url argument (no instance state), so it is
    # safe to bypass __init__.
    return AsyncUrlSeeder.__new__(AsyncUrlSeeder)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/en",
        "https://example.com/en/",   # the bug: canonical trailing-slash form
        "https://example.com/de/",
        "https://example.com/fr/",
        "https://example.com/es/",
        "https://example.com/it/",
        "https://example.com/",
        "https://example.com/about",
    ],
)
def test_language_roots_are_not_filtered(seeder, url):
    assert seeder._is_nonsense_url(url) is False


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/ab/",   # genuinely short, non-language path
        "https://example.com/x",
        "https://example.com/robots.txt",
    ],
)
def test_short_junk_and_utility_still_filtered(seeder, url):
    assert seeder._is_nonsense_url(url) is True
