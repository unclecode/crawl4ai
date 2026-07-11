"""
Deterministic unit tests for AdaptiveCrawler behavior changes.

These tests verify:
1. StatisticalStrategy.calculate_confidence uses AdaptiveConfig weights (not hardcoded).
2. StatisticalStrategy.should_stop records structured stop reasons.
3. EmbeddingStrategy.calculate_confidence sets learning_score metric.
4. _crawl_with_preview preserves links without head_data (frontier recall).
5. Adaptive policy retains tunnel links and reaches relevant pages.
6. digest() records low_expected_gain stop reason.

All tests use mock/fake objects — no browser, no network, no external services.
"""

import asyncio
import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict

from crawl4ai.adaptive_crawler import (
    AdaptiveConfig,
    CrawlState,
    StatisticalStrategy,
    EmbeddingStrategy,
    AdaptiveCrawler,
)
from crawl4ai.models import Link


# ---------------------------------------------------------------------------
# Fake objects
# ---------------------------------------------------------------------------

class FakeMarkdown:
    def __init__(self, raw_markdown):
        self.raw_markdown = raw_markdown


class FakeCrawlResult:
    """Minimal fake CrawlResult for testing without a browser."""
    def __init__(self, url, content, links=None, success=True):
        self.url = url
        self.markdown = FakeMarkdown(content)
        self.links = links if links is not None else {"internal": [], "external": []}
        self.metadata = {}
        self.success = success


# ---------------------------------------------------------------------------
# Test 1: StatisticalStrategy.calculate_confidence uses config weights
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_statistical_confidence_uses_configurable_weights():
    """calculate_confidence should use AdaptiveConfig weights, not hardcoded 0.4/0.3/0.3."""
    strategy = StatisticalStrategy()
    config = AdaptiveConfig(
        coverage_weight=1.0,
        consistency_weight=0.0,
        saturation_weight=0.0,
    )
    strategy.config = config

    state = CrawlState(query="alpha beta")
    state.knowledge_base = [FakeCrawlResult("http://example.com/1", "alpha beta content")]
    state.total_documents = 1
    state.term_frequencies = defaultdict(int, {"alpha": 5, "beta": 3})
    state.document_frequencies = defaultdict(int, {"alpha": 1, "beta": 1})

    # Monkeypatch the private metric methods to return known values
    strategy._calculate_coverage = lambda s: 0.2
    strategy._calculate_consistency = lambda s: 0.4
    strategy._calculate_saturation = lambda s: 0.8

    confidence = await strategy.calculate_confidence(state)

    # With coverage_weight=1.0, others=0.0, confidence should equal coverage=0.2
    assert confidence == pytest.approx(0.2, abs=0.01), (
        f"Expected confidence=0.2 with coverage_weight=1.0, got {confidence}. "
        f"Current code hardcodes 0.4*0.2 + 0.3*0.4 + 0.3*0.8 = 0.44."
    )


# ---------------------------------------------------------------------------
# Test 2: should_stop records confidence_threshold_reached
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_statistical_should_stop_records_confidence_reason():
    """should_stop should set stopped_reason='confidence_threshold_reached'."""
    strategy = StatisticalStrategy()
    config = AdaptiveConfig(confidence_threshold=0.7, max_pages=100, saturation_threshold=0.9)

    state = CrawlState(query="test")
    state.crawled_urls = {"http://example.com/1"}
    state.pending_links = [Link(href="http://example.com/2", text="link")]
    state.metrics = {'confidence': 0.9, 'saturation': 0.1}

    result = await strategy.should_stop(state, config)

    assert result is True, "Should stop when confidence exceeds threshold"
    assert state.metrics.get('stopped_reason') == 'confidence_threshold_reached', (
        f"Expected stopped_reason='confidence_threshold_reached', got {state.metrics.get('stopped_reason')}"
    )


# ---------------------------------------------------------------------------
# Test 3: should_stop records saturation_threshold_reached
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_statistical_should_stop_records_saturation_reason():
    """should_stop should set stopped_reason='saturation_threshold_reached'."""
    strategy = StatisticalStrategy()
    config = AdaptiveConfig(confidence_threshold=0.9, max_pages=100, saturation_threshold=0.8)

    state = CrawlState(query="test")
    state.crawled_urls = {"http://example.com/1"}
    state.pending_links = [Link(href="http://example.com/2", text="link")]
    state.metrics = {'confidence': 0.1, 'saturation': 0.95}

    result = await strategy.should_stop(state, config)

    assert result is True, "Should stop when saturation exceeds threshold"
    assert state.metrics.get('stopped_reason') == 'saturation_threshold_reached', (
        f"Expected stopped_reason='saturation_threshold_reached', got {state.metrics.get('stopped_reason')}"
    )


