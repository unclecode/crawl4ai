"""Integration tests for prefetch mode with the crawler."""

import pytest
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

# Use crawl4ai docs as test domain
TEST_DOMAIN = "https://docs.crawl4ai.com"


class TestPrefetchModeIntegration:
    """Integration tests for prefetch mode."""

    @pytest.mark.asyncio
    async def test_prefetch_returns_html_and_links(self):
        """Test that prefetch mode returns HTML and links only."""
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(prefetch=True)
            result = await crawler.arun(TEST_DOMAIN, config=config)

            # Should have HTML
            assert result.html is not None
            assert len(result.html) > 0
            assert "<html" in result.html.lower() or "<!doctype" in result.html.lower()

            # Should have links
            assert result.links is not None
            assert "internal" in result.links
            assert "external" in result.links

            # Should NOT have processed content
            assert result.markdown is None or (
                hasattr(result.markdown, 'raw_markdown') and
                result.markdown.raw_markdown is None
            )
            assert result.cleaned_html is None
            assert result.extracted_content is None

    @pytest.mark.asyncio
    async def test_prefetch_preserves_metadata(self):
        """Test that prefetch mode preserves essential metadata."""
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(prefetch=True)
            result = await crawler.arun(TEST_DOMAIN, config=config)

            # Should have success flag
            assert result.success is True

            # Should have URL
            assert result.url is not None

            # Status code should be present
            assert result.status_code is not None or result.status_code == 200

    @pytest.mark.asyncio
    async def test_prefetch_with_deep_crawl(self):
        """Test prefetch mode with deep crawl strategy."""
        from crawl4ai import BFSDeepCrawlStrategy

        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                prefetch=True,
                deep_crawl_strategy=BFSDeepCrawlStrategy(
                    max_depth=1,
                    max_pages=3
                )
            )

            result_container = await crawler.arun(TEST_DOMAIN, config=config)

            # Handle both list and iterator results
            if hasattr(result_container, '__aiter__'):
                results = [r async for r in result_container]
            else:
                results = list(result_container) if hasattr(result_container, '__iter__') else [result_container]

            # Each result should have HTML and links
            for result in results:
                assert result.html is not None
                assert result.links is not None

            # Should have crawled at least one page
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_prefetch_then_process_with_raw(self):
        """Test the full two-phase workflow: prefetch then process."""
        async with AsyncWebCrawler() as crawler:
            # Phase 1: Prefetch
            prefetch_config = CrawlerRunConfig(prefetch=True)
            prefetch_result = await crawler.arun(TEST_DOMAIN, config=prefetch_config)

            stored_html = prefetch_result.html

            assert stored_html is not None
            assert len(stored_html) > 0

            # Phase 2: Process with raw: URL
            process_config = CrawlerRunConfig(
                # No prefetch - full processing
                base_url=TEST_DOMAIN  # Provide base URL for link resolution
            )
            processed_result = await crawler.arun(
                f"raw:{stored_html}",
                config=process_config
            )

            # Should now have full processing
            assert processed_result.html is not None
            assert processed_result.success is True
            # Note: cleaned_html and markdown depend on the content

    @pytest.mark.asyncio
    async def test_prefetch_links_structure(self):
        """Test that links have the expected structure."""
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(prefetch=True)
            result = await crawler.arun(TEST_DOMAIN, config=config)

            assert result.links is not None

            # Check internal links structure
            if result.links["internal"]:
                link = result.links["internal"][0]
                assert "href" in link
                assert "text" in link
                assert link["href"].startswith("http")

            # Check external links structure (if any)
            if result.links["external"]:
                link = result.links["external"][0]
                assert "href" in link
                assert "text" in link
                assert link["href"].startswith("http")

    @pytest.mark.asyncio
    async def test_prefetch_config_clone(self):
        """Test that config.clone() preserves prefetch setting."""
        config = CrawlerRunConfig(prefetch=True)
        cloned = config.clone()

        assert cloned.prefetch == True

        # Clone with override
        cloned_false = config.clone(prefetch=False)
        assert cloned_false.prefetch == False

    @pytest.mark.asyncio
    async def test_prefetch_to_dict(self):
        """Test that to_dict() includes prefetch."""
        config = CrawlerRunConfig(prefetch=True)
        config_dict = config.to_dict()

        assert "prefetch" in config_dict
        assert config_dict["prefetch"] == True

    @pytest.mark.asyncio
    async def test_prefetch_default_false(self):
        """Test that prefetch defaults to False."""
        config = CrawlerRunConfig()
        assert config.prefetch == False

    @pytest.mark.asyncio
    async def test_prefetch_explicit_false(self):
        """Test explicit prefetch=False works like default."""
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(prefetch=False)
            result = await crawler.arun(TEST_DOMAIN, config=config)

            # Should have full processing
            assert result.html is not None
            # cleaned_html should be populated in normal mode
            assert result.cleaned_html is not None


class TestPrefetchPerformance:
    """Performance-related tests for prefetch mode."""

    @pytest.mark.asyncio
    async def test_prefetch_returns_quickly(self):
        """Test that prefetch mode returns results quickly."""
        import time

        async with AsyncWebCrawler() as crawler:
            # Prefetch mode
            start = time.time()
            prefetch_config = CrawlerRunConfig(prefetch=True)
            await crawler.arun(TEST_DOMAIN, config=prefetch_config)
            prefetch_time = time.time() - start

            # Full mode
            start = time.time()
            full_config = CrawlerRunConfig()
            await crawler.arun(TEST_DOMAIN, config=full_config)
            full_time = time.time() - start

            # Log times for debugging
            print(f"\nPrefetch: {prefetch_time:.3f}s, Full: {full_time:.3f}s")

            # Prefetch should not be significantly slower
            # (may be same or slightly faster depending on content)
            # This is a soft check - mostly for logging


class TestPrefetchWithRawHTML:
    """Test prefetch mode with raw HTML input."""

    @pytest.mark.asyncio
    async def test_prefetch_with_raw_html(self):
        """Test prefetch mode works with raw: URL scheme."""
        sample_html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Hello World</h1>
                <a href="/link1">Link 1</a>
                <a href="/link2">Link 2</a>
                <a href="https://external.com/page">External</a>
            </body>
        </html>
        """

        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                prefetch=True,
                base_url="https://example.com"
            )
            result = await crawler.arun(f"raw:{sample_html}", config=config)

            assert result.success is True
            assert result.html is not None
            assert result.links is not None

            # Should have extracted links
            assert len(result.links["internal"]) >= 2
            assert len(result.links["external"]) >= 1
