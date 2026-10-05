import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Enable robots.txt checking
    config = CrawlerRunConfig(check_robots_txt=True)
    
    async with AsyncWebCrawler() as crawler:
        # The path /awardsearch/advancedSearch.jsp is disallowed in nsf.gov/robots.txt
        url = "https://www.nsf.gov/awardsearch/advancedSearch.jsp"
        result = await crawler.arun(url=url, config=config)
        
        if result.success:
            print(f"Bug reproduced: Successfully crawled {url} despite robots.txt disallow.")
        else:
            print(f"Fixed/Expected behavior: Blocked from crawling. Message: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
    