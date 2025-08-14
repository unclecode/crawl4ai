Overview of Some Important Advanced Features
============================================

(Proxy, PDF, Screenshot, SSL, Headers, & Storage State)

Crawl4AI offers multiple power-user features that go beyond simple crawling. This tutorial covers:

1. **Proxy Usage**
2. **Capturing PDFs & Screenshots**
3. **Handling SSL Certificates**
4. **Custom Headers**
5. **Session Persistence & Local Storage**
6. **Robots.txt Compliance**

> **Prerequisites**
> - You have a basic grasp of [AsyncWebCrawler Basics](../../core/simple-crawling/)
> - You know how to run or configure your Python environment with Playwright installed

---

1. Proxy Usage
--------------

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
```

**Key Points**
- **`proxy_config`** expects a dict with `server` and optional auth credentials.
- Many commercial proxies provide an HTTP/HTTPS “gateway” server that you specify in `server`.
- If your proxy doesn’t need auth, omit `username`/`password`.

---