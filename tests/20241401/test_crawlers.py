
# example_usageexample_usageexample_usage# example_usage.py
import asyncio
from crawl4ai.crawlers import get_crawler

async def main():
    # Get the registered crawler
    example_crawler = get_crawler("example_site.content")
    
    # Crawl example.com
    result = await example_crawler(url="https://example.com")
        
    print(result)
            

if __name__ == "__main__":
    asyncio.run(main())