### Session-Based Crawling for Dynamic Content

In modern web applications, content is often loaded dynamically without changing the URL. Examples include "Load More" buttons, infinite scrolling, or paginated content that updates via JavaScript. Crawl4AI provides session-based crawling capabilities to handle such scenarios effectively.

This guide explores advanced techniques for crawling dynamic content using Crawl4AI's session management features.

---

## Understanding Session-Based Crawling

Session-based crawling allows you to reuse a persistent browser session across multiple actions. This means the same browser tab (or page object) is used throughout, enabling:

1. **Efficient handling of dynamic content** without reloading the page.
2. **JavaScript actions before and after crawling** (e.g., clicking buttons or scrolling).
3. **State maintenance** for authenticated sessions or multi-step workflows.
4. **Faster sequential crawling**, as it avoids reopening tabs or reallocating resources.

**Note:** Session-based crawling is ideal for sequential operations, not parallel tasks.

---

## Basic Concepts

Before diving into examples, here are some key concepts:

- **Session ID**: A unique identifier for a browsing session. Use the same `session_id` across multiple requests to maintain state.
- **BrowserConfig & CrawlerRunConfig**: These configuration objects control browser settings and crawling behavior.
- **JavaScript Execution**: Use `js_code` to perform actions like clicking buttons.
- **CSS Selectors**: Target specific elements for interaction or data extraction.
- **Extraction Strategy**: Define rules to extract structured data.
- **Wait Conditions**: Specify conditions to wait for before proceeding.

---

## Example 1: Basic Session-Based Crawling

A simple example using session-based crawling:

```python
import asyncio
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.cache_context import CacheMode

async def basic_session_crawl():
    async with AsyncWebCrawler() as crawler:
        session_id = "dynamic_content_session"
        url = "https://example.com/dynamic-content"

        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                js_code="document.querySelector('.load-more-button').click();" if page > 0 else None,
                css_selector=".content-item",
                cache_mode=CacheMode.BYPASS
            )
            
            result = await crawler.arun(config=config)
            print(f"Page {page + 1}: Found {result.extracted_content.count('.content-item')} items")

        await crawler.crawler_strategy.kill_session(session_id)

asyncio.run(basic_session_crawl())
```

This example shows:
1. Reusing the same `session_id` across multiple requests.
2. Executing JavaScript to load more content dynamically.
3. Properly closing the session to free resources.

---

## Advanced Technique 1: Custom Execution Hooks

Use custom hooks to handle complex scenarios, such as waiting for content to load dynamically:

```python
async def advanced_session_crawl_with_hooks():
    first_commit = ""

    async def on_execution_started(page):
        nonlocal first_commit
        try:
            while True:
                await page.wait_for_selector("li.commit-item h4")
                commit = await page.query_selector("li.commit-item h4")
                commit = await commit.evaluate("(element) => element.textContent").strip()
                if commit and commit != first_commit:
                    first_commit = commit
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Warning: New content didn't appear: {e}")

    async with AsyncWebCrawler() as crawler:
        session_id = "commit_session"
        url = "https://github.com/example/repo/commits/main"
        crawler.crawler_strategy.set_hook("on_execution_started", on_execution_started)

        js_next_page = """document.querySelector('a.pagination-next').click();"""

        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                js_code=js_next_page if page > 0 else None,
                css_selector="li.commit-item",
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            print(f"Page {page + 1}: Found {len(result.extracted_content)} commits")

        await crawler.crawler_strategy.kill_session(session_id)

asyncio.run(advanced_session_crawl_with_hooks())
```

This technique ensures new content loads before the next action.

---

## Advanced Technique 2: Integrated JavaScript Execution and Waiting

Combine JavaScript execution and waiting logic for concise handling of dynamic content:

```python
async def integrated_js_and_wait_crawl():
    async with AsyncWebCrawler() as crawler:
        session_id = "integrated_session"
        url = "https://github.com/example/repo/commits/main"

        js_next_page_and_wait = """
        (async () => {
            const getCurrentCommit = () => document.querySelector('li.commit-item h4').textContent.trim();
            const initialCommit = getCurrentCommit();
            document.querySelector('a.pagination-next').click();
            while (getCurrentCommit() === initialCommit) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        })();
        """

        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                js_code=js_next_page_and_wait if page > 0 else None,
                css_selector="li.commit-item",
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            print(f"Page {page + 1}: Found {len(result.extracted_content)} commits")

        await crawler.crawler_strategy.kill_session(session_id)

asyncio.run(integrated_js_and_wait_crawl())
```

---

## Best Practices for Session-Based Crawling

1. **Unique Session IDs**: Assign descriptive and unique `session_id` values.
2. **Close Sessions**: Always clean up sessions with `kill_session` after use.
3. **Error Handling**: Anticipate and handle errors gracefully.
4. **Respect Websites**: Follow terms of service and robots.txt.
5. **Delays**: Add delays to avoid overwhelming servers.
6. **Optimize JavaScript**: Keep scripts concise for better performance.
7. **Monitor Resources**: Track memory and CPU usage for long sessions.

---

## Conclusion

Session-based crawling in Crawl4AI is a robust solution for handling dynamic content and multi-step workflows. By combining session management, JavaScript execution, and structured extraction strategies, you can effectively navigate and extract data from modern web applications. Always adhere to ethical web scraping practices and respect website policies.