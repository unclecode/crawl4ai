import asyncio
from crawl4ai import AsyncWebCrawler, AsyncPlaywrightCrawlerStrategy

async def main():
    # Example 1: Setting language when creating the crawler
    crawler1 = AsyncWebCrawler(
        crawler_strategy=AsyncPlaywrightCrawlerStrategy(
            headers={"Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"}
        )
    )
    result1 = await crawler1.arun("https://www.example.com")
    print("Example 1 result:", result1.extracted_content[:100])  # Print first 100 characters

    # Example 2: Setting language before crawling
    crawler2 = AsyncWebCrawler()
    crawler2.crawler_strategy.headers["Accept-Language"] = "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7"
    result2 = await crawler2.arun("https://www.example.com")
    print("Example 2 result:", result2.extracted_content[:100])

    # Example 3: Setting language when calling arun method
    crawler3 = AsyncWebCrawler()
    result3 = await crawler3.arun(
        "https://www.example.com",
        headers={"Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"}
    )
    print("Example 3 result:", result3.extracted_content[:100])

    # Example 4: Crawling multiple pages with different languages
    urls = [
        ("https://www.example.com", "fr-FR,fr;q=0.9"),
        ("https://www.example.org", "es-ES,es;q=0.9"),
        ("https://www.example.net", "de-DE,de;q=0.9"),
    ]
    
    crawler4 = AsyncWebCrawler()
    results = await asyncio.gather(*[
        crawler4.arun(url, headers={"Accept-Language": lang})
        for url, lang in urls
    ])
    
    for url, result in zip([u for u, _ in urls], results):
        print(f"Result for {url}:", result.extracted_content[:100])

if __name__ == "__main__":
    asyncio.run(main())