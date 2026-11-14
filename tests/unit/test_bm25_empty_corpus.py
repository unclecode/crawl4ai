"""BM25 filtering handles pages whose candidates contain only noise tokens."""

import pytest

from crawl4ai.content_filter_strategy import BM25ContentFilter


@pytest.mark.parametrize("use_stemming", [False, True])
@pytest.mark.parametrize("threshold", [0.0, 1.0])
def test_filter_returns_no_content_for_an_empty_cleaned_corpus(use_stemming, threshold):
    content_filter = BM25ContentFilter(
        user_query="orchards", bm25_threshold=threshold, use_stemming=use_stemming
    )

    assert content_filter.filter_content("<p>the and of in</p><p>to is it</p>") == []


@pytest.mark.parametrize("use_stemming", [False, True])
def test_filter_preserves_matching_content_in_a_mixed_corpus(use_stemming):
    content_filter = BM25ContentFilter(
        user_query="orchards", bm25_threshold=0.1, use_stemming=use_stemming
    )
    html = (
        "<p>orchards apples pears</p>" "<p>the and of</p>" "<p>volcanoes magma lava</p>"
    )

    assert content_filter.filter_content(html) == ["<p>orchards apples pears</p>"]
