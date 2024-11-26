# Prefix-Based Input Handling in Crawl4AI

This guide will walk you through using the Crawl4AI library to crawl web pages, local HTML files, and raw HTML strings. We'll demonstrate these capabilities using a Wikipedia page as an example.

## Table of Contents
- [Prefix-Based Input Handling in Crawl4AI](#prefix-based-input-handling-in-crawl4ai)
  - [Table of Contents](#table-of-contents)
    - [Crawling a Web URL](#crawling-a-web-url)
    - [Crawling a Local HTML File](#crawling-a-local-html-file)
    - [Crawling Raw HTML Content](#crawling-raw-html-content)
  - [Complete Example](#complete-example)
    - [**How It Works**](#how-it-works)
    - [**Running the Example**](#running-the-example)
  - [Conclusion](#conclusion)

---


### Crawling a Web URL

To crawl a live web page, provide the URL starting with `http://` or `https://`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def crawl_web():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://en.wikipedia.org/wiki/apple", bypass_cache=True)
        if result.success:
            print("Markdown Content:")
            print(result.markdown)
        else:
            print(f"Failed to crawl: {result.error_message}")

asyncio.run(crawl_web())
```

### Crawling a Local HTML File

To crawl a local HTML file, prefix the file path with `file://`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def crawl_local_file():
    local_file_path = "/path/to/apple.html"  # Replace with your file path
    file_url = f"file://{local_file_path}"
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=file_url, bypass_cache=True)
        if result.success:
            print("Markdown Content from Local File:")
            print(result.markdown)
        else:
            print(f"Failed to crawl local file: {result.error_message}")

asyncio.run(crawl_local_file())
```

### Crawling Raw HTML Content

To crawl raw HTML content, prefix the HTML string with `raw:`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def crawl_raw_html():
    raw_html = "<html><body><h1>Hello, World!</h1></body></html>"
    raw_html_url = f"raw:{raw_html}"
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=raw_html_url, bypass_cache=True)
        if result.success:
            print("Markdown Content from Raw HTML:")
            print(result.markdown)
        else:
            print(f"Failed to crawl raw HTML: {result.error_message}")

asyncio.run(crawl_raw_html())
```

---

## Complete Example

Below is a comprehensive script that:
1. **Crawls the Wikipedia page for "Apple".**
2. **Saves the HTML content to a local file (`apple.html`).**
3. **Crawls the local HTML file and verifies the markdown length matches the original crawl.**
4. **Crawls the raw HTML content from the saved file and verifies consistency.**

```python
import os
import sys
import asyncio
from pathlib import Path

# Adjust the parent directory to include the crawl4ai module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai import AsyncWebCrawler

async def main():
    # Define the URL to crawl
    wikipedia_url = "https://en.wikipedia.org/wiki/apple"
    
    # Define the path to save the HTML file
    # Save the file in the same directory as the script
    script_dir = Path(__file__).parent
    html_file_path = script_dir / "apple.html"
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        print("\n=== Step 1: Crawling the Wikipedia URL ===")
        # Crawl the Wikipedia URL
        result = await crawler.arun(url=wikipedia_url, bypass_cache=True)
        
        # Check if crawling was successful
        if not result.success:
            print(f"Failed to crawl {wikipedia_url}: {result.error_message}")
            return
        
        # Save the HTML content to a local file
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(result.html)
        print(f"Saved HTML content to {html_file_path}")
        
        # Store the length of the generated markdown
        web_crawl_length = len(result.markdown)
        print(f"Length of markdown from web crawl: {web_crawl_length}\n")
        
        print("=== Step 2: Crawling from the Local HTML File ===")
        # Construct the file URL with 'file://' prefix
        file_url = f"file://{html_file_path.resolve()}"
        
        # Crawl the local HTML file
        local_result = await crawler.arun(url=file_url, bypass_cache=True)
        
        # Check if crawling was successful
        if not local_result.success:
            print(f"Failed to crawl local file {file_url}: {local_result.error_message}")
            return
        
        # Store the length of the generated markdown from local file
        local_crawl_length = len(local_result.markdown)
        print(f"Length of markdown from local file crawl: {local_crawl_length}")
        
        # Compare the lengths
        assert web_crawl_length == local_crawl_length, (
            f"Markdown length mismatch: Web crawl ({web_crawl_length}) != Local file crawl ({local_crawl_length})"
        )
        print("✅ Markdown length matches between web crawl and local file crawl.\n")
        
        print("=== Step 3: Crawling Using Raw HTML Content ===")
        # Read the HTML content from the saved file
        with open(html_file_path, 'r', encoding='utf-8') as f:
            raw_html_content = f.read()
        
        # Prefix the raw HTML content with 'raw:'
        raw_html_url = f"raw:{raw_html_content}"
        
        # Crawl using the raw HTML content
        raw_result = await crawler.arun(url=raw_html_url, bypass_cache=True)
        
        # Check if crawling was successful
        if not raw_result.success:
            print(f"Failed to crawl raw HTML content: {raw_result.error_message}")
            return
        
        # Store the length of the generated markdown from raw HTML
        raw_crawl_length = len(raw_result.markdown)
        print(f"Length of markdown from raw HTML crawl: {raw_crawl_length}")
        
        # Compare the lengths
        assert web_crawl_length == raw_crawl_length, (
            f"Markdown length mismatch: Web crawl ({web_crawl_length}) != Raw HTML crawl ({raw_crawl_length})"
        )
        print("✅ Markdown length matches between web crawl and raw HTML crawl.\n")
        
        print("All tests passed successfully!")
        
    # Clean up by removing the saved HTML file
    if html_file_path.exists():
        os.remove(html_file_path)
        print(f"Removed the saved HTML file: {html_file_path}")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
```

### **How It Works**

1. **Step 1: Crawl the Web URL**
   - Crawls `https://en.wikipedia.org/wiki/apple`.
   - Saves the HTML content to `apple.html`.
   - Records the length of the generated markdown.

2. **Step 2: Crawl from the Local HTML File**
   - Uses the `file://` prefix to crawl `apple.html`.
   - Ensures the markdown length matches the original web crawl.

3. **Step 3: Crawl Using Raw HTML Content**
   - Reads the HTML from `apple.html`.
   - Prefixes it with `raw:` and crawls.
   - Verifies the markdown length matches the previous results.

4. **Cleanup**
   - Deletes the `apple.html` file after testing.

### **Running the Example**

1. **Save the Script:**
   - Save the above code as `test_crawl4ai.py` in your project directory.

2. **Execute the Script:**
   - Run the script using:
     ```bash
     python test_crawl4ai.py
     ```

3. **Observe the Output:**
   - The script will print logs detailing each step.
   - Assertions ensure consistency across different crawling methods.
   - Upon success, it confirms that all markdown lengths match.

---

## Conclusion

With the new prefix-based input handling in **Crawl4AI**, you can effortlessly crawl web URLs, local HTML files, and raw HTML strings using a unified `url` parameter. This enhancement simplifies the API usage and provides greater flexibility for diverse crawling scenarios.

