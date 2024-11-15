# Crawl4AI

## Episode 1: Introduction to Crawl4AI and Basic Installation

### Quick Intro
Walk through installation from PyPI, setup, and verification. Show how to install with options like `torch` or `transformer` for advanced capabilities.

Here's a condensed outline of the **Installation and Setup** video content:

---

1) **Introduction to Crawl4AI**:

   - Briefly explain that Crawl4AI is a powerful tool for web scraping, data extraction, and content processing, with customizable options for various needs.

2) **Installation Overview**:

   - **Basic Install**: Run `pip install crawl4ai` and `playwright install` (to set up browser dependencies).
   - **Optional Advanced Installs**:
     - `pip install crawl4ai[torch]` - Adds PyTorch for clustering.
     - `pip install crawl4ai[transformer]` - Adds support for LLM-based extraction.
     - `pip install crawl4ai[all]` - Installs all features for complete functionality.

3) **Verifying the Installation**:

   - Walk through a simple test script to confirm the setup:
      ```python
      import asyncio
      from crawl4ai import AsyncWebCrawler
      
      async def main():
          async with AsyncWebCrawler(verbose=True) as crawler:
              result = await crawler.arun(url="https://www.example.com")
              print(result.markdown[:500])  # Show first 500 characters

      asyncio.run(main())
      ```
   - Explain that this script initializes the crawler and runs it on a test URL, displaying part of the extracted content to verify functionality.

4) **Important Tips**:

   - **Run** `playwright install` **after installation** to set up dependencies.
   - **For full performance** on text-related tasks, run `crawl4ai-download-models` after installing with `[torch]`, `[transformer]`, or `[all]` options.
   - If you encounter issues, refer to the documentation or GitHub issues.

5) **Wrap Up**:

   - Introduce the next topic in the series, which will cover Crawl4AI's browser configuration options (like choosing between `chromium`, `firefox`, and `webkit`).

---

This structure provides a concise, effective guide to get viewers up and running with Crawl4AI in minutes.# Crawl4AI

## Episode 2: Overview of Advanced Features

### Quick Intro
A general overview of advanced features like hooks, CSS selectors, and JSON CSS extraction.

Here's a condensed outline for an **Overview of Advanced Features** video covering Crawl4AI's powerful customization and extraction options:

---

### **Overview of Advanced Features**

1) **Introduction to Advanced Features**:

   - Briefly introduce Crawl4AI’s advanced tools, which let users go beyond basic crawling to customize and fine-tune their scraping workflows.

2) **Taking Screenshots**:

   - Explain the screenshot capability for capturing page state and verifying content.
   - **Example**:
      ```python
      result = await crawler.arun(url="https://www.example.com", screenshot=True)
      ```
   - Mention that screenshots are saved as a base64 string in `result`, allowing easy decoding and saving.

3) **Media and Link Extraction**:

   - Demonstrate how to pull all media (images, videos) and links (internal and external) from a page for deeper analysis or content gathering.
   - **Example**:
      ```python
      result = await crawler.arun(url="https://www.example.com")
      print("Media:", result.media)
      print("Links:", result.links)
      ```

4) **Custom User Agent**:

   - Show how to set a custom user agent to disguise the crawler or simulate specific devices/browsers.
   - **Example**:
      ```python
      result = await crawler.arun(url="https://www.example.com", user_agent="Mozilla/5.0 (compatible; MyCrawler/1.0)")
      ```

5) **Custom Hooks for Enhanced Control**:

   - Briefly cover how to use hooks, which allow custom actions like setting headers or handling login during the crawl.
   - **Example**: Setting a custom header with `before_get_url` hook.
      ```python
      async def before_get_url(page):
          await page.set_extra_http_headers({"X-Test-Header": "test"})
      ```

6) **CSS Selectors for Targeted Extraction**:

   - Explain the use of CSS selectors to extract specific elements, ideal for structured data like articles or product details.
   - **Example**:
      ```python
      result = await crawler.arun(url="https://www.example.com", css_selector="h2")
      print("H2 Tags:", result.extracted_content)
      ```

7) **Crawling Inside Iframes**:

   - Mention how enabling `process_iframes=True` allows extracting content within iframes, useful for sites with embedded content or ads.
   - **Example**:
      ```python
      result = await crawler.arun(url="https://www.example.com", process_iframes=True)
      ```

8) **Wrap-Up**:

   - Summarize these advanced features and how they allow users to customize every part of their web scraping experience.
   - Tease upcoming videos where each feature will be explored in detail.

---

This covers each advanced feature with a brief example, providing a useful overview to prepare viewers for the more in-depth videos.# Crawl4AI

## Episode 3: Browser Configurations & Headless Crawling

### Quick Intro
Explain browser options (`chromium`, `firefox`, `webkit`) and settings for headless mode, caching, and verbose logging.

Here’s a streamlined outline for the **Browser Configurations & Headless Crawling** video:

---

### **Browser Configurations & Headless Crawling**

1) **Overview of Browser Options**:

   - Crawl4AI supports three browser engines:
     - **Chromium** (default) - Highly compatible.
     - **Firefox** - Great for specialized use cases.
     - **Webkit** - Lightweight, ideal for basic needs.
   - **Example**:
      ```python
      # Using Chromium (default)
      crawler = AsyncWebCrawler(browser_type="chromium")
      
      # Using Firefox
      crawler = AsyncWebCrawler(browser_type="firefox")
      
      # Using WebKit
      crawler = AsyncWebCrawler(browser_type="webkit")
      ```

2) **Headless Mode**:

   - Headless mode runs the browser without a visible GUI, making it faster and less resource-intensive.
   - To enable or disable:
      ```python
      # Headless mode (default is True)
      crawler = AsyncWebCrawler(headless=True)
      
      # Disable headless mode for debugging
      crawler = AsyncWebCrawler(headless=False)
      ```

3) **Verbose Logging**:

   - Use `verbose=True` to get detailed logs for each action, useful for debugging:
      ```python
      crawler = AsyncWebCrawler(verbose=True)
      ```

4) **Running a Basic Crawl with Configuration**:

   - Example of a simple crawl with custom browser settings:
      ```python
      async with AsyncWebCrawler(browser_type="firefox", headless=True, verbose=True) as crawler:
          result = await crawler.arun(url="https://www.example.com")
          print(result.markdown[:500])  # Show first 500 characters
      ```
   - This example uses Firefox in headless mode with logging enabled, demonstrating the flexibility of Crawl4AI’s setup.

5) **Recap & Next Steps**:

   - Recap the power of selecting different browsers and running headless mode for speed and efficiency.
   - Tease the next video: **Proxy & Security Settings** for navigating blocked or restricted content and protecting IP identity.

---

This breakdown covers browser configuration essentials in Crawl4AI, providing users with practical steps to optimize their scraping setup.# Crawl4AI

## Episode 4: Advanced Proxy and Security Settings

### Quick Intro
Showcase proxy configurations (HTTP, SOCKS5, authenticated proxies). Demo: Use rotating proxies and set custom headers to avoid IP blocking and enhance security.

Here’s a focused outline for the **Proxy and Security Settings** video:

---

### **Proxy & Security Settings**

1) **Why Use Proxies in Web Crawling**:

   - Proxies are essential for bypassing IP-based restrictions, improving anonymity, and managing rate limits.
   - Crawl4AI supports simple proxies, authenticated proxies, and proxy rotation for robust web scraping.

