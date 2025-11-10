# Proxy & Security

This guide covers proxy configuration and security features in Crawl4AI, including SSL certificate analysis and proxy rotation strategies.

## Understanding Proxy Configuration

Crawl4AI supports proxy configuration at two levels:

### BrowserConfig.proxy_config
Sets proxy at the **browser level** - affects all pages/tabs in that browser instance. Use this when:
- You want all crawls from this browser to use the same proxy
- You're using a single proxy for the entire session
- You need persistent proxy settings across multiple crawls

### CrawlerRunConfig.proxy_config
Sets proxy at the **request level** - can be different for each crawl operation. Use this when:
- You want per-request proxy control
- You're implementing proxy rotation
- Different URLs need different proxies

## Basic Proxy Setup

### Browser-Level Proxy (BrowserConfig)

Configure proxies that apply to the entire browser session:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

# Using dictionary configuration
browser_config = BrowserConfig(proxy_config={
    "server": "http://proxy.example.com:8080"
})

# Using ProxyConfig object
from crawl4ai import ProxyConfig
proxy = ProxyConfig(server="http://proxy.example.com:8080")
browser_config = BrowserConfig(proxy_config=proxy)

# Using string (auto-parsed)
browser_config = BrowserConfig(proxy_config="http://proxy.example.com:8080")

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com")
```

### Request-Level Proxy (CrawlerRunConfig)

Configure proxies that can be customized per crawl operation:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Using dictionary configuration
run_config = CrawlerRunConfig(proxy_config={
    "server": "http://proxy.example.com:8080"
})

# Using ProxyConfig object
from crawl4ai import ProxyConfig
proxy = ProxyConfig(server="http://proxy.example.com:8080")
run_config = CrawlerRunConfig(proxy_config=proxy)

# Using string (auto-parsed)
run_config = CrawlerRunConfig(proxy_config="http://proxy.example.com:8080")

browser_config = BrowserConfig()
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com", config=run_config)
```

!!! note "Priority Order"
    When both `BrowserConfig.proxy_config` and `CrawlerRunConfig.proxy_config` are set, `CrawlerRunConfig.proxy_config` takes precedence for that specific crawl operation.

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
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Using dictionary
run_config = CrawlerRunConfig(proxy_config={
    "server": "http://proxy.example.com:8080",
    "username": "your_username",
    "password": "your_password"
})

# Using ProxyConfig object
from crawl4ai import ProxyConfig
proxy = ProxyConfig(
    server="http://proxy.example.com:8080",
    username="your_username",
    password="your_password"
)
run_config = CrawlerRunConfig(proxy_config=proxy)

browser_config = BrowserConfig()
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(url="https://example.com", config=run_config)
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
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, ProxyConfig
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy
import re

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

asyncio.run(main())
```

## SSL Certificate Analysis

Combine proxy usage with SSL certificate inspection for enhanced security analysis. SSL certificate fetching is configured per request via `CrawlerRunConfig`.

### Per-Request SSL Certificate Analysis
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Configure proxy with SSL certificate fetching per request
run_config = CrawlerRunConfig(
    proxy_config={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass"
    },
    fetch_ssl_certificate=True  # Enable SSL certificate analysis for this request
)

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
```

## Security Best Practices

### 1. Proxy Rotation for Anonymity
```python
# Use multiple proxies to avoid IP blocking
proxies = ProxyConfig.from_env("PROXIES")
strategy = RoundRobinProxyStrategy(proxies)

# Configure rotation per request (recommended)
run_config = CrawlerRunConfig(proxy_rotation_strategy=strategy)

# If you want a single static proxy across all requests, set a fixed ProxyConfig at browser-level:
# browser_config = BrowserConfig(proxy_config=proxies[0])
```

### 2. SSL Certificate Verification
```python
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
# Prefer SOCKS5 proxies for better protocol support
# Browser-level
browser_config = BrowserConfig(proxy_config="socks5://proxy.example.com:1080")

# Or request-level
run_config = CrawlerRunConfig(proxy_config="socks5://proxy.example.com:1080")
```

## Migration from Deprecated `proxy` Parameter

!!! warning "Deprecation Notice"
    The `proxy` parameter in `BrowserConfig` is deprecated. Use `proxy_config` in either `BrowserConfig` or `CrawlerRunConfig` instead.

```python
# Old (deprecated)
browser_config = BrowserConfig(proxy="http://proxy.example.com:8080")

# You will see a warning similar to:
# DeprecationWarning: BrowserConfig.proxy is deprecated and ignored. Use proxy_config instead.

# New (recommended) - Browser-level default
browser_config = BrowserConfig(proxy_config="http://proxy.example.com:8080")

# Or request-level override (takes precedence per request)
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

1. **Proxy Connection Failed**
   - Verify proxy server is accessible
   - Check authentication credentials
   - Ensure correct protocol (http/https/socks5)

2. **SSL Certificate Errors**
   - Some proxies may interfere with SSL inspection
   - Try different proxy or disable SSL verification if necessary

3. **Environment Variables Not Loading**
   - Ensure PROXIES variable is set correctly
   - Check comma separation and format: `ip:port:user:pass,ip:port:user:pass`

4. **Proxy Rotation Not Working**
   - Verify proxies are loaded: `len(proxies) > 0`
    - Check proxy strategy is set on `CrawlerRunConfig` via `proxy_rotation_strategy`
    - Ensure `proxy_config` is a valid `ProxyConfig` (when using a static proxy)

<!-- Removed duplicate Supported Proxy Formats section (already covered above) -->

