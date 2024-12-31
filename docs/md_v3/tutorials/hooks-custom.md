# Hooks & Custom Code

Crawl4AI supports a **hook** system that lets you run your own Python code at specific points in the crawling pipeline. By injecting logic into these hooks, you can automate tasks like:

- **Authentication** (log in before navigating)  
- **Content manipulation** (modify HTML, inject scripts, etc.)  
- **Session or browser configuration** (e.g., adjusting user agents, local storage)  
- **Custom data collection** (scrape extra details or track state at each stage)

In this tutorial, you’ll learn about:

1. What hooks are available  
2. How to attach code to each hook  
3. Practical examples (auth flows, user agent changes, content manipulation, etc.)

> **Prerequisites**  
> - Familiar with [AsyncWebCrawler Basics](./async-webcrawler-basics.md).  
> - Comfortable with Python async/await.

---

## 1. Overview of Available Hooks

| Hook Name                | Called When / Purpose                                           | Context / Objects Provided                         |
|--------------------------|-----------------------------------------------------------------|-----------------------------------------------------|
| **`on_browser_created`** | Immediately after the browser is launched, but **before** any page or context is created. | **Browser** object only (no `page` yet). Use it for broad browser-level config. |
| **`on_page_context_created`** | Right after a new page context is created. Perfect for setting default timeouts, injecting scripts, etc. | Typically provides `page` and `context`.           |
| **`on_user_agent_updated`** | Whenever the user agent changes. For advanced user agent logic or additional header updates. | Typically provides `page` and updated user agent string. |
| **`on_execution_started`** | Right before your main crawling logic runs (before rendering the page). Good for one-time setup or variable initialization. | Typically provides `page`, possibly `context`.      |
| **`before_goto`**        | Right before navigating to the URL (i.e., `page.goto(...)`). Great for setting cookies, altering the URL, or hooking in authentication steps. | Typically provides `page`, `context`, and `goto_params`. |
| **`after_goto`**         | Immediately after navigation completes, but before scraping. For post-login checks or initial content adjustments. | Typically provides `page`, `context`, `response`.   |
| **`before_retrieve_html`** | Right before retrieving or finalizing the page’s HTML content. Good for in-page manipulation (e.g., removing ads or disclaimers). | Typically provides `page` or final HTML reference.  |
| **`before_return_html`** | Just before the HTML is returned to the crawler pipeline. Last chance to alter or sanitize content. | Typically provides final HTML or a `page`.          |

### A Note on `on_browser_created` (the “unbrowser” hook)
- **No `page`** object is available because no page context exists yet. You can, however, set up browser-wide properties.  
- For example, you might control [CDP sessions][cdp] or advanced browser flags here.

---

## 2. Registering Hooks

You can attach hooks by calling:

```python
crawler.crawler_strategy.set_hook("hook_name", your_hook_function)
```

or by passing a `hooks` dictionary to `AsyncWebCrawler` or your strategy constructor:

```python
hooks = {
    "before_goto": my_before_goto_hook,
    "after_goto": my_after_goto_hook,
    # ... etc.
}
async with AsyncWebCrawler(hooks=hooks) as crawler:
    ...
```

### Hook Signature

Each hook is a function (async or sync, depending on your usage) that receives **certain parameters**—most often `page`, `context`, or custom arguments relevant to that stage. The library then awaits or calls your hook before continuing.

---

## 3. Real-Life Examples

Below are concrete scenarios where hooks come in handy.

---

### 3.1 Authentication Before Navigation

One of the most frequent tasks is logging in or applying authentication **before** the crawler navigates to a URL (so that the user is recognized immediately).

#### Using `before_goto`

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def before_goto_auth_hook(page, context, goto_params, **kwargs):
    """
    Example: Set cookies or localStorage to simulate login.
    This hook runs right before page.goto() is called.
    """
    # Example: Insert cookie-based auth or local storage data
    # (You could also do more complex actions, like fill forms if you already have a 'page' open.)
    print("[HOOK] Setting auth data before goto.")
    await context.add_cookies([
        {
            "name": "session",
            "value": "abcd1234",
            "domain": "example.com",
            "path": "/"
        }
    ])
    # Optionally manipulate goto_params if needed:
    # goto_params["url"] = goto_params["url"] + "?debug=1"

