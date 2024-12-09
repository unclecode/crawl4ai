import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.data_persistence_strategy import HFDataPersistenceStrategy


async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        persistence_strategy = HFDataPersistenceStrategy(
            repo_id="crawl4ai_hf_page_md", private=False, verbose=True
        )

        result = await crawler.arun(
            url="https://huggingface.co/",
            data_persistence_strategy=persistence_strategy,
        )

        print(f"Successfully crawled markdown: {result.markdown}")
        print(f"Persistence details: {result.storage_metadata}")


# Run the async main function
asyncio.run(main())
