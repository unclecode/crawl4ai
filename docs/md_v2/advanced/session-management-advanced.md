# Session-Based Crawling for Dynamic Content

In modern web applications, content is often loaded dynamically without changing the URL. Examples include "Load More" buttons, infinite scrolling, or paginated content that updates via JavaScript. To effectively crawl such websites, Crawl4AI provides powerful session-based crawling capabilities.

This guide will explore advanced techniques for crawling dynamic content using Crawl4AI's session management features.

## Understanding Session-Based Crawling

Session-based crawling allows you to maintain a persistent browser session across multiple requests. This is crucial when:

1. The content changes dynamically without URL changes
2. You need to interact with the page (e.g., clicking buttons) between requests
3. The site requires authentication or maintains state across pages

Crawl4AI's `AsyncWebCrawler` class supports session-based crawling through the `session_id` parameter and related methods.

## Basic Concepts

Before diving into examples, let's review some key concepts:

- **Session ID**: A unique identifier for a browsing session. Use the same `session_id` across multiple `arun` calls to maintain state.
- **JavaScript Execution**: Use the `js_code` parameter to execute JavaScript on the page, such as clicking a "Load More" button.
- **CSS Selectors**: Use these to target specific elements for extraction or interaction.
- **Extraction Strategy**: Define how to extract structured data from the page.
- **Wait Conditions**: Specify conditions to wait for before considering the page loaded.

## Example 1: Basic Session-Based Crawling

Let's start with a basic example of session-based crawling:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def basic_session_crawl():
    async with AsyncWebCrawler(verbose=True) as crawler:
        session_id = "my_session"
        url = "https://example.com/dynamic-content"

        for page in range(3):
            result = await crawler.arun(
                url=url,
                session_id=session_id,
                js_code="document.querySelector('.load-more-button').click();" if page > 0 else None,
                css_selector=".content-item",
                bypass_cache=True
            )
            
            print(f"Page {page + 1}: Found {result.extracted_content.count('.content-item')} items")

        await crawler.crawler_strategy.kill_session(session_id)

asyncio.run(basic_session_crawl())
```

This example demonstrates:
1. Using a consistent `session_id` across multiple `arun` calls
2. Executing JavaScript to load more content after the first page
3. Using a CSS selector to extract specific content
4. Properly closing the session after crawling

## Advanced Technique 1: Custom Execution Hooks

Crawl4AI allows you to set custom hooks that execute at different stages of the crawling process. This is particularly useful for handling complex loading scenarios.

Here's an example that waits for new content to appear before proceeding:

```python
async def advanced_session_crawl_with_hooks():
    first_commit = ""

    async def on_execution_started(page):
        nonlocal first_commit
        try:
            while True:
                await page.wait_for_selector("li.commit-item h4")
                commit = await page.query_selector("li.commit-item h4")
                commit = await commit.evaluate("(element) => element.textContent")
                commit = commit.strip()
                if commit and commit != first_commit:
                    first_commit = commit
                    break
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Warning: New content didn't appear after JavaScript execution: {e}")

    async with AsyncWebCrawler(verbose=True) as crawler:
        crawler.crawler_strategy.set_hook("on_execution_started", on_execution_started)

        url = "https://github.com/example/repo/commits/main"
        session_id = "commit_session"
        all_commits = []

        js_next_page = """
        const button = document.querySelector('a.pagination-next');
        if (button) button.click();
        """

        for page in range(3):
            result = await crawler.arun(
                url=url,
                session_id=session_id,
                css_selector="li.commit-item",
                js_code=js_next_page if page > 0 else None,
                bypass_cache=True,
                js_only=page > 0
            )

            commits = result.extracted_content.select("li.commit-item")
            all_commits.extend(commits)
            print(f"Page {page + 1}: Found {len(commits)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")

