from abc import ABC, abstractmethod
from .models import ScraperResult, ScraperPageResult
from ..async_configs import BrowserConfig, CrawlerRunConfig
from typing import Union, AsyncGenerator
class ScraperStrategy(ABC):
    @abstractmethod
    async def ascrape(
        self,
        url: str,
        crawler_config: CrawlerRunConfig,
        browser_config: BrowserConfig,
        stream: bool = False,
    ) -> Union[AsyncGenerator[ScraperPageResult, None], ScraperResult]:
        """Scrape the given URL using the specified crawler.

        Args:
            url (str): The starting URL for the scrape.
            crawler_config (CrawlerRunConfig): Configuration for the crawler run.
            browser_config (BrowserConfig): Configuration for the browser.
            stream (bool): If True, yields individual crawl results as they are ready;
                                if False, accumulates results and returns a final ScraperResult.

        Yields:
            ScraperPageResult: Individual page results if stream is True.

        Returns:
            ScraperResult: A summary of the scrape results containing the final extracted data
            and the list of crawled URLs if stream is False.
        """
        pass

    @abstractmethod
    async def can_process_url(self, url: str, depth: int) -> bool:
        """Check if URL can be processed based on strategy rules"""
        pass

    @abstractmethod
    async def shutdown(self):
        """Clean up resources used by the strategy"""
        pass
