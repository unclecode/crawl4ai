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

## SSL Certificate Verification

Crawl4AI can retrieve and analyze SSL certificates from HTTPS websites. This is useful for:
- Verifying website authenticity
- Detecting potential security issues
- Analyzing certificate chains
- Exporting certificates for further analysis

Enable SSL certificate retrieval with `CrawlerRunConfig`:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

config = CrawlerRunConfig(fetch_ssl_certificate=True)
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com", config=config)
    
    if result.success and result.ssl_certificate:
        cert = result.ssl_certificate
        
        # Access certificate properties
        print(f"Issuer: {cert.issuer.get('CN', '')}")
        print(f"Valid until: {cert.valid_until}")
        print(f"Fingerprint: {cert.fingerprint}")
        
        # Export certificate in different formats
        cert.to_json("cert.json")  # For analysis
        cert.to_pem("cert.pem")    # For web servers
        cert.to_der("cert.der")    # For Java applications
```

The SSL certificate object provides:
- Direct access to certificate fields (issuer, subject, validity dates)
- Methods to export in common formats (JSON, PEM, DER)
- Certificate chain information and extensions
