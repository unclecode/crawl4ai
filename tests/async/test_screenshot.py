import base64
import io
import sys

import pytest
from PIL import Image

from crawl4ai import CacheMode
from crawl4ai.async_webcrawler import AsyncWebCrawler


@pytest.mark.asyncio
async def test_basic_screenshot():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://example.com"  # A static website
        result = await crawler.arun(
            url=url, cache_mode=CacheMode.BYPASS, screenshot=True
        )

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
            url=url, cache_mode=CacheMode.BYPASS, screenshot=True, wait_for=wait_for
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
        url = "https://example.com"
        wait_for = "js:() => document.querySelector('h1') !== null"

        result = await crawler.arun(
            url=url, cache_mode=CacheMode.BYPASS, screenshot=True, wait_for=wait_for
        )

        assert result.success
        assert result.screenshot is not None

        image_data = base64.b64decode(result.screenshot)
        image = Image.open(io.BytesIO(image_data))
        assert image.format in ("PNG", "BMP")


@pytest.mark.asyncio
async def test_screenshot_without_wait_for():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nytimes.com"  # A website with lots of dynamic content

        result = await crawler.arun(
            url=url, cache_mode=CacheMode.BYPASS, screenshot=True
        )

        assert result.success
        assert result.screenshot is not None

        image_data = base64.b64decode(result.screenshot)
        image = Image.open(io.BytesIO(image_data))
        assert image.format in ("PNG", "BMP")


@pytest.mark.asyncio
async def test_screenshot_comparison():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://example.com"
        wait_for = (
            "css:body > div > p:nth-child(3) > a"  # Wait for the more information link.
        )

        # Take screenshot without wait_for
        result_without_wait = await crawler.arun(
            url=url, cache_mode=CacheMode.BYPASS, screenshot=True
        )

        assert result_without_wait.success
        assert result_without_wait.screenshot is not None

        # Take screenshot with wait_for
        result_with_wait = await crawler.arun(
            url=url, cache_mode=CacheMode.BYPASS, screenshot=True, wait_for=wait_for
        )

        assert result_with_wait.success
        assert result_with_wait.screenshot is not None

        # Compare the two screenshots
        image_without_wait = Image.open(
            io.BytesIO(base64.b64decode(result_without_wait.screenshot))
        )
        image_with_wait = Image.open(
            io.BytesIO(base64.b64decode(result_with_wait.screenshot))
        )

        # This is a simple size comparison. In a real-world scenario, you might want to use
        # more sophisticated image comparison techniques.
        assert image_with_wait.size[0] == image_without_wait.size[0]
        assert image_with_wait.size[1] == image_without_wait.size[1]


# Entry point for debugging
if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
