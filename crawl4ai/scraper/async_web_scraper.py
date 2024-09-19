import asyncio
from typing import List, Dict
from .scraper_strategy import ScraperStrategy
from .bfs_scraper_strategy import BFSScraperStrategy
from .models import ScraperResult
from ..async_webcrawler import AsyncWebCrawler

class BatchProcessor:
    def __init__(self, batch_size: int, concurrency_limit: int):
        self.batch_size = batch_size
        self.concurrency_limit = concurrency_limit

    async def process_batch(self, scraper: 'AsyncWebScraper', urls: List[str]) -> List[ScraperResult]:
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        async def scrape_with_semaphore(url):
            async with semaphore:
                return await scraper.ascrape(url)
        return await asyncio.gather(*[scrape_with_semaphore(url) for url in urls])

class AsyncWebScraper:
    def __init__(self, crawler: AsyncWebCrawler, strategy: ScraperStrategy, batch_size: int = 10, concurrency_limit: int = 5):
        self.crawler = crawler
        self.strategy = strategy
        self.batch_processor = BatchProcessor(batch_size, concurrency_limit)

    async def ascrape(self, url: str) -> ScraperResult:
        return await self.strategy.ascrape(url, self.crawler)

    async def ascrape_many(self, urls: List[str]) -> List[ScraperResult]:
        all_results = []
        for i in range(0, len(urls), self.batch_processor.batch_size):
            batch = urls[i:i+self.batch_processor.batch_size]
            batch_results = await self.batch_processor.process_batch(self, batch)
            all_results.extend(batch_results)
        return all_results