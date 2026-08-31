# Tutorial: Clicking Buttons to Load More Content with Crawl4AI

## Introduction

When scraping dynamic websites, it’s common to encounter “Load More” or “Next” buttons that must be clicked to reveal new content. Crawl4AI provides a straightforward way to handle these situations using JavaScript execution and waiting conditions. In this tutorial, we’ll cover two approaches:

1. **Step-by-step (Session-based) Approach:** Multiple calls to `arun()` to progressively load more content.
2. **Single-call Approach:** Execute a more complex JavaScript snippet inside a single `arun()` call to handle all clicks at once before the extraction.

## Prerequisites

- A working installation of Crawl4AI
- Basic familiarity with Python’s `async`/`await` syntax

## Step-by-Step Approach

Use a session ID to maintain state across multiple `arun()` calls:

```python
from crawl4ai import AsyncWebCrawler, CacheMode

js_code = [
    # This JS finds the “Next” button and clicks it
    "const nextButton = document.querySelector('button.next'); nextButton && nextButton.click();"
]

wait_for_condition = "css:.new-content-class"

async with AsyncWebCrawler(headless=True, verbose=True) as crawler:
    # 1. Load the initial page
    result_initial = await crawler.arun(
        url="https://example.com",
        cache_mode=CacheMode.BYPASS,
        session_id="my_session"
    )

    # 2. Click the 'Next' button and wait for new content
    result_next = await crawler.arun(
        url="https://example.com",
        session_id="my_session",
        js_code=js_code,
        wait_for=wait_for_condition,
        js_only=True,
        cache_mode=CacheMode.BYPASS
    )

# `result_next` now contains the updated HTML after clicking 'Next'
```

**Key Points:**
- **`session_id`**: Keeps the same browser context open.
- **`js_code`**: Executes JavaScript in the context of the already loaded page.
- **`wait_for`**: Ensures the crawler waits until new content is fully loaded.
- **`js_only=True`**: Runs the JS in the current session without reloading the page.

By repeating the `arun()` call multiple times and modifying the `js_code` (e.g., clicking different modules or pages), you can iteratively load all the desired content.

## Single-call Approach

If the page allows it, you can run a single `arun()` call with a more elaborate JavaScript snippet that:
- Iterates over all the modules or "Next" buttons
- Clicks them one by one
- Waits for content updates between each click
- Once done, returns control to Crawl4AI for extraction.

Example snippet:

```python
from crawl4ai import AsyncWebCrawler, CacheMode

js_code = [
    # Example JS that clicks multiple modules:
    """
    (async () => {
      const modules = document.querySelectorAll('.module-item');
      for (let i = 0; i < modules.length; i++) {
        modules[i].scrollIntoView();
        modules[i].click();
        // Wait for each module’s content to load, adjust 100ms as needed
        await new Promise(r => setTimeout(r, 100));
      }
    })();
    """
]

async with AsyncWebCrawler(headless=True, verbose=True) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        js_code=js_code,
        wait_for="css:.final-loaded-content-class",
        cache_mode=CacheMode.BYPASS
    )

# `result` now contains all content after all modules have been clicked in one go.
```

**Key Points:**
- All interactions (clicks and waits) happen before the extraction.
- Ideal for pages where all steps can be done in a single pass.

## Choosing the Right Approach

- **Step-by-Step (Session-based)**: 
  - Good when you need fine-grained control or must dynamically check conditions before clicking the next page.
  - Useful if the page requires multiple conditions checked at runtime.

- **Single-call**:
  - Perfect if the sequence of interactions is known in advance.
  - Cleaner code if the page’s structure is consistent and predictable.

## Conclusion

Crawl4AI makes it easy to handle dynamic content:
- Use session IDs and multiple `arun()` calls for stepwise crawling.
- Or pack all actions into one `arun()` call if the interactions are well-defined upfront.

This flexibility ensures you can handle a wide range of dynamic web pages efficiently.
