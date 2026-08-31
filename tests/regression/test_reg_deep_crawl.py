"""
Crawl4AI Regression Tests - Deep Crawling

Tests deep crawling strategies (BFS, DFS, BestFirst), URL filters, URL scorers,
URL normalization, and streaming mode using real browser crawling with no mocking.
"""

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.deep_crawling import (
    BFSDeepCrawlStrategy,
    DFSDeepCrawlStrategy,
    BestFirstCrawlingStrategy,
)
from crawl4ai.deep_crawling.filters import (
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter,
    FilterChain,
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer, CompositeScorer
from crawl4ai.utils import (
    normalize_url_for_deep_crawl,
    efficient_normalize_url_for_deep_crawl,
)


def _to_ip_url(local_server: str) -> str:
    """Convert http://localhost:PORT to http://127.0.0.1:PORT.

    Deep crawl strategies reject netlocs without a dot (e.g. 'localhost'),
    so we use the IP form which contains dots and passes validation.
    """
    return local_server.replace("localhost", "127.0.0.1")


# ---------------------------------------------------------------------------
# BFS Deep Crawl
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bfs_basic(local_server):
    """BFS deep crawl of /deep/hub at depth 1 should return hub + sub pages."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=10)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        assert len(result_list) >= 1, "Should return at least the hub page"

        # First result should be the hub
        assert "/deep/hub" in result_list[0].url, "First result should be the hub page"

        # Check sub pages are present
        sub_urls = [r.url for r in result_list if "/deep/sub" in r.url]
        assert len(sub_urls) >= 1, "Should discover at least one sub page"

        # Verify metadata has depth key
        for r in result_list:
            assert r.metadata is not None, "Each result should have metadata"
            assert "depth" in r.metadata, "Metadata should contain 'depth' key"

        # Hub should be at depth 0
        hub_result = result_list[0]
        assert hub_result.metadata["depth"] == 0, "Hub should be at depth 0"

        # Sub pages should be at depth 1
        for r in result_list:
            if "/deep/sub" in r.url:
                assert r.metadata["depth"] == 1, f"Sub page {r.url} should be at depth 1"


@pytest.mark.asyncio
async def test_bfs_depth_enforcement(local_server):
    """BFS with max_depth=1 must not include leaf pages at depth 2."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=20)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        leaf_urls = [r.url for r in result_list if "leaf" in r.url]
        assert len(leaf_urls) == 0, (
            f"No leaf pages should appear at max_depth=1, but found: {leaf_urls}"
        )


@pytest.mark.asyncio
async def test_bfs_max_pages(local_server):
    """BFS with max_pages=3 should return at most 3 results."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BFSDeepCrawlStrategy(max_depth=3, max_pages=3)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        assert len(result_list) <= 3, (
            f"Expected at most 3 results, got {len(result_list)}"
        )


@pytest.mark.asyncio
async def test_bfs_level_order(local_server):
    """BFS should return results in level order: depth 0 before depth 1 before depth 2."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=20)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        depths = [r.metadata["depth"] for r in result_list]

        # Verify ordering: once a higher depth appears, no lower depth should follow
        max_depth_seen = -1
        for i, d in enumerate(depths):
            if d < max_depth_seen:
                pytest.fail(
                    f"BFS level order violated at index {i}: depth {d} appeared "
                    f"after depth {max_depth_seen}. Full sequence: {depths}"
                )
            max_depth_seen = max(max_depth_seen, d)


# ---------------------------------------------------------------------------
# DFS Deep Crawl
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dfs_basic(local_server):
    """DFS deep crawl at depth 2 should find both sub pages and leaf pages."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = DFSDeepCrawlStrategy(max_depth=2, max_pages=10)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        urls = [r.url for r in result_list]

        sub_pages = [u for u in urls if "/deep/sub" in u and "leaf" not in u]
        leaf_pages = [u for u in urls if "leaf" in u]

        assert len(sub_pages) >= 1, "DFS should visit at least one sub page"
        assert len(leaf_pages) >= 1, "DFS at depth 2 should visit at least one leaf page"


@pytest.mark.asyncio
async def test_dfs_depth_first_order(local_server):
    """DFS should explore depth-first: some leaf page should appear before all sub pages are visited."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    # Give enough pages to see the DFS pattern
    strategy = DFSDeepCrawlStrategy(max_depth=2, max_pages=15)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        urls = [r.url for r in result_list]

        # Find indices of sub pages and leaf pages
        sub_indices = [i for i, u in enumerate(urls) if "/deep/sub" in u and "leaf" not in u]
        leaf_indices = [i for i, u in enumerate(urls) if "leaf" in u]

        if sub_indices and leaf_indices:
            # In DFS, at least one leaf should appear before the last sub page
            earliest_leaf = min(leaf_indices)
            latest_sub = max(sub_indices)
            assert earliest_leaf < latest_sub, (
                "DFS should explore a branch deeply before exhausting all sub pages. "
                f"Earliest leaf at index {earliest_leaf}, latest sub at index {latest_sub}."
            )


@pytest.mark.asyncio
async def test_dfs_max_depth(local_server):
    """DFS with max_depth=1 should only visit hub and sub pages, no leaves."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = DFSDeepCrawlStrategy(max_depth=1, max_pages=20)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        leaf_urls = [r.url for r in result_list if "leaf" in r.url]
        assert len(leaf_urls) == 0, (
            f"DFS with max_depth=1 should not reach leaf pages, found: {leaf_urls}"
        )


# ---------------------------------------------------------------------------
# BestFirst Deep Crawl
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bestfirst_basic(local_server):
    """BestFirst deep crawl should return results from /deep/hub."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BestFirstCrawlingStrategy(max_depth=2, max_pages=10)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        assert len(result_list) >= 1, "BestFirst should return at least the start page"
        assert result_list[0].success, "First result should be successful"


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_url_pattern_filter_include(local_server):
    """URLPatternFilter with sub1 pattern should only crawl the sub1 branch."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    url_filter = URLPatternFilter(patterns=["*/sub1*"])
    chain = FilterChain(filters=[url_filter])
    strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=10, filter_chain=chain)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        # Hub (depth 0) bypasses filter; subsequent URLs should only match sub1
        non_hub = [r for r in result_list if r.metadata.get("depth", 0) > 0]
        for r in non_hub:
            assert "sub1" in r.url, (
                f"All non-hub results should be in sub1 branch, but found: {r.url}"
            )


@pytest.mark.asyncio
async def test_url_pattern_filter_exclude(local_server):
    """URLPatternFilter with reverse=True should exclude leaf pages."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    url_filter = URLPatternFilter(patterns=["*/leaf*"], reverse=True)
    chain = FilterChain(filters=[url_filter])
    strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=15, filter_chain=chain)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        leaf_urls = [r.url for r in result_list if "leaf" in r.url]
        assert len(leaf_urls) == 0, (
            f"Reverse pattern filter should exclude leaf pages, found: {leaf_urls}"
        )


