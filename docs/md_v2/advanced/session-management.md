### Session Management

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
    config1 = CrawlerRunConfig(url="https://example.com/page1", session_id=session_id)
    config2 = CrawlerRunConfig(url="https://example.com/page2", session_id=session_id)

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
            "fields": [{"name": "title", "selector": "h4.markdown-title", "type": "text"}],
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

#### Session Best Practices

1. **Descriptive Session IDs**:
   Use meaningful names for session IDs to organize workflows:
   ```python
   session_id = "login_flow_session"
   session_id = "product_catalog_session"
   ```

2. **Resource Management**:
   Always ensure sessions are cleaned up to free resources:
   ```python
   try:
       # Your crawling code here
       pass
   finally:
       await crawler.crawler_strategy.kill_session(session_id)
   ```

3. **State Maintenance**:
   Reuse the session for subsequent actions within the same workflow:
   ```python
   # Step 1: Login
   login_config = CrawlerRunConfig(
       url="https://example.com/login",
       session_id=session_id,
       js_code="document.querySelector('form').submit();"
   )
   await crawler.arun(config=login_config)

   # Step 2: Verify login success
   dashboard_config = CrawlerRunConfig(
       url="https://example.com/dashboard",
       session_id=session_id,
       wait_for="css:.user-profile"  # Wait for authenticated content
   )
   result = await crawler.arun(config=dashboard_config)
   ```

---

#### Common Use Cases for Sessions

1. **Authentication Flows**: Login and interact with secured pages.
2. **Pagination Handling**: Navigate through multiple pages.
3. **Form Submissions**: Fill forms, submit, and process results.
4. **Multi-step Processes**: Complete workflows that span multiple actions.
5. **Dynamic Content Navigation**: Handle JavaScript-rendered or event-triggered content.
