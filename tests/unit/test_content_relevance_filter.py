from unittest.mock import AsyncMock

import pytest

from crawl4ai.deep_crawling.filters import ContentRelevanceFilter, HeadPeekr


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "accepted"), [("retrieval", True), ("unrelated", False)]
)
async def test_content_relevance_filter_matches_a_single_word_title(
    monkeypatch, query, accepted
):
    monkeypatch.setattr(
        HeadPeekr,
        "peek_html",
        AsyncMock(return_value="<head><title>Retrieval</title></head>"),
    )
    relevance_filter = ContentRelevanceFilter(query=query, threshold=0.1)

    assert await relevance_filter.apply("https://example.com/docs") is accepted


def test_content_relevance_filter_preserves_weighted_word_boundaries():
    relevance_filter = ContentRelevanceFilter(query="retrieval", threshold=0.1)
    fields = {
        "title": "Vector Retrieval",
        "meta": {"description": "Search documents", "keywords": "RAG"},
    }

    assert relevance_filter._build_document(fields).split() == (
        ["Vector", "Retrieval"] * 3
        + ["Search", "documents"] * 2
        + ["RAG", "Search", "documents", "RAG"]
    )
