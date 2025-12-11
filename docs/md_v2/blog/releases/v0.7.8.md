# Crawl4AI v0.7.8: Stability & Bug Fix Release

*December 2025*

---

I'm releasing Crawl4AI v0.7.8—a focused stability release that addresses 11 bugs reported by the community. While there are no new features in this release, these fixes resolve important issues affecting Docker deployments, LLM extraction, URL handling, and dependency compatibility.

## What's Fixed at a Glance

- **Docker API**: Fixed ContentRelevanceFilter deserialization, ProxyConfig serialization, and cache folder permissions
- **LLM Extraction**: Configurable rate limiter backoff, HTML input format support, and proper URL handling for raw HTML
- **URL Handling**: Correct relative URL resolution after JavaScript redirects
- **Dependencies**: Replaced deprecated PyPDF2 with pypdf, Pydantic v2 ConfigDict compatibility
- **AdaptiveCrawler**: Fixed query expansion to actually use LLM instead of hardcoded mock data

## Bug Fixes

### Docker & API Fixes

#### ContentRelevanceFilter Deserialization (#1642)

**The Problem:** When sending deep crawl requests to the Docker API with `ContentRelevanceFilter`, the server failed to deserialize the filter, causing requests to fail.

**The Fix:** I added `ContentRelevanceFilter` to the public exports and enhanced the deserialization logic with dynamic imports.

```python
# This now works correctly in Docker API
import httpx

request = {
    "urls": ["https://docs.example.com"],
    "crawler_config": {
        "deep_crawl_strategy": {
            "type": "BFSDeepCrawlStrategy",
            "max_depth": 2,
            "filter_chain": [
                {
                    "type": "ContentRelevanceFilter",
                    "query": "API documentation",
                    "threshold": 0.3
                }
            ]
        }
    }
}

async with httpx.AsyncClient() as client:
    response = await client.post("http://localhost:11235/crawl", json=request)
    # Previously failed, now works!
```

#### ProxyConfig JSON Serialization (#1629)

**The Problem:** `BrowserConfig.to_dict()` failed when `proxy_config` was set because `ProxyConfig` wasn't being serialized to a dictionary.

**The Fix:** `ProxyConfig.to_dict()` is now called during serialization.

```python
from crawl4ai import BrowserConfig
from crawl4ai.async_configs import ProxyConfig

proxy = ProxyConfig(
    server="http://proxy.example.com:8080",
    username="user",
    password="pass"
)

config = BrowserConfig(headless=True, proxy_config=proxy)

# Previously raised TypeError, now works
config_dict = config.to_dict()
json.dumps(config_dict)  # Valid JSON
```

#### Docker Cache Folder Permissions (#1638)

**The Problem:** The `.cache` folder in the Docker image had incorrect permissions, causing crawling to fail when caching was enabled.

**The Fix:** Corrected ownership and permissions during image build.

```bash
# Cache now works correctly in Docker
docker run -d -p 11235:11235 \
    --shm-size=1g \
    -v ./my-cache:/app/.cache \
    unclecode/crawl4ai:0.7.8
```

---

### LLM & Extraction Fixes

#### Configurable Rate Limiter Backoff (#1269)

**The Problem:** The LLM rate limiting backoff parameters were hardcoded, making it impossible to adjust retry behavior for different API rate limits.

**The Fix:** `LLMConfig` now accepts three new parameters for complete control over retry behavior.

```python
from crawl4ai import LLMConfig

# Default behavior (unchanged)
default_config = LLMConfig(provider="openai/gpt-4o-mini")
# backoff_base_delay=2, backoff_max_attempts=3, backoff_exponential_factor=2

# Custom configuration for APIs with strict rate limits
custom_config = LLMConfig(
    provider="openai/gpt-4o-mini",
    backoff_base_delay=5,           # Wait 5 seconds on first retry
    backoff_max_attempts=5,          # Try up to 5 times
    backoff_exponential_factor=3     # Multiply delay by 3 each attempt
)

# Retry sequence: 5s -> 15s -> 45s -> 135s -> 405s
```

#### LLM Strategy HTML Input Support (#1178)

**The Problem:** `LLMExtractionStrategy` always sent markdown to the LLM, but some extraction tasks work better with HTML structure preserved.

**The Fix:** Added `input_format` parameter supporting `"markdown"`, `"html"`, `"fit_markdown"`, `"cleaned_html"`, and `"fit_html"`.

```python
from crawl4ai import LLMExtractionStrategy, LLMConfig

# Default: markdown input (unchanged)
markdown_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="openai/gpt-4o-mini"),
    instruction="Extract product information"
)

# NEW: HTML input - preserves table/list structure
html_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="openai/gpt-4o-mini"),
    instruction="Extract the data table preserving structure",
    input_format="html"
)

# NEW: Filtered markdown - only relevant content
fit_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="openai/gpt-4o-mini"),
    instruction="Summarize the main content",
    input_format="fit_markdown"
)
```

