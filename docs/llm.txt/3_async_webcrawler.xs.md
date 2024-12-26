# Crawl4AI: AsyncWebCrawler Reference

> Minimal code-oriented reference. Focus on parameters, usage patterns, and code.

(See full code: [async_webcrawler.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/async_webcrawler.py))

## Setup & Quick Start
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig
import asyncio

async def main():
    async with AsyncWebCrawler(config=BrowserConfig(browser_type="chromium", headless=True)) as c:
        r = await c.arun("https://example.com")
        print(r.markdown)

asyncio.run(main())
```

## BrowserConfig & Docker
**Params:** `browser_type`, `headless`, `viewport_width`, `viewport_height`, `verbose`, `proxy`.
```python
browser_config = BrowserConfig(browser_type="firefox", headless=False)
async with AsyncWebCrawler(config=browser_config) as c:
    r = await c.arun("https://site.com")
```

**Docker Example:**
```dockerfile
FROM python:3.10-slim
RUN pip install crawl4ai playwright
RUN playwright install chromium
COPY script.py /app/
WORKDIR /app
CMD ["python", "script.py"]
```

## Asynchronous Strategies
Default: `AsyncPlaywrightCrawlerStrategy`
```python
from crawl4ai import AsyncWebCrawler, AsyncPlaywrightCrawlerStrategy
crawler = AsyncWebCrawler(crawler_strategy=AsyncPlaywrightCrawlerStrategy())
```

## Dynamic Content (js_code)
```python
js_code = ["""
(async () => {
    document.querySelector(".load-more").click();
    await new Promise(r => setTimeout(r, 2000));
})();
"""]
from crawl4ai import CrawlerRunConfig
config = CrawlerRunConfig(js_code=js_code)
```

## Extraction & Filtering
**Strategies:** `JsonCssExtractionStrategy`, `LLMExtractionStrategy`, `NoExtractionStrategy`.  
**Chunking:** `RegexChunking`, NLP-based.  
```python
config = CrawlerRunConfig(extraction_strategy=JsonCssExtractionStrategy(selectors={"title": "h1"}))
```

## Caching & Performance
**Cache Modes:** `ENABLED`, `BYPASS`, `DISABLED`
```python
await c.aclear_cache()
await c.aflush_cache()
```

## Batch Crawling & Parallelization
```python
urls = ["https://site1.com", "https://site2.com"]
config = CrawlerRunConfig(semaphore_count=10)
async with AsyncWebCrawler() as c:
    results = await c.arun_many(urls, config=config)
```

## Screenshots & PDFs
```python
config = CrawlerRunConfig(screenshot=True, pdf=True)
result = await c.arun("https://example.com", config=config)
with open("page.png","wb") as f: f.write(result.screenshot)
with open("page.pdf","wb") as f: f.write(result.pdf)
```

## Common Issues & Fixes
- Browser not launching: `playwright install chromium`
- Timeouts: Increase delays in `CrawlerRunConfig`
- JS not executing: Use `js_code` or headless=False
- Stale cache: `await c.aclear_cache()`
- Extraction fail: Check CSS selectors or try different strategy

## Best Practices & Tips
- Modularize crawl logic
- Use proxies/rotating user agents
- Add delays to avoid blocking
- Use `async with` for resource cleanup

## Links & FAQ
- GitHub: [crawl4ai](https://github.com/yourusername/crawl4ai)
- Playwright Docs: [https://playwright.dev/](https://playwright.dev/)

**FAQ:**
- Custom user agent: `user_agent="MyUserAgent"`
- Local files: `file://` or `raw:`
- LLM extraction: Set `extraction_strategy=LLMExtractionStrategy(...)`

## Links

- [async_webcrawler.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/async_webcrawler.py)
