import os
import sys
import asyncio
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.data_persistence_strategy import HFDataPersistenceStrategy

# Add the parent directory to the Python path
parent_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler


async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        schema = {
            "name": "News Teaser Extractor",
            "baseSelector": ".wide-tease-item__wrapper",
            "fields": [
                {
                    "name": "category",
                    "selector": ".unibrow span[data-testid='unibrow-text']",
                    "type": "text",
                },
                {
                    "name": "headline",
                    "selector": ".wide-tease-item__headline",
                    "type": "text",
                },
                {
                    "name": "summary",
                    "selector": ".wide-tease-item__description",
                    "type": "text",
                },
                {
                    "name": "link",
                    "selector": "a[href]",
                    "type": "attribute",
                    "attribute": "href",
                },
            ],
        }

        extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
        persistence_strategy = HFDataPersistenceStrategy(
            repo_id="crawl4ai_nbcnews_structured", private=False, verbose=True
        )

        result = await crawler.arun(
            url=url,
            bypass_cache=True,
            extraction_strategy=extraction_strategy,
            data_persistence_strategy=persistence_strategy,
        )
        if result.success:
            print(f"Successfully crawled: {result.url}")
            print(f"Persistence details: {result.storage_metadata}")
        else:
            print(f"Failed to crawl: {result.url}")
            print(f"Error: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())
