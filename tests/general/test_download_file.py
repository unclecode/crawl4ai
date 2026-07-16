import asyncio
from crawl4ai import CrawlerRunConfig, AsyncWebCrawler, BrowserConfig
from pathlib import Path
import os

async def test_basic_download():
    
    # Custom folder (otherwise defaults to ~/.crawl4ai/downloads)
    downloads_path = os.path.join(Path.home(), ".crawl4ai", "downloads")
    os.makedirs(downloads_path, exist_ok=True)
    browser_config = BrowserConfig(
        accept_downloads=True,
        downloads_path=downloads_path
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        run_config = CrawlerRunConfig(
            js_code="""
                const link = document.querySelector('a[href$=".exe"]');
                if (link) { link.click(); }
            """,
            delay_before_return_html=5  
        )
        result = await crawler.arun("https://www.python.org/downloads/", config=run_config)

        if result.downloaded_files:
            print("Downloaded files:")
            for file_path in result.downloaded_files:
                print("•", file_path)
        else:
            print("No files downloaded.")

if __name__ == "__main__":
    asyncio.run(test_basic_download())
 