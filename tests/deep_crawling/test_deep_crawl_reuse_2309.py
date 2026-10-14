"""
Regression tests for #2309: reusing a deep crawl strategy must not carry the
previous run's max_pages budget into a fresh run.

A fresh run (no resume_state) starts its page counter at zero; a resumed run
still continues from the saved pages_crawled.
"""

import pytest
from unittest.mock import MagicMock

from crawl4ai.deep_crawling import (
    BFSDeepCrawlStrategy,
    DFSDeepCrawlStrategy,
    BestFirstCrawlingStrategy,
)


STRATEGIES = [BFSDeepCrawlStrategy, DFSDeepCrawlStrategy, BestFirstCrawlingStrategy]


def create_mock_config(stream=False):
    config = MagicMock()
    config.stream = stream

    def clone_config(**kwargs):
        new_config = MagicMock()
        new_config.stream = kwargs.get("stream", stream)
        new_config.clone = MagicMock(side_effect=clone_config)
        return new_config

    config.clone = MagicMock(side_effect=clone_config)
    return config


def create_mock_crawler():
    """Crawler that succeeds on every URL; each start page links to one child."""

    async def mock_arun_many(urls, config):
        results = []
        for url in urls:
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}
            links = [] if url.endswith("/child") else [{"href": f"{url}/child"}]
            result.links = {"internal": links, "external": []}
            results.append(result)

        if config.stream:
            async def gen():
                for r in results:
                    yield r
            return gen()
        return results

    crawler = MagicMock()
    crawler.arun_many = mock_arun_many
    return crawler


async def run_strategy(strategy, start_url, stream):
    config = create_mock_config(stream=stream)
    if stream:
        gen = await strategy.arun(start_url, create_mock_crawler(), config)
        return [r async for r in gen]
    return await strategy.arun(start_url, create_mock_crawler(), config)


@pytest.mark.asyncio
@pytest.mark.parametrize("strategy_cls", STRATEGIES)
@pytest.mark.parametrize("stream", [False, True])
async def test_reused_strategy_gets_fresh_page_budget(strategy_cls, stream):
    # Each run crawls two pages (start + child), below max_pages, so only a
    # counter leaked from the previous run can cut the second run short.
    strategy = strategy_cls(max_depth=1, max_pages=3)

    for url in ["https://example.test/first", "https://example.test/second"]:
        results = await run_strategy(strategy, url, stream)
        assert sorted(r.url for r in results) == [url, f"{url}/child"]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_resumed_run_keeps_saved_page_count(stream):
    saved_state = {
        "strategy_type": "bfs",
        "visited": ["https://example.test/"],
        "pending": [{"url": "https://example.test/next", "parent_url": "https://example.test/"}],
        "depths": {"https://example.test/": 0, "https://example.test/next": 1},
        "pages_crawled": 1,
    }
    strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=1, resume_state=saved_state)

    results = await run_strategy(strategy, "https://example.test/", stream)

    # The saved run already used the whole budget, so nothing more is crawled.
    assert results == []
