# Crawl4AI

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

This outline provides a practical overview of Crawl4AI’s link analysis and filtering features, helping users target only essential links while eliminating distractions.