async def main():
    hooks = {
        "before_goto": before_goto_auth_hook
    }

    browser_cfg = BrowserConfig(headless=True)
    crawler_cfg = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_cfg, hooks=hooks) as crawler:
        result = await crawler.arun(url="https://example.com/protected", config=crawler_cfg)
        if result.success:
            print("[OK] Logged in and fetched protected page.")
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**  
- `before_goto` receives `page`, `context`, `goto_params` so you can add cookies, localStorage, or even change the URL itself.  
- If you need to run a real login flow (submitting forms), consider `on_browser_created` or `on_page_context_created` if you want to do it once at the start.

---

### 3.2 Setting Up the Browser in `on_browser_created`

If you need to do advanced browser-level configuration (e.g., hooking into the Chrome DevTools Protocol, adjusting command-line flags, etc.), you’ll use `on_browser_created`. No `page` is available yet, but you can set up the **browser** instance itself.

```python
async def on_browser_created_hook(browser, **kwargs):
    """
    Runs immediately after the browser is created, before any pages.
    'browser' here is a Playwright Browser object.
    """
    print("[HOOK] Browser created. Setting up custom stuff.")
    # Possibly connect to DevTools or create an incognito context
    # Example (pseudo-code):
    # devtools_url = await browser.new_context(devtools=True)

# Usage:
async with AsyncWebCrawler(hooks={"on_browser_created": on_browser_created_hook}) as crawler:
    ...
```

---

### 3.3 Adjusting Page or Context in `on_page_context_created`

If you’d like to set default timeouts or inject scripts right after a page context is spun up:

```python
async def on_page_context_created_hook(page, context, **kwargs):
    print("[HOOK] Page context created. Setting default timeouts or scripts.")
    await page.set_default_timeout(20000)  # 20 seconds
    # Possibly inject a script or set user locale

# Usage:
hooks = {
    "on_page_context_created": on_page_context_created_hook
}
```

---

### 3.4 Dynamically Updating User Agents

`on_user_agent_updated` is fired whenever the strategy updates the user agent. For instance, you might want to set certain cookies or console-log changes for debugging:

```python
async def on_user_agent_updated_hook(page, context, new_ua, **kwargs):
    print(f"[HOOK] User agent updated to {new_ua}")
    # Maybe add a custom header based on new UA
    await context.set_extra_http_headers({"X-UA-Source": new_ua})

hooks = {
    "on_user_agent_updated": on_user_agent_updated_hook
}
```

---

### 3.5 Initializing Stuff with `on_execution_started`

`on_execution_started` runs before your main crawling logic. It’s a good place for short, one-time setup tasks (like clearing old caches, or storing a timestamp).

```python
async def on_execution_started_hook(page, context, **kwargs):
    print("[HOOK] Execution started. Setting a start timestamp or logging.")
    context.set_default_navigation_timeout(45000)  # 45s if your site is slow

hooks = {
    "on_execution_started": on_execution_started_hook
}
```

---

### 3.6 Post-Processing with `after_goto`

After the crawler finishes navigating (i.e., the page has presumably loaded), you can do additional checks or manipulations—like verifying you’re on the right page, or removing interstitials:

```python
async def after_goto_hook(page, context, response, **kwargs):
    """
    Called right after page.goto() finishes, but before the crawler extracts HTML.
    """
    if response and response.ok:
        print("[HOOK] After goto. Status:", response.status)
        # Maybe remove popups or check if we landed on a login failure page.
        await page.evaluate("""() => {
            const popup = document.querySelector(".annoying-popup");
            if (popup) popup.remove();
        }""")
    else:
        print("[HOOK] Navigation might have failed, status not ok or no response.")

hooks = {
    "after_goto": after_goto_hook
}
```

---

### 3.7 Last-Minute Modifications in `before_retrieve_html` or `before_return_html`

Sometimes you need to tweak the page or raw HTML right before it’s captured.

