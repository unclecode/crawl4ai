import os
import sys
import pytest
import asyncio
import base64
from PIL import Image
import io

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler

@pytest.mark.asyncio
async def test_basic_screenshot():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://example.com"  # A static website
        result = await crawler.arun(url=url, bypass_cache=True, screenshot=True)
        
        assert result.success
        assert result.screenshot is not None
        
        # Verify the screenshot is a valid image
        image_data = base64.b64decode(result.screenshot)
        image = Image.open(io.BytesIO(image_data))
        assert image.format == "PNG"

@pytest.mark.asyncio
async def test_screenshot_with_wait_for():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Using a website with dynamic content
        url = "https://www.youtube.com"
        wait_for = "css:#content"  # Wait for the main content to load
        
        result = await crawler.arun(
            url=url, 
            bypass_cache=True, 
            screenshot=True, 
            wait_for=wait_for
        )
        
        assert result.success
        assert result.screenshot is not None
        
        # Verify the screenshot is a valid image
        image_data = base64.b64decode(result.screenshot)
        image = Image.open(io.BytesIO(image_data))
        assert image.format == "PNG"
        
        # You might want to add more specific checks here, like image dimensions
        # or even use image recognition to verify certain elements are present

@pytest.mark.asyncio
async def test_screenshot_with_js_wait_for():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.amazon.com"
        wait_for = "js:() => document.querySelector('#nav-logo-sprites') !== null"
        
        result = await crawler.arun(
            url=url, 
            bypass_cache=True, 
            screenshot=True, 
            wait_for=wait_for
        )
        
        assert result.success
        assert result.screenshot is not None
        
        image_data = base64.b64decode(result.screenshot)
        image = Image.open(io.BytesIO(image_data))
        assert image.format == "PNG"

@pytest.mark.asyncio
async def test_screenshot_without_wait_for():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nytimes.com"  # A website with lots of dynamic content
        
        result = await crawler.arun(url=url, bypass_cache=True, screenshot=True)
        
        assert result.success
        assert result.screenshot is not None
        
        image_data = base64.b64decode(result.screenshot)
        image = Image.open(io.BytesIO(image_data))
        assert image.format == "PNG"

@pytest.mark.asyncio
async def test_screenshot_comparison():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.reddit.com"
        wait_for = "css:#SHORTCUT_FOCUSABLE_DIV"
        
        # Take screenshot without wait_for
        result_without_wait = await crawler.arun(
            url=url, 
            bypass_cache=True, 
            screenshot=True
        )
        
        # Take screenshot with wait_for
        result_with_wait = await crawler.arun(
            url=url, 
            bypass_cache=True, 
            screenshot=True, 
            wait_for=wait_for
        )
        
        assert result_without_wait.success and result_with_wait.success
        assert result_without_wait.screenshot is not None
        assert result_with_wait.screenshot is not None
        
        # Compare the two screenshots
        image_without_wait = Image.open(io.BytesIO(base64.b64decode(result_without_wait.screenshot)))
        image_with_wait = Image.open(io.BytesIO(base64.b64decode(result_with_wait.screenshot)))
        
        # This is a simple size comparison. In a real-world scenario, you might want to use
        # more sophisticated image comparison techniques.
        assert image_with_wait.size[0] >= image_without_wait.size[0]
        assert image_with_wait.size[1] >= image_without_wait.size[1]

# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])