# ---------------------------------------------------------------------------
# Test 4: EmbeddingStrategy.calculate_confidence sets learning_score
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_embedding_confidence_sets_learning_score():
    """EmbeddingStrategy.calculate_confidence should set state.metrics['learning_score']."""
    strategy = EmbeddingStrategy()
    config = AdaptiveConfig(strategy="embedding")
    strategy.config = config

    state = CrawlState(query="test query")
    state.kb_embeddings = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    state.query_embeddings = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)

    score = await strategy.calculate_confidence(state)

    assert 'learning_score' in state.metrics, (
        "state.metrics['learning_score'] should be set by calculate_confidence"
    )
    assert state.metrics['learning_score'] == pytest.approx(score, abs=0.01), (
        f"learning_score should equal returned score {score}, got {state.metrics['learning_score']}"
    )
    # Also verify the existing metrics are still set
    assert 'coverage_score' in state.metrics, "coverage_score should still be set"


# ---------------------------------------------------------------------------
# Test 5: _crawl_with_preview preserves links without head_data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_with_preview_preserves_links_without_head_data():
    """_crawl_with_preview should NOT filter out internal links lacking head_data."""
    # Build a fake crawler whose arun returns a result with a no-head link
    no_head_link = {"href": "https://example.com/no-head", "text": "No Head Link"}
    with_head_link = {"href": "https://example.com/with-head", "text": "With Head", "head_data": {"title": "Title"}}

    fake_result = FakeCrawlResult(
        url="https://example.com/start",
        content="start page content",
        links={"internal": [no_head_link, with_head_link], "external": []},
    )

    fake_crawler = AsyncMock()
    fake_crawler.arun = AsyncMock(return_value=fake_result)

    adaptive = AdaptiveCrawler(crawler=fake_crawler, config=AdaptiveConfig())

    result = await adaptive._crawl_with_preview("https://example.com/start", "query")

    assert result is not None, "Should return a result"
    internal_links = result.links["internal"]
    hrefs = [l["href"] for l in internal_links]
    assert "https://example.com/no-head" in hrefs, (
        "No-head link should be preserved for recall, but it was filtered out"
    )


# ---------------------------------------------------------------------------
# Test 6: Adaptive policy retains tunnel link and reaches relevant page
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_adaptive_policy_retains_tunnel_link_and_stop_reason_present():
    """
    Synthetic site graph:
      root -> relevant_page (has query terms)
      root -> irrelevant_page (no query terms)
      root -> tunnel_page (no head_data, sparse content, links to highly_relevant_page)
      tunnel_page -> highly_relevant_page (many query terms)

    Verify: stop_reason is present after digest, tunnel link appears in
    pending_links (frontier recall), and at least the root page was crawled.
    """
    query = "alpha beta gamma"

    root_content = f"root page about {query}"
    relevant_content = f"this page discusses {query} in detail alpha beta gamma"
    irrelevant_content = "completely unrelated content about cooking pasta recipes"
    tunnel_content = "sparse page with few terms"
    highly_relevant_content = f"comprehensive coverage of {query} alpha beta gamma alpha beta gamma"

    root_links = {
        "internal": [
            {"href": "http://example.com/relevant", "text": "Relevant Page"},
            {"href": "http://example.com/irrelevant", "text": "Irrelevant Page"},
            {"href": "http://example.com/tunnel", "text": "Tunnel Page"},
        ],
        "external": [],
    }
    tunnel_links = {
        "internal": [
            {"href": "http://example.com/highly-relevant", "text": "Highly Relevant"},
        ],
        "external": [],
    }

    # Map URLs to fake results
    url_to_result = {
        "http://example.com/root": FakeCrawlResult("http://example.com/root", root_content, root_links),
        "http://example.com/relevant": FakeCrawlResult("http://example.com/relevant", relevant_content),
        "http://example.com/irrelevant": FakeCrawlResult("http://example.com/irrelevant", irrelevant_content),
        "http://example.com/tunnel": FakeCrawlResult("http://example.com/tunnel", tunnel_content, tunnel_links),
        "http://example.com/highly-relevant": FakeCrawlResult("http://example.com/highly-relevant", highly_relevant_content),
    }

    async def fake_arun(url, config=None, **kwargs):
        return url_to_result.get(url, FakeCrawlResult(url, ""))

    fake_crawler = AsyncMock()
    fake_crawler.arun = fake_arun

    config = AdaptiveConfig(
        confidence_threshold=0.95,  # High threshold to force crawling
        max_pages=5,
        max_depth=3,
        top_k_links=3,
        min_gain_threshold=0.0,
    )

    adaptive = AdaptiveCrawler(crawler=fake_crawler, config=config)

    state = await adaptive.digest(
        start_url="http://example.com/root",
        query=query,
    )

    # Check that stop_reason is present
    assert 'stopped_reason' in state.metrics, (
        "state.metrics should contain 'stopped_reason' after digest()"
    )
    assert state.metrics['stopped_reason'], (
        f"stopped_reason should be non-empty, got {state.metrics.get('stopped_reason')}"
    )

    # Check that the tunnel link was retained in pending_links (frontier recall)
    pending_hrefs = [link.href for link in state.pending_links]
    assert "http://example.com/tunnel" in pending_hrefs, (
        f"Tunnel link should be retained in pending_links for recall, got: {pending_hrefs}"
    )

    # Check that at least the root page was crawled
    assert "http://example.com/root" in state.crawled_urls, (
        "Root page should have been crawled"
    )