2) **Basic Proxy Setup**:

   - **Using a Simple Proxy**:
     ```python
     # HTTP proxy
     crawler = AsyncWebCrawler(proxy="http://proxy.example.com:8080")
     
     # SOCKS proxy
     crawler = AsyncWebCrawler(proxy="socks5://proxy.example.com:1080")
     ```

3) **Authenticated Proxies**:

   - Use `proxy_config` for proxies requiring a username and password:
     ```python
     proxy_config = {
         "server": "http://proxy.example.com:8080",
         "username": "user",
         "password": "pass"
     }
     crawler = AsyncWebCrawler(proxy_config=proxy_config)
     ```

4) **Rotating Proxies**:

   - Rotating proxies helps avoid IP bans by switching IP addresses for each request:
     ```python
     async def get_next_proxy():
         # Define proxy rotation logic here
         return {"server": "http://next.proxy.com:8080"}
     
     async with AsyncWebCrawler() as crawler:
         for url in urls:
             proxy = await get_next_proxy()
             crawler.update_proxy(proxy)
             result = await crawler.arun(url=url)
     ```
   - This setup periodically switches the proxy for enhanced security and access.

5) **Custom Headers for Additional Security**:

   - Set custom headers to mask the crawler’s identity and avoid detection:
     ```python
     headers = {
         "X-Forwarded-For": "203.0.113.195",
         "Accept-Language": "en-US,en;q=0.9",
         "Cache-Control": "no-cache",
         "Pragma": "no-cache"
     }
     crawler = AsyncWebCrawler(headers=headers)
     ```

6) **Combining Proxies with Magic Mode for Anti-Bot Protection**:

   - For sites with aggressive bot detection, combine `proxy` settings with `magic=True`:
     ```python
     async with AsyncWebCrawler(proxy="http://proxy.example.com:8080", headers={"Accept-Language": "en-US"}) as crawler:
         result = await crawler.arun(
             url="https://example.com",
             magic=True  # Enables anti-detection features
         )
     ```
   - **Magic Mode** automatically enables user simulation, random timing, and browser property masking.

7) **Wrap Up & Next Steps**:

   - Summarize the importance of proxies and anti-detection in accessing restricted content and avoiding bans.
   - Tease the next video: **JavaScript Execution and Handling Dynamic Content** for working with interactive and dynamically loaded pages.

---

This outline provides a practical guide to setting up proxies and security configurations, empowering users to navigate restricted sites while staying undetected.# Crawl4AI

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

This outline explains how to handle dynamic content and JavaScript-based interactions effectively, enabling users to scrape and interact with complex, modern websites.# Crawl4AI

## Episode 6: Magic Mode and Anti-Bot Protection

### Quick Intro
Highlight `Magic Mode` and anti-bot features like user simulation, navigator overrides, and timing randomization. Demo: Access a site with anti-bot protection and show how `Magic Mode` seamlessly handles it.

Here’s a concise outline for the **Magic Mode and Anti-Bot Protection** video:

---

### **Magic Mode & Anti-Bot Protection**

1) **Why Anti-Bot Protection is Important**:

   - Many websites use bot detection mechanisms to block automated scraping. Crawl4AI’s anti-detection features help avoid IP bans, CAPTCHAs, and access restrictions.
   - **Magic Mode** is a one-step solution to enable a range of anti-bot features without complex configuration.

2) **Enabling Magic Mode**:

   - Simply set `magic=True` to activate Crawl4AI’s full anti-bot suite:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         magic=True  # Enables all anti-detection features
     )
     ```
   - This enables a blend of stealth techniques, including masking automation signals, randomizing timings, and simulating real user behavior.

3) **What Magic Mode Does Behind the Scenes**:

   - **User Simulation**: Mimics human actions like mouse movements and scrolling.
   - **Navigator Overrides**: Hides signals that indicate an automated browser.
   - **Timing Randomization**: Adds random delays to simulate natural interaction patterns.
   - **Cookie Handling**: Accepts and manages cookies dynamically to avoid triggers from cookie pop-ups.

4) **Manual Anti-Bot Options (If Not Using Magic Mode)**:

   - For granular control, you can configure individual settings without Magic Mode:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         simulate_user=True,        # Enables human-like behavior
         override_navigator=True    # Hides automation fingerprints
     )
     ```
   - **Use Cases**: This approach allows more specific adjustments when certain anti-bot features are needed but others are not.

5) **Combining Proxies with Magic Mode**:

   - To avoid rate limits or IP blocks, combine Magic Mode with a proxy:
     ```python
     async with AsyncWebCrawler(
         proxy="http://proxy.example.com:8080",
         headers={"Accept-Language": "en-US"}
     ) as crawler:
         result = await crawler.arun(
             url="https://example.com",
             magic=True  # Full anti-detection
         )
     ```
   - This setup maximizes stealth by pairing anti-bot detection with IP obfuscation.

6) **Example of Anti-Bot Protection in Action**:

   - Full example with Magic Mode and proxies to scrape a protected page:
     ```python
     async with AsyncWebCrawler() as crawler:
         result = await crawler.arun(
             url="https://example.com/protected-content",
             magic=True,
             proxy="http://proxy.example.com:8080",
             wait_for="css:.content-loaded"  # Wait for the main content to load
         )
         print(result.markdown[:500])  # Display first 500 characters of the content
     ```
   - This example ensures seamless access to protected content by combining anti-detection and waiting for full content load.

7) **Wrap Up & Next Steps**:

   - Recap the power of Magic Mode and anti-bot features for handling restricted websites.
   - Tease the next video: **Content Cleaning and Fit Markdown** to show how to extract clean and focused content from a page.

---

This outline shows users how to easily avoid bot detection and access restricted content, demonstrating both the power and simplicity of Magic Mode in Crawl4AI.# Crawl4AI

## Episode 7: Content Cleaning and Fit Markdown

### Quick Intro
Explain content cleaning options, including `fit_markdown` to keep only the most relevant content. Demo: Extract and compare regular vs. fit markdown from a news site or blog.

Here’s a streamlined outline for the **Content Cleaning and Fit Markdown** video:

---

### **Content Cleaning & Fit Markdown**

1) **Overview of Content Cleaning in Crawl4AI**:

   - Explain that web pages often include extra elements like ads, navigation bars, footers, and popups.
   - Crawl4AI’s content cleaning features help extract only the main content, reducing noise and enhancing readability.

