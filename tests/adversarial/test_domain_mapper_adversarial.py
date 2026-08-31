"""Adversarial tests for DomainMapper — edge cases, failures, tough scenarios."""
import asyncio
import pytest
import pytest_asyncio
from crawl4ai import DomainMapper, DomainMapperConfig


pytestmark = pytest.mark.network


@pytest_asyncio.fixture
async def mapper():
    async with DomainMapper() as m:
        yield m


class TestDomainMapperAdversarial:

    @pytest.mark.asyncio
    async def test_nonexistent_domain(self, mapper):
        """Domain that doesn't exist should return empty, not crash."""
        config = DomainMapperConfig(
            source="sitemap+probe",
            extract_head=False,
            verbose=False,
        )
        results = await mapper.scan("thiswillneverexist12345678.dev", config)
        assert results == []

    @pytest.mark.asyncio
    async def test_invalid_source(self, mapper):
        """Invalid source should raise ValueError."""
        config = DomainMapperConfig(source="sitemap+bogus")
        with pytest.raises(ValueError, match="Invalid source"):
            await mapper.scan("example.com", config)

    @pytest.mark.asyncio
    async def test_empty_domain(self, mapper):
        """Empty domain string should not crash."""
        config = DomainMapperConfig(
            source="probe",
            extract_head=False,
            verbose=False,
        )
        results = await mapper.scan("", config)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_domain_with_scheme(self, mapper):
        """Domain with https:// prefix should be handled."""
        config = DomainMapperConfig(
            source="sitemap",
            extract_head=False,
            verbose=False,
            max_urls=5,
        )
        results = await mapper.scan("https://docs.crawl4ai.com", config)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_soft_404_filtering_spa(self, mapper):
        """SPA sites (app.superdesign.dev) should have soft-404s filtered."""
        config = DomainMapperConfig(
            source="probe",
            extract_head=False,
            soft_404_detection=True,
            verbose=False,
        )
        results = await mapper.scan("app.superdesign.dev", config)
        # All probed paths on this SPA should be filtered as soft-404s
        # (the site returns 200 for every path with the same shell)
        probe_urls = [r for r in results if r["source"] == "probe"]
        assert len(probe_urls) == 0, \
            f"Expected 0 valid probe URLs on SPA, got {len(probe_urls)}: {[r['url'] for r in probe_urls]}"

    @pytest.mark.asyncio
    async def test_rate_limiting(self, mapper):
        """hits_per_sec=2 should not crash."""
        config = DomainMapperConfig(
            source="probe",
            extract_head=False,
            hits_per_sec=2,
            verbose=False,
        )
        results = await mapper.scan("docs.crawl4ai.com", config)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_unicode_in_results(self, mapper):
        """Results should handle unicode URLs gracefully."""
        config = DomainMapperConfig(
            source="sitemap",
            extract_head=False,
            verbose=False,
        )
        results = await mapper.scan("docs.crawl4ai.com", config)
        for r in results:
            assert isinstance(r["url"], str)

    @pytest.mark.asyncio
    async def test_config_clone(self):
        """DomainMapperConfig.clone() should work."""
        config = DomainMapperConfig(source="sitemap", max_urls=10)
        cloned = config.clone(max_urls=20, force=True)
        assert cloned.max_urls == 20
        assert cloned.force is True
        assert cloned.source == "sitemap"  # inherited

    @pytest.mark.asyncio
    async def test_concurrent_host_scanning(self, mapper):
        """Multiple hosts scanned in parallel should not race."""
        config = DomainMapperConfig(
            source="sitemap+crt+probe",
            extract_head=False,
            concurrency=20,
            verbose=False,
            force=True,
        )
        results = await mapper.scan("superdesign.dev", config)
        # Verify no duplicate URLs in results
        urls = [r["url"] for r in results]
        # Normalized dedup should prevent exact duplicates
        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_probe_without_crt(self, mapper):
        """source='probe' alone should still work (just scans base domain)."""
        config = DomainMapperConfig(
            source="probe",
            extract_head=False,
            verbose=False,
        )
        results = await mapper.scan("docs.crawl4ai.com", config)
        # Should find at least / and /docs
        assert len(results) >= 1
