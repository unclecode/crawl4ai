import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    CrawlResult
)

                   

async def main():    
    browser_config = BrowserConfig(
        headless=False, 
        verbose=True,
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            session_id= "hello_world", # This help us to use the same page 
        )
        result : CrawlResult = await crawler.arun(
            url="https://www.helloworld.org", config=crawler_config
        )
        # Add a breakpoint here, then you will the page is open and browser is not closed
        print(result.markdown.raw_markdown[:500])
        
        new_config = crawler_config.clone(js_code=["(() => ({'data':'hello'}))()"], js_only=True)
        result : CrawlResult = await crawler.arun( # This time there is no fetch and this only executes JS in the same opened page
            url="https://www.helloworld.org", config= new_config
        )
        print(result.js_execution_result) # You should see {'data':'hello'} in the console
        
        # Get direct access to Playwright paege object. This works only if you use the same session_id and pass same config 
        page, context = crawler.crawler_strategy.get_page(new_config)

if __name__ == "__main__":
    asyncio.run(main())
