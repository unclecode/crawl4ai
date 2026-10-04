"""Filter-chain statistics count each URL once, regardless of filter count."""

import asyncio

from crawl4ai.deep_crawling.filters import FilterChain, URLFilter


class AsyncResultFilter(URLFilter):
    def __init__(self, result):
        super().__init__()
        self.result = result

    async def apply(self, url):
        return self.result


def test_multiple_async_rejections_count_one_url():
    chain = FilterChain([AsyncResultFilter(False), AsyncResultFilter(False)])

    assert asyncio.run(chain.apply("https://example.com/one")) is False
    assert chain.stats.total_urls == 1
    assert chain.stats.rejected_urls == 1
    assert chain.stats.passed_urls == 0


def test_falsy_async_result_counts_as_rejection():
    chain = FilterChain([AsyncResultFilter(None)])

    assert asyncio.run(chain.apply("https://example.com/one")) is False
    assert chain.stats.total_urls == 1
    assert chain.stats.rejected_urls == 1


def test_repeated_calls_keep_url_counter_invariant():
    first = AsyncResultFilter(True)
    second = AsyncResultFilter(True)
    chain = FilterChain([first, second])
    assert asyncio.run(chain.apply("https://example.com/pass")) is True

    first.result = second.result = False
    assert asyncio.run(chain.apply("https://example.com/reject")) is False
    assert chain.stats.total_urls == 2
    assert chain.stats.passed_urls == 1
    assert chain.stats.rejected_urls == 1
    assert chain.stats.total_urls == chain.stats.passed_urls + chain.stats.rejected_urls