asyncio.run(advanced_session_crawl_with_hooks())
```

This technique uses a custom `on_execution_started` hook to ensure new content has loaded before proceeding to the next step.

## Advanced Technique 2: Integrated JavaScript Execution and Waiting

Instead of using separate hooks, you can integrate the waiting logic directly into your JavaScript execution. This approach can be more concise and easier to manage for some scenarios.

Here's an example:

```python
async def integrated_js_and_wait_crawl():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://github.com/example/repo/commits/main"
        session_id = "integrated_session"
        all_commits = []

        js_next_page_and_wait = """
        (async () => {
            const getCurrentCommit = () => {
                const commits = document.querySelectorAll('li.commit-item h4');
                return commits.length > 0 ? commits[0].textContent.trim() : null;
            };

            const initialCommit = getCurrentCommit();
            const button = document.querySelector('a.pagination-next');
            if (button) button.click();

            while (true) {
                await new Promise(resolve => setTimeout(resolve, 100));
                const newCommit = getCurrentCommit();
                if (newCommit && newCommit !== initialCommit) {
                    break;
                }
            }
        })();
        """

        schema = {
            "name": "Commit Extractor",
            "baseSelector": "li.commit-item",
            "fields": [
                {
                    "name": "title",
                    "selector": "h4.commit-title",
                    "type": "text",
                    "transform": "strip",
                },
            ],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

        for page in range(3):
            result = await crawler.arun(
                url=url,
                session_id=session_id,
                css_selector="li.commit-item",
                extraction_strategy=extraction_strategy,
                js_code=js_next_page_and_wait if page > 0 else None,
                js_only=page > 0,
                bypass_cache=True
            )

            commits = json.loads(result.extracted_content)
            all_commits.extend(commits)
            print(f"Page {page + 1}: Found {len(commits)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")

asyncio.run(integrated_js_and_wait_crawl())
```

This approach combines the JavaScript for clicking the "next" button and waiting for new content to load into a single script.

## Advanced Technique 3: Using the `wait_for` Parameter

Crawl4AI provides a `wait_for` parameter that allows you to specify a condition to wait for before considering the page fully loaded. This can be particularly useful for dynamic content.

Here's an example:

```python
async def wait_for_parameter_crawl():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://github.com/example/repo/commits/main"
        session_id = "wait_for_session"
        all_commits = []

        js_next_page = """
        const commits = document.querySelectorAll('li.commit-item h4');
        if (commits.length > 0) {
            window.lastCommit = commits[0].textContent.trim();
        }
        const button = document.querySelector('a.pagination-next');
        if (button) button.click();
        """

        wait_for = """() => {
            const commits = document.querySelectorAll('li.commit-item h4');
            if (commits.length === 0) return false;
            const firstCommit = commits[0].textContent.trim();
            return firstCommit !== window.lastCommit;
        }"""
        
        schema = {
            "name": "Commit Extractor",
            "baseSelector": "li.commit-item",
            "fields": [
                {
                    "name": "title",
                    "selector": "h4.commit-title",
                    "type": "text",
                    "transform": "strip",
                },
            ],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

        for page in range(3):
            result = await crawler.arun(
                url=url,
                session_id=session_id,
                css_selector="li.commit-item",
                extraction_strategy=extraction_strategy,
                js_code=js_next_page if page > 0 else None,
                wait_for=wait_for if page > 0 else None,
                js_only=page > 0,
                bypass_cache=True
            )

            commits = json.loads(result.extracted_content)
            all_commits.extend(commits)
            print(f"Page {page + 1}: Found {len(commits)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")

asyncio.run(wait_for_parameter_crawl())
```

This technique separates the JavaScript execution (clicking the "next" button) from the waiting condition, providing more flexibility and clarity in some scenarios.

## Best Practices for Session-Based Crawling

1. **Use Unique Session IDs**: Ensure each crawling session has a unique `session_id` to prevent conflicts.
2. **Close Sessions**: Always close sessions using `kill_session` when you're done to free up resources.
3. **Handle Errors**: Implement proper error handling to deal with unexpected situations during crawling.
4. **Respect Website Terms**: Ensure your crawling adheres to the website's terms of service and robots.txt file.
5. **Implement Delays**: Add appropriate delays between requests to avoid overwhelming the target server.
6. **Use Extraction Strategies**: Leverage `JsonCssExtractionStrategy` or other extraction strategies for structured data extraction.
7. **Optimize JavaScript**: Keep your JavaScript execution concise and efficient to improve crawling speed.
8. **Monitor Performance**: Keep an eye on memory usage and crawling speed, especially for long-running sessions.

## Conclusion

Session-based crawling with Crawl4AI provides powerful capabilities for handling dynamic content and complex web applications. By leveraging session management, JavaScript execution, and waiting strategies, you can effectively crawl and extract data from a wide range of modern websites.

Remember to use these techniques responsibly and in compliance with website policies and ethical web scraping practices.

For more advanced usage and API details, refer to the Crawl4AI API documentation.