# Crawl4AI

## Episode 14: Hooks and Custom Workflow with AsyncWebCrawler

### Quick Intro
Cover hooks (`on_browser_created`, `before_goto`, `after_goto`) to add custom workflows. Demo: Use hooks to add custom cookies or headers, log HTML, or trigger specific events on page load.

Here’s a detailed outline for the **Hooks and Custom Workflow with AsyncWebCrawler** video, covering each hook’s purpose, usage, and example implementations.

---

### **13. Hooks and Custom Workflow with AsyncWebCrawler**

#### **1. Introduction to Hooks in Crawl4AI**
   - **What are Hooks**: Hooks are customizable entry points in the crawling process that allow users to inject custom actions or logic at specific stages.
   - **Why Use Hooks**:
     - They enable fine-grained control over the crawling workflow.
     - Useful for performing additional tasks (e.g., logging, modifying headers) dynamically during the crawl.
     - Hooks provide the flexibility to adapt the crawler to complex site structures or unique project needs.

#### **2. Overview of Available Hooks**
   - Crawl4AI offers seven key hooks to modify and control different stages in the crawling lifecycle:
     - `on_browser_created`
     - `on_user_agent_updated`
     - `on_execution_started`
     - `before_goto`
     - `after_goto`
     - `before_return_html`
     - `before_retrieve_html`

#### **3. Hook-by-Hook Explanation and Examples**

---

##### **Hook 1: `on_browser_created`**
   - **Purpose**: Triggered right after the browser instance is created.
   - **Use Case**:
     - Initializing browser-specific settings or performing setup actions.
     - Configuring browser extensions or scripts before any page is opened.
   - **Example**:
     ```python
     async def log_browser_creation(browser):
         print("Browser instance created:", browser)
     
     crawler.crawler_strategy.set_hook('on_browser_created', log_browser_creation)
     ```
   - **Explanation**: This hook logs the browser creation event, useful for tracking when a new browser instance starts.

---

##### **Hook 2: `on_user_agent_updated`**
   - **Purpose**: Called whenever the user agent string is updated.
   - **Use Case**:
     - Modifying the user agent based on page requirements, e.g., changing to a mobile user agent for mobile-only pages.
   - **Example**:
     ```python
     def update_user_agent(user_agent):
         print(f"User Agent Updated: {user_agent}")
     
     crawler.crawler_strategy.set_hook('on_user_agent_updated', update_user_agent)
     crawler.update_user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)")
     ```
   - **Explanation**: This hook provides a callback every time the user agent changes, helpful for debugging or dynamically altering user agent settings based on conditions.

---

##### **Hook 3: `on_execution_started`**
   - **Purpose**: Called right before the crawler begins any interaction (e.g., JavaScript execution, clicks).
   - **Use Case**:
     - Performing setup actions, such as inserting cookies or initiating custom scripts.
   - **Example**:
     ```python
     async def log_execution_start(page):
         print("Execution started on page:", page.url)
     
     crawler.crawler_strategy.set_hook('on_execution_started', log_execution_start)
     ```
   - **Explanation**: Logs the start of any major interaction on the page, ideal for cases where you want to monitor each interaction.

---

##### **Hook 4: `before_goto`**
   - **Purpose**: Triggered before navigating to a new URL with `page.goto()`.
   - **Use Case**:
     - Modifying request headers or setting up conditions right before the page loads.
     - Adding headers or dynamically adjusting options for specific URLs.
   - **Example**:
     ```python
     async def modify_headers_before_goto(page):
         await page.set_extra_http_headers({"X-Custom-Header": "CustomValue"})
         print("Custom headers set before navigation")
     
     crawler.crawler_strategy.set_hook('before_goto', modify_headers_before_goto)
     ```
   - **Explanation**: This hook allows injecting headers or altering settings based on the page’s needs, particularly useful for pages with custom requirements.

---