#### Raw HTML URL Variable (#1116)

**The Problem:** When using `url="raw:<html>..."`, the entire HTML content was being passed to extraction strategies as the URL parameter, polluting LLM prompts.

**The Fix:** The URL is now correctly set to `"Raw HTML"` for raw HTML inputs.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

html = "<html><body><h1>Test</h1></body></html>"

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url=f"raw:{html}",
        config=CrawlerRunConfig(extraction_strategy=my_strategy)
    )
    # extraction_strategy receives url="Raw HTML" instead of the HTML blob
```

---

### URL Handling Fix

#### Relative URLs After Redirects (#1268)

**The Problem:** When JavaScript caused a page redirect, relative links were resolved against the original URL instead of the final URL.

**The Fix:** `redirected_url` now captures the actual page URL after all JavaScript execution completes.

```python
from crawl4ai import AsyncWebCrawler

async with AsyncWebCrawler() as crawler:
    # Page at /old-page redirects via JS to /new-page
    result = await crawler.arun(url="https://example.com/old-page")

    # BEFORE: redirected_url = "https://example.com/old-page"
    # AFTER:  redirected_url = "https://example.com/new-page"

    # Links are now correctly resolved against the final URL
    for link in result.links['internal']:
        print(link['href'])  # Relative links resolved correctly
```

---

### Dependency & Compatibility Fixes

#### PyPDF2 Replaced with pypdf (#1412)

**The Problem:** PyPDF2 was deprecated in 2022 and is no longer maintained.

**The Fix:** Replaced with the actively maintained `pypdf` library.

```python
# Installation (unchanged)
pip install crawl4ai[pdf]

# The PDF processor now uses pypdf internally
# No code changes required - API remains the same
```

#### Pydantic v2 ConfigDict Compatibility (#678)

**The Problem:** Using the deprecated `class Config` syntax caused deprecation warnings with Pydantic v2.

**The Fix:** Migrated to `model_config = ConfigDict(...)` syntax.

```python
# No more deprecation warnings when importing crawl4ai models
from crawl4ai.models import CrawlResult
from crawl4ai import CrawlerRunConfig, BrowserConfig

# All models are now Pydantic v2 compatible
```

---

### AdaptiveCrawler Fix

#### Query Expansion Using LLM (#1621)

**The Problem:** The `EmbeddingStrategy` in AdaptiveCrawler had commented-out LLM code and was using hardcoded mock query variations instead.

**The Fix:** Uncommented and activated the LLM call for actual query expansion.

```python
# AdaptiveCrawler query expansion now actually uses the LLM
# Instead of hardcoded variations like:
# variations = {'queries': ['what are the best vegetables...']}

# The LLM generates relevant query variations based on your actual query
```

---

### Code Formatting Fix

#### Import Statement Formatting (#1181)

**The Problem:** When extracting code from web pages, import statements were sometimes concatenated without proper line separation.

**The Fix:** Import statements now maintain proper newline separation.

```python
# BEFORE: "import osimport sysfrom pathlib import Path"
# AFTER:
# import os
# import sys
# from pathlib import Path
```

---

## Breaking Changes

**None!** This release is fully backward compatible.

- All existing code continues to work without modification
- New parameters have sensible defaults matching previous behavior
- No API changes to existing functionality

---

## Upgrade Instructions

### Python Package

```bash
pip install --upgrade crawl4ai
# or
pip install crawl4ai==0.7.8
```

### Docker

```bash
# Pull the latest version
docker pull unclecode/crawl4ai:0.7.8

# Run
docker run -d -p 11235:11235 --shm-size=1g unclecode/crawl4ai:0.7.8
```

---

## Verification

Run the verification tests to confirm all fixes are working:

```bash
python docs/releases_review/demo_v0.7.8.py
```

This runs actual tests that verify each bug fix is properly implemented.

---

## Acknowledgments

Thank you to everyone who reported these issues and provided detailed reproduction steps. Your bug reports make Crawl4AI better for everyone.

Issues fixed: #1642, #1638, #1629, #1621, #1412, #1269, #1268, #1181, #1178, #1116, #678

---

## Support & Resources

- **Documentation**: [docs.crawl4ai.com](https://docs.crawl4ai.com)
- **GitHub**: [github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
- **Discord**: [discord.gg/crawl4ai](https://discord.gg/jP8KfhDhyN)
- **Twitter**: [@unclecode](https://x.com/unclecode)

---

**This stability release ensures Crawl4AI works reliably across Docker deployments, LLM extraction workflows, and various edge cases. Thank you for your continued support and feedback!**

**Happy crawling!**

*- unclecode*
