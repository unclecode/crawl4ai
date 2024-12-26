# Introduction

## Quick Start (Minimal Example)
For a fast hands-on start, try crawling a single URL and printing its Markdown output:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

This simple snippet should immediately confirm your environment is set up correctly. If you see the page content in Markdown format, you’re good to go.

---

## Overview of Crawl4AI
Crawl4AI is a state-of-the-art, **asynchronous** web crawling library optimized for large-scale data collection. It’s built to integrate seamlessly into AI workflows such as fine-tuning, retrieval-augmented generation (RAG), and data pipelines. By focusing on generating structured, AI-ready data (like Markdown), it helps you build robust applications quickly.

**Why Asynchronous?**  
Async architecture allows you to concurrently crawl multiple URLs without waiting on slow network operations. This results in drastically improved performance and efficiency, especially when dealing with large-scale data extraction.

### Purpose and Vision
- Offer an open-source alternative to expensive commercial APIs.
- Provide clean, structured, Markdown-based outputs for easy AI integration.
- Democratize large-scale, high-speed, and reliable web crawling solutions.

### Key Features
- **Markdown Generation**: Produces AI-friendly, concise Markdown.
- **High-Performance Crawling**: Asynchronous operations let you crawl numerous URLs concurrently.
- **Browser Control**: Fine-tune browser sessions, user agents, proxies, and viewport.
- **JavaScript Support**: Handle dynamic pages by injecting custom JavaScript snippets.
- **Content Filtering**: Use advanced strategies (e.g., BM25) to focus on what matters.
- **Extensibility**: Define custom extraction strategies for complex data schemas.
- **Deployment Ready**: Easy Docker deployment for production and scalability.

---

## Use Cases
- **LLM Training and Fine-Tuning**: Collect and preprocess large web datasets to train machine learning models.
- **RAG Pipelines**: Generate context documents for retrieval-augmented generation tasks.
- **Content Summarization**: Extract pages and produce summaries directly in Markdown.
- **Structured Data Extraction**: Pull structured JSON data suitable for building knowledge graphs or databases.

**Example: Creating a Fine-Tuning Dataset**
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    urls = ["https://example.com/dataset_page_1", "https://example.com/dataset_page_2"]
    async with AsyncWebCrawler(verbose=True) as crawler:
        results = await asyncio.gather(*[crawler.arun(url=u) for u in urls])
        # Combine Markdown outputs into a single file for model fine-tuning
        with open("fine_tuning_data.md", "w") as f:
            for res in results:
                f.write(res.markdown + "\n")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Installation and Setup

### Environment Setup (Recommended)
Use a virtual environment to keep dependencies isolated:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Basic Installation
```bash
pip install crawl4ai
crawl4ai-setup
```

By default, this installs the asynchronous version and sets up Playwright.

### Verify Installation
Run a quick test:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://crawl4ai.com")
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

If you see the page content printed as Markdown, you’re ready.

### Handling JavaScript-Heavy Pages
For pages that require JavaScript actions (like clicking a “Load More” button), use the `js_code` parameter:

```python
js_code = """
(async () => {
    const loadMoreBtn = document.querySelector('button.load-more');
    if (loadMoreBtn) loadMoreBtn.click();
    await new Promise(r => setTimeout(r, 1000));
})();
"""

async with AsyncWebCrawler(verbose=True) as crawler:
    result = await crawler.arun(
        url="https://example.com/js-page",
        js_code=[js_code]
    )
    print(result.markdown)
```

### Using Cache Modes
`CacheMode` can speed up repeated crawls by reusing previously fetched data. For instance:

```python
from crawl4ai import AsyncWebCrawler, CacheMode

async with AsyncWebCrawler(verbose=True) as crawler:
    result = await crawler.arun(
        url="https://example.com/large-page",
        cache_mode=CacheMode.ENABLED
    )
    print(result.markdown)
```

---

## Quick Start Guide

### Minimal Working Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://crawl4ai.com")
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

### Multiple Concurrent Crawls
Harness async concurrency to run multiple crawls in parallel:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def crawl_url(crawler, url):
    return await crawler.arun(url=url)

async def main():
    urls = ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"]
    async with AsyncWebCrawler(verbose=True) as crawler:
        results = await asyncio.gather(*[crawl_url(crawler, u) for u in urls])
        for r in results:
            print(r.markdown[:200])

if __name__ == "__main__":
    asyncio.run(main())
```

### Dockerized Setup
Run Crawl4AI in Docker for production environments:

```bash
docker pull unclecode/crawl4ai:basic-amd64
docker run -p 11235:11235 unclecode/crawl4ai:basic-amd64
curl http://localhost:11235/health
```

### Proxy and Security Configurations
```python
async with AsyncWebCrawler(
    proxies={"http": "http://proxy.server:port", "https": "https://proxy.server:port"}
) as crawler:
    result = await crawler.arun(url="https://crawl4ai.com")
    print(result.markdown)
```

You can also add basic auth:

```python
async with AsyncWebCrawler(
    proxies={"http": "http://user:password@proxy.server:port"}
) as crawler:
    result = await crawler.arun(url="https://crawl4ai.com")
    print(result.markdown)
```

### Customizing Browser Settings
Customize headers, user agents, and viewport:

```python
async with AsyncWebCrawler(
    verbose=True,
    headers={"User-Agent": "MyCustomBrowser/1.0"},
    viewport={"width": 1280, "height": 800}
) as crawler:
    result = await crawler.arun("https://example.com")
    print(result.markdown)
```

---

## Troubleshooting Installation

### Playwright Errors
If `crawl4ai-setup` fails, install manually:
```bash
playwright install chromium
pip install crawl4ai[all]
```

### SSL or Proxy Issues
- Check certificates or disable SSL verification (for dev only).
- Verify proxy credentials and server details.

Use `verbose=True` for detailed logs:
```python
async with AsyncWebCrawler(verbose=True) as crawler:
    result = await crawler.arun(url="https://crawl4ai.com")
    print(result.markdown)
```

---

## Common Pitfalls

1. **Missing Playwright Installation**: Run `playwright install chromium`.
2. **Time-Out on JavaScript-Heavy Pages**: Increase wait time or use `js_code` for page interactions.
3. **Empty Markdown**: Check if the page is JavaScript-rendered and adjust `js_code` or `wait_for` conditions.
4. **Permission Errors**: Run commands with appropriate permissions or use a virtual environment.

---

## Support and Community
- **GitHub Issues**: Have questions or found a bug? Open an issue on the [GitHub Repo](https://github.com/unclecode/crawl4ai/issues).
- **Contributions**: We welcome pull requests. Check out the [contribution guidelines](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTING.md).
- **Community Discussions**: Join discussions on GitHub to share tips, best practices, and feedback.

---

## Further Exploration
- **Advanced Extraction Strategies**: Dive into specialized extraction strategies like `JsonCssExtractionStrategy` or `LLMExtractionStrategy` for structured data output.
- **Content Filtering**: Explore BM25-based strategies to highlight the most relevant parts of a page.
- **Production Deployment**: Refer to the Docker and environment variable configurations for large-scale, distributed crawling setups.

For more detailed code examples and advanced topics, refer to the accompanying [README](https://github.com/unclecode/crawl4ai) and the `QUICKSTART` Python file included with this distribution.