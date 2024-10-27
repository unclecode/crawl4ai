# Proxy & Security

Configure proxy settings and enhance security features in Crawl4AI for reliable data extraction.

## Basic Proxy Setup

Simple proxy configuration:

```python
# Using proxy URL
async with AsyncWebCrawler(
    proxy="http://proxy.example.com:8080"
) as crawler:
    result = await crawler.arun(url="https://example.com")

# Using SOCKS proxy
async with AsyncWebCrawler(
    proxy="socks5://proxy.example.com:1080"
) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Authenticated Proxy

Use proxy with authentication:

```python
proxy_config = {
    "server": "http://proxy.example.com:8080",
    "username": "user",
    "password": "pass"
}

async with AsyncWebCrawler(proxy_config=proxy_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Rotating Proxies

Example using a proxy rotation service:

```python
async def get_next_proxy():
    # Your proxy rotation logic here
    return {"server": "http://next.proxy.com:8080"}

async with AsyncWebCrawler() as crawler:
    # Update proxy for each request
    for url in urls:
        proxy = await get_next_proxy()
        crawler.update_proxy(proxy)
        result = await crawler.arun(url=url)
```

## Custom Headers

Add security-related headers:

```python
headers = {
    "X-Forwarded-For": "203.0.113.195",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

async with AsyncWebCrawler(headers=headers) as crawler:
    result = await crawler.arun(url="https://example.com")
```

## Combining with Magic Mode

For maximum protection, combine proxy with Magic Mode:

```python
async with AsyncWebCrawler(
    proxy="http://proxy.example.com:8080",
    headers={"Accept-Language": "en-US"}
) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        magic=True  # Enable all anti-detection features
    )
```