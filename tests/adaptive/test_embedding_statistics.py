"""
Tests for statistics calculation in EmbeddingStrategy and AdaptiveCrawler.

Verifies that EmbeddingStrategy calculates lexical statistics (term frequencies,
document frequencies, new terms history, crawl order), saturation, consistency,
learning_score, and vector distance metrics, and correctly exposes them in
coverage_stats and print_stats.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock
import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))

from crawl4ai.adaptive_crawler import (
    AdaptiveCrawler,
    AdaptiveConfig,
    CrawlState,
    EmbeddingStrategy,
)
from crawl4ai.models import CrawlResult


def create_mock_result(url: str, markdown_content: str):
    """Helper to create mock CrawlResult with markdown text."""

    class MockMarkdown:
        def __init__(self, raw: str):
            self.raw_markdown = raw

    result = MagicMock(spec=CrawlResult)
    result.url = url
    result.success = True
    result.markdown = MockMarkdown(markdown_content)
    return result


def test_embedding_strategy_text_statistics():
    """Verify EmbeddingStrategy updates term frequencies, document frequencies, and crawl order."""
    strategy = EmbeddingStrategy()
    state = CrawlState(query="deep learning neural networks")

    doc1 = create_mock_result(
        "https://example.com/page1",
        "Deep learning is a subset of machine learning based on artificial neural networks.",
    )
    doc2 = create_mock_result(
        "https://example.com/page2",
        "Neural networks use layers of nodes to learn patterns from complex data.",
    )

    # 1. Update with first document
    strategy._update_text_statistics(state, [doc1])

    assert state.total_documents == 1
    assert len(state.term_frequencies) > 0
    assert "learning" in state.term_frequencies
    assert "neural" in state.term_frequencies
    assert state.document_frequencies["neural"] == 1
    assert len(state.new_terms_history) == 1
    initial_new_terms = state.new_terms_history[0]
    assert initial_new_terms > 0
    assert state.crawl_order == ["https://example.com/page1"]

    # 2. Update with second document
    strategy._update_text_statistics(state, [doc2])

    assert state.total_documents == 2
    assert state.document_frequencies["neural"] == 2
    assert len(state.new_terms_history) == 2
    assert state.crawl_order == [
        "https://example.com/page1",
        "https://example.com/page2",
    ]

    # 3. Saturation calculation
    saturation = strategy._calculate_saturation(state)
    assert 0.0 <= saturation <= 1.0

    print("PASS: test_embedding_strategy_text_statistics")


def test_embedding_strategy_confidence_and_distance_metrics():
    """Verify EmbeddingStrategy.calculate_confidence calculates learning_score, distances, and saturation."""

    async def _run():
        strategy = EmbeddingStrategy()
        strategy.config = AdaptiveConfig(strategy="embedding")
        state = CrawlState(query="python async programming")

        doc1 = create_mock_result(
            "https://example.com/1", "Python async and await with asyncio library."
        )
        doc2 = create_mock_result(
            "https://example.com/2", "Concurrency and event loops in Python asyncio."
        )
        strategy._update_text_statistics(state, [doc1, doc2])

        # Mock embeddings: 2 queries, 2 documents in KB (dim=4)
        state.query_embeddings = np.array(
            [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]], dtype=np.float32
        )

        state.kb_embeddings = np.array(
            [[0.9, 0.1, 0.0, 0.0], [0.1, 0.8, 0.0, 0.0]], dtype=np.float32
        )

        score = await strategy.calculate_confidence(state)

        assert score > 0.0
        assert state.metrics.get("learning_score") == score
        assert state.metrics.get("coverage") == score
        assert "saturation" in state.metrics
        assert 0.0 <= state.metrics["saturation"] <= 1.0
        assert "consistency" in state.metrics
        assert "avg_min_distance" in state.metrics
        assert state.metrics["avg_min_distance"] >= 0.0
        assert "avg_close_neighbors" in state.metrics
        assert "avg_very_close_neighbors" in state.metrics
        assert state.metrics.get("total_kb_docs") == 2

        # Verify quality confidence mapping does not return 0.0
        quality_conf = strategy.get_quality_confidence(state)
        assert quality_conf > 0.0

    asyncio.run(_run())
    print("PASS: test_embedding_strategy_confidence_and_distance_metrics")


def test_adaptive_crawler_coverage_stats_and_print():
    """Verify coverage_stats and print_stats work with populated metrics for EmbeddingStrategy."""

    async def _run():
        config = AdaptiveConfig(strategy="embedding")
        with MagicMock() as mock_crawler:
            crawler = AdaptiveCrawler(crawler=mock_crawler, config=config)

        crawler.state = CrawlState(query="web scraping agents")
        doc1 = create_mock_result(
            "https://example.com/crawl1",
            "Web scraping with automated agents and tools.",
        )
        doc2 = create_mock_result(
            "https://example.com/crawl2", "Extraction of markdown from web pages."
        )

        crawler.state.knowledge_base = [doc1, doc2]
        crawler.state.crawled_urls = {
            "https://example.com/crawl1",
            "https://example.com/crawl2",
        }

        # Update state
        crawler.strategy._update_text_statistics(crawler.state, [doc1, doc2])

        # Setup embeddings and calculate metrics
        crawler.state.query_embeddings = np.array(
            [[1.0, 0.0], [0.5, 0.5]], dtype=np.float32
        )
        crawler.state.kb_embeddings = np.array(
            [[0.95, 0.05], [0.6, 0.4]], dtype=np.float32
        )

        await crawler.strategy.calculate_confidence(crawler.state)
        crawler.state.metrics["confidence"] = crawler.strategy.get_quality_confidence(
            crawler.state
        )

        stats = crawler.coverage_stats

        # Assert metrics are now calculated and populated
        assert stats["pages_crawled"] == 2
        assert stats["unique_terms"] > 0
        assert stats["total_terms"] > 0
        assert stats["confidence"] > 0.0
        assert "saturation" in stats
        assert stats["saturation"] >= 0.0
        assert "coverage" in stats

        # Verify print_stats runs without error for both summary and detailed views
        crawler.print_stats(detailed=False)
        crawler.print_stats(detailed=True)

    asyncio.run(_run())
    print("PASS: test_adaptive_crawler_coverage_stats_and_print")


def main():
    test_embedding_strategy_text_statistics()
    test_embedding_strategy_confidence_and_distance_metrics()
    test_adaptive_crawler_coverage_stats_and_print()
    print("\n============================================================")
    print("ALL EMBEDDING STATISTICS TESTS PASSED!")
    print("============================================================")


if __name__ == "__main__":
    main()
