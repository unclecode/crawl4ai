import asyncio
import os
from pathlib import Path
import aiohttp
import json
from crawl4ai import AsyncWebCrawler
from crawl4ai.content_filter_strategy import BM25ContentFilter

# 1. File Download Processing Example
async def download_example():
    """Example of downloading files from Python.org"""
    # downloads_path = os.path.join(os.getcwd(), "downloads")
    downloads_path = os.path.join(Path.home(), ".crawl4ai", "downloads")
    os.makedirs(downloads_path, exist_ok=True)
    
    print(f"Downloads will be saved to: {downloads_path}")
    
    async with AsyncWebCrawler(
        accept_downloads=True,
        downloads_path=downloads_path,
        verbose=True
    ) as crawler:
        result = await crawler.arun(
            url="https://www.python.org/downloads/",
            js_code="""
            // Find and click the first Windows installer link
            const downloadLink = document.querySelector('a[href$=".exe"]');
            if (downloadLink) {
                console.log('Found download link:', downloadLink.href);
                downloadLink.click();
            } else {
                console.log('No .exe download link found');
            }
            """,
            wait_for=5  # Wait 5 seconds to ensure download starts
        )
        
        if result.downloaded_files:
            print("\nDownload successful!")
            print("Downloaded files:")
            for file_path in result.downloaded_files:
                print(f"- {file_path}")
                print(f"  File size: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
        else:
            print("\nNo files were downloaded")

# 2. Content Filtering with BM25 Example
async def content_filtering_example():
    """Example of using the new BM25 content filtering"""
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Create filter with custom query for OpenAI's blog
        content_filter = BM25ContentFilter(
            user_query="AI language models research innovation",
            bm25_threshold=1.0
        )
        
        result = await crawler.arun(
            url="https://openai.com/blog",
            extraction_strategy=content_filter
        )
        
        print(f"Filtered content: {result.extracted_content}")

# 3. Local File and Raw HTML Processing Example
async def local_and_raw_html_example():
    """Example of processing local files and raw HTML"""
    # Create a sample HTML file
    sample_file = "sample.html"
    with open(sample_file, "w") as f:
        f.write("""
        <html><body>
            <h1>Test Content</h1>
            <p>This is a test paragraph.</p>
        </body></html>
        """)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Process local file
        local_result = await crawler.arun(
            url=f"file://{os.path.abspath(sample_file)}"
        )
        
        # Process raw HTML
        raw_html = """
        <html><body>
            <h1>Raw HTML Test</h1>
            <p>This is a test of raw HTML processing.</p>
        </body></html>
        """
        raw_result = await crawler.arun(
            url=f"raw:{raw_html}"
        )
        
        # Clean up
        os.remove(sample_file)
        
        print("Local file content:", local_result.markdown)
        print("\nRaw HTML content:", raw_result.markdown)

# 4. Browser Management Example
async def browser_management_example():
    """Example of using enhanced browser management features"""
    # Use the specified user directory path
    user_data_dir = os.path.join(Path.home(), ".crawl4ai", "browser_profile")
    os.makedirs(user_data_dir, exist_ok=True)
    
    print(f"Browser profile will be saved to: {user_data_dir}")
    
    async with AsyncWebCrawler(
        use_managed_browser=True,
        user_data_dir=user_data_dir,
        headless=False,
        verbose=True
    ) as crawler:
        # Use GitHub as an example - it's a good test for browser management
        # because it requires proper browser handling
        result = await crawler.arun(
            url="https://github.com/trending",
            session_id="persistent_session_1",
            js_code="""
            // Custom JavaScript to execute on GitHub's trending page
            const repos = document.querySelectorAll('article.Box-row');
            const data = Array.from(repos).map(repo => ({
                name: repo.querySelector('h2')?.textContent?.trim(),
                description: repo.querySelector('p')?.textContent?.trim(),
                language: repo.querySelector('[itemprop="programmingLanguage"]')?.textContent?.trim()
            }));
            console.log('Trending repositories:', JSON.stringify(data, null, 2));
            """
        )
        
        print("\nBrowser session result:", result.success)
        if result.success:
            print("Page title:", result.metadata.get('title', 'No title found'))

# 5. API Usage Example
async def api_example():
    """Example of using the new API endpoints"""
    async with aiohttp.ClientSession() as session:
        # Submit crawl job
        crawl_request = {
            "urls": ["https://news.ycombinator.com"],  # Hacker News as an example
            "extraction_config": {
                "type": "json_css",
                "params": {
                    "selectors": {
                        "titles": ".title a",
                        "scores": ".score",
                        "comments": ".comment-tree"
                    }
                }
            },
            "crawler_params": {
                "headless": True,
                "use_managed_browser": True
            },
            "screenshot": True,
            "magic": True
        }
        
        async with session.post(
            "http://localhost:11235/crawl",
            json=crawl_request
        ) as response:
            task_data = await response.json()
            task_id = task_data["task_id"]
            
            # Check task status
            async with session.get(
                f"http://localhost:11235/task/{task_id}"
            ) as status_response:
                result = await status_response.json()
                print(f"Task result: {result}")

# Main execution
async def main():
    print("Running Crawl4AI feature examples...")
    
    print("\n1. Running Download Example:")
    await download_example()
    
    print("\n2. Running Content Filtering Example:")
    await content_filtering_example()
    
    print("\n3. Running Local and Raw HTML Example:")
    await local_and_raw_html_example()
    
    print("\n4. Running Browser Management Example:")
    await browser_management_example()
    
    print("\n5. Running API Example:")
    await api_example()

if __name__ == "__main__":
    asyncio.run(main())