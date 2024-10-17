from .scraper_strategy import ScraperStrategy
from .models import ScraperResult, CrawlResult
from ..async_webcrawler import AsyncWebCrawler
from typing import Union, AsyncGenerator

class AsyncWebScraper:
    def __init__(self, crawler: AsyncWebCrawler, strategy: ScraperStrategy):
        self.crawler = crawler
        self.strategy = strategy

    async def ascrape(self, url: str, parallel_processing: bool = True, stream: bool = False) -> Union[AsyncGenerator[CrawlResult, None], ScraperResult]:
        if stream:
            return self._ascrape_yielding(url, parallel_processing)
        else:
            return await self._ascrape_collecting(url, parallel_processing)

    async def _ascrape_yielding(self, url: str, parallel_processing: bool) -> AsyncGenerator[CrawlResult, None]:
        result_generator = self.strategy.ascrape(url, self.crawler, parallel_processing)
        async for res in result_generator:  # Consume the async generator
            yield res  # Yielding individual results

    async def _ascrape_collecting(self, url: str, parallel_processing: bool) -> ScraperResult:
        extracted_data = {}
        result_generator = self.strategy.ascrape(url, self.crawler, parallel_processing)
        async for res in result_generator:  # Consume the async generator
            extracted_data[res.url] = res

        # Return a final ScraperResult
        return ScraperResult(
            url=url,
            crawled_urls=list(extracted_data.keys()),
            extracted_data=extracted_data
        )