@pytest.mark.asyncio
async def test_domain_filter(local_server):
    """DomainFilter allowing only 127.0.0.1 should keep local URLs only."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    domain_filter = DomainFilter(allowed_domains=["127.0.0.1"])
    chain = FilterChain(filters=[domain_filter])
    strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=10, filter_chain=chain)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        for r in result_list:
            assert "127.0.0.1" in r.url, (
                f"All results should be local, but found: {r.url}"
            )


@pytest.mark.asyncio
async def test_filter_chain(local_server):
    """FilterChain combining URLPatternFilter and DomainFilter should apply both."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    url_filter = URLPatternFilter(patterns=["*/sub1*"])
    domain_filter = DomainFilter(allowed_domains=["127.0.0.1"])
    chain = FilterChain(filters=[url_filter, domain_filter])
    strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=10, filter_chain=chain)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        non_hub = [r for r in result_list if r.metadata.get("depth", 0) > 0]
        for r in non_hub:
            assert "sub1" in r.url, (
                f"URL pattern filter not applied: {r.url}"
            )
            assert "127.0.0.1" in r.url, (
                f"Domain filter not applied: {r.url}"
            )


def test_content_type_filter():
    """ContentTypeFilter should pass HTML URLs and reject image/pdf extensions."""
    ct_filter = ContentTypeFilter(allowed_types=["text/html"])

    assert ct_filter.apply("http://example.com/page") is True, (
        "URL with no extension should pass (assumed HTML)"
    )
    assert ct_filter.apply("http://example.com/page.html") is True, (
        ".html should pass text/html filter"
    )
    assert ct_filter.apply("http://example.com/photo.jpg") is False, (
        ".jpg should be rejected by text/html filter"
    )
    assert ct_filter.apply("http://example.com/doc.pdf") is False, (
        ".pdf should be rejected by text/html filter"
    )