2) **Basic Content Cleaning Options**:

   - **Removing Unwanted Elements**: Exclude specific HTML tags, like forms or navigation bars:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         word_count_threshold=10,       # Filter out blocks with fewer than 10 words
         excluded_tags=['form', 'nav'], # Exclude specific tags
         remove_overlay_elements=True   # Remove popups and modals
     )
     ```
   - This example extracts content while excluding forms, navigation, and modal overlays, ensuring clean results.

3) **Fit Markdown for Main Content Extraction**:

   - **What is Fit Markdown**: Uses advanced analysis to identify the most relevant content (ideal for articles, blogs, and documentation).
   - **How it Works**: Analyzes content density, removes boilerplate elements, and maintains formatting for a clear output.
   - **Example**:
     ```python
     result = await crawler.arun(url="https://example.com")
     main_content = result.fit_markdown  # Extracted main content
     print(main_content[:500])  # Display first 500 characters
     ```
   - Fit Markdown is especially helpful for long-form content like news articles or blog posts.

4) **Comparing Fit Markdown with Regular Markdown**:

   - **Fit Markdown** returns the primary content without extraneous elements.
   - **Regular Markdown** includes all extracted text in markdown format.
   - Example to show the difference:
     ```python
     all_content = result.markdown      # Full markdown
     main_content = result.fit_markdown # Only the main content
     
     print(f"All Content Length: {len(all_content)}")
     print(f"Main Content Length: {len(main_content)}")
     ```
   - This comparison shows the effectiveness of Fit Markdown in focusing on essential content.

5) **Media and Metadata Handling with Content Cleaning**:

   - **Media Extraction**: Crawl4AI captures images and videos with metadata like alt text, descriptions, and relevance scores:
     ```python
     for image in result.media["images"]:
         print(f"Source: {image['src']}, Alt Text: {image['alt']}, Relevance Score: {image['score']}")
     ```
   - **Use Case**: Useful for saving only relevant images or videos from an article or content-heavy page.

6) **Example of Clean Content Extraction in Action**:

   - Full example extracting cleaned content and Fit Markdown:
     ```python
     async with AsyncWebCrawler() as crawler:
         result = await crawler.arun(
             url="https://example.com",
             word_count_threshold=10,
             excluded_tags=['nav', 'footer'],
             remove_overlay_elements=True
         )
         print(result.fit_markdown[:500])  # Show main content
     ```
   - This example demonstrates content cleaning with settings for filtering noise and focusing on the core text.

7) **Wrap Up & Next Steps**:

   - Summarize the power of Crawl4AI’s content cleaning features and Fit Markdown for capturing clean, relevant content.
   - Tease the next video: **Link Analysis and Smart Filtering** to focus on analyzing and filtering links within crawled pages.

---

This outline covers Crawl4AI’s content cleaning features and the unique benefits of Fit Markdown, showing users how to retrieve focused, high-quality content from web pages.# Crawl4AI

## Episode 8: Media Handling: Images, Videos, and Audio

### Quick Intro
Showcase Crawl4AI’s media extraction capabilities, including lazy-loaded media and metadata. Demo: Crawl a multimedia page, extract images, and show metadata (alt text, context, relevance score).

Here’s a clear and focused outline for the **Media Handling: Images, Videos, and Audio** video:

---

### **Media Handling: Images, Videos, and Audio**

1) **Overview of Media Extraction in Crawl4AI**:

   - Crawl4AI can detect and extract different types of media (images, videos, and audio) along with useful metadata.
   - This functionality is essential for gathering visual content from multimedia-heavy pages like e-commerce sites, news articles, and social media feeds.

2) **Image Extraction and Metadata**:

   - Crawl4AI captures images with detailed metadata, including:
     - **Source URL**: The direct URL to the image.
     - **Alt Text**: Image description if available.
     - **Relevance Score**: A score (0–10) indicating how relevant the image is to the main content.
     - **Context**: Text surrounding the image on the page.
   - **Example**:
     ```python
     result = await crawler.arun(url="https://example.com")
     
     for image in result.media["images"]:
         print(f"Source: {image['src']}")
         print(f"Alt Text: {image['alt']}")
         print(f"Relevance Score: {image['score']}")
         print(f"Context: {image['context']}")
     ```
   - This example shows how to access each image’s metadata, making it easy to filter for the most relevant visuals.

3) **Handling Lazy-Loaded Images**:

   - Crawl4AI automatically supports lazy-loaded images, which are commonly used to optimize webpage loading.
   - **Example with Wait for Lazy-Loaded Content**:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         wait_for="css:img[data-src]",  # Wait for lazy-loaded images
         delay_before_return_html=2.0   # Allow extra time for images to load
     )
     ```
   - This setup waits for lazy-loaded images to appear, ensuring they are fully captured.

4) **Video Extraction and Metadata**:

   - Crawl4AI captures video elements, including:
     - **Source URL**: The video’s direct URL.
     - **Type**: Format of the video (e.g., MP4).
     - **Thumbnail**: A poster or thumbnail image if available.
     - **Duration**: Video length, if metadata is provided.
   - **Example**:
     ```python
     for video in result.media["videos"]:
         print(f"Video Source: {video['src']}")
         print(f"Type: {video['type']}")
         print(f"Thumbnail: {video.get('poster')}")
         print(f"Duration: {video.get('duration')}")
     ```
   - This allows users to gather video content and relevant details for further processing or analysis.

5) **Audio Extraction and Metadata**:

   - Audio elements can also be extracted, with metadata like:
     - **Source URL**: The audio file’s direct URL.
     - **Type**: Format of the audio file (e.g., MP3).
     - **Duration**: Length of the audio, if available.
   - **Example**:
     ```python
     for audio in result.media["audios"]:
         print(f"Audio Source: {audio['src']}")
         print(f"Type: {audio['type']}")
         print(f"Duration: {audio.get('duration')}")
     ```
   - Useful for sites with podcasts, sound bites, or other audio content.

6) **Filtering Media by Relevance**:

   - Use metadata like relevance score to filter only the most useful media content:
     ```python
     relevant_images = [img for img in result.media["images"] if img['score'] > 5]
     ```
   - This is especially helpful for content-heavy pages where you only want media directly related to the main content.

7) **Example: Full Media Extraction with Content Filtering**:

   - Full example extracting images, videos, and audio along with filtering by relevance:
     ```python
     async with AsyncWebCrawler() as crawler:
         result = await crawler.arun(
             url="https://example.com",
             word_count_threshold=10,  # Filter content blocks for relevance
             exclude_external_images=True  # Only keep internal images
         )
         
         # Display media summaries
         print(f"Relevant Images: {len(relevant_images)}")
         print(f"Videos: {len(result.media['videos'])}")
         print(f"Audio Clips: {len(result.media['audios'])}")
     ```
   - This example shows how to capture and filter various media types, focusing on what’s most relevant.

8) **Wrap Up & Next Steps**:

   - Recap the comprehensive media extraction capabilities, emphasizing how metadata helps users focus on relevant content.
   - Tease the next video: **Link Analysis and Smart Filtering** to explore how Crawl4AI handles internal, external, and social media links for more focused data gathering.

---

This outline provides users with a complete guide to handling images, videos, and audio in Crawl4AI, using metadata to enhance relevance and precision in multimedia extraction.# Crawl4AI

## Episode 9: Link Analysis and Smart Filtering

### Quick Intro
Walk through internal and external link classification, social media link filtering, and custom domain exclusion. Demo: Analyze links on a website, focusing on internal navigation vs. external or ad links.

Here’s a focused outline for the **Link Analysis and Smart Filtering** video:

---

### **Link Analysis & Smart Filtering**

1) **Importance of Link Analysis in Web Crawling**:

   - Explain that web pages often contain numerous links, including internal links, external links, social media links, and ads.
   - Crawl4AI’s link analysis and filtering options help extract only relevant links, enabling more targeted and efficient crawls.

2) **Automatic Link Classification**:

   - Crawl4AI categorizes links automatically into internal, external, and social media links.
   - **Example**:
     ```python
     result = await crawler.arun(url="https://example.com")

     # Access internal and external links
     internal_links = result.links["internal"]
     external_links = result.links["external"]

     # Print first few links for each type
     print("Internal Links:", internal_links[:3])
     print("External Links:", external_links[:3])
     ```

