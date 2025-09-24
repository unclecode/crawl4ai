### Task 6: Build HTTP crawler with content extraction

**Description:**

````
This task focuses on creating the `WebCrawler` class that fetches web page content using `httpx`.

6. Build HTTP crawler with content extraction
- Create WebCrawler class using httpx with connection pooling
- Implement URL validation and normalization
- Add retry logic with exponential backoff for network errors
- Implement timeout handling (30 seconds per request)
- Create stealth headers for bot detection avoidance
- Write unit tests for crawler functionality and error scenarios
Requirements: 4.1, 7.1, 7.2, 7.3

**Class Structure (`app/services/crawler.py`):**
Implement the `WebCrawler` class with at least the following method signature:
```python
class WebCrawler:
    async def crawl_url(self, url: str, options: CrawlOptions) -> CrawlResult
    # ... other methods for extraction, conversion ...
````

````
**Retry Logic:**
Implement retry logic with exponential backoff for network errors, based on this configuration model:
```python
class RetryConfig(BaseModel):
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
````

**Globs:**

```
app/services/crawler.py
app/models/config.py # For RetryConfig
tests/services/test_crawler.py
```
