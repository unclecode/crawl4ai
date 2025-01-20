from typing import Union, AsyncGenerator, Optional
from .scraper_strategy import ScraperStrategy
from .models import ScraperResult, CrawlResult
from ..async_webcrawler import AsyncWebCrawler
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager

@dataclass
class ScrapingProgress:
    """Tracks the progress of a scraping operation."""
    processed_urls: int = 0
    failed_urls: int = 0
    current_url: Optional[str] = None

class AsyncWebScraper:
    """
    A high-level web scraper that combines an async crawler with a scraping strategy.
    
    Args:
        crawler (AsyncWebCrawler): The async web crawler implementation
        strategy (ScraperStrategy): The scraping strategy to use
        logger (Optional[logging.Logger]): Custom logger for the scraper
    """
    
    def __init__(
        self, 
        crawler: AsyncWebCrawler, 
        strategy: ScraperStrategy,
        logger: Optional[logging.Logger] = None
    ):
        if not isinstance(crawler, AsyncWebCrawler):
            raise TypeError("crawler must be an instance of AsyncWebCrawler")
        if not isinstance(strategy, ScraperStrategy):
            raise TypeError("strategy must be an instance of ScraperStrategy")
            
        self.crawler = crawler
        self.strategy = strategy
        self.logger = logger or logging.getLogger(__name__)
        self._progress = ScrapingProgress()

    @property
    def progress(self) -> ScrapingProgress:
        """Get current scraping progress."""
        return self._progress

    @asynccontextmanager
    async def _error_handling_context(self, url: str):
        """Context manager for handling errors during scraping."""
        try:
            yield
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            self._progress.failed_urls += 1
            raise

    async def ascrape(
        self, 
        url: str, 
        parallel_processing: bool = True, 
        stream: bool = False
    ) -> Union[AsyncGenerator[CrawlResult, None], ScraperResult]:
        """
        Scrape a website starting from the given URL.
        
        Args:
            url: Starting URL for scraping
            parallel_processing: Whether to process URLs in parallel
            stream: If True, yield results as they come; if False, collect all results
            
        Returns:
            Either an async generator yielding CrawlResults or a final ScraperResult
        """
        self._progress = ScrapingProgress()  # Reset progress
        
        async with self._error_handling_context(url):
            if stream:
                return self._ascrape_yielding(url, parallel_processing)
            return await self._ascrape_collecting(url, parallel_processing)

    async def _ascrape_yielding(
        self, 
        url: str, 
        parallel_processing: bool
    ) -> AsyncGenerator[CrawlResult, None]:
        """Stream scraping results as they become available."""
        try:
            result_generator = self.strategy.ascrape(url, self.crawler, parallel_processing)
            async for res in result_generator:
                self._progress.processed_urls += 1
                self._progress.current_url = res.url
                yield res
        except Exception as e:
            self.logger.error(f"Error in streaming scrape: {str(e)}")
            raise

    async def _ascrape_collecting(
        self, 
        url: str, 
        parallel_processing: bool
    ) -> ScraperResult:
        """Collect all scraping results before returning."""
        extracted_data = {}
        
        try:
            result_generator = self.strategy.ascrape(url, self.crawler, parallel_processing)
            async for res in result_generator:
                self._progress.processed_urls += 1
                self._progress.current_url = res.url
                extracted_data[res.url] = res
                
            return ScraperResult(
                url=url,
                crawled_urls=list(extracted_data.keys()),
                extracted_data=extracted_data,
                stats={
                    'processed_urls': self._progress.processed_urls,
                    'failed_urls': self._progress.failed_urls
                }
            )
        except Exception as e:
            self.logger.error(f"Error in collecting scrape: {str(e)}")
            raise