3) **Filtering Out Unwanted Links**:

   - **Exclude External Links**: Remove all links pointing to external sites.
   - **Exclude Social Media Links**: Filter out social media domains like Facebook or Twitter.
   - **Example**:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         exclude_external_links=True,         # Remove external links
         exclude_social_media_links=True      # Remove social media links
     )
     ```

4) **Custom Domain Filtering**:

   - **Exclude Specific Domains**: Filter links from particular domains, e.g., ad sites.
   - **Custom Social Media Domains**: Add additional social media domains if needed.
   - **Example**:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         exclude_domains=["ads.com", "trackers.com"],
         exclude_social_media_domains=["facebook.com", "linkedin.com"]
     )
     ```

5) **Accessing Link Context and Metadata**:

   - Crawl4AI provides additional metadata for each link, including its text, type (e.g., navigation or content), and surrounding context.
   - **Example**:
     ```python
     for link in result.links["internal"]:
         print(f"Link: {link['href']}, Text: {link['text']}, Context: {link['context']}")
     ```
   - **Use Case**: Helps users understand the relevance of links based on where they are placed on the page (e.g., navigation vs. article content).

6) **Example of Comprehensive Link Filtering and Analysis**:

   - Full example combining link filtering, metadata access, and contextual information:
     ```python
     async with AsyncWebCrawler() as crawler:
         result = await crawler.arun(
             url="https://example.com",
             exclude_external_links=True,
             exclude_social_media_links=True,
             exclude_domains=["ads.com"],
             css_selector=".main-content"  # Focus only on main content area
         )
         for link in result.links["internal"]:
             print(f"Internal Link: {link['href']}, Text: {link['text']}, Context: {link['context']}")
     ```
   - This example filters unnecessary links, keeping only internal and relevant links from the main content area.

7) **Wrap Up & Next Steps**:

   - Summarize the benefits of link filtering for efficient crawling and relevant content extraction.
   - Tease the next video: **Custom Headers, Identity Management, and User Simulation** to explain how to configure identity settings and simulate user behavior for stealthier crawls.

---

This outline provides a practical overview of Crawl4AI’s link analysis and filtering features, helping users target only essential links while eliminating distractions.# Crawl4AI

## Episode 10: Custom Headers, Identity, and User Simulation

### Quick Intro
Teach how to use custom headers, user-agent strings, and simulate real user interactions. Demo: Set custom user-agent and headers to access a site that blocks typical crawlers.

Here’s a concise outline for the **Custom Headers, Identity Management, and User Simulation** video:

---

### **Custom Headers, Identity Management, & User Simulation**

1) **Why Customize Headers and Identity in Crawling**:

   - Websites often track request headers and browser properties to detect bots. Customizing headers and managing identity help make requests appear more human, improving access to restricted sites.

2) **Setting Custom Headers**:

   - Customize HTTP headers to mimic genuine browser requests or meet site-specific requirements:
     ```python
     headers = {
         "Accept-Language": "en-US,en;q=0.9",
         "X-Requested-With": "XMLHttpRequest",
         "Cache-Control": "no-cache"
     }
     crawler = AsyncWebCrawler(headers=headers)
     ```
   - **Use Case**: Customize the `Accept-Language` header to simulate local user settings, or `Cache-Control` to bypass cache for fresh content.

3) **Setting a Custom User Agent**:

   - Some websites block requests from common crawler user agents. Setting a custom user agent string helps bypass these restrictions:
     ```python
     crawler = AsyncWebCrawler(
         user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
     )
     ```
   - **Tip**: Use user-agent strings from popular browsers (e.g., Chrome, Firefox) to improve access and reduce detection risks.

