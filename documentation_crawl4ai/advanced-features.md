[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/advanced/advanced-features/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * [URL Seeding](https://docs.crawl4ai.com/core/url-seeding/)
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * [Fit Markdown](https://docs.crawl4ai.com/core/fit-markdown/)
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * Overview
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * [SSL Certificate](https://docs.crawl4ai.com/advanced/ssl-certificate/)
    * [Network & Console Capture](https://docs.crawl4ai.com/advanced/network-console-capture/)
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [Overview of Some Important Advanced Features](https://docs.crawl4ai.com/advanced/advanced-features/#overview-of-some-important-advanced-features)
  * [1. Proxy Usage](https://docs.crawl4ai.com/advanced/advanced-features/#1-proxy-usage)
  * [2. Capturing PDFs & Screenshots](https://docs.crawl4ai.com/advanced/advanced-features/#2-capturing-pdfs-screenshots)
  * [3. Handling SSL Certificates](https://docs.crawl4ai.com/advanced/advanced-features/#3-handling-ssl-certificates)
  * [4. Custom Headers](https://docs.crawl4ai.com/advanced/advanced-features/#4-custom-headers)
  * [5. Session Persistence & Local Storage](https://docs.crawl4ai.com/advanced/advanced-features/#5-session-persistence-local-storage)
  * [6. Robots.txt Compliance](https://docs.crawl4ai.com/advanced/advanced-features/#6-robotstxt-compliance)
  * [Putting It All Together](https://docs.crawl4ai.com/advanced/advanced-features/#putting-it-all-together)
  * [7. Anti-Bot Features (Stealth Mode & Undetected Browser)](https://docs.crawl4ai.com/advanced/advanced-features/#7-anti-bot-features-stealth-mode-undetected-browser)
  * [Conclusion & Next Steps](https://docs.crawl4ai.com/advanced/advanced-features/#conclusion-next-steps)


# Overview of Some Important Advanced Features
(Proxy, PDF, Screenshot, SSL, Headers, & Storage State)
Crawl4AI offers multiple power-user features that go beyond simple crawling. This tutorial covers:
1. **Proxy Usage**
2. **Capturing PDFs & Screenshots**
3. **Handling SSL Certificates**
4. **Custom Headers**
5. **Session Persistence & Local Storage**
6. **Robots.txt Compliance**
> **Prerequisites**
>  - You have a basic grasp of [AsyncWebCrawler Basics](https://docs.crawl4ai.com/core/simple-crawling/)
>  - You know how to run or configure your Python environment with Playwright installed
* * *
## 1. Proxy Usage
If you need to route your crawl traffic through a proxy—whether for IP rotation, geo-testing, or privacy—Crawl4AI supports it via `BrowserConfig.proxy_config`.
```
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
Copy
```

**Key Points**
- **`proxy_config`**expects a dict with`server` and optional auth credentials.
- Many commercial proxies provide an HTTP/HTTPS “gateway” server that you specify in `server`.
- If your proxy doesn’t need auth, omit `username`/`password`.
* * *
## 2. Capturing PDFs & Screenshots
Sometimes you need a visual record of a page or a PDF “printout.” Crawl4AI can do both in one pass:
```
import os, asyncio
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

async def main():
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        screenshot=True,
        pdf=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/List_of_common_misconceptions",
            config=run_config
        )
        if result.success:
            print(f"Screenshot data present: {result.screenshot is not None}")
            print(f"PDF data present: {result.pdf is not None}")

            if result.screenshot:
                print(f"[OK] Screenshot captured, size: {len(result.screenshot)} bytes")
                with open("wikipedia_screenshot.png", "wb") as f:
                    f.write(b64decode(result.screenshot))
            else:
                print("[WARN] Screenshot data is None.")

            if result.pdf:
                print(f"[OK] PDF captured, size: {len(result.pdf)} bytes")
                with open("wikipedia_page.pdf", "wb") as f:
                    f.write(result.pdf)
            else:
                print("[WARN] PDF data is None.")

        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

**Why PDF + Screenshot?**
- Large or complex pages can be slow or error-prone with “traditional” full-page screenshots.
- Exporting a PDF is more reliable for very long pages. Crawl4AI automatically converts the first PDF page into an image if you request both.
**Relevant Parameters**
- **`pdf=True`**: Exports the current page as a PDF (base64-encoded in`result.pdf`).
- **`screenshot=True`**: Creates a screenshot (base64-encoded in`result.screenshot`).
- **`scan_full_page`**or advanced hooking can further refine how the crawler captures content.
* * *
## 3. Handling SSL Certificates
If you need to verify or export a site’s SSL certificate—for compliance, debugging, or data analysis—Crawl4AI can fetch it during the crawl:
```
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
Copy
```

**Key Points**
- **`fetch_ssl_certificate=True`**triggers certificate retrieval.
- `result.ssl_certificate` includes methods (`to_json`, `to_pem`, `to_der`) for saving in various formats (handy for server config, Java keystores, etc.).
* * *
## 4. Custom Headers
Sometimes you need to set custom headers (e.g., language preferences, authentication tokens, or specialized user-agent strings). You can do this in multiple ways:
```
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
Copy
```

**Notes**
- Some sites may react differently to certain headers (e.g., `Accept-Language`).
- If you need advanced user-agent randomization or client hints, see [Identity-Based Crawling (Anti-Bot)](https://docs.crawl4ai.com/advanced/identity-based-crawling/) or use `UserAgentGenerator`.
* * *
## 5. Session Persistence & Local Storage
Crawl4AI can preserve cookies and localStorage so you can continue where you left off—ideal for logging into sites or skipping repeated auth flows.
### 5.1 `storage_state`
```
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
Copy
```

### 5.2 Exporting & Reusing State
You can sign in once, export the browser context, and reuse it later—without re-entering credentials.
  * **`await context.storage_state(path="my_storage.json")`**: Exports cookies, localStorage, etc. to a file.
  * Provide `storage_state="my_storage.json"` on subsequent runs to skip the login step.


**See** : [Detailed session management tutorial](https://docs.crawl4ai.com/advanced/session-management/) or [Explanations → Browser Context & Managed Browser](https://docs.crawl4ai.com/advanced/identity-based-crawling/) for more advanced scenarios (like multi-step logins, or capturing after interactive pages).
* * *
## 6. Robots.txt Compliance
Crawl4AI supports respecting robots.txt rules with efficient caching:
```
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
Copy
```

**Key Points** - Robots.txt files are cached locally for efficiency - Cache is stored in `~/.crawl4ai/robots/robots_cache.db` - Cache has a default TTL of 7 days - If robots.txt can't be fetched, crawling is allowed - Returns 403 status code if URL is disallowed
* * *
## Putting It All Together
Here’s a snippet that combines multiple “advanced” features (proxy, PDF, screenshot, SSL, custom headers, and session reuse) into one run. Normally, you’d tailor each setting to your project’s needs.
```
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
Copy
```

* * *
* * *
## 7. Anti-Bot Features (Stealth Mode & Undetected Browser)
Crawl4AI provides two powerful features to bypass bot detection:
### 7.1 Stealth Mode
Stealth mode uses playwright-stealth to modify browser fingerprints and behaviors. Enable it with a simple flag:
```
browser_config = BrowserConfig(
    enable_stealth=True,  # Activates stealth mode
    headless=False
)
Copy
```

**When to use** : Sites with basic bot detection (checking navigator.webdriver, plugins, etc.)
### 7.2 Undetected Browser
For advanced bot detection, use the undetected browser adapter:
```
from crawl4ai import UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

# Create undetected adapter
adapter = UndetectedAdapter()
strategy = AsyncPlaywrightCrawlerStrategy(
    browser_config=browser_config,
    browser_adapter=adapter
)

async with AsyncWebCrawler(crawler_strategy=strategy, config=browser_config) as crawler:
    # Your crawling code
Copy
```

**When to use** : Sites with sophisticated bot detection (Cloudflare, DataDome, etc.)
### 7.3 Combining Both
For maximum evasion, combine stealth mode with undetected browser:
```
browser_config = BrowserConfig(
    enable_stealth=True,  # Enable stealth
    headless=False
)

adapter = UndetectedAdapter()  # Use undetected browser
Copy
```

### Choosing the Right Approach
Detection Level | Recommended Approach
---|---
No protection | Regular browser
Basic checks | Regular + Stealth mode
Advanced protection | Undetected browser
Maximum evasion | Undetected + Stealth mode
**Best Practice** : Start with regular browser + stealth mode. Only use undetected browser if needed, as it may be slightly slower.
See [Undetected Browser Mode](https://docs.crawl4ai.com/advanced/undetected-browser/) for detailed examples.
* * *
## Conclusion & Next Steps
You've now explored several **advanced** features:
  * **Proxy Usage**
  * **PDF & Screenshot** capturing for large or critical pages
  * **SSL Certificate** retrieval & exporting
  * **Custom Headers** for language or specialized requests
  * **Session Persistence** via storage state
  * **Robots.txt Compliance**
  * **Anti-Bot Features** (Stealth Mode & Undetected Browser)


With these power tools, you can build robust scraping workflows that mimic real user behavior, handle secure sites, capture detailed snapshots, manage sessions across multiple runs, and bypass bot detection—streamlining your entire data collection pipeline.
**Note** : In future versions, we may enable stealth mode and undetected browser by default. For now, users should explicitly enable these features when needed.
**Last Updated** : 2025-01-17
#### On this page
  * [1. Proxy Usage](https://docs.crawl4ai.com/advanced/advanced-features/#1-proxy-usage)
  * [2. Capturing PDFs & Screenshots](https://docs.crawl4ai.com/advanced/advanced-features/#2-capturing-pdfs-screenshots)
  * [3. Handling SSL Certificates](https://docs.crawl4ai.com/advanced/advanced-features/#3-handling-ssl-certificates)
  * [4. Custom Headers](https://docs.crawl4ai.com/advanced/advanced-features/#4-custom-headers)
  * [5. Session Persistence & Local Storage](https://docs.crawl4ai.com/advanced/advanced-features/#5-session-persistence-local-storage)
  * [5.1 storage_state](https://docs.crawl4ai.com/advanced/advanced-features/#51-storage_state)
  * [5.2 Exporting & Reusing State](https://docs.crawl4ai.com/advanced/advanced-features/#52-exporting-reusing-state)
  * [6. Robots.txt Compliance](https://docs.crawl4ai.com/advanced/advanced-features/#6-robotstxt-compliance)
  * [Putting It All Together](https://docs.crawl4ai.com/advanced/advanced-features/#putting-it-all-together)
  * [7. Anti-Bot Features (Stealth Mode & Undetected Browser)](https://docs.crawl4ai.com/advanced/advanced-features/#7-anti-bot-features-stealth-mode-undetected-browser)
  * [7.1 Stealth Mode](https://docs.crawl4ai.com/advanced/advanced-features/#71-stealth-mode)
  * [7.2 Undetected Browser](https://docs.crawl4ai.com/advanced/advanced-features/#72-undetected-browser)
  * [7.3 Combining Both](https://docs.crawl4ai.com/advanced/advanced-features/#73-combining-both)
  * [Choosing the Right Approach](https://docs.crawl4ai.com/advanced/advanced-features/#choosing-the-right-approach)
  * [Conclusion & Next Steps](https://docs.crawl4ai.com/advanced/advanced-features/#conclusion-next-steps)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
