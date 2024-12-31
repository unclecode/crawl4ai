Below is a **draft** of a follow-up tutorial, **“Smart Crawling Techniques,”** building on the **“AsyncWebCrawler Basics”** tutorial. This tutorial focuses on three main points:

1. **Advanced usage of CSS selectors** (e.g., partial extraction, exclusions)
2. **Handling iframes** (if relevant for your workflow)
3. **Waiting for dynamic content** using `wait_for`, including the new `css:` and `js:` prefixes

Feel free to adjust code snippets, wording, or emphasis to match your library updates or user feedback.

---

# Smart Crawling Techniques

In the previous tutorial ([AsyncWebCrawler Basics](./async-webcrawler-basics.md)), you learned how to create an `AsyncWebCrawler` instance, run a basic crawl, and inspect the `CrawlResult`. Now it’s time to explore some of the **targeted crawling** features that let you:

1. Select specific parts of a webpage using CSS selectors  
2. Exclude or ignore certain page elements  
3. Wait for dynamic content to load using `wait_for` (with `css:` or `js:` rules)  
4. (Optionally) Handle iframes if your target site embeds additional content

> **Prerequisites**  
> - You’ve read or completed [AsyncWebCrawler Basics](./async-webcrawler-basics.md).  
> - You have a working environment for Crawl4AI (Playwright installed, etc.).

---

## 1. Targeting Specific Elements with CSS Selectors

### 1.1 Simple CSS Selector Usage

Let’s say you only need to crawl the main article content of a news page. By setting `css_selector` in `CrawlerRunConfig`, your final HTML or Markdown output focuses on that region. For example:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    browser_cfg = BrowserConfig(headless=True)
    crawler_cfg = CrawlerRunConfig(
        css_selector=".article-body",  # Only capture .article-body content
        excluded_tags=["nav", "footer"]  # Optional: skip big nav & footer sections
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://news.example.com/story/12345",
            config=crawler_cfg
        )
        if result.success:
            print("[OK] Extracted content length:", len(result.html))
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Parameters**:
- **`css_selector`**: Tells the crawler to focus on `.article-body`.  
- **`excluded_tags`**: Tells the crawler to skip specific HTML tags altogether (e.g., `nav` or `footer`).  

**Tip**: For extremely noisy pages, you can further refine how you exclude certain elements by using `excluded_selector`, which takes a CSS selector you want removed from the final output.

### 1.2 Excluding Content with `excluded_selector`

If you want to remove certain sections within `.article-body` (like “related stories” sidebars), set:

```python
CrawlerRunConfig(
    css_selector=".article-body",
    excluded_selector=".related-stories, .ads-banner"
)
```

This combination grabs the main article content while filtering out sidebars or ads.

---

## 2. Handling Iframes

Some sites embed extra content via `<iframe>` elements—for example, embedded videos or external forms. If you want the crawler to traverse these iframes and merge their content into the final HTML or Markdown, set:

```python
crawler_cfg = CrawlerRunConfig(
    process_iframes=True
)
```

- **`process_iframes=True`**: Tells the crawler (specifically the underlying Playwright strategy) to recursively fetch iframe content and integrate it into `result.html` and `result.markdown`.

**Warning**: Not all sites allow iframes to be crawled (some cross-origin policies might block it). If you see partial or missing data, check the domain policy or logs for warnings.

---

## 3. Waiting for Dynamic Content

Many modern sites load content dynamically (e.g., after user interaction or asynchronously). Crawl4AI helps you wait for specific conditions before capturing the final HTML. Let’s look at `wait_for`.

### 3.1 `wait_for` Basics

In `CrawlerRunConfig`, `wait_for` can be a simple CSS selector or a JavaScript condition. Under the hood, Crawl4AI uses `smart_wait` to interpret what you provide.

```python
crawler_cfg = CrawlerRunConfig(
    wait_for="css:.main-article-loaded",
    page_timeout=30000
)
```

**Example**: `css:.main-article-loaded` means “Wait for an element with the class `.main-article-loaded` to appear in the DOM.” If it doesn’t appear within `30` seconds, you’ll get a timeout.