4) **User Simulation for Human-like Behavior**:

   - Enable `simulate_user=True` to mimic natural user interactions, such as random timing and simulated mouse movements:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         simulate_user=True  # Simulates human-like behavior
     )
     ```
   - **Behavioral Effects**: Adds subtle variations in interactions, making the crawler harder to detect on bot-protected sites.

5) **Navigator Overrides and Magic Mode for Full Identity Masking**:

   - Use `override_navigator=True` to mask automation indicators like `navigator.webdriver`, which websites check to detect bots:
     ```python
     result = await crawler.arun(
         url="https://example.com",
         override_navigator=True  # Masks bot-related signals
     )
     ```
   - **Combining with Magic Mode**: For a complete anti-bot setup, combine these identity options with `magic=True` for maximum protection:
     ```python
     async with AsyncWebCrawler() as crawler:
         result = await crawler.arun(
             url="https://example.com",
             magic=True,  # Enables all anti-bot detection features
             user_agent="Custom-Agent",  # Custom agent with Magic Mode
         )
     ```
   - This setup includes all anti-detection techniques like navigator masking, random timing, and user simulation.

6) **Example: Comprehensive Setup for Identity Management**:

   - A full example combining custom headers, user-agent, and user simulation for a realistic browsing profile:
     ```python
     async with AsyncWebCrawler(
         headers={"Accept-Language": "en-US", "Cache-Control": "no-cache"},
         user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0",
     ) as crawler:
         result = await crawler.arun(
            url="https://example.com/secure-page",
            simulate_user=True
        )
         print(result.markdown[:500])  # Display extracted content
     ```
   - This example enables detailed customization for evading detection and accessing protected pages smoothly.

7) **Wrap Up & Next Steps**:

   - Recap the value of headers, user-agent customization, and simulation in bypassing bot detection.
   - Tease the next video: **Extraction Strategies: JSON CSS, LLM, and Cosine** to dive into structured data extraction methods for high-quality content retrieval.

---

This outline equips users with tools for managing crawler identity and human-like behavior, essential for accessing bot-protected or restricted websites.Here’s a detailed outline for the **JSON-CSS Extraction Strategy** video, covering all key aspects and supported structures in Crawl4AI:

---

### **10.1 JSON-CSS Extraction Strategy**

#### **1. Introduction to JSON-CSS Extraction**
   - JSON-CSS Extraction is used for pulling structured data from pages with repeated patterns, like product listings, article feeds, or directories.
   - This strategy allows defining a schema with CSS selectors and data fields, making it easy to capture nested, list-based, or singular elements.

#### **2. Basic Schema Structure**
   - **Schema Fields**: The schema has two main components:
     - `baseSelector`: A CSS selector to locate the main elements you want to extract (e.g., each article or product block).
     - `fields`: Defines the data fields for each element, supporting various data types and structures.

#### **3. Simple Field Extraction**
   - **Example HTML**:
     ```html
     <div class="product">
         <h2 class="title">Sample Product</h2>
         <span class="price">$19.99</span>
         <p class="description">This is a sample product.</p>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text"},
             {"name": "price", "selector": ".price", "type": "text"},
             {"name": "description", "selector": ".description", "type": "text"}
         ]
     }
     ```
   - **Explanation**: Each field captures text content from specified CSS selectors within each `.product` element.

#### **4. Supported Field Types: Text, Attribute, HTML, Regex**
   - **Field Type Options**:
     - `text`: Extracts visible text.
     - `attribute`: Captures an HTML attribute (e.g., `src`, `href`).
     - `html`: Extracts the raw HTML of an element.
     - `regex`: Allows regex patterns to extract part of the text.

   - **Example HTML** (including an image):
     ```html
     <div class="product">
         <h2 class="title">Sample Product</h2>
         <img class="product-image" src="image.jpg" alt="Product Image">
         <span class="price">$19.99</span>
         <p class="description">Limited time offer.</p>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text"},
             {"name": "image_url", "selector": ".product-image", "type": "attribute", "attribute": "src"},
             {"name": "price", "selector": ".price", "type": "regex", "pattern": r"\$(\d+\.\d+)"},
             {"name": "description_html", "selector": ".description", "type": "html"}
         ]
     }
     ```
   - **Explanation**:
     - `attribute`: Extracts the `src` attribute from `.product-image`.
     - `regex`: Extracts the numeric part from `$19.99`.
     - `html`: Retrieves the full HTML of the description element.

#### **5. Nested Field Extraction**
   - **Use Case**: Useful when content contains sub-elements, such as an article with author details within it.
   - **Example HTML**:
     ```html
     <div class="article">
         <h1 class="title">Sample Article</h1>
         <div class="author">
             <span class="name">John Doe</span>
             <span class="bio">Writer and editor</span>
         </div>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".article",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text"},
             {"name": "author", "type": "nested", "selector": ".author", "fields": [
                 {"name": "name", "selector": ".name", "type": "text"},
                 {"name": "bio", "selector": ".bio", "type": "text"}
             ]}
         ]
     }
     ```
   - **Explanation**:
     - `nested`: Extracts `name` and `bio` within `.author`, grouping the author details in a single `author` object.

#### **6. List and Nested List Extraction**
   - **List**: Extracts multiple elements matching the selector as a list.
   - **Nested List**: Allows lists within lists, useful for items with sub-lists (e.g., specifications for each product).
   - **Example HTML**:
     ```html
     <div class="product">
         <h2 class="title">Product with Features</h2>
         <ul class="features">
             <li class="feature">Feature 1</li>
             <li class="feature">Feature 2</li>
             <li class="feature">Feature 3</li>
         </ul>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text"},
             {"name": "features", "type": "list", "selector": ".features .feature", "fields": [
                 {"name": "feature", "type": "text"}
             ]}
         ]
     }
     ```
   - **Explanation**:
     - `list`: Captures each `.feature` item within `.features`, outputting an array of features under the `features` field.

#### **7. Transformations for Field Values**
   - Transformations allow you to modify extracted values (e.g., converting to lowercase).
   - Supported transformations: `lowercase`, `uppercase`, `strip`.
   - **Example HTML**:
     ```html
     <div class="product">
         <h2 class="title">Special Product</h2>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text", "transform": "uppercase"}
         ]
     }
     ```
   - **Explanation**: The `transform` property changes the `title` to uppercase, useful for standardized outputs.

#### **8. Full JSON-CSS Extraction Example**
   - Combining all elements in a single schema example for a comprehensive crawl:
   - **Example HTML**:
     ```html
     <div class="product">
         <h2 class="title">Featured Product</h2>
         <img class="product-image" src="product.jpg">
         <span class="price">$99.99</span>
         <p class="description">Best product of the year.</p>
         <ul class="features">
             <li class="feature">Durable</li>
             <li class="feature">Eco-friendly</li>
         </ul>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text", "transform": "uppercase"},
             {"name": "image_url", "selector": ".product-image", "type": "attribute", "attribute": "src"},
             {"name": "price", "selector": ".price", "type": "regex", "pattern": r"\$(\d+\.\d+)"},
             {"name": "description", "selector": ".description", "type": "html"},
             {"name": "features", "type": "list", "selector": ".features .feature", "fields": [
                 {"name": "feature", "type": "text"}
             ]}
         ]
     }
     ```
   - **Explanation**: This schema captures and transforms each aspect of the product, illustrating the JSON-CSS strategy’s versatility for structured extraction.

#### **9. Wrap Up & Next Steps**
   - Summarize JSON-CSS Extraction’s flexibility for structured, pattern-based extraction.
   - Tease the next video: **10.2 LLM Extraction Strategy**, focusing on using language models to extract data based on intelligent content analysis.

---

This outline covers each JSON-CSS Extraction option in Crawl4AI, with practical examples and schema configurations, making it a thorough guide for users.# Crawl4AI

## Episode 11: Extraction Strategies: JSON CSS, LLM, and Cosine

### Quick Intro
Introduce JSON CSS Extraction Strategy for structured data, LLM Extraction Strategy for intelligent parsing, and Cosine Strategy for clustering similar content. Demo: Use JSON CSS to scrape product details from an e-commerce site.

Here’s a comprehensive outline for the **LLM Extraction Strategy** video, covering key details and example applications.

---

### **10.2 LLM Extraction Strategy**

#### **1. Introduction to LLM Extraction Strategy**
   - The LLM Extraction Strategy leverages language models to interpret and extract structured data from complex web content.
   - Unlike traditional CSS selectors, this strategy uses natural language instructions and schemas to guide the extraction, ideal for unstructured or diverse content.
   - Supports **OpenAI**, **Azure OpenAI**, **HuggingFace**, and **Ollama** models, enabling flexibility with both proprietary and open-source providers.

#### **2. Key Components of LLM Extraction Strategy**
   - **Provider**: Specifies the LLM provider (e.g., OpenAI, HuggingFace, Azure).
   - **API Token**: Required for most providers, except Ollama (local LLM model).
   - **Instruction**: Custom extraction instructions sent to the model, providing flexibility in how the data is structured and extracted.
   - **Schema**: Optional, defines structured fields to organize extracted data into JSON format.
   - **Extraction Type**: Supports `"block"` for simpler text blocks or `"schema"` when a structured output format is required.
   - **Chunking Parameters**: Breaks down large documents, with options to adjust chunk size and overlap rate for more accurate extraction across lengthy texts.

#### **3. Basic Extraction Example: OpenAI Model Pricing**
   - **Goal**: Extract model names and their input and output fees from the OpenAI pricing page.
   - **Schema Definition**:
     - **Model Name**: Text for model identification.
     - **Input Fee**: Token cost for input processing.
     - **Output Fee**: Token cost for output generation.

   - **Schema**:
     ```python
     class OpenAIModelFee(BaseModel):
         model_name: str = Field(..., description="Name of the OpenAI model.")
         input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
         output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")
     ```

   - **Example Code**:
     ```python
     async def extract_openai_pricing():
         async with AsyncWebCrawler() as crawler:
             result = await crawler.arun(
                 url="https://openai.com/api/pricing/",
                 extraction_strategy=LLMExtractionStrategy(
                     provider="openai/gpt-4o",
                     api_token=os.getenv("OPENAI_API_KEY"),
                     schema=OpenAIModelFee.schema(),
                     extraction_type="schema",
                     instruction="Extract model names and fees for input and output tokens from the page."
                 ),
                 bypass_cache=True
             )
             print(result.extracted_content)
     ```

   - **Explanation**:
     - The extraction strategy combines a schema and detailed instruction to guide the LLM in capturing structured data.
     - Each model’s name, input fee, and output fee are extracted in a JSON format.

#### **4. Knowledge Graph Extraction Example**
   - **Goal**: Extract entities and their relationships from a document for use in a knowledge graph.
   - **Schema Definition**:
     - **Entities**: Individual items with descriptions (e.g., people, organizations).
     - **Relationships**: Connections between entities, including descriptions and relationship types.

   - **Schema**:
     ```python
     class Entity(BaseModel):
         name: str
         description: str

     class Relationship(BaseModel):
         entity1: Entity
         entity2: Entity
         description: str
         relation_type: str

     class KnowledgeGraph(BaseModel):
         entities: List[Entity]
         relationships: List[Relationship]
     ```

   - **Example Code**:
     ```python
     async def extract_knowledge_graph():
         extraction_strategy = LLMExtractionStrategy(
             provider="azure/gpt-4o-mini",
             api_token=os.getenv("AZURE_API_KEY"),
             schema=KnowledgeGraph.schema(),
             extraction_type="schema",
             instruction="Extract entities and relationships from the content to build a knowledge graph."
         )
         async with AsyncWebCrawler() as crawler:
             result = await crawler.arun(
                 url="https://example.com/some-article",
                 extraction_strategy=extraction_strategy,
                 bypass_cache=True
             )
             print(result.extracted_content)
     ```

   - **Explanation**:
     - In this setup, the LLM extracts entities and their relationships based on the schema and instruction.
     - The schema organizes results into a JSON-based knowledge graph format.

#### **5. Key Settings in LLM Extraction**
   - **Chunking Options**:
     - For long pages, set `chunk_token_threshold` to specify maximum token count per section.
     - Adjust `overlap_rate` to control the overlap between chunks, useful for contextual consistency.
   - **Example**:
     ```python
     extraction_strategy = LLMExtractionStrategy(
         provider="openai/gpt-4",
         api_token=os.getenv("OPENAI_API_KEY"),
         chunk_token_threshold=3000,
         overlap_rate=0.2,  # 20% overlap between chunks
         instruction="Extract key insights and relationships."
     )
     ```
   - This setup ensures that longer texts are divided into manageable chunks with slight overlap, enhancing the quality of extraction.

#### **6. Flexible Provider Options for LLM Extraction**
   - **Using Proprietary Models**: OpenAI, Azure, and HuggingFace provide robust language models, often suited for complex or detailed extractions.
   - **Using Open-Source Models**: Ollama and other open-source models can be deployed locally, suitable for offline or cost-effective extraction.
   - **Example Call**:
     ```python
     await extract_structured_data_using_llm("huggingface/meta-llama/Meta-Llama-3.1-8B-Instruct", os.getenv("HUGGINGFACE_API_KEY"))
     await extract_structured_data_using_llm("openai/gpt-4o", os.getenv("OPENAI_API_KEY"))
     await extract_structured_data_using_llm("ollama/llama3.2")   
     ```

#### **7. Complete Example of LLM Extraction Setup**
   - Code to run both the OpenAI pricing and Knowledge Graph extractions, using various providers:
     ```python
     async def main():
         await extract_openai_pricing()
         await extract_knowledge_graph()
     
     if __name__ == "__main__":
         asyncio.run(main())
     ```

#### **8. Wrap Up & Next Steps**
   - Recap the power of LLM extraction for handling unstructured or complex data extraction tasks.
   - Tease the next video: **10.3 Cosine Similarity Strategy** for clustering similar content based on semantic similarity.

---

This outline explains LLM Extraction in Crawl4AI, with examples showing how to extract structured data using custom schemas and instructions. It demonstrates flexibility with multiple providers, ensuring practical application for different use cases.# Crawl4AI

## Episode 11: Extraction Strategies: JSON CSS, LLM, and Cosine

### Quick Intro
Introduce JSON CSS Extraction Strategy for structured data, LLM Extraction Strategy for intelligent parsing, and Cosine Strategy for clustering similar content. Demo: Use JSON CSS to scrape product details from an e-commerce site.

Here’s a structured outline for the **Cosine Similarity Strategy** video, covering key concepts, configuration, and a practical example.

---

### **10.3 Cosine Similarity Strategy**

#### **1. Introduction to Cosine Similarity Strategy**
   - The Cosine Similarity Strategy clusters content by semantic similarity, offering an efficient alternative to LLM-based extraction, especially when speed is a priority.
   - Ideal for grouping similar sections of text, this strategy is well-suited for pages with content sections that may need to be classified or tagged, like news articles, product descriptions, or reviews.

#### **2. Key Configuration Options**
   - **semantic_filter**: A keyword-based filter to focus on relevant content.
   - **word_count_threshold**: Minimum number of words per cluster, filtering out shorter, less meaningful clusters.
   - **max_dist**: Maximum allowable distance between elements in clusters, impacting cluster tightness.
   - **linkage_method**: Method for hierarchical clustering, such as `'ward'` (for well-separated clusters).
   - **top_k**: Specifies the number of top categories for each cluster.
   - **model_name**: Defines the model for embeddings, such as `sentence-transformers/all-MiniLM-L6-v2`.
   - **sim_threshold**: Minimum similarity threshold for filtering, allowing control over cluster relevance.

#### **3. How Cosine Similarity Clustering Works**
   - **Step 1**: Embeddings are generated for each text section, transforming them into vectors that capture semantic meaning.
   - **Step 2**: Hierarchical clustering groups similar sections based on cosine similarity, forming clusters with related content.
   - **Step 3**: Clusters are filtered based on word count, removing those below the `word_count_threshold`.
   - **Step 4**: Each cluster is then categorized with tags, if enabled, providing context to each grouped content section.

#### **4. Example Use Case: Clustering Blog Article Sections**
   - **Goal**: Group related sections of a blog or news page to identify distinct topics or discussion areas.
   - **Example HTML Sections**:
     ```text
     "The economy is showing signs of recovery, with markets up this quarter.",
     "In the sports world, several major teams are preparing for the upcoming season.",
     "New advancements in AI technology are reshaping the tech landscape.",
     "Market analysts are optimistic about continued growth in tech stocks."
     ```

   - **Code Setup**:
     ```python
     async def extract_blog_sections():
         extraction_strategy = CosineStrategy(
             word_count_threshold=15,
             max_dist=0.3,
             sim_threshold=0.2,
             model_name="sentence-transformers/all-MiniLM-L6-v2",
             top_k=2
         )
         async with AsyncWebCrawler() as crawler:
             url = "https://example.com/blog-page"
             result = await crawler.arun(
                 url=url,
                 extraction_strategy=extraction_strategy,
                 bypass_cache=True
             )
             print(result.extracted_content)
     ```

   - **Explanation**:
     - **word_count_threshold**: Ensures only clusters with meaningful content are included.
     - **sim_threshold**: Filters out clusters with low similarity, focusing on closely related sections.
     - **top_k**: Selects top tags, useful for identifying main topics.

#### **5. Applying Semantic Filtering with Cosine Similarity**
   - **Semantic Filter**: Filters sections based on relevance to a specific keyword, such as “technology” for tech articles.
   - **Example Code**:
     ```python
     extraction_strategy = CosineStrategy(
         semantic_filter="technology",
         word_count_threshold=10,
         max_dist=0.25,
         model_name="sentence-transformers/all-MiniLM-L6-v2"
     )
     ```
   - **Explanation**:
     - **semantic_filter**: Only sections with high similarity to the “technology” keyword will be included in the clustering, making it easy to focus on specific topics within a mixed-content page.

#### **6. Clustering Product Reviews by Similarity**
   - **Goal**: Organize product reviews by themes, such as “price,” “quality,” or “durability.”
   - **Example Reviews**:
     ```text
     "The quality of this product is outstanding and well worth the price.",
     "I found the product to be durable but a bit overpriced.",
     "Great value for the money and long-lasting.",
     "The build quality is good, but I expected a lower price point."
     ```

   - **Code Setup**:
     ```python
     async def extract_product_reviews():
         extraction_strategy = CosineStrategy(
             word_count_threshold=20,
             max_dist=0.35,
             sim_threshold=0.25,
             model_name="sentence-transformers/all-MiniLM-L6-v2"
         )
         async with AsyncWebCrawler() as crawler:
             url = "https://example.com/product-reviews"
             result = await crawler.arun(
                 url=url,
                 extraction_strategy=extraction_strategy,
                 bypass_cache=True
             )
             print(result.extracted_content)
     ```

   - **Explanation**:
     - This configuration clusters similar reviews, grouping feedback by common themes, helping businesses understand customer sentiments around particular product aspects.

#### **7. Performance Advantages of Cosine Strategy**
   - **Speed**: The Cosine Similarity Strategy is faster than LLM-based extraction, as it doesn’t rely on API calls to external LLMs.
   - **Local Processing**: The strategy runs locally with pre-trained sentence embeddings, ideal for high-throughput scenarios where cost and latency are concerns.
   - **Comparison**: With a well-optimized local model, this method can perform clustering on large datasets quickly, making it suitable for tasks requiring rapid, repeated analysis.

#### **8. Full Code Example for Clustering News Articles**
   - **Code**:
     ```python
     async def main():
         await extract_blog_sections()
         await extract_product_reviews()
     
     if __name__ == "__main__":
         asyncio.run(main())
     ```

#### **9. Wrap Up & Next Steps**
   - Recap the efficiency and effectiveness of Cosine Similarity for clustering related content quickly.
   - Close with a reminder of Crawl4AI’s flexibility across extraction strategies, and prompt users to experiment with different settings to optimize clustering for their specific content.

---

This outline covers Cosine Similarity Strategy’s speed and effectiveness, providing examples that showcase its potential for clustering various content types efficiently.# Crawl4AI

## Episode 12: Session-Based Crawling for Dynamic Websites

### Quick Intro
Show session management for handling websites with multiple pages or actions (like “load more” buttons). Demo: Crawl a paginated content page, persisting session data across multiple requests.

Here’s a detailed outline for the **Session-Based Crawling for Dynamic Websites** video, explaining why sessions are necessary, how to use them, and providing practical examples and a visual diagram to illustrate the concept.

---

### **11. Session-Based Crawling for Dynamic Websites**

#### **1. Introduction to Session-Based Crawling**
   - **What is Session-Based Crawling**: Session-based crawling maintains a continuous browsing session across multiple page states, allowing the crawler to interact with a page and retrieve content that loads dynamically or based on user interactions.
   - **Why It’s Needed**:
     - In static pages, all content is available directly from a single URL.
     - In dynamic websites, content often loads progressively or based on user actions (e.g., clicking “load more,” submitting forms, scrolling).
     - Session-based crawling helps simulate user actions, capturing content that is otherwise hidden until specific actions are taken.

#### **2. Conceptual Diagram for Session-Based Crawling**

   ```mermaid
   graph TD
       Start[Start Session] --> S1[Initial State (S1)]
       S1 -->|Crawl| Content1[Extract Content S1]
       S1 -->|Action: Click Load More| S2[State S2]
       S2 -->|Crawl| Content2[Extract Content S2]
       S2 -->|Action: Scroll Down| S3[State S3]
       S3 -->|Crawl| Content3[Extract Content S3]
       S3 -->|Action: Submit Form| S4[Final State]
       S4 -->|Crawl| Content4[Extract Content S4]
       Content4 --> End[End Session]
   ```

   - **Explanation of Diagram**:
     - **Start**: Initializes the session and opens the starting URL.
     - **State Transitions**: Each action (e.g., clicking “load more,” scrolling) transitions to a new state, where additional content becomes available.
     - **Session Persistence**: Keeps the same browsing session active, preserving the state and allowing for a sequence of actions to unfold.
     - **End**: After reaching the final state, the session ends, and all accumulated content has been extracted.

#### **3. Key Components of Session-Based Crawling in Crawl4AI**
   - **Session ID**: A unique identifier to maintain the state across requests, allowing the crawler to “remember” previous actions.
   - **JavaScript Execution**: Executes JavaScript commands (e.g., clicks, scrolls) to simulate interactions.
   - **Wait Conditions**: Ensures the crawler waits for content to load in each state before moving on.
   - **Sequential State Transitions**: By defining actions and wait conditions between states, the crawler can navigate through the page as a user would.

#### **4. Basic Session Example: Multi-Step Content Loading**
   - **Goal**: Crawl an article feed that requires several “load more” clicks to display additional content.
   - **Code**:
     ```python
     async def crawl_article_feed():
         async with AsyncWebCrawler() as crawler:
             session_id = "feed_session"
             
             for page in range(3):
                 result = await crawler.arun(
                     url="https://example.com/articles",
                     session_id=session_id,
                     js_code="document.querySelector('.load-more-button').click();" if page > 0 else None,
                     wait_for="css:.article",
                     css_selector=".article"  # Target article elements
                 )
                 print(f"Page {page + 1}: Extracted {len(result.extracted_content)} articles")
     ```
   - **Explanation**:
     - **session_id**: Ensures all requests share the same browsing state.
     - **js_code**: Clicks the “load more” button after the initial page load, expanding content on each iteration.
     - **wait_for**: Ensures articles have loaded after each click before extraction.

#### **5. Advanced Example: E-Commerce Product Search with Filter Selection**
   - **Goal**: Interact with filters on an e-commerce page to extract products based on selected criteria.
   - **Example Steps**:
     1. **State 1**: Load the main product page.
     2. **State 2**: Apply a filter (e.g., “On Sale”) by selecting a checkbox.
     3. **State 3**: Scroll to load additional products and capture updated results.

   - **Code**:
     ```python
     async def extract_filtered_products():
         async with AsyncWebCrawler() as crawler:
             session_id = "product_session"
             
             # Step 1: Open product page
             result = await crawler.arun(
                 url="https://example.com/products",
                 session_id=session_id,
                 wait_for="css:.product-item"
             )
             
             # Step 2: Apply filter (e.g., "On Sale")
             result = await crawler.arun(
                 url="https://example.com/products",
                 session_id=session_id,
                 js_code="document.querySelector('#sale-filter-checkbox').click();",
                 wait_for="css:.product-item"
             )

             # Step 3: Scroll to load additional products
             for _ in range(2):  # Scroll down twice
                 result = await crawler.arun(
                     url="https://example.com/products",
                     session_id=session_id,
                     js_code="window.scrollTo(0, document.body.scrollHeight);",
                     wait_for="css:.product-item"
                 )
                 print(f"Loaded {len(result.extracted_content)} products after scroll")
     ```
   - **Explanation**:
     - **State Persistence**: Each action (filter selection and scroll) builds on the previous session state.
     - **Multiple Interactions**: Combines clicking a filter with scrolling, demonstrating how the session preserves these actions.

#### **6. Key Benefits of Session-Based Crawling**
   - **Accessing Hidden Content**: Retrieves data that loads only after user actions.
   - **Simulating User Behavior**: Handles interactive elements such as “load more” buttons, dropdowns, and filters.
   - **Maintaining Continuity Across States**: Enables a sequential process, moving logically from one state to the next, capturing all desired content without reloading the initial state each time.

#### **7. Additional Configuration Tips**
   - **Manage Session End**: Always conclude the session after the final state to release resources.
   - **Optimize with Wait Conditions**: Use `wait_for` to ensure complete loading before each extraction.
   - **Handling Errors in Session-Based Crawling**: Include error handling for interactions that may fail, ensuring robustness across state transitions.

#### **8. Complete Code Example: Multi-Step Session Workflow**
   - **Example**:
     ```python
     async def main():
         await crawl_article_feed()
         await extract_filtered_products()
     
     if __name__ == "__main__":
         asyncio.run(main())
     ```

#### **9. Wrap Up & Next Steps**
   - Recap the usefulness of session-based crawling for dynamic content extraction.
   - Tease the next video: **Hooks and Custom Workflow with AsyncWebCrawler** to cover advanced customization options for further control over the crawling process.

---

This outline covers session-based crawling from both a conceptual and practical perspective, helping users understand its importance, configure it effectively, and use it to handle complex dynamic content.# Crawl4AI

## Episode 13: Chunking Strategies for Large Text Processing

### Quick Intro
Explain Regex, NLP, and Fixed-Length chunking, and when to use each. Demo: Chunk a large article or document for processing by topics or sentences.

Here’s a structured outline for the **Chunking Strategies for Large Text Processing** video, emphasizing how chunking works within extraction and why it’s crucial for effective data aggregation.

Here’s a structured outline for the **Chunking Strategies for Large Text Processing** video, explaining each strategy, when to use it, and providing examples to illustrate.

---

### **12. Chunking Strategies for Large Text Processing**

#### **1. Introduction to Chunking in Crawl4AI**
   - **What is Chunking**: Chunking is the process of dividing large text into manageable sections or “chunks,” enabling efficient processing in extraction tasks.
   - **Why It’s Needed**:
     - When processing large text, feeding it directly into an extraction function (like `F(x)`) can overwhelm memory or token limits.
     - Chunking breaks down `x` (the text) into smaller pieces, which are processed sequentially or in parallel by the extraction function, with the final result being an aggregation of all chunks’ processed output.

#### **2. Key Chunking Strategies and Use Cases**
   - Crawl4AI offers various chunking strategies to suit different text structures, chunk sizes, and processing requirements.
   - **Choosing a Strategy**: Select based on the type of text (e.g., articles, transcripts) and extraction needs (e.g., simple splitting or context-sensitive processing).

#### **3. Strategy 1: Regex-Based Chunking**
   - **Description**: Uses regular expressions to split text based on specified patterns (e.g., paragraphs or section breaks).
   - **Use Case**: Ideal for dividing text by paragraphs or larger logical blocks where sections are clearly separated by line breaks or punctuation.
   - **Example**:
     - **Pattern**: `r'\n\n'` for double line breaks.
     ```python
     chunker = RegexChunking(patterns=[r'\n\n'])
     text_chunks = chunker.chunk(long_text)
     print(text_chunks)  # Output: List of paragraphs
     ```
   - **Pros**: Flexible for pattern-based chunking.
   - **Cons**: Limited to text with consistent formatting.

#### **4. Strategy 2: NLP Sentence-Based Chunking**
   - **Description**: Uses NLP to split text by sentences, ensuring grammatically complete segments.
   - **Use Case**: Useful for extracting individual statements, such as in news articles, quotes, or legal text.
   - **Example**:
     ```python
     chunker = NlpSentenceChunking()
     sentence_chunks = chunker.chunk(long_text)
     print(sentence_chunks)  # Output: List of sentences
     ```
   - **Pros**: Maintains sentence structure, ideal for tasks needing semantic completeness.
   - **Cons**: May create very small chunks, which could limit contextual extraction.

#### **5. Strategy 3: Topic-Based Segmentation Using TextTiling**
   - **Description**: Segments text into topics using TextTiling, identifying topic shifts and key segments.
   - **Use Case**: Ideal for long articles, reports, or essays where each section covers a different topic.
   - **Example**:
     ```python
     chunker = TopicSegmentationChunking(num_keywords=3)
     topic_chunks = chunker.chunk_with_topics(long_text)
     print(topic_chunks)  # Output: List of topic segments with keywords
     ```
   - **Pros**: Groups related content, preserving topical coherence.
   - **Cons**: Depends on identifiable topic shifts, which may not be present in all texts.

#### **6. Strategy 4: Fixed-Length Word Chunking**
   - **Description**: Splits text into chunks based on a fixed number of words.
   - **Use Case**: Ideal for text where exact segment size is required, such as processing word-limited documents for LLMs.
   - **Example**:
     ```python
     chunker = FixedLengthWordChunking(chunk_size=100)
     word_chunks = chunker.chunk(long_text)
     print(word_chunks)  # Output: List of 100-word chunks
     ```
   - **Pros**: Ensures uniform chunk sizes, suitable for token-based extraction limits.
   - **Cons**: May split sentences, affecting semantic coherence.

#### **7. Strategy 5: Sliding Window Chunking**
   - **Description**: Uses a fixed window size with a step, creating overlapping chunks to maintain context.
   - **Use Case**: Useful for maintaining context across sections, as with documents where context is needed for neighboring sections.
   - **Example**:
     ```python
     chunker = SlidingWindowChunking(window_size=100, step=50)
     window_chunks = chunker.chunk(long_text)
     print(window_chunks)  # Output: List of overlapping word chunks
     ```
   - **Pros**: Retains context across adjacent chunks, ideal for complex semantic extraction.
   - **Cons**: Overlap increases data size, potentially impacting processing time.

#### **8. Strategy 6: Overlapping Window Chunking**
   - **Description**: Similar to sliding windows but with a defined overlap, allowing chunks to share content at the edges.
   - **Use Case**: Suitable for handling long texts with essential overlapping information, like research articles or medical records.
   - **Example**:
     ```python
     chunker = OverlappingWindowChunking(window_size=1000, overlap=100)
     overlap_chunks = chunker.chunk(long_text)
     print(overlap_chunks)  # Output: List of overlapping chunks with defined overlap
     ```
   - **Pros**: Allows controlled overlap for consistent content coverage across chunks.
   - **Cons**: Redundant data in overlapping areas may increase computation.

#### **9. Practical Example: Using Chunking with an Extraction Strategy**
   - **Goal**: Combine chunking with an extraction strategy to process large text effectively.
   - **Example Code**:
     ```python
     from crawl4ai.extraction_strategy import LLMExtractionStrategy

     async def extract_large_text():
         # Initialize chunker and extraction strategy
         chunker = FixedLengthWordChunking(chunk_size=200)
         extraction_strategy = LLMExtractionStrategy(provider="openai/gpt-4", api_token="your_api_token")
         
         # Split text into chunks
         text_chunks = chunker.chunk(large_text)
         
         async with AsyncWebCrawler() as crawler:
             for chunk in text_chunks:
                 result = await crawler.arun(
                     url="https://example.com",
                     extraction_strategy=extraction_strategy,
                     content=chunk
                 )
                 print(result.extracted_content)
     ```

   - **Explanation**:
     - `chunker.chunk()`: Divides the `large_text` into smaller segments based on the chosen strategy.
     - `extraction_strategy`: Processes each chunk separately, and results are then aggregated to form the final output.

#### **10. Choosing the Right Chunking Strategy**
   - **Text Structure**: If text has clear sections (e.g., paragraphs, topics), use Regex or Topic Segmentation.
   - **Extraction Needs**: If context is crucial, consider Sliding or Overlapping Window Chunking.
   - **Processing Constraints**: For word-limited extractions (e.g., LLMs with token limits), Fixed-Length Word Chunking is often most effective.

#### **11. Wrap Up & Next Steps**
   - Recap the benefits of each chunking strategy and when to use them in extraction workflows.
   - Tease the next video: **Hooks and Custom Workflow with AsyncWebCrawler**, focusing on customizing crawler behavior with hooks for a fine-tuned extraction process.

---

This outline provides a complete understanding of chunking strategies, explaining each method’s strengths and best-use scenarios to help users process large texts effectively in Crawl4AI.# Crawl4AI

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