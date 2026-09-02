"""
Regression tests for ``fast_urljoin`` root-absolute path handling.

``fast_urljoin`` previously appended a root-absolute href (``"/path"``) to the
full base URL instead of resolving it against base's ``scheme://authority``
root, so a link like ``/api`` on a crawled sub-page
``https://site/docs/guide.html`` became ``https://site/docs/guide.html/api``
instead of ``https://site/api``. These joins feed
``DefaultMarkdownGenerator.convert_links_to_citations``, so every root-absolute
link produced a broken citation/reference URL.

``fast_urljoin`` documents ``urllib.parse.urljoin`` as its fallback, so its
output for these cases must match ``urljoin``.
"""
from urllib.parse import urljoin

import pytest

from crawl4ai.markdown_generation_strategy import (
    DefaultMarkdownGenerator,
    fast_urljoin,
)

# (base, href) pairs that must all agree with urllib.parse.urljoin.
URLJOIN_PARITY_CASES = [
    # root-absolute href on a base that carries a path (the bug)
    ("https://example.com/docs/guide.html", "/api/reference"),
    ("https://example.com/a/b/c", "/x"),
    ("https://example.com:8080/docs/page", "/login"),
    ("https://example.com/docs/guide.html", "/a/b/c?x=1#frag"),
    ("https://sub.example.com/a/b?q=1#f", "/root"),
    # root-absolute href on a base that is just scheme://authority (already ok)
    ("https://example.com", "/api"),
    ("https://example.com/", "/api"),
    # non-root-absolute forms keep delegating to urljoin
    ("https://example.com/docs/", "rel/page"),
    ("https://example.com/docs/guide.html", "../up"),
    ("https://example.com/docs/guide.html", "sibling.html"),
]


class TestFastUrljoinRootAbsolute:
    @pytest.mark.parametrize("base, href", URLJOIN_PARITY_CASES)
    def test_matches_urljoin(self, base, href):
        assert fast_urljoin(base, href) == urljoin(base, href)

    def test_root_absolute_replaces_base_path(self):
        # The specific bug: a root-absolute link on a sub-page must not inherit
        # the sub-page's path.
        assert (
            fast_urljoin("https://example.com/docs/guide.html", "/api/reference")
            == "https://example.com/api/reference"
        )

    def test_absolute_and_special_schemes_unchanged(self):
        # Pre-existing fast paths must be preserved.
        assert fast_urljoin("https://example.com/p", "https://other.com/x") == "https://other.com/x"
        assert fast_urljoin("https://example.com/p", "mailto:a@b.com") == "mailto:a@b.com"

    def test_citations_use_corrected_urls(self):
        # End-to-end through the public markdown citation path.
        gen = DefaultMarkdownGenerator()
        md = "See the [API](/api/reference)."
        _, references = gen.convert_links_to_citations(
            md, base_url="https://example.com/docs/guide.html"
        )
        assert "https://example.com/api/reference" in references
        assert "guide.html/api" not in references
