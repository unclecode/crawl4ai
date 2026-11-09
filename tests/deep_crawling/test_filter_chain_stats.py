"""FilterChain stats must count URLs, not per-filter verdicts.

A URL refused by several filters was counted once per refusing filter, so
``rejected_urls`` could exceed ``total_urls`` and ``passed + rejected`` no longer
matched the number of URLs the chain was asked about.
"""

import pytest

from crawl4ai.deep_crawling.filters import FilterChain, FilterStats, URLFilter


class _Verdict(URLFilter):
    def __init__(self, verdict: bool):
        super().__init__()
        self._verdict = verdict

    def apply(self, url: str) -> bool:
        return self._verdict


class _AsyncVerdict(URLFilter):
    def __init__(self, verdict: bool):
        super().__init__()
        self._verdict = verdict

    async def apply(self, url: str) -> bool:
        return self._verdict


@pytest.mark.asyncio
async def test_two_async_filters_rejecting_one_url_count_it_once():
    chain = FilterChain([_AsyncVerdict(False), _AsyncVerdict(False)])

    assert await chain.apply("https://example.com/a") is False

    stats: FilterStats = chain.stats
    assert stats.total_urls == 1
    assert stats.passed_urls == 0
    assert stats.rejected_urls == 1


@pytest.mark.asyncio
async def test_counters_stay_consistent_across_mixed_verdicts():
    chain = FilterChain([_Verdict(True), _AsyncVerdict(True), _AsyncVerdict(False)])

    assert await chain.apply("https://example.com/a") is False
    assert await chain.apply("https://example.com/b") is False

    stats = chain.stats
    assert stats.total_urls == 2
    assert stats.passed_urls + stats.rejected_urls == stats.total_urls


@pytest.mark.asyncio
async def test_passing_urls_are_still_counted():
    chain = FilterChain([_Verdict(True), _AsyncVerdict(True)])

    assert await chain.apply("https://example.com/a") is True

    assert (chain.stats.total_urls, chain.stats.passed_urls, chain.stats.rejected_urls) == (1, 1, 0)