# ---------------------------------------------------------------------------
# Scorers
# ---------------------------------------------------------------------------


def test_keyword_scorer():
    """KeywordRelevanceScorer should rank URLs containing keywords higher."""
    scorer = KeywordRelevanceScorer(keywords=["technology", "science"])

    tech_score = scorer.score("http://example.com/technology/article")
    generic_score = scorer.score("http://example.com/about/contact")

    assert tech_score > generic_score, (
        f"URL with keyword should score higher: tech={tech_score}, generic={generic_score}"
    )

    both_score = scorer.score("http://example.com/technology/science-report")
    assert both_score >= tech_score, (
        "URL matching both keywords should score at least as high as one keyword"
    )


def test_composite_scorer():
    """CompositeScorer combining two scorers should produce scores without error."""
    scorer1 = KeywordRelevanceScorer(keywords=["python"], weight=1.0)
    scorer2 = KeywordRelevanceScorer(keywords=["crawl"], weight=0.5)
    composite = CompositeScorer(scorers=[scorer1, scorer2])

    score = composite.score("http://example.com/python-crawl-guide")
    assert isinstance(score, float), "Composite score should be a float"
    assert score > 0, "URL matching both scorers' keywords should have positive score"

    zero_score = composite.score("http://example.com/unrelated-page")
    assert zero_score == 0.0, "URL matching no keywords should score zero"


# ---------------------------------------------------------------------------
# URL normalization in deep crawl context
# ---------------------------------------------------------------------------


def test_deep_crawl_url_normalization():
    """normalize_url_for_deep_crawl should resolve relative URLs against base."""
    base = "http://example.com/deep/hub"

    result = normalize_url_for_deep_crawl("/deep/sub1", base)
    assert result == "http://example.com/deep/sub1", (
        f"Relative URL not resolved correctly: {result}"
    )

    result2 = normalize_url_for_deep_crawl("sub2", base)
    assert "example.com" in result2, "Relative path should resolve against base"
    assert "sub2" in result2, "Relative path should include the target"


def test_deep_crawl_trailing_slash():
    """Trailing slashes should be preserved during normalization (fix #1520)."""
    base = "http://example.com/"

    with_slash = normalize_url_for_deep_crawl("/path/", base)
    without_slash = normalize_url_for_deep_crawl("/path", base)

    # The function uses `parsed.path or '/'` which preserves trailing slashes
    assert with_slash.endswith("/path/"), (
        f"Trailing slash should be preserved: {with_slash}"
    )
    assert not without_slash.endswith("/"), (
        f"No trailing slash should be added: {without_slash}"
    )


def test_deep_crawl_deduplication():
    """Same URL with different fragments should normalize to the same string."""
    base = "http://example.com/"

    url1 = normalize_url_for_deep_crawl("/page#section1", base)
    url2 = normalize_url_for_deep_crawl("/page#section2", base)
    url3 = normalize_url_for_deep_crawl("/page", base)

    assert url1 == url2, (
        f"Fragment-only difference should normalize to same URL: {url1} vs {url2}"
    )
    assert url1 == url3, (
        f"URL with and without fragment should normalize the same: {url1} vs {url3}"
    )


def test_deep_crawl_efficient_normalization():
    """efficient_normalize_url_for_deep_crawl should produce consistent results."""
    base = "http://example.com/deep/hub"

    result = efficient_normalize_url_for_deep_crawl("/deep/sub1", base)
    assert result == "http://example.com/deep/sub1", (
        f"Efficient normalization failed: {result}"
    )

    # Fragments should be removed
    result_frag = efficient_normalize_url_for_deep_crawl("/page#anchor", base)
    assert "#" not in result_frag, "Fragments should be stripped"


def test_deep_crawl_normalization_none_input():
    """Normalizing None or empty string should return None."""
    result_none = normalize_url_for_deep_crawl(None, "http://example.com/")
    assert result_none is None, "None input should return None"

    result_empty = normalize_url_for_deep_crawl("", "http://example.com/")
    assert result_empty is None, "Empty string should return None"


def test_deep_crawl_normalization_case():
    """Hostname normalization should be case-insensitive."""
    base = "http://Example.COM/"

    result = normalize_url_for_deep_crawl("/Page", base)
    assert "example.com" in result, (
        f"Hostname should be lowercased: {result}"
    )


