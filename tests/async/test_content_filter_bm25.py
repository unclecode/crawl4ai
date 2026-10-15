import os, sys
import pytest
from bs4 import BeautifulSoup

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.content_filter_strategy import BM25ContentFilter


@pytest.fixture
def basic_html():
    return """
    <html>
        <head>
            <title>Test Article</title>
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, keywords">
        </head>
        <body>
            <h1>Main Heading</h1>
            <article>
                <p>This is a long paragraph with more than fifty words. It continues with more text to ensure we meet the minimum word count threshold. We need to make sure this paragraph is substantial enough to be considered for extraction according to our filtering rules. This should be enough words now.</p>
                <div class="navigation">Skip this nav content</div>
            </article>
        </body>
    </html>
    """


@pytest.fixture
def wiki_html():
    return """
    <html>
        <head>
            <title>Wikipedia Article</title>
        </head>
        <body>
            <h1>Article Title</h1>
            <h2>Section 1</h2>
            <p>Short but important section header description.</p>
            <div class="content">
                <p>Long paragraph with sufficient words to meet the minimum threshold. This paragraph continues with more text to ensure we have enough content for proper testing. We need to make sure this has enough words to pass our filters and be considered valid content for extraction purposes.</p>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def no_meta_html():
    return """
    <html>
        <body>
            <h1>Simple Page</h1>
            <p>First paragraph that should be used as fallback for query when no meta tags exist. This text needs to be long enough to serve as a meaningful fallback for our content extraction process.</p>
        </body>
    </html>
    """


class TestBM25ContentFilter:
    def test_basic_extraction(self, basic_html):
        """Test basic content extraction functionality"""
        filter = BM25ContentFilter()
        contents = filter.filter_content(basic_html)

        assert contents, "Should extract content"
        assert len(contents) >= 1, "Should extract at least one content block"
        assert "long paragraph" in " ".join(contents).lower()
        assert "navigation" not in " ".join(contents).lower()

    def test_user_query_override(self, basic_html):
        """Test that user query overrides metadata extraction"""
        user_query = "specific test query"
        filter = BM25ContentFilter(user_query=user_query)

        # Access internal state to verify query usage
        soup = BeautifulSoup(basic_html, "lxml")
        extracted_query = filter.extract_page_query(soup.find("head"))

        assert extracted_query == user_query
        assert "Test description" not in extracted_query

    def test_header_extraction(self, wiki_html):
        """Test that headers are properly extracted despite length"""
        filter = BM25ContentFilter()
        contents = filter.filter_content(wiki_html)

        combined_content = " ".join(contents).lower()
        assert "section 1" in combined_content, "Should include section header"
        assert "article title" in combined_content, "Should include main title"

    def test_no_metadata_fallback(self, no_meta_html):
        """Test fallback behavior when no metadata is present"""
        filter = BM25ContentFilter()
        contents = filter.filter_content(no_meta_html)

        assert contents, "Should extract content even without metadata"
        assert "First paragraph" in " ".join(
            contents
        ), "Should use first paragraph content"

    def test_empty_input(self):
        """Test handling of empty input"""
        filter = BM25ContentFilter()
        assert filter.filter_content("") == []
        assert filter.filter_content(None) == []

    def test_malformed_html(self):
        """Test handling of malformed HTML"""
        malformed_html = "<p>Unclosed paragraph<div>Nested content</p></div>"
        filter = BM25ContentFilter()
        contents = filter.filter_content(malformed_html)

        assert isinstance(contents, list), "Should return list even with malformed HTML"

    def test_threshold_behavior(self, basic_html):
        """Test different BM25 threshold values"""
        strict_filter = BM25ContentFilter(bm25_threshold=2.0)
        lenient_filter = BM25ContentFilter(bm25_threshold=0.5)

        strict_contents = strict_filter.filter_content(basic_html)
        lenient_contents = lenient_filter.filter_content(basic_html)

        assert len(strict_contents) <= len(
            lenient_contents
        ), "Strict threshold should extract fewer elements"

    def test_html_cleaning(self, basic_html):
        """Test HTML cleaning functionality"""
        filter = BM25ContentFilter()
        contents = filter.filter_content(basic_html)

        cleaned_content = " ".join(contents)
        assert "class=" not in cleaned_content, "Should remove class attributes"
        assert "style=" not in cleaned_content, "Should remove style attributes"
        assert "<script" not in cleaned_content, "Should remove script tags"

    def test_large_content(self):
        """Test handling of large content blocks"""
        large_html = f"""
        <html><body>
            <article>{'<p>Test content. ' * 1000}</article>
        </body></html>
        """
        filter = BM25ContentFilter()
        contents = filter.filter_content(large_html)
        assert contents, "Should handle large content blocks"

    @pytest.mark.parametrize(
        "unwanted_tag", ["script", "style", "nav", "footer", "header"]
    )
    def test_excluded_tags(self, unwanted_tag):
        """Test that specific tags are properly excluded"""
        html = f"""
        <html><body>
            <{unwanted_tag}>Should not appear</{unwanted_tag}>
            <p>Should appear</p>
        </body></html>
        """
        filter = BM25ContentFilter()
        contents = filter.filter_content(html)

        combined_content = " ".join(contents).lower()
        assert "should not appear" not in combined_content

    def test_performance(self, basic_html):
        """Test performance with timer"""
        filter = BM25ContentFilter()

        import time

        start = time.perf_counter()
        filter.filter_content(basic_html)
        duration = time.perf_counter() - start

        assert duration < 1.0, f"Processing took too long: {duration:.2f} seconds"


class TestWhitespaceBoundaries:
    """Regression tests for whitespace handling between adjacent HTML text nodes.

    extract_text_chunks() used to strip each text node individually before
    concatenating them, which destroyed the only whitespace boundary between
    adjacent nodes (e.g. "Grundpreis" + "40,00 € / Kilogramm" became
    "Grundpreis40,00 € / Kilogramm"). The fix keeps each node's original
    whitespace until the chunk is complete, and normalizes only on the fully
    assembled chunk. clean_element() had the same issue at the
    serialization stage.
    """

    @staticmethod
    def _chunks(html):
        """Extract candidate text chunks from a full HTML document."""
        content_filter = BM25ContentFilter()
        soup = BeautifulSoup(html, "lxml")
        body = soup.find("body")
        if body is None:
            soup = BeautifulSoup(f"<body>{html}</body>", "lxml")
            body = soup.find("body")
        return [chunk for _, chunk, _, _ in content_filter.extract_text_chunks(body)]

    def test_label_followed_by_inline_value(self):
        """A label and an inline value in separate text nodes keep their boundary."""
        html = """
        <html><head><title>Produkt</title></head>
        <body>
            <div>Grundpreis <span>40,00&nbsp;€ / Kilogramm</span></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Grundpreis 40,00 € / Kilogramm" in chunks, chunks

    def test_word_split_by_inline_formatting(self):
        """A word split by inline formatting must not gain an artificial space."""
        html = """
        <html><head><title>Produkt</title></head>
        <body>
            <div>40,00 € / Kilo<b>gramm</b></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "40,00 € / Kilogramm" in chunks, chunks
        assert "Kilo gramm" not in " ".join(chunks), chunks

    def test_whitespace_only_node_between_inline_tags(self):
        """Whitespace existing as its own text node between inline tags survives."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div><span>Hello</span> <span>world</span></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Hello world" in chunks, chunks

    def test_adjacent_inline_elements_without_source_whitespace(self):
        """No space is invented where the source contains none."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div><span>Hello</span><span>world</span></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Helloworld" in chunks, chunks

    def test_repeated_whitespace_normalized(self):
        """Repeated whitespace and newlines collapse to single spaces."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>  price&nbsp;of   <span>the&nbsp;item</span>
            </div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "price of the item" in chunks, chunks

    def test_comments_not_extracted(self):
        """HTML comment content must not enter extracted text chunks."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>visible text <!-- hidden comment --></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert all("hidden comment" not in chunk for chunk in chunks), chunks
        assert "visible text" in " ".join(chunks), chunks

    def test_cdata_not_serialized_by_clean_element(self):
        """CDATA content must not leak into clean_element() output."""
        from bs4 import CData

        content_filter = BM25ContentFilter()
        soup = BeautifulSoup("<div></div>", "lxml")
        soup.div.append("abc")
        soup.div.append(CData("secret payload"))
        cleaned = content_filter.clean_element(soup.div)
        assert "secret payload" not in cleaned
        assert "abc" in cleaned

    def test_filter_content_preserves_word_boundaries(self):
        """End-to-end: returned elements keep word boundaries after clean_element()."""
        html = """
        <html><body>
            <div>
                Grundpreis
                <span class="base-price-value">
                    40,00&nbsp;€ / Kilogramm
                </span>
            </div>
            <p>Unrelated filler paragraph about apples and oranges and how they are harvested every autumn in the southern provinces.</p>
            <p>Another unrelated paragraph with completely different vocabulary that does not overlap with the price label above in any way.</p>
            <p>More unrelated content here, talking about weather patterns, football matches, and the stock market over several months.</p>
            <p>Yet another distinct paragraph covering gardening tips, baking recipes, and travel itineraries across the continent.</p>
            <p>This paragraph discusses the history of the region, its castles, and the festivals that take place every summer evening.</p>
            <p>A paragraph about coffee culture, local cafes, and the various roasting traditions that have developed over the past decades.</p>
            <p>Information about public transport, ticket prices for trains, and the new station opening scheduled for next spring.</p>
            <p>A short text about the local theatre, its season programme, and the upcoming premiere of the classic play.</p>
            <p>Notes on the university library, opening hours, and the newly digitized collection of old manuscripts and maps.</p>
            <p>A description of the harbor, the fishing fleet, and the seasonal festivals celebrating the catch every winter.</p>
            <p>Details about the cycling routes, the best viewpoints, and the small museums found along the river valley.</p>
            <p>A paragraph on the local food market, the producers, and the specialities that visitors tend to buy as gifts.</p>
        </body></html>
        """
        content_filter = BM25ContentFilter(user_query="Grundpreis")
        contents = content_filter.filter_content(html)
        assert contents, "Should select the chunk containing the query"
        # The price chunk must be selected (default threshold 1.0)
        assert any("Grundpreis" in c for c in contents), contents
        # Text content of the returned elements keeps the word boundary
        texts = [
            " ".join(BeautifulSoup(c, "lxml").get_text().split()) for c in contents
        ]
        assert any("Grundpreis 40,00" in t for t in texts), contents
        assert not any("Grundpreis40,00" in t for t in texts), contents

    # --- Patterns adopted from PR #2271 (html2text empty-emphasis fix) ---

    def test_whitespace_only_inline_element_between_words(self):
        """`Hello<b> </b>world` must not merge into `Helloworld`.

        Same pattern as PR #2271 for html2text: an inline element holding
        only whitespace carries the word boundary.
        """
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>Hello<b> </b>world</div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Hello world" in chunks, chunks

    def test_space_in_its_own_styled_element(self):
        """Editors that emit one element per styled run put the space in its
        own element: `<b>Hello</b><b> </b><b>world</b>` (PR #2271)."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div><b>Hello</b><b> </b><b>world</b></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Hello world" in chunks, chunks

    def test_whitespace_outside_element_not_doubled(self):
        """Whitespace already present outside the element is not doubled
        (PR #2271): normalization collapses it to a single space."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>Hello <b> </b>world</div>
        </body></html>
        """
        assert "Hello world" in self._chunks(html)

        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>Hello<b> </b> world</div>
        </body></html>
        """
        assert "Hello world" in self._chunks(html)

    def test_no_space_between_styled_runs_without_source_whitespace(self):
        """Control (PR #2271): adjacent styled runs with no whitespace in the
        source stay adjacent — no space is invented."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div><b>Hello</b><b>world</b></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Helloworld" in chunks, chunks

    def test_nested_inline_elements_keep_boundaries(self):
        """Nested inline tags (`<b><i>x</i></b>`, PR #2271) keep surrounding
        word boundaries."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>Hello <b><i>x</i></b> world</div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Hello x world" in chunks, chunks

    # --- Patterns adopted from PR #2329 (whitespace-only separator spans) ---

    def test_character_level_spans_with_whitespace_span(self):
        """Character-level spans separated by a whitespace-only span
        (`<span>H</span><span>i</span><span> </span><span>t</span>...`,
        PR #2329) must come out as `Hi there`, not `Hithere`."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div><span>H</span><span>i</span><span> </span><span>t</span><span>h</span><span>e</span><span>r</span><span>e</span></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Hi there" in chunks, chunks

    def test_whitespace_spans_between_several_words(self):
        """Whitespace-only spans between several words (PR #2329)."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div><span>one</span><span> </span><span>two</span><span> </span><span>three</span></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "one two three" in chunks, chunks

    # --- Own boundary-semantics cases ---

    def test_comment_between_words(self):
        """Comments are skipped without inventing or removing boundaries."""
        # No whitespace in the source -> words stay adjacent.
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>Hello<!-- hidden -->world</div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Helloworld" in chunks, chunks
        assert all("hidden" not in chunk for chunk in chunks), chunks

        # Whitespace on both sides survives, collapsed to one space.
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>Hello <!-- hidden --> world</div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Hello world" in chunks, chunks

    def test_source_newline_is_word_separator(self):
        """Documented boundary semantics: whitespace in the *source* between
        text nodes is a word separator. A word split across inline tags
        with a newline in the source tokenizes as two words; the inline
        (no whitespace) case is covered by
        test_word_split_by_inline_formatting."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>Kilo
<b>gramm</b></div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Kilo gramm" in chunks, chunks

    def test_multiple_boundaries_in_one_chunk(self):
        """One chunk with several mixed boundaries: label/value, a word split
        mid-word across two tags, and a closing parenthesis."""
        html = """
        <html><head><title>Test</title></head>
        <body>
            <div>Grundpreis: <span>40,00&nbsp;€</span> pro <b>Kilo</b><b>gramm</b> (netto)</div>
        </body></html>
        """
        chunks = self._chunks(html)
        assert "Grundpreis: 40,00 € pro Kilogramm (netto)" in chunks, chunks

    def test_clean_element_preserves_word_boundaries(self):
        """clean_element() serialization keeps the boundary (not only
        extract_text_chunks)."""
        from bs4 import BeautifulSoup

        content_filter = BM25ContentFilter()
        soup = BeautifulSoup(
            '<div>Grundpreis <span class="base-price-value">'
            "40,00&nbsp;€ / Kilogramm</span></div>",
            "lxml",
        )
        cleaned = content_filter.clean_element(soup.div)
        assert "Grundpreis <span" in cleaned, cleaned
        assert "Grundpreis40,00" not in cleaned, cleaned

    def test_clean_element_skips_comments_between_words(self):
        """Comment content does not leak into clean_element() output and
        removes no whitespace boundary."""
        from bs4 import BeautifulSoup

        content_filter = BM25ContentFilter()
        soup = BeautifulSoup("<div>visible<!-- hidden -->text</div>", "lxml")
        cleaned = content_filter.clean_element(soup.div)
        assert "hidden" not in cleaned, cleaned
        assert "visible" in cleaned, cleaned

    def test_filter_content_query_matches_word_split_by_inline_tag(self):
        """End-to-end anti-over-splitting guard: the inline split of
        `Kilo<b>gramm</b>` must NOT gain a space, so a query for the full
        word still matches the chunk (pre-fix behavior accidentally OK
        here — must stay OK after the fix)."""
        html = """
        <html><body>
            <div>40,00 € / Kilo<b>gramm</b></div>
            <p>Unrelated filler paragraph about apples and oranges and how they are harvested every autumn in the southern provinces.</p>
            <p>Another unrelated paragraph with completely different vocabulary that does not overlap with the price label above in any way.</p>
            <p>More unrelated content here, talking about weather patterns, football matches, and the stock market over several months.</p>
            <p>Yet another distinct paragraph covering gardening tips, baking recipes, and travel itineraries across the continent.</p>
            <p>This paragraph discusses the history of the region, its castles, and the festivals that take place every summer evening.</p>
            <p>A paragraph about coffee culture, local cafes, and the various roasting traditions that have developed over the past decades.</p>
            <p>Information about public transport, ticket prices for trains, and the new station opening scheduled for next spring.</p>
            <p>A short text about the local theatre, its season programme, and the upcoming premiere of the classic play.</p>
            <p>Notes on the university library, opening hours, and the newly digitized collection of old manuscripts and maps.</p>
            <p>A description of the harbor, the fishing fleet, and the seasonal festivals celebrating the catch every winter.</p>
            <p>Details about the cycling routes, the best viewpoints, and the small museums found along the river valley.</p>
            <p>A paragraph on the local food market, the producers, and the specialities that visitors tend to buy as gifts.</p>
        </body></html>
        """
        content_filter = BM25ContentFilter(user_query="Kilogramm")
        contents = content_filter.filter_content(html)
        assert contents, "Query for a word split inline must still match"
        texts = [
            " ".join(BeautifulSoup(c, "lxml").get_text().split()) for c in contents
        ]
        assert any("Kilogramm" in t for t in texts), contents
        assert not any("Kilo gramm" in t for t in texts), contents


if __name__ == "__main__":
    pytest.main([__file__])
