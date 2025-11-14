# Proxy & Security

This guide covers proxy configuration and security features in Crawl4AI, including SSL certificate analysis and proxy rotation strategies.

## Understanding Proxy Configuration

Crawl4AI recommends configuring proxies per request through `CrawlerRunConfig.proxy_config`. This gives you precise control, enables rotation strategies, and keeps examples simple enough to copy, paste, and run.

## Basic Proxy Setup

Configure proxies that apply to each crawl operation:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, ProxyConfig

run_config = CrawlerRunConfig(proxy_config=ProxyConfig(server="http://proxy.example.com:8080"))
# run_config = CrawlerRunConfig(proxy_config={"server": "http://proxy.example.com:8080"})
# run_config = CrawlerRunConfig(proxy_config="http://proxy.example.com:8080")


async def main():
    browser_config = BrowserConfig()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com", config=run_config)
        print(f"Success: {result.success} -> {result.url}")


if __name__ == "__main__":
    asyncio.run(main())
```

!!! note "Why request-level?"
    `CrawlerRunConfig.proxy_config` keeps each request self-contained, so swapping proxies or rotation strategies is just a matter of building a new run configuration.

## Supported Proxy Formats

The `ProxyConfig.from_string()` method supports multiple formats:

```python
from crawl4ai import ProxyConfig

# HTTP proxy with authentication
proxy1 = ProxyConfig.from_string("http://user:pass@192.168.1.1:8080")

# HTTPS proxy
proxy2 = ProxyConfig.from_string("https://proxy.example.com:8080")

# SOCKS5 proxy
proxy3 = ProxyConfig.from_string("socks5://proxy.example.com:1080")

# Simple IP:port format
proxy4 = ProxyConfig.from_string("192.168.1.1:8080")

# IP:port:user:pass format
proxy5 = ProxyConfig.from_string("192.168.1.1:8080:user:pass")
```

## Authenticated Proxies

For proxies requiring authentication:

```python
import asyncio
from crawl4ai import AsyncWebCrawler,BrowserConfig, CrawlerRunConfig, ProxyConfig

run_config = CrawlerRunConfig(
    proxy_config=ProxyConfig(
        server="http://proxy.example.com:8080",
        username="your_username",
        password="your_password",
    )
)
# Or dictionary style:
# run_config = CrawlerRunConfig(proxy_config={
#     "server": "http://proxy.example.com:8080",
#     "username": "your_username",
#     "password": "your_password",
# })


