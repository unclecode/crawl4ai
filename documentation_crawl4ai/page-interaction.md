[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/core/page-interaction/)


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
    * Page Interaction
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
  * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/#page-interaction)
  * [1. JavaScript Execution](https://docs.crawl4ai.com/core/page-interaction/#1-javascript-execution)
  * [2. Wait Conditions](https://docs.crawl4ai.com/core/page-interaction/#2-wait-conditions)
  * [3. Handling Dynamic Content](https://docs.crawl4ai.com/core/page-interaction/#3-handling-dynamic-content)
  * [4. Timing Control](https://docs.crawl4ai.com/core/page-interaction/#4-timing-control)
  * [5. Multi-Step Interaction Example](https://docs.crawl4ai.com/core/page-interaction/#5-multi-step-interaction-example)
  * [6. Combine Interaction with Extraction](https://docs.crawl4ai.com/core/page-interaction/#6-combine-interaction-with-extraction)
  * [7. Relevant CrawlerRunConfig Parameters](https://docs.crawl4ai.com/core/page-interaction/#7-relevant-crawlerrunconfig-parameters)
  * [8. Conclusion](https://docs.crawl4ai.com/core/page-interaction/#8-conclusion)
  * [9. Virtual Scrolling](https://docs.crawl4ai.com/core/page-interaction/#9-virtual-scrolling)


# Page Interaction
Crawl4AI provides powerful features for interacting with **dynamic** webpages, handling JavaScript execution, waiting for conditions, and managing multi-step flows. By combining **js_code** , **wait_for** , and certain **CrawlerRunConfig** parameters, you can:
  1. Click “Load More” buttons
  2. Fill forms and submit them
  3. Wait for elements or data to appear
  4. Reuse sessions across multiple steps


Below is a quick overview of how to do it.
* * *
## 1. JavaScript Execution
### Basic Execution
**`js_code`**in**`CrawlerRunConfig`**accepts either a single JS string or a list of JS snippets.
**Example** : We’ll scroll to the bottom of the page, then optionally click a “Load More” button.
```
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
Copy
```

**Relevant`CrawlerRunConfig` params**: - **`js_code`**: A string or list of strings with JavaScript to run after the page loads. -**`js_only`**: If set to`True` on subsequent calls, indicates we’re continuing an existing session without a new full navigation.
- **`session_id`**: If you want to keep the same page across multiple calls, specify an ID.
* * *
## 2. Wait Conditions
### 2.1 CSS-Based Waiting
Sometimes, you just want to wait for a specific element to appear. For example:
```
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
Copy
```

**Key param** : - **`wait_for="css:..."`**: Tells the crawler to wait until that CSS selector is present.
### 2.2 JavaScript-Based Waiting
For more complex conditions (e.g., waiting for content length to exceed a threshold), prefix `js:`:
```
wait_condition = """() => {
    const items = document.querySelectorAll('.athing');
    return items.length > 50;  // Wait for at least 51 items
}"""

config = CrawlerRunConfig(wait_for=f"js:{wait_condition}")
Copy
```

**Behind the Scenes** : Crawl4AI keeps polling the JS function until it returns `true` or a timeout occurs.
* * *
## 3. Handling Dynamic Content
Many modern sites require **multiple steps** : scrolling, clicking “Load More,” or updating via JavaScript. Below are typical patterns.
### 3.1 Load More Example (Hacker News “More” Link)
```
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
Copy
```

**Key params** : - **`session_id="hn_session"`**: Keep the same page across multiple calls to`arun()`. - **`js_only=True`**: We’re not performing a full reload, just applying JS in the existing page. -**`wait_for`**with`js:` : Wait for item count to grow beyond 30.
* * *
### 3.2 Form Interaction
If the site has a search or login form, you can fill fields and submit them with **`js_code`**. For instance, if GitHub had a local search form:
```
js_form_interaction = """
document.querySelector('#your-search').value = 'TypeScript commits';
document.querySelector('form').submit();
"""

config = CrawlerRunConfig(
    js_code=js_form_interaction,
    wait_for="css:.commit"
)
result = await crawler.arun(url="https://github.com/search", config=config)
Copy
```

**In reality** : Replace IDs or classes with the real site’s form selectors.
* * *
## 4. Timing Control
1. **`page_timeout`**(ms): Overall page load or script execution time limit.
2. **`delay_before_return_html`**(seconds): Wait an extra moment before capturing the final HTML.
3. **`mean_delay`** & **`max_range`**: If you call`arun_many()` with multiple URLs, these add a random pause between each request.
**Example** :
```
config = CrawlerRunConfig(
    page_timeout=60000,  # 60s limit
    delay_before_return_html=2.5
)
Copy
```

* * *
## 5. Multi-Step Interaction Example
Below is a simplified script that does multiple “Load More” clicks on GitHub’s TypeScript commits page. It **re-uses** the same session to accumulate new commits each time. The code includes the relevant **`CrawlerRunConfig`**parameters you’d rely on.
```
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
Copy
```

**Key Points** :
  * **`session_id`**: Keep the same page open.
  * **`js_code`**+**`wait_for`**+**`js_only=True`**: We do partial refreshes, waiting for new commits to appear.
  * **`cache_mode=CacheMode.BYPASS`**ensures we always see fresh data each step.


* * *
## 6. Combine Interaction with Extraction
Once dynamic content is loaded, you can attach an **`extraction_strategy`**(like`JsonCssExtractionStrategy` or `LLMExtractionStrategy`). For example:
```
from crawl4ai import JsonCssExtractionStrategy

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
Copy
```

When done, check `result.extracted_content` for the JSON.
* * *
## 7. Relevant `CrawlerRunConfig` Parameters
Below are the key interaction-related parameters in `CrawlerRunConfig`. For a full list, see [Configuration Parameters](https://docs.crawl4ai.com/api/parameters/).
  * **`js_code`**: JavaScript to run after initial load.
  * **`js_only`**: If`True` , no new page navigation—only JS in the existing session.
  * **`wait_for`**: CSS (`"css:..."`) or JS (`"js:..."`) expression to wait for.
  * **`session_id`**: Reuse the same page across calls.
  * **`cache_mode`**: Whether to read/write from the cache or bypass.
  * **`remove_overlay_elements`**: Remove certain popups automatically.
  * **`simulate_user`,`override_navigator` , `magic`**: Anti-bot or “human-like” interactions.


* * *
## 8. Conclusion
Crawl4AI’s **page interaction** features let you:
1. **Execute JavaScript** for scrolling, clicks, or form filling.
2. **Wait** for CSS or custom JS conditions before capturing data.
3. **Handle** multi-step flows (like “Load More”) with partial reloads or persistent sessions.
4. Combine with **structured extraction** for dynamic sites.
With these tools, you can scrape modern, interactive webpages confidently. For advanced hooking, user simulation, or in-depth config, check the [API reference](https://docs.crawl4ai.com/api/parameters/) or related advanced docs. Happy scripting!
* * *
## 9. Virtual Scrolling
For sites that use **virtual scrolling** (where content is replaced rather than appended as you scroll, like Twitter or Instagram), Crawl4AI provides a dedicated `VirtualScrollConfig`:
```
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, VirtualScrollConfig

async def crawl_twitter_timeline():
    # Configure virtual scroll for Twitter-like feeds
    virtual_config = VirtualScrollConfig(
        container_selector="[data-testid='primaryColumn']",  # Twitter's main column
        scroll_count=30,                # Scroll 30 times
        scroll_by="container_height",   # Scroll by container height each time
        wait_after_scroll=1.0          # Wait 1 second after each scroll
    )

    config = CrawlerRunConfig(
        virtual_scroll_config=virtual_config
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://twitter.com/search?q=AI",
            config=config
        )
        # result.html now contains ALL tweets from the virtual scroll
Copy
```

### Virtual Scroll vs JavaScript Scrolling
Feature | Virtual Scroll | JS Code Scrolling
---|---|---
**Use Case** | Content replaced during scroll | Content appended or simple scroll
**Configuration** |  `VirtualScrollConfig` object |  `js_code` with scroll commands
**Automatic Merging** | Yes - merges all unique content | No - captures final state only
**Best For** | Twitter, Instagram, virtual tables | Traditional pages, load more buttons
For detailed examples and configuration options, see the [Virtual Scroll documentation](https://docs.crawl4ai.com/advanced/virtual-scroll/).
#### On this page
  * [1. JavaScript Execution](https://docs.crawl4ai.com/core/page-interaction/#1-javascript-execution)
  * [Basic Execution](https://docs.crawl4ai.com/core/page-interaction/#basic-execution)
  * [2. Wait Conditions](https://docs.crawl4ai.com/core/page-interaction/#2-wait-conditions)
  * [2.1 CSS-Based Waiting](https://docs.crawl4ai.com/core/page-interaction/#21-css-based-waiting)
  * [2.2 JavaScript-Based Waiting](https://docs.crawl4ai.com/core/page-interaction/#22-javascript-based-waiting)
  * [3. Handling Dynamic Content](https://docs.crawl4ai.com/core/page-interaction/#3-handling-dynamic-content)
  * [3.1 Load More Example (Hacker News “More” Link)](https://docs.crawl4ai.com/core/page-interaction/#31-load-more-example-hacker-news-more-link)
  * [3.2 Form Interaction](https://docs.crawl4ai.com/core/page-interaction/#32-form-interaction)
  * [4. Timing Control](https://docs.crawl4ai.com/core/page-interaction/#4-timing-control)
  * [5. Multi-Step Interaction Example](https://docs.crawl4ai.com/core/page-interaction/#5-multi-step-interaction-example)
  * [6. Combine Interaction with Extraction](https://docs.crawl4ai.com/core/page-interaction/#6-combine-interaction-with-extraction)
  * [7. Relevant CrawlerRunConfig Parameters](https://docs.crawl4ai.com/core/page-interaction/#7-relevant-crawlerrunconfig-parameters)
  * [8. Conclusion](https://docs.crawl4ai.com/core/page-interaction/#8-conclusion)
  * [9. Virtual Scrolling](https://docs.crawl4ai.com/core/page-interaction/#9-virtual-scrolling)
  * [Virtual Scroll vs JavaScript Scrolling](https://docs.crawl4ai.com/core/page-interaction/#virtual-scroll-vs-javascript-scrolling)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")