##### **Hook 5: `after_goto`**
   - **Purpose**: Executed immediately after a page has loaded (after `page.goto()`).
   - **Use Case**:
     - Checking the loaded page state, modifying the DOM, or performing post-navigation actions (e.g., scrolling).
   - **Example**:
     ```python
     async def post_navigation_scroll(page):
         await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
         print("Scrolled to the bottom after navigation")
     
     crawler.crawler_strategy.set_hook('after_goto', post_navigation_scroll)
     ```
   - **Explanation**: This hook scrolls to the bottom of the page after loading, which can help load dynamically added content like infinite scroll elements.

---

##### **Hook 6: `before_return_html`**
   - **Purpose**: Called right before HTML content is retrieved and returned.
   - **Use Case**:
     - Removing overlays or cleaning up the page for a cleaner HTML extraction.
   - **Example**:
     ```python
     async def remove_advertisements(page, html):
         await page.evaluate("document.querySelectorAll('.ad-banner').forEach(el => el.remove());")
         print("Advertisements removed before returning HTML")
     
     crawler.crawler_strategy.set_hook('before_return_html', remove_advertisements)
     ```
   - **Explanation**: The hook removes ad banners from the HTML before it’s retrieved, ensuring a cleaner data extraction.

---

##### **Hook 7: `before_retrieve_html`**
   - **Purpose**: Runs right before Crawl4AI initiates HTML retrieval.
   - **Use Case**:
     - Finalizing any page adjustments (e.g., setting timers, waiting for specific elements).
   - **Example**:
     ```python
     async def wait_for_content_before_retrieve(page):
         await page.wait_for_selector('.main-content')
         print("Main content loaded, ready to retrieve HTML")
     
     crawler.crawler_strategy.set_hook('before_retrieve_html', wait_for_content_before_retrieve)
     ```
   - **Explanation**: This hook waits for the main content to load before retrieving the HTML, ensuring that all essential content is captured.

#### **4. Setting Hooks in Crawl4AI**
   - **How to Set Hooks**:
     - Use `set_hook` to define a custom function for each hook.
     - Each hook function can be asynchronous (useful for actions like waiting or retrieving async data).
   - **Example Setup**:
     ```python
     crawler.crawler_strategy.set_hook('on_browser_created', log_browser_creation)
     crawler.crawler_strategy.set_hook('before_goto', modify_headers_before_goto)
     crawler.crawler_strategy.set_hook('after_goto', post_navigation_scroll)
     ```

#### **5. Complete Example: Using Hooks for a Customized Crawl Workflow**
   - **Goal**: Log each key step, set custom headers before navigation, and clean up the page before retrieving HTML.
   - **Example Code**:
     ```python
     async def custom_crawl():
         async with AsyncWebCrawler() as crawler:
             # Set hooks for custom workflow
             crawler.crawler_strategy.set_hook('on_browser_created', log_browser_creation)
             crawler.crawler_strategy.set_hook('before_goto', modify_headers_before_goto)
             crawler.crawler_strategy.set_hook('after_goto', post_navigation_scroll)
             crawler.crawler_strategy.set_hook('before_return_html', remove_advertisements)
             
             # Perform the crawl
             url = "https://example.com"
             result = await crawler.arun(url=url)
             print(result.html)  # Display or process HTML
     ```

#### **6. Benefits of Using Hooks in Custom Crawling Workflows**
   - **Enhanced Control**: Hooks offer precise control over each stage, allowing adjustments based on content and structure.
   - **Efficient Modifications**: Avoid reloading or restarting the session; hooks can alter actions dynamically.
   - **Context-Sensitive Actions**: Hooks enable custom logic tailored to specific pages or sections, maximizing extraction quality.

#### **7. Wrap Up & Next Steps**
   - Recap how hooks empower customized workflows in Crawl4AI, enabling flexibility at every stage.
   - Tease the next video: **Automating Post-Processing with Crawl4AI**, covering automated steps after data extraction.

---

This outline provides a thorough understanding of hooks, their practical applications, and examples for customizing the crawling workflow in Crawl4AI.