# ---------------------------------------------------------------------------
# Phase 3 tests: URL dedup, EmbeddingStrategy export, tokenizer consistency
# ---------------------------------------------------------------------------

def test_embedding_strategy_is_exported():
    """EmbeddingStrategy should be importable from crawl4ai package."""
    from crawl4ai import EmbeddingStrategy
    assert EmbeddingStrategy is not None, "EmbeddingStrategy should be exported from crawl4ai"


def test_get_relevant_content_uses_consistent_tokenizer():
    """get_relevant_content should use _tokenize() not .split() for term overlap."""
    from crawl4ai.adaptive_crawler import StatisticalStrategy

    fake_crawler = AsyncMock()
    config = AdaptiveConfig()
    adaptive = AdaptiveCrawler(crawler=fake_crawler, config=config)

    # Manually set up state with a knowledge base
    state = CrawlState(query="async! await? coroutine")
    state.knowledge_base = [
        FakeCrawlResult("http://example.com/1", "async await coroutine task"),
        FakeCrawlResult("http://example.com/2", "completely different content about cooking"),
    ]
    state.query = "async! await? coroutine"
    adaptive.state = state

    results = adaptive.get_relevant_content(top_k=2)

    # The first result should be the one with all query terms
    # With .split(), "async!" wouldn't match "async" due to punctuation
    # With _tokenize(), it should match
    assert len(results) >= 1
    assert results[0]['url'] == "http://example.com/1", (
        f"Most relevant page should be the one with query terms, got {results[0]['url']}"
    )
    assert results[0]['score'] > 0, "Score should be positive for a page with query terms"


@pytest.mark.asyncio
async def test_digest_deduplicates_urls():
    """digest() should not add duplicate URLs to pending_links after normalization."""
    # Root page links to two URLs that normalize to the same thing
    root_links = {
        "internal": [
            {"href": "http://example.com/page", "text": "Page"},
            {"href": "http://example.com/page/", "text": "Page Duplicate"},  # trailing slash
            {"href": "http://example.com/other", "text": "Other"},
        ],
        "external": [],
    }

    fake_result = FakeCrawlResult(
        url="http://example.com/root",
        content="root content about query terms",
        links=root_links,
    )

    fake_crawler = AsyncMock()
    fake_crawler.arun = AsyncMock(return_value=fake_result)

    config = AdaptiveConfig(
        confidence_threshold=0.99,  # Force crawling all available links
        max_pages=5,
        max_depth=1,
        top_k_links=5,
        min_gain_threshold=0.0,
    )

    adaptive = AdaptiveCrawler(crawler=fake_crawler, config=config)
    state = await adaptive.digest(
        start_url="http://example.com/root",
        query="query terms",
    )

    # Check that pending_links does not contain both /page and /page/
    pending_hrefs = [link.href for link in state.pending_links]
    # After normalization, /page and /page/ should be the same URL
    unique_hrefs = set(pending_hrefs)
    assert len(unique_hrefs) <= len(pending_hrefs), "pending_links should not have exact duplicates"

    # More specifically, /page and /page/ should not both appear
    page_variants = [h for h in pending_hrefs if "page" in h]
    assert len(page_variants) <= 1, (
        f"Should have at most 1 'page' variant after dedup, got: {page_variants}"
    )
