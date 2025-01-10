# Page Interaction

Crawl4AI provides powerful features for interacting with **dynamic** webpages, handling JavaScript execution, waiting for conditions, and managing multi-step flows. By combining **js_code**, **wait_for**, and certain **CrawlerRunConfig** parameters, you can:

1. Click “Load More” buttons  
2. Fill forms and submit them  
3. Wait for elements or data to appear  
4. Reuse sessions across multiple steps  

Below is a quick overview of how to do it.

---

## 1. JavaScript Execution

### Basic Execution

**`js_code`** in **`CrawlerRunConfig`** accepts either a single JS string or a list of JS snippets.  
**Example**: We’ll scroll to the bottom of the page, then optionally click a “Load More” button.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Single JS command
    config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",  # Example site
            config=config
        )
        print("Crawled length:", len(result.cleaned_html))

    # Multiple commands
    js_commands = [
        "window.scrollTo(0, document.body.scrollHeight);",
        # 'More' link on Hacker News
        "document.querySelector('a.morelink')?.click();",  
    ]
    config = CrawlerRunConfig(js_code=js_commands)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",  # Another pass
            config=config
        )
        print("After scroll+click, length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
```

**Relevant `CrawlerRunConfig` params**:
- **`js_code`**: A string or list of strings with JavaScript to run after the page loads.
- **`js_only`**: If set to `True` on subsequent calls, indicates we’re continuing an existing session without a new full navigation.  
- **`session_id`**: If you want to keep the same page across multiple calls, specify an ID.

---

## 2. Wait Conditions

### 2.1 CSS-Based Waiting

Sometimes, you just want to wait for a specific element to appear. For example:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        # Wait for at least 30 items on Hacker News
        wait_for="css:.athing:nth-child(30)"  
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=config
        )
        print("We have at least 30 items loaded!")
        # Rough check
        print("Total items in HTML:", result.cleaned_html.count("athing"))  

if __name__ == "__main__":
    asyncio.run(main())
```

**Key param**:
- **`wait_for="css:..."`**: Tells the crawler to wait until that CSS selector is present.

### 2.2 JavaScript-Based Waiting

For more complex conditions (e.g., waiting for content length to exceed a threshold), prefix `js:`:

```python
wait_condition = """() => {
    const items = document.querySelectorAll('.athing');
    return items.length > 50;  // Wait for at least 51 items
}"""

config = CrawlerRunConfig(wait_for=f"js:{wait_condition}")
```

**Behind the Scenes**: Crawl4AI keeps polling the JS function until it returns `true` or a timeout occurs.

---

## 3. Handling Dynamic Content

Many modern sites require **multiple steps**: scrolling, clicking “Load More,” or updating via JavaScript. Below are typical patterns.

### 3.1 Load More Example (Hacker News “More” Link)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Step 1: Load initial Hacker News page
    config = CrawlerRunConfig(
        wait_for="css:.athing:nth-child(30)"  # Wait for 30 items
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=config
        )
        print("Initial items loaded.")

        # Step 2: Let's scroll and click the "More" link
        load_more_js = [
            "window.scrollTo(0, document.body.scrollHeight);",
            # The "More" link at page bottom
            "document.querySelector('a.morelink')?.click();"  
        ]
        
        next_page_conf = CrawlerRunConfig(
            js_code=load_more_js,
            wait_for="""js:() => {
                return document.querySelectorAll('.athing').length > 30;
            }""",
            # Mark that we do not re-navigate, but run JS in the same session:
            js_only=True,
            session_id="hn_session"
        )

        # Re-use the same crawler session
        result2 = await crawler.arun(
            url="https://news.ycombinator.com",  # same URL but continuing session
            config=next_page_conf
        )
        total_items = result2.cleaned_html.count("athing")
        print("Items after load-more:", total_items)

if __name__ == "__main__":
    asyncio.run(main())
```

**Key params**:
- **`session_id="hn_session"`**: Keep the same page across multiple calls to `arun()`.
- **`js_only=True`**: We’re not performing a full reload, just applying JS in the existing page.
- **`wait_for`** with `js:`: Wait for item count to grow beyond 30.

---

### 3.2 Form Interaction

If the site has a search or login form, you can fill fields and submit them with **`js_code`**. For instance, if GitHub had a local search form:

```python
js_form_interaction = """
document.querySelector('#your-search').value = 'TypeScript commits';
document.querySelector('form').submit();
"""

config = CrawlerRunConfig(
    js_code=js_form_interaction,
    wait_for="css:.commit"
)
result = await crawler.arun(url="https://github.com/search", config=config)
```

**In reality**: Replace IDs or classes with the real site’s form selectors.

---

## 4. Timing Control

1. **`page_timeout`** (ms): Overall page load or script execution time limit.  
2. **`delay_before_return_html`** (seconds): Wait an extra moment before capturing the final HTML.  
3. **`mean_delay`** & **`max_range`**: If you call `arun_many()` with multiple URLs, these add a random pause between each request.

**Example**:

```python
config = CrawlerRunConfig(
    page_timeout=60000,  # 60s limit
    delay_before_return_html=2.5
)
```

---

## 5. Multi-Step Interaction Example

Below is a simplified script that does multiple “Load More” clicks on GitHub’s TypeScript commits page. It **re-uses** the same session to accumulate new commits each time. The code includes the relevant **`CrawlerRunConfig`** parameters you’d rely on.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def multi_page_commits():
    browser_cfg = BrowserConfig(
        headless=False,  # Visible for demonstration
        verbose=True
    )
    session_id = "github_ts_commits"
    
    base_wait = """js:() => {
        const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
        return commits.length > 0;
    }"""

    # Step 1: Load initial commits
    config1 = CrawlerRunConfig(
        wait_for=base_wait,
        session_id=session_id,
        cache_mode=CacheMode.BYPASS,
        # Not using js_only yet since it's our first load
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://github.com/microsoft/TypeScript/commits/main",
            config=config1
        )
        print("Initial commits loaded. Count:", result.cleaned_html.count("commit"))

        # Step 2: For subsequent pages, we run JS to click 'Next Page' if it exists
        js_next_page = """
        const selector = 'a[data-testid="pagination-next-button"]';
        const button = document.querySelector(selector);
        if (button) button.click();
        """
        
        # Wait until new commits appear
        wait_for_more = """js:() => {
            const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
            if (!window.firstCommit && commits.length>0) {
                window.firstCommit = commits[0].textContent;
                return false;
            }
            // If top commit changes, we have new commits
            const topNow = commits[0]?.textContent.trim();
            return topNow && topNow !== window.firstCommit;
        }"""

        for page in range(2):  # let's do 2 more "Next" pages
            config_next = CrawlerRunConfig(
                session_id=session_id,
                js_code=js_next_page,
                wait_for=wait_for_more,
                js_only=True,       # We're continuing from the open tab
                cache_mode=CacheMode.BYPASS
            )
            result2 = await crawler.arun(
                url="https://github.com/microsoft/TypeScript/commits/main",
                config=config_next
            )
            print(f"Page {page+2} commits count:", result2.cleaned_html.count("commit"))

        # Optionally kill session
        await crawler.crawler_strategy.kill_session(session_id)

async def main():
    await multi_page_commits()

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**:

- **`session_id`**: Keep the same page open.  
- **`js_code`** + **`wait_for`** + **`js_only=True`**: We do partial refreshes, waiting for new commits to appear.  
- **`cache_mode=CacheMode.BYPASS`** ensures we always see fresh data each step.

---

## 6. Combine Interaction with Extraction

Once dynamic content is loaded, you can attach an **`extraction_strategy`** (like `JsonCssExtractionStrategy` or `LLMExtractionStrategy`). For example:

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "name": "Commits",
    "baseSelector": "li.Box-sc-g0xbh4-0",
    "fields": [
        {"name": "title", "selector": "h4.markdown-title", "type": "text"}
    ]
}
config = CrawlerRunConfig(
    session_id="ts_commits_session",
    js_code=js_next_page,
    wait_for=wait_for_more,
    extraction_strategy=JsonCssExtractionStrategy(schema)
)
```

When done, check `result.extracted_content` for the JSON.

---

## 7. Relevant `CrawlerRunConfig` Parameters

Below are the key interaction-related parameters in `CrawlerRunConfig`. For a full list, see [Configuration Parameters](../api/parameters.md).

- **`js_code`**: JavaScript to run after initial load.  
- **`js_only`**: If `True`, no new page navigation—only JS in the existing session.  
- **`wait_for`**: CSS (`"css:..."`) or JS (`"js:..."`) expression to wait for.  
- **`session_id`**: Reuse the same page across calls.  
- **`cache_mode`**: Whether to read/write from the cache or bypass.  
- **`remove_overlay_elements`**: Remove certain popups automatically.  
- **`simulate_user`, `override_navigator`, `magic`**: Anti-bot or “human-like” interactions.

---

## 8. Conclusion

Crawl4AI’s **page interaction** features let you:

1. **Execute JavaScript** for scrolling, clicks, or form filling.  
2. **Wait** for CSS or custom JS conditions before capturing data.  
3. **Handle** multi-step flows (like “Load More”) with partial reloads or persistent sessions.  
4. Combine with **structured extraction** for dynamic sites.

With these tools, you can scrape modern, interactive webpages confidently. For advanced hooking, user simulation, or in-depth config, check the [API reference](../api/parameters.md) or related advanced docs. Happy scripting!