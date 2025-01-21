# Overview of Some Important Advanced Features 
(Proxy, PDF, Screenshot, SSL, Headers, & Storage State)

Crawl4AI offers multiple power-user features that go beyond simple crawling. This tutorial covers:

1. **Proxy Usage**  
2. **Capturing PDFs & Screenshots**  
3. **Handling SSL Certificates**  
4. **Custom Headers**  
5. **Session Persistence & Local Storage**
6. **Robots.txt Compliance**

> **Prerequisites**  
> - You have a basic grasp of [AsyncWebCrawler Basics](../core/simple-crawling.md)  
> - You know how to run or configure your Python environment with Playwright installed

---

## 1. Proxy Usage

If you need to route your crawl traffic through a proxy—whether for IP rotation, geo-testing, or privacy—Crawl4AI supports it via `BrowserConfig.proxy_config`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    browser_cfg = BrowserConfig(
        proxy_config={
            "server": "http://proxy.example.com:8080",
            "username": "myuser",
            "password": "mypass",
        },
        headless=True
    )
    crawler_cfg = CrawlerRunConfig(
        verbose=True
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://www.whatismyip.com/",
            config=crawler_cfg
        )
        if result.success:
            print("[OK] Page fetched via proxy.")
            print("Page HTML snippet:", result.html[:200])
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**  
- **`proxy_config`** expects a dict with `server` and optional auth credentials.  
- Many commercial proxies provide an HTTP/HTTPS “gateway” server that you specify in `server`.  
- If your proxy doesn’t need auth, omit `username`/`password`.

---

## 2. Capturing PDFs & Screenshots

Sometimes you need a visual record of a page or a PDF “printout.” Crawl4AI can do both in one pass:

```python
import os, asyncio
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, CacheMode

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/List_of_common_misconceptions",
            cache_mode=CacheMode.BYPASS,
            pdf=True,
            screenshot=True
        )
        
        if result.success:
            # Save screenshot
            if result.screenshot:
                with open("wikipedia_screenshot.png", "wb") as f:
                    f.write(b64decode(result.screenshot))
            
            # Save PDF
            if result.pdf:
                with open("wikipedia_page.pdf", "wb") as f:
                    f.write(result.pdf)
            
            print("[OK] PDF & screenshot captured.")
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Why PDF + Screenshot?**  
- Large or complex pages can be slow or error-prone with “traditional” full-page screenshots.  
- Exporting a PDF is more reliable for very long pages. Crawl4AI automatically converts the first PDF page into an image if you request both.  

**Relevant Parameters**  
- **`pdf=True`**: Exports the current page as a PDF (base64-encoded in `result.pdf`).  
- **`screenshot=True`**: Creates a screenshot (base64-encoded in `result.screenshot`).  
- **`scan_full_page`** or advanced hooking can further refine how the crawler captures content.

---

## 3. Handling SSL Certificates

If you need to verify or export a site’s SSL certificate—for compliance, debugging, or data analysis—Crawl4AI can fetch it during the crawl:

```python
import asyncio, os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    
    config = CrawlerRunConfig(
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        
        if result.success and result.ssl_certificate:
            cert = result.ssl_certificate
            print("\nCertificate Information:")
            print(f"Issuer (CN): {cert.issuer.get('CN', '')}")
            print(f"Valid until: {cert.valid_until}")
            print(f"Fingerprint: {cert.fingerprint}")

            # Export in multiple formats:
            cert.to_json(os.path.join(tmp_dir, "certificate.json"))
            cert.to_pem(os.path.join(tmp_dir, "certificate.pem"))
            cert.to_der(os.path.join(tmp_dir, "certificate.der"))
            
            print("\nCertificate exported to JSON/PEM/DER in 'tmp' folder.")
        else:
            print("[ERROR] No certificate or crawl failed.")

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**  
- **`fetch_ssl_certificate=True`** triggers certificate retrieval.  
- `result.ssl_certificate` includes methods (`to_json`, `to_pem`, `to_der`) for saving in various formats (handy for server config, Java keystores, etc.).

---

## 4. Custom Headers

Sometimes you need to set custom headers (e.g., language preferences, authentication tokens, or specialized user-agent strings). You can do this in multiple ways:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Option 1: Set headers at the crawler strategy level
    crawler1 = AsyncWebCrawler(
        # The underlying strategy can accept headers in its constructor
        crawler_strategy=None  # We'll override below for clarity
    )
    crawler1.crawler_strategy.update_user_agent("MyCustomUA/1.0")
    crawler1.crawler_strategy.set_custom_headers({
        "Accept-Language": "fr-FR,fr;q=0.9"
    })
    result1 = await crawler1.arun("https://www.example.com")
    print("Example 1 result success:", result1.success)

    # Option 2: Pass headers directly to `arun()`
    crawler2 = AsyncWebCrawler()
    result2 = await crawler2.arun(
        url="https://www.example.com",
        headers={"Accept-Language": "es-ES,es;q=0.9"}
    )
    print("Example 2 result success:", result2.success)

if __name__ == "__main__":
    asyncio.run(main())
```

**Notes**  
- Some sites may react differently to certain headers (e.g., `Accept-Language`).  
- If you need advanced user-agent randomization or client hints, see [Identity-Based Crawling (Anti-Bot)](./identity-based-crawling.md) or use `UserAgentGenerator`.

---

## 5. Session Persistence & Local Storage

Crawl4AI can preserve cookies and localStorage so you can continue where you left off—ideal for logging into sites or skipping repeated auth flows.

### 5.1 `storage_state`

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    storage_dict = {
        "cookies": [
            {
                "name": "session",
                "value": "abcd1234",
                "domain": "example.com",
                "path": "/",
                "expires": 1699999999.0,
                "httpOnly": False,
                "secure": False,
                "sameSite": "None"
            }
        ],
        "origins": [
            {
                "origin": "https://example.com",
                "localStorage": [
                    {"name": "token", "value": "my_auth_token"}
                ]
            }
        ]
    }

    # Provide the storage state as a dictionary to start "already logged in"
    async with AsyncWebCrawler(
        headless=True,
        storage_state=storage_dict
    ) as crawler:
        result = await crawler.arun("https://example.com/protected")
        if result.success:
            print("Protected page content length:", len(result.html))
        else:
            print("Failed to crawl protected page")

if __name__ == "__main__":
    asyncio.run(main())
```

### 5.2 Exporting & Reusing State

You can sign in once, export the browser context, and reuse it later—without re-entering credentials.

- **`await context.storage_state(path="my_storage.json")`**: Exports cookies, localStorage, etc. to a file.  
- Provide `storage_state="my_storage.json"` on subsequent runs to skip the login step.

**See**: [Detailed session management tutorial](./session-management.md) or [Explanations → Browser Context & Managed Browser](./identity-based-crawling.md) for more advanced scenarios (like multi-step logins, or capturing after interactive pages).

---

## 6. Robots.txt Compliance

Crawl4AI supports respecting robots.txt rules with efficient caching:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Enable robots.txt checking in config
    config = CrawlerRunConfig(
        check_robots_txt=True  # Will check and respect robots.txt rules
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            "https://example.com",
            config=config
        )
        
        if not result.success and result.status_code == 403:
            print("Access denied by robots.txt")

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**
- Robots.txt files are cached locally for efficiency
- Cache is stored in `~/.crawl4ai/robots/robots_cache.db`
- Cache has a default TTL of 7 days
- If robots.txt can't be fetched, crawling is allowed
- Returns 403 status code if URL is disallowed

---

## Putting It All Together

Here’s a snippet that combines multiple “advanced” features (proxy, PDF, screenshot, SSL, custom headers, and session reuse) into one run. Normally, you’d tailor each setting to your project’s needs.

```python
import os, asyncio
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    # 1. Browser config with proxy + headless
    browser_cfg = BrowserConfig(
        proxy_config={
            "server": "http://proxy.example.com:8080",
            "username": "myuser",
            "password": "mypass",
        },
        headless=True,
    )

    # 2. Crawler config with PDF, screenshot, SSL, custom headers, and ignoring caches
    crawler_cfg = CrawlerRunConfig(
        pdf=True,
        screenshot=True,
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS,
        headers={"Accept-Language": "en-US,en;q=0.8"},
        storage_state="my_storage.json",  # Reuse session from a previous sign-in
        verbose=True,
    )

    # 3. Crawl
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url = "https://secure.example.com/protected", 
            config=crawler_cfg
        )
        
        if result.success:
            print("[OK] Crawled the secure page. Links found:", len(result.links.get("internal", [])))
            
            # Save PDF & screenshot
            if result.pdf:
                with open("result.pdf", "wb") as f:
                    f.write(b64decode(result.pdf))
            if result.screenshot:
                with open("result.png", "wb") as f:
                    f.write(b64decode(result.screenshot))
            
            # Check SSL cert
            if result.ssl_certificate:
                print("SSL Issuer CN:", result.ssl_certificate.issuer.get("CN", ""))
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Conclusion & Next Steps

You’ve now explored several **advanced** features:

- **Proxy Usage**  
- **PDF & Screenshot** capturing for large or critical pages  
- **SSL Certificate** retrieval & exporting  
- **Custom Headers** for language or specialized requests  
- **Session Persistence** via storage state
- **Robots.txt Compliance**

With these power tools, you can build robust scraping workflows that mimic real user behavior, handle secure sites, capture detailed snapshots, and manage sessions across multiple runs—streamlining your entire data collection pipeline.

**Last Updated**: 2025-01-01