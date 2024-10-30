# Crawl4AI

## Episode 5: JavaScript Execution and Dynamic Content Handling

### Quick Intro
Explain JavaScript code injection with examples (e.g., simulating scrolling, clicking ‘load more’). Demo: Extract content from a page that uses dynamic loading with lazy-loaded images.

Here’s a focused outline for the **JavaScript Execution and Dynamic Content Handling** video:

---

### **JavaScript Execution & Dynamic Content Handling**

1) **Why JavaScript Execution Matters**:

   - Many modern websites load content dynamically via JavaScript, requiring special handling to access all elements.
   - Crawl4AI can execute JavaScript on pages, enabling it to interact with elements like “load more” buttons, infinite scrolls, and content that appears only after certain actions.

2) **Basic JavaScript Execution**:

   - Use `js_code` to execute JavaScript commands on a page:
     ```python
     # Scroll to bottom of the page
     result = await crawler.arun(
         url="https://example.com",
         js_code="window.scrollTo(0, document.body.scrollHeight);"
     )
     ```
   - This command scrolls to the bottom, triggering any lazy-loaded or dynamically added content.

3) **Multiple Commands & Simulating Clicks**:

   - Combine multiple JavaScript commands to interact with elements like “load more” buttons:
     ```python
     js_commands = [
         "window.scrollTo(0, document.body.scrollHeight);",
         "document.querySelector('.load-more').click();"
     ]
     result = await crawler.arun(
         url="https://example.com",
         js_code=js_commands
     )
     ```
   - This script scrolls down and then clicks the “load more” button, useful for loading additional content blocks.

4) **Waiting for Dynamic Content**:

   - Use `wait_for` to ensure the page loads specific elements before proceeding:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         js_code="window.scrollTo(0, document.body.scrollHeight);",
         wait_for="css:.dynamic-content"  # Wait for elements with class `.dynamic-content`
     )
     ```
   - This example waits until elements with `.dynamic-content` are loaded, helping to capture content that appears after JavaScript actions.

5) **Handling Complex Dynamic Content (e.g., Infinite Scroll)**:

   - Combine JavaScript execution with conditional waiting to handle infinite scrolls or paginated content:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         js_code=[
             "window.scrollTo(0, document.body.scrollHeight);",
             "const loadMore = document.querySelector('.load-more'); if (loadMore) loadMore.click();"
         ],
         wait_for="js:() => document.querySelectorAll('.item').length > 10"  # Wait until 10 items are loaded
     )
     ```
   - This example scrolls and clicks "load more" repeatedly, waiting each time for a specified number of items to load.

6) **Complete Example: Dynamic Content Handling with Extraction**:

   - Full example demonstrating a dynamic load and content extraction in one process:
     ```python
     async with AsyncWebCrawler() as crawler:
         result = await crawler.arun(
             url="https://example.com",
             js_code=[
                 "window.scrollTo(0, document.body.scrollHeight);",
                 "document.querySelector('.load-more').click();"
             ],
             wait_for="css:.main-content",
             css_selector=".main-content"
         )
         print(result.markdown[:500])  # Output the main content extracted
     ```

7) **Wrap Up & Next Steps**:

   - Recap how JavaScript execution allows access to dynamic content, enabling powerful interactions.
   - Tease the next video: **Content Cleaning and Fit Markdown** to show how Crawl4AI can extract only the most relevant content from complex pages.

---

This outline explains how to handle dynamic content and JavaScript-based interactions effectively, enabling users to scrape and interact with complex, modern websites.