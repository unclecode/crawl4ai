import os
import sys
from pathlib import Path

import pytest
from playwright.async_api import Browser, BrowserType, async_playwright

from crawl4ai.async_configs import BrowserConfig
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.async_webcrawler import CrawlResultContainer


@pytest.fixture(scope="session")
def downloads_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("downloads")


def assert_downloaded(result: CrawlResultContainer):
    assert result.downloaded_files, "No files downloaded"
    missing: list[str] = []

    # Best effort to clean up downloaded files
    for file in result.downloaded_files:
        if not os.path.exists(file):
            missing.append(file)
            continue

        os.remove(file)
    assert not missing, f"Files not downloaded: {missing}"


class TestDownloads:
    @pytest.mark.asyncio
    async def test_basic_download(self, downloads_path: Path):
        """Test basic file download functionality."""
        async with AsyncWebCrawler(
            accept_downloads=True,
            downloads_path=downloads_path.as_posix(),
            verbose=True,
        ) as crawler:
            # Python.org downloads page typically has stable download links
            result: CrawlResultContainer = await crawler.arun(
                url="https://www.python.org/downloads/",
                js_code="""
                // Click first download link
                const downloadLink = document.querySelector('a[href$=".exe"]');
                if (downloadLink) downloadLink.click();
                """,
            )
            assert_downloaded(result)

    @pytest.mark.asyncio
    async def test_persistent_context_download(
        self, tmp_path_factory: pytest.TempPathFactory, downloads_path: Path
    ):
        """Test downloads with persistent context."""
        user_data_dir: Path = tmp_path_factory.mktemp("user_data")

        async with AsyncWebCrawler(
            accept_downloads=True,
            downloads_path=downloads_path,
            use_persistent_context=True,
            user_data_dir=user_data_dir,
            verbose=True,
        ) as crawler:
            result: CrawlResultContainer = await crawler.arun(
                url="https://www.python.org/downloads/",
                js_code="""
                const downloadLink = document.querySelector('a[href$=".exe"]');
                if (downloadLink) downloadLink.click();
                """,
            )
            assert_downloaded(result)

    @pytest.mark.asyncio
    async def test_multiple_downloads(self, downloads_path: Path):
        """Test multiple simultaneous downloads."""
        async with AsyncWebCrawler(
            accept_downloads=True, downloads_path=downloads_path, verbose=True
        ) as crawler:
            result: CrawlResultContainer = await crawler.arun(
                url="https://www.python.org/downloads/",
                js_code="""
                // Click multiple download links
                const downloadLinks = document.querySelectorAll('a[href$=".exe"]');
                downloadLinks.forEach(link => link.click());
                """,
            )
            assert_downloaded(result)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("browser_type", ["chromium", "firefox", "webkit"])
    async def test_different_browsers(self, browser_type: str, downloads_path: Path):
        """Test downloads across different browser types."""
        try:
            # Check if the browser is installed and skip if not.
            async with async_playwright() as p:
                browsers: dict[str, BrowserType] = {
                    "chromium": p.chromium,
                    "firefox": p.firefox,
                    "webkit": p.webkit,
                }
                if browser_type not in browsers:
                    raise ValueError(f"Invalid browser type: {browser_type}")
                bt: BrowserType = browsers[browser_type]
                browser: Browser = await bt.launch(headless=True)
                await browser.close()
        except Exception as e:
            if "Executable doesn't exist at" in str(e):
                pytest.skip(f"{browser_type} is not installed: {e}")
                return
            raise

        async with AsyncWebCrawler(
            config=BrowserConfig(
                accept_downloads=True,
                downloads_path=downloads_path,
                browser_type=browser_type,
                verbose=True,
            ),
        ) as crawler:
            result: CrawlResultContainer = await crawler.arun(
                url="https://www.python.org/downloads/",
                js_code="""
                const downloadLink = document.querySelector('a[href$=".exe"]');
                if (downloadLink) downloadLink.click();
                """,
            )
            assert_downloaded(result)

    @pytest.mark.asyncio
    async def test_without_download_path(self):
        async with AsyncWebCrawler(accept_downloads=True, verbose=True) as crawler:
            result: CrawlResultContainer = await crawler.arun(
                url="https://www.python.org/downloads/",
                js_code="""
                const downloadLink = document.querySelector('a[href$=".exe"]');
                if (downloadLink) downloadLink.click();
                """,
            )
            assert_downloaded(result)
            for file in result.downloaded_files:  # pyright: ignore[reportOptionalIterable]
                if os.path.exists(file):
                    os.remove(file)

    @pytest.mark.asyncio
    async def test_invalid_path(self):
        with pytest.raises(ValueError):
            async with AsyncWebCrawler(
                accept_downloads=True,
                downloads_path="/invalid\0/path/that/doesnt/exist",
                verbose=True,
            ) as crawler:
                await crawler.arun(
                    url="https://www.python.org/downloads/",
                    js_code="""
                    const downloadLink = document.querySelector('a[href$=".exe"]');
                    if (downloadLink) downloadLink.click();
                    """,
                )

    @pytest.mark.asyncio
    async def test_accept_downloads_false(self):
        async with AsyncWebCrawler(accept_downloads=False, verbose=True) as crawler:
            result: CrawlResultContainer = await crawler.arun(
                url="https://www.python.org/downloads/",
                js_code="""
                const downloadLink = document.querySelector('a[href$=".exe"]');
                if (downloadLink) downloadLink.click();
                """,
            )
            assert not result.downloaded_files, "Unexpectedly downloaded files"


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
