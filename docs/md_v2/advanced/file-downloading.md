# Download Handling in Crawl4AI

This guide explains how to use Crawl4AI to handle file downloads during crawling. You'll learn how to trigger downloads, specify download locations, and access downloaded files.

## Enabling Downloads

To enable downloads, set the `accept_downloads` parameter in the `BrowserConfig` object and pass it to the crawler.

```python
from crawl4ai.async_configs import BrowserConfig, AsyncWebCrawler

async def main():
    config = BrowserConfig(accept_downloads=True)  # Enable downloads globally
    async with AsyncWebCrawler(config=config) as crawler:
        # ... your crawling logic ...

asyncio.run(main())
```

## Specifying Download Location

Specify the download directory using the `downloads_path` attribute in the `BrowserConfig` object. If not provided, Crawl4AI defaults to creating a "downloads" directory inside the `.crawl4ai` folder in your home directory.

```python
from crawl4ai.async_configs import BrowserConfig
import os

downloads_path = os.path.join(os.getcwd(), "my_downloads")  # Custom download path
os.makedirs(downloads_path, exist_ok=True)

config = BrowserConfig(accept_downloads=True, downloads_path=downloads_path)

async def main():
    async with AsyncWebCrawler(config=config) as crawler:
        result = await crawler.arun(url="https://example.com")
        # ...
```

## Triggering Downloads

Downloads are typically triggered by user interactions on a web page, such as clicking a download button. Use `js_code` in `CrawlerRunConfig` to simulate these actions and `wait_for` to allow sufficient time for downloads to start.

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig(
    js_code="""
        const downloadLink = document.querySelector('a[href$=".exe"]');
        if (downloadLink) {
            downloadLink.click();
        }
    """,
    wait_for=5  # Wait 5 seconds for the download to start
)

result = await crawler.arun(url="https://www.python.org/downloads/", config=config)
```

## Accessing Downloaded Files

The `downloaded_files` attribute of the `CrawlResult` object contains paths to downloaded files.

```python
if result.downloaded_files:
    print("Downloaded files:")
    for file_path in result.downloaded_files:
        print(f"- {file_path}")
        file_size = os.path.getsize(file_path)
        print(f"- File size: {file_size} bytes")
else:
    print("No files downloaded.")
```

## Example: Downloading Multiple Files

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os
from pathlib import Path

async def download_multiple_files(url: str, download_path: str):
    config = BrowserConfig(accept_downloads=True, downloads_path=download_path)
    async with AsyncWebCrawler(config=config) as crawler:
        run_config = CrawlerRunConfig(
            js_code="""
                const downloadLinks = document.querySelectorAll('a[download]');
                for (const link of downloadLinks) {
                    link.click();
                    // Delay between clicks
                    await new Promise(r => setTimeout(r, 2000));  
                }
            """,
            wait_for=10  # Wait for all downloads to start
        )
        result = await crawler.arun(url=url, config=run_config)

        if result.downloaded_files:
            print("Downloaded files:")
            for file in result.downloaded_files:
                print(f"- {file}")
        else:
            print("No files downloaded.")

# Usage
download_path = os.path.join(Path.home(), ".crawl4ai", "downloads")
os.makedirs(download_path, exist_ok=True)

asyncio.run(download_multiple_files("https://www.python.org/downloads/windows/", download_path))
```

## Important Considerations

- **Browser Context:** Downloads are managed within the browser context. Ensure `js_code` correctly targets the download triggers on the webpage.
- **Timing:** Use `wait_for` in `CrawlerRunConfig` to manage download timing.
- **Error Handling:** Handle errors to manage failed downloads or incorrect paths gracefully.
- **Security:** Scan downloaded files for potential security threats before use.

This revised guide ensures consistency with the `Crawl4AI` codebase by using `BrowserConfig` and `CrawlerRunConfig` for all download-related configurations. Let me know if further adjustments are needed!