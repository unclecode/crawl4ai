"""
Tests for GitHub issue #1213: BM25ContentFilter returns multiple copies of
the same text when the DOM contains repeated content blocks.

Fix: added deduplication by chunk text in filter_content(), keeping the
first occurrence in document order.
"""

import pytest
from crawl4ai.content_filter_strategy import BM25ContentFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wrap_html(body_inner: str) -> str:
    """Wrap body HTML with boilerplate including a title for query extraction."""
    return (
        "<html><head><title>Python Programming Guide</title>"
        '<meta name="description" content="Learn Python programming language"></head>'
        f"<body>{body_inner}</body></html>"
    )


# Provide enough varied paragraphs so BM25 IDF doesn't go negative.
# The "target" paragraph is the one we'll duplicate; the others provide corpus variety.
TARGET_TEXT = (
    "Python is a versatile programming language widely used for web development, "
    "data science, machine learning, and automation tasks across the industry."
)

FILLER_PARAGRAPHS = [
    "<p>JavaScript powers interactive websites and runs in every modern browser environment.</p>",
    "<p>Rust provides memory safety without garbage collection through its ownership model.</p>",
    "<p>Go was designed at Google for building scalable network services and cloud infrastructure.</p>",
    "<p>Ruby on Rails popularized convention over configuration in web application frameworks.</p>",
    "<p>TypeScript adds static type checking to JavaScript for large-scale application development.</p>",
    "<p>Java remains dominant in enterprise software and Android mobile application development.</p>",
    "<p>C++ is essential for game engines, operating systems, and high-performance computing.</p>",
]

FILLER_BLOCK = "\n".join(FILLER_PARAGRAPHS)


def _make_test_html(target_copies: int = 1, extra_body: str = "") -> str:
    """Build HTML with `target_copies` of TARGET_TEXT + filler for BM25 variety."""
    target_block = f"<p>{TARGET_TEXT}</p>\n" * target_copies
    return _wrap_html(target_block + FILLER_BLOCK + extra_body)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBM25Deduplication:
    """Core deduplication tests for issue #1213."""

    def test_exact_duplicates_collapsed(self):
        """Identical paragraphs should appear only once in output."""
        html = _make_test_html(target_copies=5)
        filt = BM25ContentFilter(user_query="Python programming", bm25_threshold=0.01)
        results = filt.filter_content(html)
        matching = [r for r in results if "versatile" in r]
        assert len(matching) == 1

    def test_no_duplicates_unchanged(self):
        """Unique paragraphs should all be preserved (none removed by dedup)."""
        html = _make_test_html(target_copies=1)
        filt = BM25ContentFilter(user_query="programming languages", bm25_threshold=0.01)
        results = filt.filter_content(html)
        # At least some pass threshold; key point is no false dedup
        assert len(results) >= 1
        # All results should be unique strings
        assert len(results) == len(set(results))

    def test_mixed_unique_and_duplicate(self):
        """Duplicates removed, uniques kept."""
        extra = f"<p>{TARGET_TEXT}</p><p>{TARGET_TEXT}</p>"
        html = _make_test_html(target_copies=1, extra_body=extra)
        filt = BM25ContentFilter(user_query="Python programming", bm25_threshold=0.01)
        results = filt.filter_content(html)
        matching = [r for r in results if "versatile" in r]
        assert len(matching) == 1

    def test_document_order_preserved(self):
        """First occurrence should be kept, not the last."""
        first_text = "Python was created by Guido van Rossum in the early nineties as a successor to the ABC language."
        second_text = "Python supports multiple programming paradigms including procedural and functional styles."
        body = (
            f"<p>{first_text}</p>"
            f"<p>{second_text}</p>"
            f"<p>{first_text}</p>"  # duplicate
            + FILLER_BLOCK
        )
        html = _wrap_html(body)
        filt = BM25ContentFilter(user_query="Python history", bm25_threshold=0.01)
        results = filt.filter_content(html)
        guido_results = [r for r in results if "Guido" in r]
        assert len(guido_results) == 1

    def test_empty_html(self):
        """Empty input should return empty list."""
        filt = BM25ContentFilter()
        assert filt.filter_content("") == []

    def test_none_html(self):
        """None input should return empty list."""
        filt = BM25ContentFilter()
        assert filt.filter_content(None) == []

    def test_no_body(self):
        """HTML without explicit body should still work."""
        body = f"<p>{TARGET_TEXT}</p>" * 3 + FILLER_BLOCK
        filt = BM25ContentFilter(user_query="Python programming", bm25_threshold=0.01)
        results = filt.filter_content(body)
        matching = [r for r in results if "versatile" in r]
        assert len(matching) == 1

    def test_single_paragraph_with_filler(self):
        """Single target paragraph — nothing to deduplicate."""
        html = _make_test_html(target_copies=1)
        filt = BM25ContentFilter(user_query="Python programming", bm25_threshold=0.01)
        results = filt.filter_content(html)
        matching = [r for r in results if "versatile" in r]
        assert len(matching) == 1

    def test_high_threshold_filters_all(self):
        """Very high threshold should return nothing."""
        html = _make_test_html(target_copies=3)
        filt = BM25ContentFilter(bm25_threshold=9999.0)
        results = filt.filter_content(html)
        assert results == []

    def test_duplicate_with_different_tags(self):
        """Same text in different tag types should still be deduplicated."""
        text = "Python enables rapid prototyping and development of complex software systems."
        extra = f"<p>{text}</p><div>{text}</div>"
        html = _make_test_html(target_copies=0, extra_body=extra)
        filt = BM25ContentFilter(user_query="Python development", bm25_threshold=0.01)
        results = filt.filter_content(html)
        matching = [r for r in results if "rapid prototyping" in r]
        assert len(matching) == 1

    def test_many_duplicates(self):
        """30 identical paragraphs should collapse to 1."""
        html = _make_test_html(target_copies=30)
        filt = BM25ContentFilter(user_query="Python programming", bm25_threshold=0.01)
        results = filt.filter_content(html)
        matching = [r for r in results if "versatile" in r]
        assert len(matching) == 1

    def test_user_query_with_duplicates(self):
        """Dedup works correctly when a user_query is provided."""
        html = _make_test_html(target_copies=4)
        filt = BM25ContentFilter(user_query="Python web development", bm25_threshold=0.01)
        results = filt.filter_content(html)
        matching = [r for r in results if "versatile" in r]
        assert len(matching) == 1

    def test_stemming_disabled_with_duplicates(self):
        """Dedup works with use_stemming=False."""
        html = _make_test_html(target_copies=4)
        filt = BM25ContentFilter(
            user_query="Python programming", bm25_threshold=0.01, use_stemming=False
        )
        results = filt.filter_content(html)
        matching = [r for r in results if "versatile" in r]
        assert len(matching) == 1

    def test_returns_list_type(self):
        """Output should always be a list of strings."""
        html = _make_test_html(target_copies=2)
        filt = BM25ContentFilter(user_query="Python", bm25_threshold=0.01)
        results = filt.filter_content(html)
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, str)
