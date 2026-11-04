import os
import asyncio
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai import LLMExtractionStrategy

class Product(BaseModel):
    name: str

async def main():
    llm_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv('OPENAI_API_KEY', 'dummy')),
        schema=Product.schema_json(),
        extraction_type="schema",
        instruction="Extract products."
    )
    crawl_config = CrawlerRunConfig(extraction_strategy=llm_strategy, cache_mode=CacheMode.ENABLED)
    
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        print("First run (caching)...")
        await crawler.arun(url="https://example.com", config=crawl_config)
        
        print("Second run (cache hit)...")
        result = await crawler.arun(url="https://example.com", config=crawl_config)
        
        if not result.extracted_content:
            print("Bug reproduced: extracted_content is empty on cache hit.")
        else:
            print("Fixed: extracted_content populated from cache.")

if __name__ == "__main__":
    asyncio.run(main())