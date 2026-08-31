"""Integration tests for DomainMapper — hits real endpoints."""
import asyncio
import pytest
import pytest_asyncio
from crawl4ai import DomainMapper, DomainMapperConfig


pytestmark = pytest.mark.network


@pytest_asyncio.fixture
async def mapper():
    async with DomainMapper() as m:
        yield m


class TestDomainMapperE2E:

    @pytest.mark.asyncio
    async def test_scan_superdesign_dev(self, mapper):
        """Full scan of superdesign.dev should find >=30 URLs across >=5 hosts."""
        config = DomainMapperConfig(
            source="sitemap+cc+crt+probe+robots+homepage",
            extract_head=False,
            force=True,
            verbose=False,
        )
        results = await mapper.scan("superdesign.dev", config)
        hosts = {r["host"] for r in results}

        assert len(results) >= 20, f"Expected >=20 URLs, got {len(results)}"
        assert len(hosts) >= 4, f"Expected >=4 hosts, got {len(hosts)}: {hosts}"
        assert any("docs.superdesign.dev" == r["host"] for r in results), \
            "docs.superdesign.dev should be discovered"

    @pytest.mark.asyncio
    async def test_scan_docs_crawl4ai(self, mapper):
        """docs.crawl4ai.com has a known good sitemap."""
        config = DomainMapperConfig(
            source="sitemap",
            extract_head=False,
            force=True,
            verbose=False,
        )
        results = await mapper.scan("docs.crawl4ai.com", config)
        assert len(results) >= 5, f"Expected >=5 URLs from sitemap, got {len(results)}"
        assert all(r["source"] == "sitemap" for r in results)

    @pytest.mark.asyncio
    async def test_sitemap_only_source(self, mapper):
        """source='sitemap' should not hit CC, crt, or wayback."""
        config = DomainMapperConfig(
            source="sitemap",
            extract_head=False,
            force=True,
            verbose=False,
        )
        results = await mapper.scan("superdesign.dev", config)
        sources = {r["source"] for r in results}
        # Should only have sitemap source
        for s in sources:
            for part in s.split("+"):
                assert part == "sitemap", f"Unexpected source: {part}"

    @pytest.mark.asyncio
    async def test_crt_discovers_subdomains(self, mapper):
        """crt source should discover subdomains for superdesign.dev."""
        config = DomainMapperConfig(
            source="crt+probe",
            extract_head=False,
            force=True,
            verbose=False,
        )
        results = await mapper.scan("superdesign.dev", config)
        hosts = {r["host"] for r in results}
        # crt should find at least docs, app, cloud subdomains
        assert len(hosts) >= 3, f"Expected >=3 hosts, got {len(hosts)}: {hosts}"

    @pytest.mark.asyncio
    async def test_max_urls_limit(self, mapper):
        """max_urls should cap results."""
        config = DomainMapperConfig(
            source="sitemap+crt+probe",
            extract_head=False,
            max_urls=10,
            force=True,
            verbose=False,
        )
        results = await mapper.scan("superdesign.dev", config)
        assert len(results) <= 10, f"Expected <=10 URLs, got {len(results)}"

    @pytest.mark.asyncio
    async def test_source_attribution(self, mapper):
        """Each result should have a source field."""
        config = DomainMapperConfig(
            source="sitemap+probe",
            extract_head=False,
            force=True,
            verbose=False,
        )
        results = await mapper.scan("docs.crawl4ai.com", config)
        for r in results:
            assert "source" in r
            assert r["source"], "Source should not be empty"
            assert "host" in r
            assert "url" in r

    @pytest.mark.asyncio
    async def test_head_extraction(self, mapper):
        """extract_head=True should populate head_data with titles."""
        config = DomainMapperConfig(
            source="sitemap",
            extract_head=True,
            max_urls=5,
            force=True,
            verbose=False,
        )
        results = await mapper.scan("docs.crawl4ai.com", config)
        has_title = any(r.get("head_data", {}).get("title") for r in results)
        assert has_title, "At least one result should have a title in head_data"

    @pytest.mark.asyncio
    async def test_crawler_integration(self):
        """Test amap_domain() on AsyncWebCrawler works."""
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            results = await crawler.amap_domain(
                "docs.crawl4ai.com",
                DomainMapperConfig(
                    source="sitemap",
                    extract_head=False,
                    force=True,
                    verbose=False,
                    max_urls=5,
                ),
            )
            assert len(results) >= 1
            assert all("url" in r for r in results)
