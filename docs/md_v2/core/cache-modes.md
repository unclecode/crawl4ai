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

## Migration Example

### Old Code (Deprecated)
```python
from crawl4ai import AsyncWebCrawler

async def old_code(crawler: AsyncWebCrawler):
    # Legacy `bypass_cache` / `disable_cache` / `no_cache_read` / `no_cache_write`
    # were removed in v0.5+. This example no longer applies:
    result = await crawler.arun(
        url="https://www.nbcnews.com/business",
        # cache_mode is the only cache option now.
    )
    print(len(result.markdown))
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

| Legacy Flag            | Replacement                |
|------------------------|----------------------------|
| `bypass_cache`    | `cache_mode=CacheMode.BYPASS`    |
| `disable_cache`   | `cache_mode=CacheMode.DISABLED`  |
| `no_cache_read`   | `cache_mode=CacheMode.READ_ONLY` |
| `no_cache_write`  | `cache_mode=CacheMode.WRITE_ONLY`|
