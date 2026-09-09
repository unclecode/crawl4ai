"""Tests for post-processing when css_selector or target_elements is set.

The bug: _scrap() deep-copies the selector match into a new content_element,
then ran only_text, base64 image cleanup, empty-element removal and attribute
stripping, plus mermaid SVG replacement, style/link/meta/noscript/script
removal and form removal, against `body`. The copy is detached from `body`,
so none of those passes reached the HTML that is serialised into
cleaned_html: <b> survived only_text, inline style, onclick, data-* and whole
base64 payloads were emitted verbatim, and a <script>, <style>, <noscript> or
<form> inside the selection survived into cleaned_html untouched.
"""

import pytest
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

BASE64_SRC = "data:image/png;base64,AAAABBBBCCCCDDDD"

SAMPLE_HTML = f"""
<html>
<body>
    <div class="job" data-tracking="abc" style="color:red" onclick="track()">
        <p>We are hiring a backend engineer for the platform team.</p>
        <p>The stack is <b>Postgres</b> and <i>Python</i> in production.</p>
        <p>Apply through <a href="/apply">our form</a> before the deadline.</p>
        <img src="{BASE64_SRC}">
        <div class="tracker"></div>
        <style>.job {{ color: red; }}</style>
        <script>track();</script>
        <noscript>Enable JS to apply.</noscript>
    </div>
    <div class="sidebar">
        <p>More roles are listed on <a href="/jobs">the jobs page</a> today.</p>
    </div>
</body>
</html>
"""

COMMON = dict(url="raw://test", html=SAMPLE_HTML, only_text=True)

SELECTORS = [
    pytest.param({}, id="no-selector"),
    pytest.param({"css_selector": ".job"}, id="css_selector"),
    pytest.param({"target_elements": [".job"]}, id="target_elements"),
    pytest.param({"css_selector": "body", "target_elements": [".job"]}, id="both"),
]


@pytest.fixture
def scraper():
    return LXMLWebScrapingStrategy()


@pytest.mark.parametrize("selector", SELECTORS)
class TestPostProcessingRunsWithSelector:
    def test_only_text_unwraps_inline_tags(self, scraper, selector):
        """only_text should unwrap <b>/<i> whether or not a selector is set."""
        cleaned = scraper._scrap(**COMMON, **selector)["cleaned_html"]
        assert "<b>" not in cleaned
        assert "<i>" not in cleaned
        assert "Postgres" in cleaned
        assert "Python" in cleaned

    def test_base64_image_src_is_truncated(self, scraper, selector):
        """The base64 payload should never reach cleaned_html."""
        cleaned = scraper._scrap(**COMMON, **selector)["cleaned_html"]
        assert "base64" not in cleaned
        assert 'src=""' in cleaned

    def test_empty_elements_are_removed(self, scraper, selector):
        """The empty <div class="tracker"> should be dropped."""
        cleaned = scraper._scrap(**COMMON, **selector)["cleaned_html"]
        assert "tracker" not in cleaned

    def test_unwanted_attributes_are_stripped(self, scraper, selector):
        """style/onclick/data-* go, class/href stay."""
        cleaned = scraper._scrap(**COMMON, **selector)["cleaned_html"]
        assert "style=" not in cleaned
        assert "onclick=" not in cleaned
        assert "data-tracking" not in cleaned
        assert 'class="job"' in cleaned
        assert 'href="/apply"' in cleaned

    def test_style_script_noscript_are_removed(self, scraper, selector):
        """style/script/noscript inside the selection must not survive."""
        cleaned = scraper._scrap(**COMMON, **selector)["cleaned_html"]
        assert "<style>" not in cleaned
        assert "<script>" not in cleaned
        assert "<noscript>" not in cleaned
        assert "track()" not in cleaned
        assert "Enable JS to apply" not in cleaned


class TestPostProcessingBoundaries:
    def test_selector_without_match_still_post_processes(self, scraper):
        """A selector matching nothing falls back to the body, still cleaned."""
        cleaned = scraper._scrap(**COMMON, css_selector=".nonexistent")["cleaned_html"]
        assert "<b>" not in cleaned
        assert "onclick=" not in cleaned
        assert "the jobs page" in cleaned

    def test_single_inline_element_selected(self, scraper):
        """The shortest selection: one inline tag that only_text unwraps."""
        cleaned = scraper._scrap(**COMMON, css_selector="b")["cleaned_html"]
        assert "<b>" not in cleaned
        assert "Postgres" in cleaned

    def test_only_text_false_keeps_inline_tags(self, scraper):
        """Without only_text the inline tags stay, but attributes still go."""
        cleaned = scraper._scrap(
            url="raw://test", html=SAMPLE_HTML, css_selector=".job"
        )["cleaned_html"]
        assert "<b>Postgres</b>" in cleaned
        assert "onclick=" not in cleaned

    def test_keep_data_attributes_with_selector(self, scraper):
        """keep_data_attributes still keeps data-* under a selector."""
        cleaned = scraper._scrap(
            **COMMON, css_selector=".job", keep_data_attributes=True
        )["cleaned_html"]
        assert 'data-tracking="abc"' in cleaned
        assert "onclick=" not in cleaned

    def test_selector_still_excludes_other_content(self, scraper):
        """Post-processing must not widen what the selector selected."""
        cleaned = scraper._scrap(**COMMON, css_selector=".job")["cleaned_html"]
        assert "We are hiring" in cleaned
        assert "the jobs page" not in cleaned

    def test_links_are_collected_from_the_whole_page(self, scraper):
        """Link extraction stays page-wide, not limited to the selection."""
        result = scraper._scrap(**COMMON, target_elements=[".job"])
        hrefs = {link["href"] for link in result["links"]["internal"]}
        assert any(href.endswith("/apply") for href in hrefs)
        assert any(href.endswith("/jobs") for href in hrefs)

    def test_form_inside_selection_is_removed(self, scraper):
        """remove_forms must reach a <form> inside the selected subtree."""
        html = SAMPLE_HTML.replace(
            '<div class="tracker"></div>',
            '<div class="tracker"></div><form><input name="apply"></form>',
        )
        cleaned = scraper._scrap(
            url="raw://test", html=html, css_selector=".job", remove_forms=True
        )["cleaned_html"]
        assert "<form>" not in cleaned
        assert "We are hiring" in cleaned
