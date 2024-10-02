# File: async_webcrawler_multiple_urls_example.py
import os, sys
# append 2 parent directories to sys.path to import crawl4ai
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Initialize the AsyncWebCrawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        # List of URLs to crawl
        urls = [
            "https://example.com",
            "https://python.org",
            "https://github.com",
            "https://stackoverflow.com",
            "https://news.ycombinator.com"
        ]

        # Set up crawling parameters
        word_count_threshold = 100

        # Run the crawling process for multiple URLs
        results = await crawler.arun_many(
            urls=urls,
            word_count_threshold=word_count_threshold,
            bypass_cache=True,
            verbose=True
        )

        # Process the results
        for result in results:
            if result.success:
                print(f"Successfully crawled: {result.url}")
                print(f"Title: {result.metadata.get('title', 'N/A')}")
                print(f"Word count: {len(result.markdown.split())}")
                print(f"Number of links: {len(result.links.get('internal', [])) + len(result.links.get('external', []))}")
                print(f"Number of images: {len(result.media.get('images', []))}")
                print("---")
            else:
                print(f"Failed to crawl: {result.url}")
                print(f"Error: {result.error_message}")
                print("---")

if __name__ == "__main__":
    asyncio.run(main())