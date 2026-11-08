"""Tests for issue #2416: text after inline style/link/meta/noscript is dropped.

The bug: LXMLWebScrapingStrategy._scrap removed style, link, meta and
noscript elements with lxml's remove(), which discards the element's tail
(the text that follows it inside the same parent). That text never reached
cleaned_html or the markdown.
"""

import pytest
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy


TAIL_HTML = """<html><body>
<p>Cargo text before.<style>.a{color:red}</style>The old warehouses stood on the quay.</p>
<p>First sentence ends here.<noscript><img src="x.png"></noscript>Second sentence follows the noscript block.</p>
<p>Before link element.<link rel="stylesheet" href="x.css">After link element text.</p>
<p>Before meta.<meta name="x" content="y">After meta text.</p>
</body></html>"""

NO_TAIL_HTML = """<html><body>
<p>Only text here.<style>.a{color:red}</style></p>
</body></html>"""

SIBLING_TAIL_HTML = """<html><body>
<p><b>Bold lead.</b><style>.a{color:red}</style>Tail after a sibling element.</p>
</body></html>"""


@pytest.fixture
def scraper():
    return LXMLWebScrapingStrategy()


class TestTailTextPreserved:
    @pytest.mark.parametrize(
        "probe",
        [
            "The old warehouses stood on the quay",
            "Second sentence follows the noscript block",
            "After link element text",
            "After meta text",
        ],
    )
    def test_text_after_removed_tag_is_kept(self, scraper, probe):
        result = scraper._scrap(url="raw://test", html=TAIL_HTML)
        assert result is not None
        cleaned = result.get("cleaned_html", "")
        assert probe in cleaned

    def test_removed_tag_content_is_gone(self, scraper):
        result = scraper._scrap(url="raw://test", html=TAIL_HTML)
        cleaned = result.get("cleaned_html", "")
        assert "color:red" not in cleaned
        assert "<style" not in cleaned
        assert "<link" not in cleaned
        assert "<meta" not in cleaned
        assert "<noscript" not in cleaned

    def test_text_before_removed_tag_is_kept(self, scraper):
        result = scraper._scrap(url="raw://test", html=TAIL_HTML)
        cleaned = result.get("cleaned_html", "")
        assert "Cargo text before." in cleaned

    def test_removed_tag_without_tail_keeps_parent_text(self, scraper):
        result = scraper._scrap(url="raw://test", html=NO_TAIL_HTML)
        cleaned = result.get("cleaned_html", "")
        assert "Only text here." in cleaned
        assert "color:red" not in cleaned

    def test_tail_attaches_after_previous_sibling(self, scraper):
        result = scraper._scrap(url="raw://test", html=SIBLING_TAIL_HTML)
        cleaned = result.get("cleaned_html", "")
        assert "Bold lead." in cleaned
        assert "Tail after a sibling element." in cleaned
