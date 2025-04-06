import asyncio
from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    DefaultMarkdownGenerator,
    PruningContentFilter
)
from pipeline import Pipeline

async def main():
    # Create configuration objects
    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48, 
                threshold_type="fixed", 
                min_word_threshold=0
            )
        ),
    )
    
    # Create and use pipeline with context manager
    async with Pipeline(browser_config=browser_config) as pipeline:
        result = await pipeline.crawl(
            url="https://www.example.com", 
            config=crawler_config
        )
        
        # Print the result
        print(f"URL: {result.url}")
        print(f"Success: {result.success}")
        
        if result.success:
            print("\nMarkdown excerpt:")
            print(result.markdown.raw_markdown[:500] + "...")
        else:
            print(f"Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())


class CrawlTarget:
    def __init__(self, urls, config=None):
        self.urls = urls
        self.config = config

    def __repr__(self):
        return f"CrawlTarget(urls={self.urls}, config={self.config})"
    



# async def main():
#     # Create configuration objects
#     browser_config = BrowserConfig(headless=True, verbose=True)
    
#     # Define different configurations
#     config1 = CrawlerRunConfig(
#         cache_mode=CacheMode.BYPASS,
#         markdown_generator=DefaultMarkdownGenerator(
#             content_filter=PruningContentFilter(threshold=0.48)
#         ),
#     )
    
#     config2 = CrawlerRunConfig(
#         cache_mode=CacheMode.ENABLED,
#         screenshot=True,
#         pdf=True
#     )
    
#     # Create crawl targets
#     targets = [
#         CrawlTarget(
#             urls=["https://www.example.com", "https://www.wikipedia.org"],
#             config=config1
#         ),
#         CrawlTarget(
#             urls="https://news.ycombinator.com",  
#             config=config2
#         ),
#         CrawlTarget(
#             urls=["https://github.com", "https://stackoverflow.com", "https://python.org"],
#             config=None
#         )
#     ]
    
#     # Create and use pipeline with context manager
#     async with Pipeline(browser_config=browser_config) as pipeline:
#         all_results = await pipeline.crawl_batch(targets)
        
#         for target_key, results in all_results.items():
#             print(f"\n===== Results for {target_key} =====")
#             print(f"Number of URLs crawled: {len(results)}")
            
#             for i, result in enumerate(results):
#                 print(f"\nURL {i+1}: {result.url}")
#                 print(f"Success: {result.success}")
                
#                 if result.success:
#                     print(f"Content length: {len(result.markdown.raw_markdown)} chars")
#                 else:
#                     print(f"Error: {result.error_message}")

# if __name__ == "__main__":
#     asyncio.run(main())