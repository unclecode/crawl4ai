# Session Management

Session management in Crawl4AI is a powerful feature that allows you to maintain state across multiple requests, making it particularly suitable for handling complex multi-step crawling tasks. It enables you to reuse the same browser tab (or page object) across sequential actions and crawls, which is beneficial for:

- **Performing JavaScript actions before and after crawling.**
- **Executing multiple sequential crawls faster** without needing to reopen tabs or allocate memory repeatedly.

**Note:** This feature is designed for sequential workflows and is not suitable for parallel operations.

---

#### Basic Session Usage

Use `BrowserConfig` and `CrawlerRunConfig` to maintain state with a `session_id`:

```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async with AsyncWebCrawler() as crawler:
    session_id = "my_session"

    # Define configurations
    config1 = CrawlerRunConfig(
        url="https://example.com/page1", session_id=session_id
    )
    config2 = CrawlerRunConfig(
        url="https://example.com/page2", session_id=session_id
    )

    # First request
    result1 = await crawler.arun(config=config1)

    # Subsequent request using the same session
    result2 = await crawler.arun(config=config2)

    # Clean up when done
    await crawler.crawler_strategy.kill_session(session_id)
```

---

#### Dynamic Content with Sessions

Here's an example of crawling GitHub commits across multiple pages while preserving session state:

```python
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.cache_context import CacheMode

async def crawl_dynamic_content():
    async with AsyncWebCrawler() as crawler:
        session_id = "github_commits_session"
        url = "https://github.com/microsoft/TypeScript/commits/main"
        all_commits = []

        # Define extraction schema
        schema = {
            "name": "Commit Extractor",
            "baseSelector": "li.Box-sc-g0xbh4-0",
            "fields": [{
                "name": "title", "selector": "h4.markdown-title", "type": "text"
            }],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema)

        # JavaScript and wait configurations
        js_next_page = """document.querySelector('a[data-testid="pagination-next-button"]').click();"""
        wait_for = """() => document.querySelectorAll('li.Box-sc-g0xbh4-0').length > 0"""

        # Crawl multiple pages
        for page in range(3):
            config = CrawlerRunConfig(
                url=url,
                session_id=session_id,
                extraction_strategy=extraction_strategy,
                js_code=js_next_page if page > 0 else None,
                wait_for=wait_for if page > 0 else None,
                js_only=page > 0,
                cache_mode=CacheMode.BYPASS
            )

            result = await crawler.arun(config=config)
            if result.success:
                commits = json.loads(result.extracted_content)
                all_commits.extend(commits)
                print(f"Page {page + 1}: Found {len(commits)} commits")

        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
        return all_commits
```

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

> Warning: You might feel confused by the end of the next few examples 😅, so make sure you are comfortable with the order of the parts before you start this.

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

#### Common Use Cases for Sessions

1. **Authentication Flows**: Login and interact with secured pages.

2. **Pagination Handling**: Navigate through multiple pages.

3. **Form Submissions**: Fill forms, submit, and process results.

4. **Multi-step Processes**: Complete workflows that span multiple actions.

5. **Dynamic Content Navigation**: Handle JavaScript-rendered or event-triggered content.
