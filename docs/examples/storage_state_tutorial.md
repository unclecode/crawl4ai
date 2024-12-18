### Using `storage_state` to Pre-Load Cookies and LocalStorage

Crawl4ai’s `AsyncWebCrawler` lets you preserve and reuse session data, including cookies and localStorage, across multiple runs. By providing a `storage_state`, you can start your crawls already “logged in” or with any other necessary session data—no need to repeat the login flow every time.

#### What is `storage_state`?

`storage_state` can be:

- A dictionary containing cookies and localStorage data.
- A path to a JSON file that holds this information.

When you pass `storage_state` to the crawler, it applies these cookies and localStorage entries before loading any pages. This means your crawler effectively starts in a known authenticated or pre-configured state.

#### Example Structure

Here’s an example storage state:

```json
{
  "cookies": [
    {
      "name": "session",
      "value": "abcd1234",
      "domain": "example.com",
      "path": "/",
      "expires": 1675363572.037711,
      "httpOnly": false,
      "secure": false,
      "sameSite": "None"
    }
  ],
  "origins": [
    {
      "origin": "https://example.com",
      "localStorage": [
        { "name": "token", "value": "my_auth_token" },
        { "name": "refreshToken", "value": "my_refresh_token" }
      ]
    }
  ]
}
```

This JSON sets a `session` cookie and two localStorage entries (`token` and `refreshToken`) for `https://example.com`.

---

### Passing `storage_state` as a Dictionary

You can directly provide the data as a dictionary:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    storage_dict = {
        "cookies": [
            {
                "name": "session",
                "value": "abcd1234",
                "domain": "example.com",
                "path": "/",
                "expires": 1675363572.037711,
                "httpOnly": False,
                "secure": False,
                "sameSite": "None"
            }
        ],
        "origins": [
            {
                "origin": "https://example.com",
                "localStorage": [
                    {"name": "token", "value": "my_auth_token"},
                    {"name": "refreshToken", "value": "my_refresh_token"}
                ]
            }
        ]
    }

    async with AsyncWebCrawler(
        headless=True,
        storage_state=storage_dict
    ) as crawler:
        result = await crawler.arun(url='https://example.com/protected')
        if result.success:
            print("Crawl succeeded with pre-loaded session data!")
            print("Page HTML length:", len(result.html))

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Passing `storage_state` as a File

If you prefer a file-based approach, save the JSON above to `mystate.json` and reference it:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(
        headless=True,
        storage_state="mystate.json"  # Uses a JSON file instead of a dictionary
    ) as crawler:
        result = await crawler.arun(url='https://example.com/protected')
        if result.success:
            print("Crawl succeeded with pre-loaded session data!")
            print("Page HTML length:", len(result.html))

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Using `storage_state` to Avoid Repeated Logins (Sign In Once, Use Later)

A common scenario is when you need to log in to a site (entering username/password, etc.) to access protected pages. Doing so every crawl is cumbersome. Instead, you can:

1. Perform the login once in a hook.
2. After login completes, export the resulting `storage_state` to a file.
3. On subsequent runs, provide that `storage_state` to skip the login step.

**Step-by-Step Example:**

**First Run (Perform Login and Save State):**

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def on_browser_created_hook(browser):
    # Access the default context and create a page
    context = browser.contexts[0]
    page = await context.new_page()
    
    # Navigate to the login page
    await page.goto("https://example.com/login", wait_until="domcontentloaded")
    
    # Fill in credentials and submit
    await page.fill("input[name='username']", "myuser")
    await page.fill("input[name='password']", "mypassword")
    await page.click("button[type='submit']")
    await page.wait_for_load_state("networkidle")
    
    # Now the site sets tokens in localStorage and cookies
    # Export this state to a file so we can reuse it
    await context.storage_state(path="my_storage_state.json")
    await page.close()

async def main():
    # First run: perform login and export the storage_state
    async with AsyncWebCrawler(
        headless=True,
        verbose=True,
        hooks={"on_browser_created": on_browser_created_hook},
        use_persistent_context=True,
        user_data_dir="./my_user_data"
    ) as crawler:
        
        # After on_browser_created_hook runs, we have storage_state saved to my_storage_state.json
        result = await crawler.arun(
            url='https://example.com/protected-page',
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("First run result success:", result.success)
        if result.success:
            print("Protected page HTML length:", len(result.html))

if __name__ == "__main__":
    asyncio.run(main())
```

**Second Run (Reuse Saved State, No Login Needed):**

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    # Second run: no need to hook on_browser_created this time.
    # Just provide the previously saved storage state.
    async with AsyncWebCrawler(
        headless=True,
        verbose=True,
        use_persistent_context=True,
        user_data_dir="./my_user_data",
        storage_state="my_storage_state.json"  # Reuse previously exported state
    ) as crawler:
        
        # Now the crawler starts already logged in
        result = await crawler.arun(
            url='https://example.com/protected-page',
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True}),
        )
        print("Second run result success:", result.success)
        if result.success:
            print("Protected page HTML length:", len(result.html))

if __name__ == "__main__":
    asyncio.run(main())
```

**What’s Happening Here?**

- During the first run, the `on_browser_created_hook` logs into the site.  
- After logging in, the crawler exports the current session (cookies, localStorage, etc.) to `my_storage_state.json`.  
- On subsequent runs, passing `storage_state="my_storage_state.json"` starts the browser context with these tokens already in place, skipping the login steps.

**Sign Out Scenario:**  
If the website allows you to sign out by clearing tokens or by navigating to a sign-out URL, you can also run a script that uses `on_browser_created_hook` or `arun` to simulate signing out, then export the resulting `storage_state` again. That would give you a baseline “logged out” state to start fresh from next time.

---

### Conclusion

By using `storage_state`, you can skip repetitive actions, like logging in, and jump straight into crawling protected content. Whether you provide a file path or a dictionary, this powerful feature helps maintain state between crawls, simplifying your data extraction pipelines.