```python
async def before_retrieve_html_hook(page, context, **kwargs):
    """
    Modify the DOM just before the crawler finalizes the HTML.
    """
    print("[HOOK] Removing adverts before capturing HTML.")
    await page.evaluate("""() => {
        const ads = document.querySelectorAll(".ad-banner");
        ads.forEach(ad => ad.remove());
    }""")

async def before_return_html_hook(page, context, html, **kwargs):
    """
    'html' is the near-finished HTML string. Return an updated string if you like.
    """
    # For example, remove personal data or certain tags from the final text
    print("[HOOK] Sanitizing final HTML.")
    sanitized_html = html.replace("PersonalInfo:", "[REDACTED]")
    return sanitized_html

hooks = {
    "before_retrieve_html": before_retrieve_html_hook,
    "before_return_html": before_return_html_hook
}
```

**Note**: If you want to make last-second changes in `before_return_html`, you can manipulate the `html` string directly. Return a new string if you want to override.

---

## 4. Putting It All Together

You can combine multiple hooks in a single run. For instance:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def on_browser_created_hook(browser, **kwargs):
    print("[HOOK] Browser is up, no page yet. Good for broad config.")

async def before_goto_auth_hook(page, context, goto_params, **kwargs):
    print("[HOOK] Adding cookies for auth.")
    await context.add_cookies([{"name": "session", "value": "abcd1234", "domain": "example.com"}])

async def after_goto_log_hook(page, context, response, **kwargs):
    if response:
        print("[HOOK] after_goto: Status code:", response.status)

async def main():
    hooks = {
        "on_browser_created": on_browser_created_hook,
        "before_goto": before_goto_auth_hook,
        "after_goto": after_goto_log_hook
    }

    browser_cfg = BrowserConfig(headless=True)
    crawler_cfg = CrawlerRunConfig(verbose=True)

    async with AsyncWebCrawler(config=browser_cfg, hooks=hooks) as crawler:
        result = await crawler.arun("https://example.com/protected", config=crawler_cfg)
        if result.success:
            print("[OK] Protected page length:", len(result.html))
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

This example:

1. **`on_browser_created`** sets up the brand-new browser instance.  
2. **`before_goto`** ensures you inject an auth cookie before accessing the page.  
3. **`after_goto`** logs the resulting HTTP status code.

---

## 5. Common Pitfalls & Best Practices

1. **Hook Order**: If multiple hooks do overlapping tasks (e.g., two `before_goto` hooks), be mindful of conflicts or repeated logic.  
2. **Async vs Sync**: Some hooks might be used in a synchronous or asynchronous style. Confirm your function signature. If the crawler expects `async`, define `async def`.  
3. **Mutating goto_params**: `goto_params` is a dict that eventually goes to Playwright’s `page.goto()`. Changing the `url` or adding extra fields can be powerful but can also lead to confusion. Document your changes carefully.  
4. **Browser vs Page vs Context**: Not all hooks have both `page` and `context`. For example, `on_browser_created` only has access to **`browser`**.  
5. **Avoid Overdoing It**: Hooks are powerful but can lead to complexity. If you find yourself writing massive code inside a hook, consider if a separate “how-to” function with a simpler approach might suffice.

---

## Conclusion & Next Steps

**Hooks** let you bend Crawl4AI to your will:

- **Authentication** (cookies, localStorage) with `before_goto`  
- **Browser-level config** with `on_browser_created`  
- **Page or context config** with `on_page_context_created`  
- **Content modifications** before capturing HTML (`before_retrieve_html` or `before_return_html`)  

**Where to go next**:

- **[Identity-Based Crawling & Anti-Bot](./identity-anti-bot.md)**: Combine hooks with advanced user simulation to avoid bot detection.  
- **[Reference → AsyncPlaywrightCrawlerStrategy](../../reference/browser-strategies.md)**: Learn more about how hooks are implemented under the hood.  
- **[How-To Guides](../../how-to/)**: Check short, specific recipes for tasks like scraping multiple pages with repeated “Load More” clicks.

With the hook system, you have near-complete control over the browser’s lifecycle—whether it’s setting up environment variables, customizing user agents, or manipulating the HTML. Enjoy the freedom to create sophisticated, fully customized crawling pipelines!

**Last Updated**: 2024-XX-XX
