"""
Regression tests for #2381: BestFirstCrawlingStrategy must not fetch a full
BATCH_SIZE past the max_pages budget on the final batch.

The batch-filling loop used ``range(BATCH_SIZE)`` even though the remaining
budget was computed as ``min(BATCH_SIZE, remaining)``, so with max_pages=12 the
final batch still fetched 10 URLs (21 fetches total for 12 results) and the
extra pages' results were dropped.
"""

import pytest
from unittest.mock import MagicMock

from crawl4ai.deep_crawling import BestFirstCrawlingStrategy


def create_mock_config():
    config = MagicMock()
    config.stream = True
    config.clone = MagicMock(return_value=config)
    return config


def create_mock_crawler(child_urls):
    """Crawler that succeeds on every URL and records what it fetched."""
    fetched = []

    async def mock_arun_many(urls, config):
        fetched.extend(urls)
        results = []
        for url in urls:
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}
            links = (
                [{"href": u} for u in child_urls]
                if url == "https://example.test/"
                else []
            )
            result.links = {"internal": links, "external": []}
            results.append(result)

        async def gen():
            for r in results:
                yield r

        return gen()

    crawler = MagicMock()
    crawler.arun_many = mock_arun_many
    return crawler, fetched


@pytest.mark.asyncio
async def test_best_first_final_batch_respects_max_pages():
    # max_pages=12 with BATCH_SIZE=10: batches of 1 (start), 10, then 1.
    child_urls = [f"https://example.test/p{i}" for i in range(30)]
    strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=12)
    crawler, fetched = create_mock_crawler(child_urls)

    results = [
        r
        async for r in strategy._arun_best_first(
            "https://example.test/", crawler, create_mock_config()
        )
    ]

    assert len(results) == 12
    # Without the fix this was 21: the final batch still fetched 10 URLs
    # and the 9 over-budget results were dropped.
    assert len(fetched) == 12


@pytest.mark.asyncio
async def test_best_first_exact_multiple_of_batch_size_fetches_no_extra():
    # max_pages=11: batches of 1 (start), 10. No third batch at all.
    child_urls = [f"https://example.test/p{i}" for i in range(30)]
    strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=11)
    crawler, fetched = create_mock_crawler(child_urls)

    results = [
        r
        async for r in strategy._arun_best_first(
            "https://example.test/", crawler, create_mock_config()
        )
    ]

    assert len(results) == 11
    assert len(fetched) == 11
