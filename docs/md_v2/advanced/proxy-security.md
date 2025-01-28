# Proxy 

## Basic Proxy Setup

Simple proxy configuration with `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig

# Using proxy URL
browser_config = BrowserConfig(proxy="http://proxy.example.com:8080")
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")

# Using SOCKS proxy
browser_config = BrowserConfig(proxy="socks5://proxy.example.com:1080")
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Authenticated Proxy

Use an authenticated proxy with `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig

proxy_config = {
    "server": "http://proxy.example.com:8080",
    "username": "user",
    "password": "pass"
}

browser_config = BrowserConfig(proxy_config=proxy_config)
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

Here's the corrected documentation:

## Rotating Proxies 

Example using a proxy rotation service dynamically:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def get_next_proxy():
    # Your proxy rotation logic here
    return {"server": "http://next.proxy.com:8080"}

async def main():
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig()
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # For each URL, create a new run config with different proxy
        for url in urls:
            proxy = await get_next_proxy()
            # Clone the config and update proxy - this creates a new browser context
            current_config = run_config.clone(proxy_config=proxy)
            result = await crawler.arun(url=url, config=current_config)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

