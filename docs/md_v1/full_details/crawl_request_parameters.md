# Crawl Request Parameters for AsyncWebCrawler

The `arun` method in Crawl4AI's `AsyncWebCrawler` is designed to be highly configurable, allowing you to customize the crawling and extraction process to suit your needs. Below are the parameters you can use with the `arun` method, along with their descriptions, possible values, and examples.

## Parameters

### url (str)
**Description:** The URL of the webpage to crawl.
**Required:** Yes
**Example:**
```python
url = "https://www.nbcnews.com/business"
```

### word_count_threshold (int)
**Description:** The minimum number of words a block must contain to be considered meaningful. The default value is defined by `MIN_WORD_THRESHOLD`.
**Required:** No
**Default Value:** `MIN_WORD_THRESHOLD`
**Example:**
```python
word_count_threshold = 10
```

### extraction_strategy (ExtractionStrategy)
**Description:** The strategy to use for extracting content from the HTML. It must be an instance of `ExtractionStrategy`. If not provided, the default is `NoExtractionStrategy`.
**Required:** No
**Default Value:** `NoExtractionStrategy()`
**Example:**
```python
extraction_strategy = CosineStrategy(semantic_filter="finance")
```

### chunking_strategy (ChunkingStrategy)
**Description:** The strategy to use for chunking the text before processing. It must be an instance of `ChunkingStrategy`. The default value is `RegexChunking()`.
**Required:** No
**Default Value:** `RegexChunking()`
**Example:**
```python
chunking_strategy = NlpSentenceChunking()
```

### bypass_cache (bool)
**Description:** Whether to force a fresh crawl even if the URL has been previously crawled. The default value is `False`.
**Required:** No
**Default Value:** `False`
**Example:**
```python
bypass_cache = True
```

### css_selector (str)
**Description:** The CSS selector to target specific parts of the HTML for extraction. If not provided, the entire HTML will be processed.
**Required:** No
**Default Value:** `None`
**Example:**
```python
css_selector = "div.article-content"
```

### screenshot (bool)
**Description:** Whether to take screenshots of the page. The default value is `False`.
**Required:** No
**Default Value:** `False`
**Example:**
```python
screenshot = True
```

### user_agent (str)
**Description:** The user agent to use for the HTTP requests. If not provided, a default user agent will be used.
**Required:** No
**Default Value:** `None`
**Example:**
```python
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
```

### verbose (bool)
**Description:** Whether to enable verbose logging. The default value is `True`.
**Required:** No
**Default Value:** `True`
**Example:**
```python
verbose = True
```

### **kwargs
Additional keyword arguments that can be passed to customize the crawling process further. Some notable options include:

- **only_text (bool):** Whether to extract only text content, excluding HTML tags. Default is `False`.
- **session_id (str):** A unique identifier for the crawling session. This is useful for maintaining state across multiple requests.
- **js_code (str or list):** JavaScript code to be executed on the page before extraction.
- **wait_for (str):** A CSS selector or JavaScript function to wait for before considering the page load complete.

**Example:**
```python
result = await crawler.arun(
    url="https://www.nbcnews.com/business",
    css_selector="p",
    only_text=True,
    session_id="unique_session_123",
    js_code="window.scrollTo(0, document.body.scrollHeight);",
    wait_for="article.main-article"
)
```

## Example Usage

Here's an example of how to use the `arun` method with various parameters:

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import CosineStrategy
from crawl4ai.chunking_strategy import NlpSentenceChunking

async def main():
    # Create the AsyncWebCrawler instance 
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Run the crawler with custom parameters
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            word_count_threshold=10,
            extraction_strategy=CosineStrategy(semantic_filter="finance"),
            chunking_strategy=NlpSentenceChunking(),
            bypass_cache=True,
            css_selector="div.article-content",
            screenshot=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            verbose=True,
            only_text=True,
            session_id="business_news_session",
            js_code="window.scrollTo(0, document.body.scrollHeight);",
            wait_for="footer"
        )

        print(result)

# Run the async function
asyncio.run(main())
```

This example demonstrates how to configure various parameters to customize the crawling and extraction process using the asynchronous version of Crawl4AI.

## Additional Asynchronous Methods

The `AsyncWebCrawler` class also provides other useful asynchronous methods:

### arun_many
**Description:** Crawl multiple URLs concurrently.
**Example:**
```python
urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
results = await crawler.arun_many(urls, word_count_threshold=10, bypass_cache=True)
```

### aclear_cache
**Description:** Clear the crawler's cache.
**Example:**
```python
await crawler.aclear_cache()
```

### aflush_cache
**Description:** Completely flush the crawler's cache.
**Example:**
```python
await crawler.aflush_cache()
```

### aget_cache_size
**Description:** Get the current size of the cache.
**Example:**
```python
cache_size = await crawler.aget_cache_size()
print(f"Current cache size: {cache_size}")
```

These asynchronous methods allow for efficient and flexible use of the AsyncWebCrawler in various scenarios.