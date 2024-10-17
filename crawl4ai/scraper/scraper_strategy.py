from abc import ABC, abstractmethod
from .models import ScraperResult, CrawlResult
from ..models import CrawlResult
from ..async_webcrawler import AsyncWebCrawler
from typing import Union, AsyncGenerator

class ScraperStrategy(ABC):
    @abstractmethod
    async def ascrape(self, url: str, crawler: AsyncWebCrawler, parallel_processing: bool = True, stream: bool = False) -> Union[AsyncGenerator[CrawlResult, None], ScraperResult]:
        """Scrape the given URL using the specified crawler.

        Args:
            url (str): The starting URL for the scrape.
            crawler (AsyncWebCrawler): The web crawler instance.
            parallel_processing (bool): Whether to use parallel processing. Defaults to True.
            stream (bool): If True, yields individual crawl results as they are ready; 
                                if False, accumulates results and returns a final ScraperResult.

        Yields:
            CrawlResult: Individual crawl results if stream is True.

        Returns:
            ScraperResult: A summary of the scrape results containing the final extracted data 
            and the list of crawled URLs if stream is False.
        """
        pass