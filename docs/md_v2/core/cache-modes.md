# Crawl4AI Cache System and Migration Guide

## Overview
Starting from version 0.5.0, Crawl4AI introduces a new caching system that replaces the old boolean flags with a more intuitive `CacheMode` enum. This change simplifies cache control and makes the behavior more predictable.

## Old vs New Approach

### Old Way (Deprecated)
The old system used multiple boolean flags:
- `bypass_cache`: Skip cache entirely
- `disable_cache`: Disable all caching
- `no_cache_read`: Don't read from cache
- `no_cache_write`: Don't write to cache

### New Way (Recommended)
The new system uses a single `CacheMode` enum:
- `CacheMode.ENABLED`: Normal caching (read/write)
- `CacheMode.DISABLED`: No caching at all
- `CacheMode.READ_ONLY`: Only read from cache
- `CacheMode.WRITE_ONLY`: Only write to cache
- `CacheMode.BYPASS`: Skip cache for this operation
- `CacheMode.SMART`: **NEW** - Intelligently validate cache with HEAD requests

## Migration Example

### Old Code (Deprecated)
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def use_proxy():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            bypass_cache=True  # Old way
        )
        print(len(result.markdown))

async def main():
    await use_proxy()

if __name__ == "__main__":
    asyncio.run(main())
```

### New Code (Recommended)
```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig

async def use_proxy():
    # Use CacheMode in CrawlerRunConfig
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)  
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            config=config  # Pass the configuration object
        )
        print(len(result.markdown))

async def main():
    await use_proxy()

if __name__ == "__main__":
    asyncio.run(main())
```

## Common Migration Patterns

| Old Flag              | New Mode                       |
|-----------------------|---------------------------------|
| `bypass_cache=True`   | `cache_mode=CacheMode.BYPASS`  |
| `disable_cache=True`  | `cache_mode=CacheMode.DISABLED`|
| `no_cache_read=True`  | `cache_mode=CacheMode.WRITE_ONLY` |
| `no_cache_write=True` | `cache_mode=CacheMode.READ_ONLY` |

## SMART Cache Mode: Only Crawl When Changes

Starting from version 0.7.1, Crawl4AI introduces the **SMART cache mode** - an intelligent caching strategy that validates cached content before using it. This mode uses HTTP HEAD requests to check if content has changed, potentially saving 70-95% bandwidth on unchanged content.

### How SMART Mode Works

When you use `CacheMode.SMART`, Crawl4AI:

1. **Retrieves cached content** (if available)
2. **Sends a HEAD request** with conditional headers (ETag, Last-Modified)
3. **Validates the response**:
   - If server returns `304 Not Modified` → uses cache
   - If content changed → performs fresh crawl
   - If headers indicate changes → performs fresh crawl

### Benefits

- **Bandwidth Efficient**: Only downloads full content when necessary
- **Always Fresh**: Ensures you get the latest content when it changes
- **Cost Effective**: Reduces API calls and bandwidth usage
- **Intelligent**: Uses multiple signals to detect changes (ETag, Last-Modified, Content-Length)

### Basic Usage

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.cache_context import CacheMode
from crawl4ai.async_configs import CrawlerRunConfig

async def smart_crawl():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # First crawl - caches the content
        config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
        result1 = await crawler.arun(
            url="https://example.com",
            config=config
        )
        print(f"First crawl: {len(result1.html)} bytes")
        
        # Second crawl - uses SMART mode
        smart_config = CrawlerRunConfig(cache_mode=CacheMode.SMART)
        result2 = await crawler.arun(
            url="https://example.com",
            config=smart_config
        )
        print(f"SMART crawl: {len(result2.html)} bytes (from cache if unchanged)")

asyncio.run(smart_crawl())
```

### When to Use SMART Mode

SMART mode is ideal for:

- **Periodic crawling** of websites that update irregularly
- **News sites** where you want fresh content but avoid re-downloading unchanged pages
- **API endpoints** that provide proper caching headers
- **Large-scale crawling** where bandwidth costs are significant

### How It Detects Changes

SMART mode checks these signals in order:

1. **304 Not Modified** status (most reliable)
2. **Content-Digest** header (RFC 9530)
3. **Strong ETag** comparison
4. **Last-Modified** timestamp
5. **Content-Length** changes (as a hint)

### Example: News Site Monitoring

```python
async def monitor_news_site():
    async with AsyncWebCrawler(verbose=True) as crawler:
        config = CrawlerRunConfig(cache_mode=CacheMode.SMART)
        
        # Check multiple times
        for i in range(3):
            result = await crawler.arun(
                url="https://news.ycombinator.com",
                config=config
            )
            
            # SMART mode will only re-crawl if content changed
            print(f"Check {i+1}: Retrieved {len(result.html)} bytes")
            await asyncio.sleep(300)  # Wait 5 minutes

asyncio.run(monitor_news_site())
```

### Understanding SMART Mode Logs

When using SMART mode with `verbose=True`, you'll see informative logs:

```
[SMART] ℹ SMART cache: 304 Not Modified - Content unchanged - Using cache for https://example.com
[SMART] ℹ SMART cache: Content-Length changed (12345 -> 12789) - Re-crawling https://example.com
[SMART] ℹ SMART cache: No definitive cache headers matched - Assuming content changed - Re-crawling https://example.com
```

### Limitations

- Some servers don't properly support HEAD requests
- Dynamic content without proper cache headers will always be re-crawled
- Content changes must be reflected in HTTP headers for detection

### Advanced Example

For a complete example demonstrating SMART mode with both static and dynamic content, check out `docs/examples/smart_cache.py`.

## Cache Mode Reference

| Mode | Read from Cache | Write to Cache | Use Case |
|------|----------------|----------------|----------|
| `ENABLED` | ✓ | ✓ | Normal operation |
| `DISABLED` | ✗ | ✗ | No caching needed |
| `READ_ONLY` | ✓ | ✗ | Use existing cache only |
| `WRITE_ONLY` | ✗ | ✓ | Refresh cache only |
| `BYPASS` | ✗ | ✗ | Skip cache for this request |
| `SMART` | ✓* | ✓ | Validate before using cache |

*SMART mode reads from cache but validates it first with a HEAD request.