### 3.2 Using Explicit Prefixes

**`js:`** and **`css:`** can explicitly tell the crawler which approach to use:

- **`wait_for="css:.comments-section"`** → Wait for `.comments-section` to appear  
- **`wait_for="js:() => document.querySelectorAll('.comments').length > 5"`** → Wait until there are at least 6 comment elements  

**Code Example**:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        wait_for="js:() => document.querySelectorAll('.dynamic-items li').length >= 10",
        page_timeout=20000  # 20s
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/async-list",
            config=config
        )
        if result.success:
            print("[OK] Dynamic items loaded. HTML length:", len(result.html))
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

### 3.3 Fallback Logic

If you **don’t** prefix `js:` or `css:`, Crawl4AI tries to detect whether your string looks like a CSS selector or a JavaScript snippet. It’ll first attempt a CSS selector. If that fails, it tries to evaluate it as a JavaScript function. This can be convenient but can also lead to confusion if the library guesses incorrectly. It’s often best to be explicit:

- **`"css:.my-selector"`** → Force CSS  
- **`"js:() => myAppState.isReady()"`** → Force JavaScript

**What Should My JavaScript Return?**  
- A function that returns `true` once the condition is met (or `false` if it fails).  
- The function can be sync or async, but note that the crawler wraps it in an async loop to poll until `true` or timeout.

---

## 4. Example: Targeted Crawl with Iframes & Wait-For

Below is a more advanced snippet combining these features:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    browser_cfg = BrowserConfig(headless=True)
    crawler_cfg = CrawlerRunConfig(
        css_selector=".main-content",
        process_iframes=True,
        wait_for="css:.loaded-indicator",   # Wait for .loaded-indicator to appear
        excluded_tags=["script", "style"],  # Remove script/style tags
        page_timeout=30000,
        verbose=True
    )
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://example.com/iframe-heavy",
            config=crawler_cfg
        )
        if result.success:
            print("[OK] Crawled with iframes. Length of final HTML:", len(result.html))
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**What’s Happening**:
1. **`css_selector=".main-content"`** → Focus only on `.main-content` for final extraction.  
2. **`process_iframes=True`** → Recursively handle `<iframe>` content.  
3. **`wait_for="css:.loaded-indicator"`** → Don’t extract until the page shows `.loaded-indicator`.  
4. **`excluded_tags=["script", "style"]`** → Remove script and style tags for a cleaner result.

---

## 5. Common Pitfalls & Tips

1. **Be Explicit**: Using `"js:"` or `"css:"` can spare you headaches if the library guesses incorrectly.  
2. **Timeouts**: If the site never triggers your wait condition, a `TimeoutError` can occur. Check your logs or use `verbose=True` for more clues.  
3. **Infinite Scroll**: If you have repeated “load more” loops, you might use [Hooks & Custom Code](./hooks-custom.md) or add your own JavaScript for repeated scrolling.  
4. **Iframes**: Some iframes are cross-origin or protected. In those cases, you might not be able to read their content. Check your logs for permission errors.  

---

## 6. Summary & Next Steps

With these **Targeted Crawling Techniques** you can:

- Precisely target or exclude content using CSS selectors.  
- Automatically wait for dynamic elements to load using `wait_for`.  
- Merge iframe content into your main page result.  

### Where to Go Next?

- **[Link & Media Analysis](./link-media-analysis.md)**: Dive deeper into analyzing extracted links and media items.  
- **[Hooks & Custom Code](./hooks-custom.md)**: Learn how to implement repeated actions like infinite scroll or login sequences using hooks.  
- **Reference**: For an exhaustive list of parameters and advanced usage, see [CrawlerRunConfig Reference](../../reference/configuration.md).  

If you run into issues or want to see real examples from other users, check the [How-To Guides](../../how-to/) or raise a question on GitHub.

**Last updated**: 2024-XX-XX

---

That’s it for **Targeted Crawling Techniques**! You’re now equipped to handle complex pages that rely on dynamic loading, custom CSS selectors, and iframe embedding.  