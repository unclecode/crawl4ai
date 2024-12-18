# Download Handling in Crawl4AI

This guide explains how to use Crawl4AI to handle file downloads during crawling.  You'll learn how to trigger downloads, specify download locations, and access downloaded files.

## Enabling Downloads

By default, Crawl4AI does not download files. To enable downloads, set the `accept_downloads` parameter to `True` in either the `AsyncWebCrawler` constructor or the `arun` method.

```python
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(accept_downloads=True) as crawler:  # Globally enable downloads
        # ... your crawling logic ...

asyncio.run(main())
```

Or, enable it for a specific crawl:

```python
async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="...", accept_downloads=True)
        # ...
```

## Specifying Download Location

You can specify the download directory using the `downloads_path` parameter. If not provided, Crawl4AI creates a "downloads" directory inside the `.crawl4ai` folder in your home directory.

```python
import os
from pathlib import Path

# ... inside your crawl function:

downloads_path = os.path.join(os.getcwd(), "my_downloads")  # Custom download path
os.makedirs(downloads_path, exist_ok=True)

result = await crawler.arun(url="...", downloads_path=downloads_path, accept_downloads=True)

# ...
```

If you are setting it globally, provide the path to the AsyncWebCrawler:
```python
async def crawl_with_downloads(url: str, download_path: str):
    async with AsyncWebCrawler(
        accept_downloads=True,
        downloads_path=download_path, # or set it on arun
        verbose=True
    ) as crawler:
        result = await crawler.arun(url=url) # you still need to enable downloads per call.
        # ...
```



## Triggering Downloads

Downloads are typically triggered by user interactions on a web page (e.g., clicking a download button).  You can simulate these actions with the `js_code` parameter, injecting JavaScript code to be executed within the browser context.  The `wait_for` parameter might also be crucial to allowing sufficient time for downloads to initiate before the crawler proceeds.

```python
result = await crawler.arun(
    url="https://www.python.org/downloads/",
    js_code="""
        // Find and click the first Windows installer link
        const downloadLink = document.querySelector('a[href$=".exe"]');
        if (downloadLink) {
            downloadLink.click();
        }
    """,
    wait_for=5  # Wait for 5 seconds for the download to start
)
```

## Accessing Downloaded Files

Downloaded file paths are stored in the `downloaded_files` attribute of the returned  `CrawlResult`  object.  This is a list of strings, with each string representing the absolute path to a downloaded file.

```python
if result.downloaded_files:
    print("Downloaded files:")
    for file_path in result.downloaded_files:
        print(f"- {file_path}")
        # Perform operations with downloaded files, e.g., check file size
        file_size = os.path.getsize(file_path)
        print(f"- File size: {file_size} bytes")
else:
    print("No files downloaded.")
```


##  Example: Downloading Multiple Files

```python
import asyncio
import os
from pathlib import Path
from crawl4ai import AsyncWebCrawler

async def download_multiple_files(url: str, download_path: str):

    async with AsyncWebCrawler(
        accept_downloads=True,
        downloads_path=download_path,
        verbose=True
    ) as crawler:
        result = await crawler.arun(
            url=url,
            js_code="""
            // Trigger multiple downloads (example)
            const downloadLinks = document.querySelectorAll('a[download]'); // Or a more specific selector
            for (const link of downloadLinks) {
                link.click();
                await new Promise(r => setTimeout(r, 2000)); // Add a small delay between clicks if needed
            }
            """,
            wait_for=10 # Adjust the timeout to match the expected time for all downloads to start
        )

        if result.downloaded_files:
            print("Downloaded files:")
            for file in result.downloaded_files:
                print(f"- {file}")
        else:
            print("No files downloaded.")
            

# Example usage
download_path = os.path.join(Path.home(), ".crawl4ai", "downloads")
os.makedirs(download_path, exist_ok=True) # Create directory if it doesn't exist


asyncio.run(download_multiple_files("https://www.python.org/downloads/windows/", download_path))
```

## Important Considerations

- **Browser Context:** Downloads are managed within the browser context.  Ensure your `js_code` correctly targets the download triggers on the specific web page.
- **Waiting:**  Use `wait_for` to manage the timing of the crawl process if immediate download might not occur.
- **Error Handling:** Implement proper error handling to gracefully manage failed downloads or incorrect file paths.
- **Security:** Downloaded files should be scanned for potential security threats before use.



This guide provides a foundation for handling downloads with Crawl4AI. You can adapt these techniques to manage downloads in various scenarios and integrate them into more complex crawling workflows.
