import os
import sys
import pytest
import asyncio
import json

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler

@pytest.mark.asyncio
async def test_word_count_threshold():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result_no_threshold = await crawler.arun(url=url, word_count_threshold=0, bypass_cache=True)
        result_with_threshold = await crawler.arun(url=url, word_count_threshold=50, bypass_cache=True)
        
        assert len(result_no_threshold.markdown) > len(result_with_threshold.markdown)

@pytest.mark.asyncio
async def test_css_selector():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        css_selector = "h1, h2, h3"
        result = await crawler.arun(url=url, css_selector=css_selector, bypass_cache=True)
        
        assert result.success
        assert "<h1" in result.cleaned_html or "<h2" in result.cleaned_html or "<h3" in result.cleaned_html

@pytest.mark.asyncio
async def test_javascript_execution():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"

        # Crawl without JS
        result_without_more = await crawler.arun(url=url, bypass_cache=True)
        
        js_code = ["const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"]
        result_with_more = await crawler.arun(url=url, js=js_code, bypass_cache=True)
        
        assert result_with_more.success
        assert len(result_with_more.markdown) > len(result_without_more.markdown)

@pytest.mark.asyncio
async def test_screenshot():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, screenshot=True, bypass_cache=True)
        
        assert result.success
        assert result.screenshot
        assert isinstance(result.screenshot, str)  # Should be a base64 encoded string

@pytest.mark.asyncio
async def test_custom_user_agent():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        custom_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Crawl4AI/1.0"
        result = await crawler.arun(url=url, user_agent=custom_user_agent, bypass_cache=True)
        
        assert result.success
        # Note: We can't directly verify the user agent in the result, but we can check if the crawl was successful

@pytest.mark.asyncio
async def test_extract_media_and_links():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        
        assert result.success
        assert result.media
        assert isinstance(result.media, dict)
        assert 'images' in result.media
        assert result.links
        assert isinstance(result.links, dict)
        assert 'internal' in result.links and 'external' in result.links

@pytest.mark.asyncio
async def test_metadata_extraction():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        
        assert result.success
        assert result.metadata
        assert isinstance(result.metadata, dict)
        # Check for common metadata fields
        assert any(key in result.metadata for key in ['title', 'description', 'keywords'])

# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])