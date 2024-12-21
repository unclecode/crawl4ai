# Proxy & Security

Configure proxy settings and enhance security features in Crawl4AI for reliable data extraction.

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

## Rotating Proxies

Example using a proxy rotation service and updating `BrowserConfig` dynamically:

```python
from crawl4ai.async_configs import BrowserConfig

async def get_next_proxy():
    # Your proxy rotation logic here
    return {"server": "http://next.proxy.com:8080"}

browser_config = BrowserConfig()
async with AsyncWebCrawler(config=browser_config) as crawler:
    # Update proxy for each request
    for url in urls:
        proxy = await get_next_proxy()
        browser_config.proxy_config = proxy
        result = await crawler.arun(url=url, config=browser_config)
```

## Custom Headers

Add security-related headers via `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig

headers = {
    "X-Forwarded-For": "203.0.113.195",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

browser_config = BrowserConfig(headers=headers)
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Combining with Magic Mode

For maximum protection, combine proxy with Magic Mode via `CrawlerRunConfig` and `BrowserConfig`:

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(
    proxy="http://proxy.example.com:8080",
    headers={"Accept-Language": "en-US"}
)
crawler_config = CrawlerRunConfig(magic=True)  # Enable all anti-detection features

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com", config=crawler_config)
```
