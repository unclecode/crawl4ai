[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/advanced/hooks-auth/)


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
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * Hooks & Auth
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
  * [Hooks & Auth in AsyncWebCrawler](https://docs.crawl4ai.com/advanced/hooks-auth/#hooks-auth-in-asyncwebcrawler)
  * [Example: Using Hooks in AsyncWebCrawler](https://docs.crawl4ai.com/advanced/hooks-auth/#example-using-hooks-in-asyncwebcrawler)
  * [Hook Lifecycle Summary](https://docs.crawl4ai.com/advanced/hooks-auth/#hook-lifecycle-summary)
  * [When to Handle Authentication](https://docs.crawl4ai.com/advanced/hooks-auth/#when-to-handle-authentication)
  * [Additional Considerations](https://docs.crawl4ai.com/advanced/hooks-auth/#additional-considerations)
  * [Conclusion](https://docs.crawl4ai.com/advanced/hooks-auth/#conclusion)


# Hooks & Auth in AsyncWebCrawler
Crawl4AI’s **hooks** let you customize the crawler at specific points in the pipeline:
1. **`on_browser_created`**– After browser creation.
2. **`on_page_context_created`**– After a new context & page are created.
3. **`before_goto`**– Just before navigating to a page.
4. **`after_goto`**– Right after navigation completes.
5. **`on_user_agent_updated`**– Whenever the user agent changes.
6. **`on_execution_started`**– Once custom JavaScript execution begins.
7. **`before_retrieve_html`**– Just before the crawler retrieves final HTML.
8. **`before_return_html`**– Right before returning the HTML content.
**Important** : Avoid heavy tasks in `on_browser_created` since you don’t yet have a page context. If you need to _log in_ , do so in **`on_page_context_created`**.
> note "Important Hook Usage Warning" **Avoid Misusing Hooks** : Do not manipulate page objects in the wrong hook or at the wrong time, as it can crash the pipeline or produce incorrect results. A common mistake is attempting to handle authentication prematurely—such as creating or closing pages in `on_browser_created`.
> **Use the Right Hook for Auth** : If you need to log in or set tokens, use `on_page_context_created`. This ensures you have a valid page/context to work with, without disrupting the main crawling flow.
> **Identity-Based Crawling** : For robust auth, consider identity-based crawling (or passing a session ID) to preserve state. Run your initial login steps in a separate, well-defined process, then feed that session to your main crawl—rather than shoehorning complex authentication into early hooks. Check out [Identity-Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/) for more details.
> **Be Cautious** : Overwriting or removing elements in the wrong hook can compromise the final crawl. Keep hooks focused on smaller tasks (like route filters, custom headers), and let your main logic (crawling, data extraction) proceed normally.
Below is an example demonstration.
* * *
## Example: Using Hooks in AsyncWebCrawler
```
import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext

async def main():
    print("🔗 Hooks Example: Demonstrating recommended usage")

    # 1) Configure the browser
    browser_config = BrowserConfig(
        headless=True,
        verbose=True
    )

    # 2) Configure the crawler run
    crawler_run_config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);",
        wait_for="body",
        cache_mode=CacheMode.BYPASS
    )

    # 3) Create the crawler instance
    crawler = AsyncWebCrawler(config=browser_config)

    #
    # Define Hook Functions
    #

    async def on_browser_created(browser, **kwargs):
        # Called once the browser instance is created (but no pages or contexts yet)
        print("[HOOK] on_browser_created - Browser created successfully!")
        # Typically, do minimal setup here if needed
        return browser

    async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
        # Called right after a new page + context are created (ideal for auth or route config).
        print("[HOOK] on_page_context_created - Setting up page & context.")

        # Example 1: Route filtering (e.g., block images)
        async def route_filter(route):
            if route.request.resource_type == "image":
                print(f"[HOOK] Blocking image request: {route.request.url}")
                await route.abort()
            else:
                await route.continue_()

        await context.route("**", route_filter)

        # Example 2: (Optional) Simulate a login scenario
        # (We do NOT create or close pages here, just do quick steps if needed)
        # e.g., await page.goto("https://example.com/login")
        # e.g., await page.fill("input[name='username']", "testuser")
        # e.g., await page.fill("input[name='password']", "password123")
        # e.g., await page.click("button[type='submit']")
        # e.g., await page.wait_for_selector("#welcome")
        # e.g., await context.add_cookies([...])
        # Then continue

        # Example 3: Adjust the viewport
        await page.set_viewport_size({"width": 1080, "height": 600})
        return page

    async def before_goto(
        page: Page, context: BrowserContext, url: str, **kwargs
    ):
        # Called before navigating to each URL.
        print(f"[HOOK] before_goto - About to navigate: {url}")
        # e.g., inject custom headers
        await page.set_extra_http_headers({
            "Custom-Header": "my-value"
        })
        return page

    async def after_goto(
        page: Page, context: BrowserContext,
        url: str, response, **kwargs
    ):
        # Called after navigation completes.
        print(f"[HOOK] after_goto - Successfully loaded: {url}")
        # e.g., wait for a certain element if we want to verify
        try:
            await page.wait_for_selector('.content', timeout=1000)
            print("[HOOK] Found .content element!")
        except:
            print("[HOOK] .content not found, continuing anyway.")
        return page

    async def on_user_agent_updated(
        page: Page, context: BrowserContext,
        user_agent: str, **kwargs
    ):
        # Called whenever the user agent updates.
        print(f"[HOOK] on_user_agent_updated - New user agent: {user_agent}")
        return page

    async def on_execution_started(page: Page, context: BrowserContext, **kwargs):
        # Called after custom JavaScript execution begins.
        print("[HOOK] on_execution_started - JS code is running!")
        return page

    async def before_retrieve_html(page: Page, context: BrowserContext, **kwargs):
        # Called before final HTML retrieval.
        print("[HOOK] before_retrieve_html - We can do final actions")
        # Example: Scroll again
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        return page

    async def before_return_html(
        page: Page, context: BrowserContext, html: str, **kwargs
    ):
        # Called just before returning the HTML in the result.
        print(f"[HOOK] before_return_html - HTML length: {len(html)}")
        return page

    #
    # Attach Hooks
    #

    crawler.crawler_strategy.set_hook("on_browser_created", on_browser_created)
    crawler.crawler_strategy.set_hook(
        "on_page_context_created", on_page_context_created
    )
    crawler.crawler_strategy.set_hook("before_goto", before_goto)
    crawler.crawler_strategy.set_hook("after_goto", after_goto)
    crawler.crawler_strategy.set_hook(
        "on_user_agent_updated", on_user_agent_updated
    )
    crawler.crawler_strategy.set_hook(
        "on_execution_started", on_execution_started
    )
    crawler.crawler_strategy.set_hook(
        "before_retrieve_html", before_retrieve_html
    )
    crawler.crawler_strategy.set_hook(
        "before_return_html", before_return_html
    )

    await crawler.start()

    # 4) Run the crawler on an example page
    url = "https://example.com"
    result = await crawler.arun(url, config=crawler_run_config)

    if result.success:
        print("\nCrawled URL:", result.url)
        print("HTML length:", len(result.html))
    else:
        print("Error:", result.error_message)

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

* * *
## Hook Lifecycle Summary
1. **`on_browser_created`**:
- Browser is up, but **no** pages or contexts yet.
- Light setup only—don’t try to open or close pages here (that belongs in `on_page_context_created`).
2. **`on_page_context_created`**:
- Perfect for advanced **auth** or route blocking.
- You have a **page** + **context** ready but haven’t navigated to the target URL yet.
3. **`before_goto`**:
- Right before navigation. Typically used for setting **custom headers** or logging the target URL.
4. **`after_goto`**:
- After page navigation is done. Good place for verifying content or waiting on essential elements.
5. **`on_user_agent_updated`**:
- Whenever the user agent changes (for stealth or different UA modes).
6. **`on_execution_started`**:
- If you set `js_code` or run custom scripts, this runs once your JS is about to start.
7. **`before_retrieve_html`**:
- Just before the final HTML snapshot is taken. Often you do a final scroll or lazy-load triggers here.
8. **`before_return_html`**:
- The last hook before returning HTML to the `CrawlResult`. Good for logging HTML length or minor modifications.
* * *
## When to Handle Authentication
**Recommended** : Use **`on_page_context_created`**if you need to:
  * Navigate to a login page or fill forms
  * Set cookies or localStorage tokens
  * Block resource routes to avoid ads


This ensures the newly created context is under your control **before** `arun()` navigates to the main URL.
* * *
## Additional Considerations
  * **Session Management** : If you want multiple `arun()` calls to reuse a single session, pass `session_id=` in your `CrawlerRunConfig`. Hooks remain the same.
  * **Performance** : Hooks can slow down crawling if they do heavy tasks. Keep them concise.
  * **Error Handling** : If a hook fails, the overall crawl might fail. Catch exceptions or handle them gracefully.
  * **Concurrency** : If you run `arun_many()`, each URL triggers these hooks in parallel. Ensure your hooks are thread/async-safe.


* * *
## Conclusion
Hooks provide **fine-grained** control over:
  * **Browser** creation (light tasks only)
  * **Page** and **context** creation (auth, route blocking)
  * **Navigation** phases
  * **Final HTML** retrieval


Follow the recommended usage: - **Login** or advanced tasks in `on_page_context_created`
- **Custom headers** or logs in `before_goto` / `after_goto`
- **Scrolling** or final checks in `before_retrieve_html` / `before_return_html`
#### On this page
  * [Example: Using Hooks in AsyncWebCrawler](https://docs.crawl4ai.com/advanced/hooks-auth/#example-using-hooks-in-asyncwebcrawler)
  * [Hook Lifecycle Summary](https://docs.crawl4ai.com/advanced/hooks-auth/#hook-lifecycle-summary)
  * [When to Handle Authentication](https://docs.crawl4ai.com/advanced/hooks-auth/#when-to-handle-authentication)
  * [Additional Considerations](https://docs.crawl4ai.com/advanced/hooks-auth/#additional-considerations)
  * [Conclusion](https://docs.crawl4ai.com/advanced/hooks-auth/#conclusion)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
