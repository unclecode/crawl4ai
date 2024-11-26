# Crawl4AI

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
         simulate_user=True
     ) as crawler:
         result = await crawler.arun(url="https://example.com/secure-page")
         print(result.markdown[:500])  # Display extracted content
     ```
   - This example enables detailed customization for evading detection and accessing protected pages smoothly.

7) **Wrap Up & Next Steps**:

   - Recap the value of headers, user-agent customization, and simulation in bypassing bot detection.
   - Tease the next video: **Extraction Strategies: JSON CSS, LLM, and Cosine** to dive into structured data extraction methods for high-quality content retrieval.

---

This outline equips users with tools for managing crawler identity and human-like behavior, essential for accessing bot-protected or restricted websites.