async def main():
    browser_config = BrowserConfig()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com", config=run_config)
        print(f"Success: {result.success} -> {result.url}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Environment Variable Configuration

Load proxies from environment variables for easy configuration:

```python
import os
from crawl4ai import ProxyConfig, CrawlerRunConfig

# Set environment variable
os.environ["PROXIES"] = "ip1:port1:user1:pass1,ip2:port2:user2:pass2,ip3:port3"

# Load all proxies
proxies = ProxyConfig.from_env()
print(f"Loaded {len(proxies)} proxies")

# Use first proxy
if proxies:
    run_config = CrawlerRunConfig(proxy_config=proxies[0])
```

## Rotating Proxies

Crawl4AI supports automatic proxy rotation to distribute requests across multiple proxy servers. Rotation is applied per request using a rotation strategy on `CrawlerRunConfig`.

### Proxy Rotation (recommended)
```python
import asyncio
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, ProxyConfig
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy

async def main():
    # Load proxies from environment
    proxies = ProxyConfig.from_env()
    if not proxies:
        print("No proxies found! Set PROXIES environment variable.")
        return

    # Create rotation strategy
    proxy_strategy = RoundRobinProxyStrategy(proxies)

    # Configure per-request with proxy rotation
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        proxy_rotation_strategy=proxy_strategy,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        urls = ["https://httpbin.org/ip"] * (len(proxies) * 2)  # Test each proxy twice

        print(f"🚀 Testing {len(proxies)} proxies with rotation...")
        results = await crawler.arun_many(urls=urls, config=run_config)

        for i, result in enumerate(results):
            if result.success:
                # Extract IP from response
                ip_match = re.search(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', result.html)
                if ip_match:
                    detected_ip = ip_match.group(0)
                    proxy_index = i % len(proxies)
                    expected_ip = proxies[proxy_index].ip

                    print(f"✅ Request {i+1}: Proxy {proxy_index+1} -> IP {detected_ip}")
                    if detected_ip == expected_ip:
                        print("   🎯 IP matches proxy configuration")
                    else:
                        print(f"   ⚠️  IP mismatch (expected {expected_ip})")
                else:
                    print(f"❌ Request {i+1}: Could not extract IP from response")
            else:
                print(f"❌ Request {i+1}: Failed - {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
```

## SSL Certificate Analysis

Combine proxy usage with SSL certificate inspection for enhanced security analysis. SSL certificate fetching is configured per request via `CrawlerRunConfig`.

### Per-Request SSL Certificate Analysis
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

run_config = CrawlerRunConfig(
    proxy_config={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass",
    },
    fetch_ssl_certificate=True,  # Enable SSL certificate analysis for this request
)


async def main():
    browser_config = BrowserConfig()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com", config=run_config)

        if result.success:
            print(f"✅ Crawled via proxy: {result.url}")

            # Analyze SSL certificate
            if result.ssl_certificate:
                cert = result.ssl_certificate
                print("🔒 SSL Certificate Info:")
                print(f"   Issuer: {cert.issuer}")
                print(f"   Subject: {cert.subject}")
                print(f"   Valid until: {cert.valid_until}")
                print(f"   Fingerprint: {cert.fingerprint}")

                # Export certificate
                cert.to_json("certificate.json")
                print("💾 Certificate exported to certificate.json")
            else:
                print("⚠️  No SSL certificate information available")


if __name__ == "__main__":
    asyncio.run(main())
```

## Security Best Practices

### 1. Proxy Rotation for Anonymity
```python
from crawl4ai import CrawlerRunConfig, ProxyConfig
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy

# Use multiple proxies to avoid IP blocking
proxies = ProxyConfig.from_env("PROXIES")
strategy = RoundRobinProxyStrategy(proxies)

# Configure rotation per request (recommended)
run_config = CrawlerRunConfig(proxy_rotation_strategy=strategy)

# For a fixed proxy across all requests, just reuse the same run_config instance
static_run_config = run_config
```

### 2. SSL Certificate Verification
```python
from crawl4ai import CrawlerRunConfig

# Always verify SSL certificates when possible
# Per-request (affects specific requests)
run_config = CrawlerRunConfig(fetch_ssl_certificate=True)
```

### 3. Environment Variable Security
```bash
# Use environment variables for sensitive proxy credentials
# Avoid hardcoding usernames/passwords in code
export PROXIES="ip1:port1:user1:pass1,ip2:port2:user2:pass2"
```

### 4. SOCKS5 for Enhanced Security
```python
from crawl4ai import CrawlerRunConfig

# Prefer SOCKS5 proxies for better protocol support
run_config = CrawlerRunConfig(proxy_config="socks5://proxy.example.com:1080")
```

## Migration from Deprecated `proxy` Parameter

- "Deprecation Notice"
    The legacy `proxy` argument on `BrowserConfig` is deprecated. Configure proxies through `CrawlerRunConfig.proxy_config` so each request fully describes its network settings.

```python
# Old (deprecated) approach
# from crawl4ai import BrowserConfig
# browser_config = BrowserConfig(proxy="http://proxy.example.com:8080")

# New (preferred) approach
from crawl4ai import CrawlerRunConfig
run_config = CrawlerRunConfig(proxy_config="http://proxy.example.com:8080")
```

### Safe Logging of Proxies
```python
from crawl4ai import ProxyConfig

def safe_proxy_repr(proxy: ProxyConfig):
    if getattr(proxy, "username", None):
        return f"{proxy.server} (auth: ****)"
    return proxy.server
```

## Troubleshooting

### Common Issues

- "Proxy connection failed"
    - Verify the proxy server is reachable from your network.
    - Double-check authentication credentials.
    - Ensure the protocol matches (`http`, `https`, or `socks5`).

- "SSL certificate errors"
    - Some proxies break SSL inspection; switch proxies if you see repeated failures.
    - Consider temporarily disabling certificate fetching to isolate the issue.

- "Environment variables not loading"
    - Confirm `PROXIES` (or your custom env var) is set before running the script.
    - Check formatting: `ip:port:user:pass,ip:port:user:pass`.

- "Proxy rotation not working"
    - Ensure `ProxyConfig.from_env()` actually loaded entries (`len(proxies) > 0`).
    - Attach `proxy_rotation_strategy` to `CrawlerRunConfig`.
    - Validate the proxy definitions you pass into the strategy.
