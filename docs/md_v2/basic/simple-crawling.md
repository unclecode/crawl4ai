# Simple Crawling

This guide covers the basics of web crawling with Crawl4AI. You'll learn how to set up a crawler, make your first request, and understand the response.

## Basic Usage

Here's the simplest way to crawl a webpage:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)  # Print clean markdown content

if __name__ == "__main__":
    asyncio.run(main())
```

## Understanding the Response

The `arun()` method returns a `CrawlResult` object with several useful properties. Here's a quick overview (see [CrawlResult](../api/crawl-result.md) for complete details):

```python
result = await crawler.arun(url="https://example.com")

# Different content formats
print(result.html)         # Raw HTML
print(result.cleaned_html) # Cleaned HTML
print(result.markdown)     # Markdown version
print(result.fit_markdown) # Most relevant content in markdown

# Check success status
print(result.success)      # True if crawl succeeded
print(result.status_code)  # HTTP status code (e.g., 200, 404)

# Access extracted media and links
print(result.media)        # Dictionary of found media (images, videos, audio)
print(result.links)        # Dictionary of internal and external links
```

## Adding Basic Options

Customize your crawl with these common options:

```python
result = await crawler.arun(
    url="https://example.com",
    word_count_threshold=10,        # Minimum words per content block
    exclude_external_links=True,    # Remove external links
    remove_overlay_elements=True,   # Remove popups/modals
    process_iframes=True           # Process iframe content
)
```

## Handling Errors

Always check if the crawl was successful:

```python
result = await crawler.arun(url="https://example.com")
if not result.success:
    print(f"Crawl failed: {result.error_message}")
    print(f"Status code: {result.status_code}")
```

## Logging and Debugging

Enable verbose mode for detailed logging:

```python
async with AsyncWebCrawler(verbose=True) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Complete Example

Here's a more comprehensive example showing common usage patterns:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            # Content filtering
            word_count_threshold=10,
            excluded_tags=['form', 'header'],
            exclude_external_links=True,
            
            # Content processing
            process_iframes=True,
            remove_overlay_elements=True,
            
            # Cache control
            bypass_cache=False  # Use cache if available
        )
        
        if result.success:
            # Print clean content
            print("Content:", result.markdown[:500])  # First 500 chars
            
            # Process images
            for image in result.media["images"]:
                print(f"Found image: {image['src']}")
            
            # Process links
            for link in result.links["internal"]:
                print(f"Internal link: {link['href']}")
                
        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
```
