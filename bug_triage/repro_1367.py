import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    # Bug often triggers with persistent contexts and multiple concurrent navigations
    browser_cfg = BrowserConfig(headless=True, use_persistent_context=True)
    crawl_config = CrawlerRunConfig(wait_until="networkidle")
    
    urls = ["https://example.com", "https://example.org", "https://example.net"]
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        print("Running async crawls to trigger ERR_ABORTED race condition...")
        results = await crawler.arun_many(urls=urls, config=crawl_config)
        
        reproduced = False
        for res in results:
            if not res.success and "ERR_ABORTED" in str(res.error_message):
                print(f"Bug reproduced on {res.url}: {res.error_message}")
                reproduced = True
                
        if not reproduced:
            print("Fixed or unable to reproduce: No ERR_ABORTED errors encountered.")

if __name__ == "__main__":
    asyncio.run(main())