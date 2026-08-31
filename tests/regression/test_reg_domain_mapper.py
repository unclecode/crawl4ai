"""
Crawl4AI Regression Tests - DomainMapper

Tests DomainMapper functionality: host discovery, soft-404 detection,
multi-source scanning, post-processing, and crawler integration.

All network tests use real endpoints.
"""

import pytest
import pytest_asyncio
from crawl4ai import DomainMapper, DomainMapperConfig, AsyncWebCrawler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def mapper():
    async with DomainMapper() as m:
        yield m


# ---------------------------------------------------------------------------
# Basic scan tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.network
async def test_basic_scan(mapper):
    """Scan a domain with sitemaps and get results."""
    config = DomainMapperConfig(
        source="sitemap",
        extract_head=False,
        verbose=False,
    )
    results = await mapper.scan("docs.crawl4ai.com", config)
    assert len(results) >= 1, "Should find at least 1 URL from sitemap"
    assert all("url" in r for r in results)
    assert all("host" in r for r in results)
    assert all("source" in r for r in results)


@pytest.mark.asyncio
@pytest.mark.network
async def test_scan_with_head_extraction(mapper):
    """Head extraction should populate title and meta."""
    config = DomainMapperConfig(
        source="sitemap",
        extract_head=True,
        max_urls=3,
        verbose=False,
    )
    results = await mapper.scan("docs.crawl4ai.com", config)
    assert len(results) >= 1
    has_title = any(r.get("head_data", {}).get("title") for r in results)
    assert has_title, "At least one result should have a title"


# ---------------------------------------------------------------------------
# Host discovery tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.network
async def test_crt_subdomain_discovery(mapper):
    """crt.sh should discover subdomains."""
    config = DomainMapperConfig(
        source="crt+probe",
        extract_head=False,
        verbose=False,
    )
    results = await mapper.scan("superdesign.dev", config)
    hosts = {r["host"] for r in results}
    assert len(hosts) >= 3, f"Expected >=3 hosts via crt, got {len(hosts)}: {hosts}"


@pytest.mark.asyncio
@pytest.mark.network
async def test_dns_subdomain_guessing(mapper):
    """DNS guessing should find common subdomains."""
    hosts = await mapper._guess_subdomains("crawl4ai.com", ["docs", "www", "api"], DomainMapperConfig())
    # docs.crawl4ai.com should resolve
    assert "docs.crawl4ai.com" in hosts


# ---------------------------------------------------------------------------
# Soft-404 detection tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.network
async def test_soft_404_detection(mapper):
    """SPA site should be detected as soft-404."""
    fp = await mapper._fingerprint_soft_404("app.superdesign.dev", DomainMapperConfig())
    assert fp is not None
    assert fp.status_code == 200, "SPA should return 200 for nonexistent paths"
    assert fp.title is not None, "Should capture the SPA shell title"


@pytest.mark.asyncio
@pytest.mark.network
async def test_soft_404_filters_probes(mapper):
    """Probing an SPA with soft-404 enabled should filter all paths."""
    config = DomainMapperConfig(
        source="probe",
        soft_404_detection=True,
        extract_head=False,
        verbose=False,
    )
    results = await mapper.scan("app.superdesign.dev", config)
    probe_urls = [r for r in results if r["source"] == "probe"]
    assert len(probe_urls) == 0, "All probe paths on SPA should be soft-404 filtered"


# ---------------------------------------------------------------------------
# Source isolation tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.network
async def test_sitemap_only_no_cross_contamination(mapper):
    """source='sitemap' should only produce sitemap-sourced results."""
    config = DomainMapperConfig(
        source="sitemap",
        extract_head=False,
        verbose=False,
    )
    results = await mapper.scan("docs.crawl4ai.com", config)
    for r in results:
        for part in r["source"].split("+"):
            assert part == "sitemap", f"Unexpected source: {part}"


@pytest.mark.asyncio
@pytest.mark.network
async def test_probe_only(mapper):
    """source='probe' should work standalone."""
    config = DomainMapperConfig(
        source="probe",
        extract_head=False,
        verbose=False,
    )
    results = await mapper.scan("docs.crawl4ai.com", config)
    assert isinstance(results, list)
    assert len(results) >= 1


# ---------------------------------------------------------------------------
# Post-processing tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.network
async def test_max_urls_respected(mapper):
    """max_urls should cap results."""
    config = DomainMapperConfig(
        source="sitemap+probe",
        extract_head=False,
        max_urls=5,
        verbose=False,
    )
    results = await mapper.scan("docs.crawl4ai.com", config)
    assert len(results) <= 5


@pytest.mark.asyncio
@pytest.mark.network
async def test_nonsense_filter_removes_assets(mapper):
    """Nonsense filter should remove JS/CSS/image URLs."""
    config = DomainMapperConfig(
        source="sitemap+homepage",
        extract_head=False,
        filter_nonsense_urls=True,
        verbose=False,
    )
    results = await mapper.scan("docs.crawl4ai.com", config)
    for r in results:
        url = r["url"].lower()
        assert not url.endswith(".js"), f"JS file should be filtered: {url}"
        assert not url.endswith(".css"), f"CSS file should be filtered: {url}"
        assert not url.endswith(".png"), f"Image should be filtered: {url}"


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_source_raises(mapper):
    """Invalid source should raise ValueError."""
    with pytest.raises(ValueError, match="Invalid source"):
        await mapper.scan("example.com", DomainMapperConfig(source="bogus"))


@pytest.mark.asyncio
@pytest.mark.network
async def test_nonexistent_domain(mapper):
    """Nonexistent domain should return empty list, not crash."""
    config = DomainMapperConfig(
        source="sitemap+probe",
        extract_head=False,
        verbose=False,
    )
    results = await mapper.scan("thiswillneverexist99999.dev", config)
    assert results == []


@pytest.mark.asyncio
@pytest.mark.network
async def test_domain_with_scheme_stripped(mapper):
    """Domain with https:// prefix should work."""
    config = DomainMapperConfig(
        source="sitemap",
        extract_head=False,
        max_urls=3,
        verbose=False,
    )
    results = await mapper.scan("https://docs.crawl4ai.com", config)
    assert len(results) >= 1


# ---------------------------------------------------------------------------
# Crawler integration tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.network
async def test_amap_domain_on_crawler():
    """AsyncWebCrawler.amap_domain() should work end-to-end."""
    async with AsyncWebCrawler() as crawler:
        results = await crawler.amap_domain(
            "docs.crawl4ai.com",
            DomainMapperConfig(
                source="sitemap",
                extract_head=False,
                max_urls=5,
                verbose=False,
            ),
        )
        assert len(results) >= 1
        assert all("url" in r for r in results)


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_config_clone():
    """DomainMapperConfig.clone() should produce correct copies."""
    config = DomainMapperConfig(source="sitemap", max_urls=10, verbose=True)
    cloned = config.clone(max_urls=20, force=True)
    assert cloned.max_urls == 20
    assert cloned.force is True
    assert cloned.source == "sitemap"
    assert cloned.verbose is True


@pytest.mark.asyncio
async def test_config_from_kwargs():
    """DomainMapperConfig.from_kwargs() should work."""
    config = DomainMapperConfig.from_kwargs({
        "source": "crt+probe",
        "max_urls": 50,
    })
    assert config.source == "crt+probe"
    assert config.max_urls == 50
    assert config.extract_head is True  # default
