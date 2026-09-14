"""
Regression test for BFSDeepCrawlStrategy._arun_batch double-crawling the start
URL when the start page contains a link back to itself (e.g. a "Home"/logo nav
link, a canonical self-link, or a bare href="#" which normalizes to the base
URL after fragment stripping).

_arun_stream() seeds `visited` with the current level's own URLs before
running link discovery on them (see bfs_strategy.py, `visited.update(urls)`),
but _arun_batch() never did — so the start URL (the only member of level 0,
which never passes through link_discovery's `visited.add()` since it isn't
"discovered" as a link) was absent from `visited` while its own outgoing
links were scanned. A self-link was therefore treated as a brand-new,
unvisited URL and re-queued for depth 1, silently duplicating the start page
in the results and corrupting its recorded depth.
"""
import pytest
from unittest.mock import MagicMock

from crawl4ai.deep_crawling import BFSDeepCrawlStrategy


def _make_mock_config():
    """Minimal CrawlerRunConfig stand-in supporting the .clone(...) calls
    _arun_batch/_arun_stream make internally."""
    config = MagicMock()
    config.stream = False

    def clone_config(**kwargs):
        new_config = MagicMock()
        new_config.stream = kwargs.get("stream", False)
        new_config.clone = MagicMock(side_effect=clone_config)
        return new_config

    config.clone = MagicMock(side_effect=clone_config)
    return config


def _make_mock_crawler(site: dict):
    """site: mapping of url -> list of internal href strings found on that page."""

    async def mock_arun_many(urls, config):
        results = []
        for url in urls:
            result = MagicMock()
            result.url = url
            result.success = True
            result.metadata = {}
            hrefs = site.get(url, [])
            result.links = {"internal": [{"href": h} for h in hrefs], "external": []}
            results.append(result)

        # _arun_stream awaits an async-iterable; _arun_batch awaits a plain list.
        if config.stream:
            async def gen():
                for r in results:
                    yield r
            return gen()
        return results

    crawler = MagicMock()
    crawler.arun_many = mock_arun_many
    return crawler


class TestBFSBatchSelfLink:
    @pytest.mark.asyncio
    async def test_start_url_self_link_not_recrawled(self):
        """The start page links back to itself. Batch mode must not re-queue
        and re-crawl the start URL as if it were a newly discovered page."""
        site = {
            "https://example.com/": ["/", "/about"],
            "https://example.com/about": [],
        }
        strategy = BFSDeepCrawlStrategy(max_depth=2)
        crawler = _make_mock_crawler(site)
        config = _make_mock_config()

        results = await strategy._arun_batch("https://example.com/", crawler, config)

        urls = [r.url for r in results]
        assert urls.count("https://example.com/") == 1, (
            f"start URL crawled {urls.count('https://example.com/')} times, "
            f"expected exactly 1: {urls}"
        )
        assert set(urls) == {"https://example.com/", "https://example.com/about"}

    @pytest.mark.asyncio
    async def test_start_url_depth_not_overwritten(self):
        """The duplicate-crawl bug also corrupts depths[start_url] from 0 to 1
        (link_discovery re-adds it to next_level with next_depth)."""
        site = {
            "https://example.com/": ["/"],
        }
        strategy = BFSDeepCrawlStrategy(max_depth=2)
        crawler = _make_mock_crawler(site)
        config = _make_mock_config()

        results = await strategy._arun_batch("https://example.com/", crawler, config)

        start_results = [r for r in results if r.url == "https://example.com/"]
        assert len(start_results) == 1
        assert start_results[0].metadata["depth"] == 0

    @pytest.mark.asyncio
    async def test_batch_and_stream_modes_agree_on_self_link_site(self):
        """Batch and stream mode must produce the same set of crawled URLs
        for the same site graph (stream mode was already correct; this pins
        batch mode to match it)."""
        site = {
            "https://example.com/": ["/", "/about"],
            "https://example.com/about": [],
        }

        batch_strategy = BFSDeepCrawlStrategy(max_depth=2)
        batch_crawler = _make_mock_crawler(site)
        batch_config = _make_mock_config()
        batch_results = await batch_strategy._arun_batch(
            "https://example.com/", batch_crawler, batch_config
        )

        stream_strategy = BFSDeepCrawlStrategy(max_depth=2)
        stream_crawler = _make_mock_crawler(site)
        stream_config = _make_mock_config()
        stream_config.stream = True

        async def _collect_stream():
            gen = stream_strategy._arun_stream(
                "https://example.com/", stream_crawler, stream_config
            )
            collected = []
            async for r in gen:
                collected.append(r)
            return collected

        stream_results = await _collect_stream()

        assert sorted(r.url for r in batch_results) == sorted(r.url for r in stream_results)