# ---------------------------------------------------------------------------
# Stream mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deep_crawl_stream(local_server):
    """Deep crawl with stream=True should yield results via async iteration."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=5)
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        verbose=False,
    )

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = []
        async for result in await crawler.arun(url=hub_url, config=config):
            results.append(result)

        assert len(results) > 0, "Stream mode should yield at least one result"
        assert results[0].success, "First streamed result should be successful"


# ---------------------------------------------------------------------------
# Real URL deep crawl
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.network
async def test_deep_crawl_real():
    """Deep crawl https://quotes.toscrape.com with BFS to verify real-world usage."""
    strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=3)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url="https://quotes.toscrape.com", config=config)

        result_list = list(results)
        assert len(result_list) >= 1, "Should crawl at least the start page"
        assert result_list[0].success, "Start page should crawl successfully"
        # The site has links; with max_depth=1 we should find some
        if len(result_list) > 1:
            assert result_list[1].metadata.get("depth") == 1, (
                "Second-level pages should have depth 1"
            )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bfs_max_pages_one(local_server):
    """BFS with max_pages=1 should return exactly 1 result (the start page)."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BFSDeepCrawlStrategy(max_depth=5, max_pages=1)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        assert len(result_list) == 1, (
            f"max_pages=1 should yield exactly 1 result, got {len(result_list)}"
        )
        assert "/deep/hub" in result_list[0].url, "The single result should be the hub"


@pytest.mark.asyncio
async def test_dfs_max_pages_one(local_server):
    """DFS with max_pages=1 should return exactly 1 result."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = DFSDeepCrawlStrategy(max_depth=5, max_pages=1)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        assert len(result_list) == 1, (
            f"max_pages=1 should yield exactly 1 result, got {len(result_list)}"
        )


@pytest.mark.asyncio
async def test_bfs_depth_zero(local_server):
    """BFS with max_depth=0 should only return the start page."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BFSDeepCrawlStrategy(max_depth=0, max_pages=100)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        assert len(result_list) == 1, (
            f"max_depth=0 should yield exactly 1 result, got {len(result_list)}"
        )
        assert result_list[0].metadata["depth"] == 0, "Only depth-0 page should exist"


@pytest.mark.asyncio
async def test_bfs_results_have_parent_url(local_server):
    """Each non-root result should have a parent_url in metadata."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=10)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        for r in result_list:
            assert "parent_url" in r.metadata, (
                f"Result for {r.url} should have 'parent_url' in metadata"
            )
            if r.metadata["depth"] == 0:
                assert r.metadata["parent_url"] is None, (
                    "Root page should have parent_url=None"
                )
            else:
                assert r.metadata["parent_url"] is not None, (
                    f"Non-root page {r.url} should have a parent_url"
                )


def test_url_pattern_filter_no_match():
    """URLPatternFilter should reject URLs that match no patterns."""
    f = URLPatternFilter(patterns=["*/special/*"])
    assert f.apply("http://example.com/normal/page") is False
    assert f.apply("http://example.com/special/page") is True


def test_domain_filter_blocked():
    """DomainFilter with blocked_domains should reject those domains."""
    f = DomainFilter(blocked_domains=["evil.com"])
    assert f.apply("http://evil.com/page") is False
    assert f.apply("http://good.com/page") is True


def test_domain_filter_subdomain():
    """DomainFilter should handle subdomains of allowed domains."""
    f = DomainFilter(allowed_domains=["example.com"])
    assert f.apply("http://example.com/page") is True
    assert f.apply("http://sub.example.com/page") is True
    assert f.apply("http://other.com/page") is False


def test_keyword_scorer_case_insensitive():
    """KeywordRelevanceScorer should be case-insensitive by default."""
    scorer = KeywordRelevanceScorer(keywords=["Python"])
    score_lower = scorer.score("http://example.com/python-guide")
    score_upper = scorer.score("http://example.com/PYTHON-GUIDE")
    assert score_lower > 0, "Lowercase URL should match"
    assert score_upper > 0, "Uppercase URL should match"


def test_keyword_scorer_no_match():
    """KeywordRelevanceScorer should return 0 for URLs with no keyword matches."""
    scorer = KeywordRelevanceScorer(keywords=["quantum", "physics"])
    score = scorer.score("http://example.com/cooking/recipes")
    assert score == 0.0, "No keywords matched should give zero score"
