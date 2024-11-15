# Crawl4AI

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

This outline covers Crawl4AI’s content cleaning features and the unique benefits of Fit Markdown, showing users how to retrieve focused, high-quality content from web pages.