# Session Management

Session management in Crawl4AI allows you to maintain state across multiple requests and handle complex multi-page crawling tasks, particularly useful for dynamic websites.

## Basic Session Usage

Use `session_id` to maintain state between requests:

```python
async with AsyncWebCrawler() as crawler:
    session_id = "my_session"
    
    # First request
    result1 = await crawler.arun(
        url="https://example.com/page1",
        session_id=session_id
    )
    
    # Subsequent request using same session
    result2 = await crawler.arun(
        url="https://example.com/page2",
        session_id=session_id
    )
    
    # Clean up when done
    await crawler.crawler_strategy.kill_session(session_id)
```

## Dynamic Content with Sessions

Here's a real-world example of crawling GitHub commits across multiple pages:

```python
async def crawl_dynamic_content():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://github.com/microsoft/TypeScript/commits/main"
        session_id = "typescript_commits_session"
        all_commits = []

        # Define navigation JavaScript
        js_next_page = """
        const button = document.querySelector('a[data-testid="pagination-next-button"]');
        if (button) button.click();
        """

        # Define wait condition
        wait_for = """() => {
            const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
            if (commits.length === 0) return false;
            const firstCommit = commits[0].textContent.trim();
            return firstCommit !== window.firstCommit;
        }"""
        
        # Define extraction schema
        schema = {
            "name": "Commit Extractor",
            "baseSelector": "li.Box-sc-g0xbh4-0",
            "fields": [
                {
                    "name": "title",
                    "selector": "h4.markdown-title",
                    "type": "text",
                    "transform": "strip",
                },
            ],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema)

        # Crawl multiple pages
        for page in range(3):
            result = await crawler.arun(
                url=url,
                session_id=session_id,
                extraction_strategy=extraction_strategy,
                js_code=js_next_page if page > 0 else None,
                wait_for=wait_for if page > 0 else None,
                js_only=page > 0,
                bypass_cache=True
            )

            if result.success:
                commits = json.loads(result.extracted_content)
                all_commits.extend(commits)
                print(f"Page {page + 1}: Found {len(commits)} commits")

        # Clean up session
        await crawler.crawler_strategy.kill_session(session_id)
        return all_commits
```

## Session Best Practices

1. **Session Naming**:
```python
# Use descriptive session IDs
session_id = "login_flow_session"
session_id = "product_catalog_session"
```

2. **Resource Management**:
```python
try:
    # Your crawling code
    pass
finally:
    # Always clean up sessions
    await crawler.crawler_strategy.kill_session(session_id)
```

3. **State Management**:
```python
# First page: login
result = await crawler.arun(
    url="https://example.com/login",
    session_id=session_id,
    js_code="document.querySelector('form').submit();"
)

# Second page: verify login success
result = await crawler.arun(
    url="https://example.com/dashboard",
    session_id=session_id,
    wait_for="css:.user-profile"  # Wait for authenticated content
)
```

## Common Use Cases

1. **Authentication Flows**
2. **Pagination Handling**
3. **Form Submissions**
4. **Multi-step Processes**
5. **Dynamic Content Navigation**
