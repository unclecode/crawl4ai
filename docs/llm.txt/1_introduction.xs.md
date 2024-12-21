# Crawl4AI LLM Reference

> Minimal, code-focused reference for LLM-based retrieval and answer generation.

Intended usage: A language model trained on this document can provide quick answers to developers integrating Crawl4AI.

## Installation

- Basic:
```bash
pip install crawl4ai
crawl4ai-setup
```

- If necessary:
```bash
playwright install chromium
```

## Basic Usage

- Asynchronous crawl:
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as c:
        r = await c.arun(url="https://example.com")
        print(r.markdown)

asyncio.run(main())
```

## Concurrent Crawling

- Multiple URLs:
```python
urls = ["https://example.com/page1", "https://example.com/page2"]
async with AsyncWebCrawler() as c:
    results = await asyncio.gather(*[c.arun(url=u) for u in urls])
```

## Configuration

- CacheMode:
```python
from crawl4ai import CacheMode
r = await c.arun(url="...", cache_mode=CacheMode.ENABLED)
```

- Proxies:
```python
async with AsyncWebCrawler(proxies={"http": "http://user:pass@proxy:port"}) as c:
    r = await c.arun("https://example.com")
```

- Headers & Viewport:
```python
async with AsyncWebCrawler(headers={"User-Agent": "MyUA"}, viewport={"width":1024,"height":768}) as c:
    r = await c.arun("https://example.com")
```

## JavaScript Injection

- Custom JS:
```python
js_code = ["""
(async () => {
    const btn = document.querySelector('#load-more');
    if (btn) btn.click();
    await new Promise(r => setTimeout(r, 1000));
})();
"""]

r = await c.arun(url="...", js_code=js_code)
```

## Extraction Strategies

- JSON CSS Extraction:
```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {...}
r = await c.arun(url="...", extraction_strategy=JsonCssExtractionStrategy(schema))
```

- LLM Extraction:
```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy

r = await c.arun(url="...",
    extraction_strategy=LLMExtractionStrategy(
        provider="openai/gpt-4o",
        api_token="YOUR_API_KEY",
        schema={...},
        extraction_type="schema"
    )
)
```

## Common Issues

- Playwright errors: `playwright install chromium`
- Empty output: Increase wait or use `js_code`.
- SSL issues: Check certificates or use `verify_ssl=False` (not recommended for production).

## Additional Links

- [GitHub Repository](https://github.com/unclecode/crawl4ai)
- [Documentation](https://crawl4ai.com/mkdocs/)