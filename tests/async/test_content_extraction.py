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
async def test_extract_markdown():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert result.markdown
        assert isinstance(result.markdown, str)
        assert len(result.markdown) > 0

@pytest.mark.asyncio
async def test_extract_cleaned_html():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert result.cleaned_html
        assert isinstance(result.cleaned_html, str)
        assert len(result.cleaned_html) > 0

@pytest.mark.asyncio
async def test_extract_media():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert result.media
        media = result.media
        assert isinstance(media, dict)
        assert "images" in media
        assert isinstance(media["images"], list)
        for image in media["images"]:
            assert "src" in image
            assert "alt" in image
            assert "type" in image

@pytest.mark.asyncio
async def test_extract_links():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert result.links
        links = result.links
        assert isinstance(links, dict)
        assert "internal" in links
        assert "external" in links
        assert isinstance(links["internal"], list)
        assert isinstance(links["external"], list)
        for link in links["internal"] + links["external"]:
            assert "href" in link
            assert "text" in link

@pytest.mark.asyncio
async def test_extract_metadata():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        result = await crawler.arun(url=url, bypass_cache=True)
        assert result.success
        assert result.metadata
        metadata = result.metadata
        assert isinstance(metadata, dict)
        assert "title" in metadata
        assert isinstance(metadata["title"], str)

@pytest.mark.asyncio
async def test_css_selector_extraction():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        css_selector = "h1, h2, h3"
        result = await crawler.arun(url=url, bypass_cache=True, css_selector=css_selector)
        assert result.success
        assert result.markdown
        assert all(heading in result.markdown for heading in ["#", "##", "###"])

# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])