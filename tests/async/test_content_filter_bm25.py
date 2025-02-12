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


if __name__ == "__main__":
    pytest.main([__file__])
