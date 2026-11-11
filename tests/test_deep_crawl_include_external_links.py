"""Deep-crawl link discovery must not mutate the caller's CrawlResult.

With ``include_external=True`` the strategies did ``links += external`` on the
list taken straight out of ``result.links["internal"]``, so every external link
was also appended to the result the user gets back.
"""

import asyncio

import pytest

from crawl4ai import (
    BFSDeepCrawlStrategy,
    BestFirstCrawlingStrategy,
    DFSDeepCrawlStrategy,
)
from crawl4ai.models import CrawlResult


def _result() -> CrawlResult:
    return CrawlResult(
        url="https://example.com/",
        html="<html><body>x</body></html>",
        success=True,
        links={
            "internal": [{"href": "https://example.com/a"}],
            "external": [{"href": "https://other.com/b"}],
        },
    )


def _strategies():
    return [
        pytest.param(
            lambda: BFSDeepCrawlStrategy(
                max_depth=2, max_pages=10, include_external=True
            ),
            id="bfs",
        ),
        pytest.param(
            lambda: DFSDeepCrawlStrategy(
                max_depth=2, max_pages=10, include_external=True
            ),
            id="dfs",
        ),
        pytest.param(
            lambda: BestFirstCrawlingStrategy(
                max_depth=2, max_pages=10, include_external=True
            ),
            id="best-first",
        ),
    ]


@pytest.mark.parametrize("make_strategy", _strategies())
def test_link_discovery_leaves_result_links_untouched(make_strategy):
    result = _result()
    strategy = make_strategy()

    asyncio.run(
        strategy.link_discovery(result, "https://example.com/", 0, set(), [], {})
    )

    assert [link["href"] for link in result.links["internal"]] == [
        "https://example.com/a"
    ]
    assert [link["href"] for link in result.links["external"]] == [
        "https://other.com/b"
    ]
