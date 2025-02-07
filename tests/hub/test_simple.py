# test.py
from crawl4ai import CrawlerHub
import json

async def amazon_example():
    if (crawler_cls := CrawlerHub.get("amazon_product")) :
        crawler = crawler_cls()
        print(f"Crawler version: {crawler_cls.meta['version']}")
        print(f"Rate limits: {crawler_cls.meta.get('rate_limit', 'Unlimited')}")
        print(await crawler.run("https://amazon.com/test"))
    else:
        print("Crawler not found!")

async def google_example():
    # Get crawler dynamically
    crawler_cls = CrawlerHub.get("google_search")
    crawler = crawler_cls()

    # Text search
    text_results = await crawler.run(
        query="apple inc", 
        search_type="text",  
        schema_cache_path="/Users/unclecode/.crawl4ai"
    )
    print(json.dumps(json.loads(text_results), indent=4))

    # Image search
    # image_results = await crawler.run(query="apple inc", search_type="image")
    # print(image_results)

if __name__ == "__main__":
    import asyncio
    # asyncio.run(amazon_example())
    asyncio.run(google_example())