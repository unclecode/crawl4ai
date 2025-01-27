from typing import Union, AsyncGenerator, Optional
from .scraper_strategy import ScraperStrategy
from .models import ScraperResult, CrawlResult
from ..async_configs import BrowserConfig, CrawlerRunConfig
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager
from contextlib import AbstractAsyncContextManager


@dataclass
class ScrapingProgress:
    """Tracks the progress of a scraping operation."""

    processed_urls: int = 0
    failed_urls: int = 0
    current_url: Optional[str] = None


class AsyncWebScraper(AbstractAsyncContextManager):
    """
    A high-level web scraper that combines an async crawler with a scraping strategy.

    Args:
        crawler_config (CrawlerRunConfig): Configuration for the crawler run
        browser_config (BrowserConfig): Configuration for the browser
        strategy (ScraperStrategy): The scraping strategy to use
        logger (Optional[logging.Logger]): Custom logger for the scraper
    """

    async def __aenter__(self):
        # Initialize resources, if any
        self.logger.info("Starting the async web scraper.")
        return self

    def __init__(
        self,
        crawler_config: CrawlerRunConfig,
        browser_config: BrowserConfig,
        strategy: ScraperStrategy,
        logger: Optional[logging.Logger] = None,
    ):
        if not isinstance(browser_config, BrowserConfig):
            raise TypeError("browser_config must be an instance of BrowserConfig")
        if not isinstance(crawler_config, CrawlerRunConfig):
            raise TypeError("crawler must be an instance of CrawlerRunConfig")
        if not isinstance(strategy, ScraperStrategy):
            raise TypeError("strategy must be an instance of ScraperStrategy")

        self.crawler_config = crawler_config
        self.browser_config = browser_config
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
        self, url: str, stream: bool = False
    ) -> Union[AsyncGenerator[CrawlResult, None], ScraperResult]:
        """
        Scrape a website starting from the given URL.

        Args:
            url: Starting URL for scraping
            stream: If True, yield results as they come; if False, collect all results

        Returns:
            Either an async generator yielding CrawlResults or a final ScraperResult
        """
        self._progress = ScrapingProgress()  # Reset progress

        async with self._error_handling_context(url):
            if stream:
                return self._ascrape_yielding(url)
            return await self._ascrape_collecting(url)

    async def _ascrape_yielding(
        self,
        url: str,
    ) -> AsyncGenerator[CrawlResult, None]:
        """Stream scraping results as they become available."""
        try:
            result_generator = self.strategy.ascrape(
                url, self.crawler_config, self.browser_config
            )
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
    ) -> ScraperResult:
        """Collect all scraping results before returning."""
        extracted_data = {}

        try:
            result_generator = self.strategy.ascrape(
                url, self.crawler_config, self.browser_config
            )
            async for res in result_generator:
                self._progress.processed_urls += 1
                self._progress.current_url = res.url
                extracted_data[res.url] = res

            return ScraperResult(
                url=url,
                crawled_urls=list(extracted_data.keys()),
                extracted_data=extracted_data,
                stats={
                    "processed_urls": self._progress.processed_urls,
                    "failed_urls": self._progress.failed_urls,
                },
            )
        except Exception as e:
            self.logger.error(f"Error in collecting scrape: {str(e)}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup resources or tasks
        await self.close()  # Assuming you have a close method to cleanup

    async def close(self):
        # Perform cleanup tasks
        pass
