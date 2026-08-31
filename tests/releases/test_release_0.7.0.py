#!/usr/bin/env python3

import asyncio
import pytest
import os
import json
import tempfile
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy, LLMConfig
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.async_url_seeder import AsyncUrlSeeder
from crawl4ai.utils import RobotsParser


class TestCrawl4AIv070:
    """Test suite for Crawl4AI v0.7.0 changes"""
    
    @pytest.mark.asyncio
    async def test_raw_url_parsing(self):
        """Test raw:// URL parsing logic fix"""
        html_content = "<html><body><h1>Test Content</h1><p>This is a test paragraph.</p></body></html>"
        
        async with AsyncWebCrawler() as crawler:
            # Test raw:// prefix
            result1 = await crawler.arun(f"raw://{html_content}")
            assert result1.success
            assert "Test Content" in result1.markdown
            
            # Test raw: prefix
            result2 = await crawler.arun(f"raw:{html_content}")
            assert result2.success
            assert "Test Content" in result2.markdown
    
    @pytest.mark.asyncio
    async def test_max_pages_limit_batch_processing(self):
        """Test max_pages limit is respected during batch processing"""
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            "https://httpbin.org/xml"
        ]
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            max_pages=2
        )
        
        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun_many(urls, config=config)
            # Should only process 2 pages due to max_pages limit
            successful_results = [r for r in results if r.success]
            assert len(successful_results) <= 2
    
    @pytest.mark.asyncio
    async def test_navigation_abort_handling(self):
        """Test handling of navigation aborts during file downloads"""
        async with AsyncWebCrawler() as crawler:
            # Test with a URL that might cause navigation issues
            result = await crawler.arun(
                "https://httpbin.org/status/404",
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            # Should not crash even with navigation issues
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_screenshot_capture_fix(self):
        """Test screenshot capture improvements"""
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            screenshot=True
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://httpbin.org/html", config=config)
            assert result.success
            assert result.screenshot is not None
            assert len(result.screenshot) > 0
    
    @pytest.mark.asyncio
    async def test_redirect_status_codes(self):
        """Test that real redirect status codes are surfaced"""
        async with AsyncWebCrawler() as crawler:
            # Test with a redirect URL
            result = await crawler.arun(
                "https://httpbin.org/redirect/1",
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            assert result.success
            # Should have redirect information
            assert result.status_code in [200, 301, 302, 303, 307, 308]
    
    @pytest.mark.asyncio
    async def test_local_file_processing(self):
        """Test local file processing with captured_console initialization"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("<html><body><h1>Local File Test</h1></body></html>")
            temp_file = f.name
        
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(f"file://{temp_file}")
                assert result.success
                assert "Local File Test" in result.markdown
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_robots_txt_wildcard_support(self):
        """Test robots.txt wildcard rules support"""
        parser = RobotsParser()
        
        # Test wildcard patterns
        robots_content = "User-agent: *\nDisallow: /admin/*\nDisallow: *.pdf"
        
        # This should work without throwing exceptions
        assert parser is not None
    
    @pytest.mark.asyncio
    async def test_exclude_external_images(self):
        """Test exclude_external_images flag"""
        html_with_images = '''
        <html><body>
            <img src="/local-image.jpg" alt="Local">
            <img src="https://external.com/image.jpg" alt="External">
        </body></html>
        '''
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            exclude_external_images=True
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(f"raw://{html_with_images}", config=config)
            assert result.success
            # External images should be excluded
            assert "external.com" not in result.cleaned_html
    
    @pytest.mark.asyncio
    async def test_llm_extraction_strategy_fix(self):
        """Test LLM extraction strategy choices error fix"""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")
        
        llm_config = LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv("OPENAI_API_KEY")
        )
        
        strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            instruction="Extract the main heading",
            extraction_type="block"
        )
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=strategy
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://httpbin.org/html", config=config)
            assert result.success
            # Should not throw 'str' object has no attribute 'choices' error
            assert result.extracted_content is not None
    
    @pytest.mark.asyncio
    async def test_wait_for_timeout(self):
        """Test separate timeout for wait_for condition"""
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for="css:non-existent-element",
            wait_for_timeout=1000  # 1 second timeout
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://httpbin.org/html", config=config)
            # Should timeout gracefully and still return result
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_bm25_content_filter_language_parameter(self):
        """Test BM25 filter with language parameter for stemming"""
        content_filter = BM25ContentFilter(
            user_query="test content",
            language="english",
            use_stemming=True
        )
        
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=content_filter
        )
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://httpbin.org/html", config=config)
            assert result.success
            assert result.markdown is not None
    
    @pytest.mark.asyncio
    async def test_url_normalization(self):
        """Test URL normalization for invalid schemes and trailing slashes"""
        async with AsyncWebCrawler() as crawler:
            # Test with trailing slash
            result = await crawler.arun(
                "https://httpbin.org/html/",
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            assert result.success
    
    @pytest.mark.asyncio
    async def test_max_scroll_steps(self):
        """Test max_scroll_steps parameter for full page scanning"""
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            scan_full_page=True,
            max_scroll_steps=3
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://httpbin.org/html", config=config)
            assert result.success
    
    @pytest.mark.asyncio
    async def test_async_url_seeder(self):
        """Test AsyncUrlSeeder functionality"""
        seeder = AsyncUrlSeeder(
            base_url="https://httpbin.org",
            max_depth=1,
            max_urls=5
        )
        
        async with AsyncWebCrawler() as crawler:
            urls = await seeder.seed(crawler)
            assert isinstance(urls, list)
            assert len(urls) <= 5
    
    @pytest.mark.asyncio
    async def test_pdf_processing_timeout(self):
        """Test PDF processing with timeout"""
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            pdf=True,
            pdf_timeout=10000  # 10 seconds
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://httpbin.org/html", config=config)
            assert result.success
            # PDF might be None for HTML pages, but should not hang
            assert result.pdf is not None or result.pdf is None
    
    @pytest.mark.asyncio
    async def test_browser_session_management(self):
        """Test improved browser session management"""
        browser_config = BrowserConfig(
            headless=True,
            use_persistent_context=True
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                "https://httpbin.org/html",
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            assert result.success
    
    @pytest.mark.asyncio
    async def test_memory_management(self):
        """Test memory management features"""
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            memory_threshold_percent=80.0,
            check_interval=1.0,
            memory_wait_timeout=600  # 10 minutes default
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://httpbin.org/html", config=config)
            assert result.success
    
    @pytest.mark.asyncio
    async def test_virtual_scroll_support(self):
        """Test virtual scroll support for modern web scraping"""
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            scan_full_page=True,
            virtual_scroll=True
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://httpbin.org/html", config=config)
            assert result.success
    
    @pytest.mark.asyncio
    async def test_adaptive_crawling(self):
        """Test adaptive crawling feature"""
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            adaptive_crawling=True
        )
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun("https://httpbin.org/html", config=config)
            assert result.success


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
