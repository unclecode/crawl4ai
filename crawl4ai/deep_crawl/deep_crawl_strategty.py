from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

from ..models import CrawlResult


class DeepCrawlStrategy(ABC):
    @abstractmethod
    async def arun(
        self,
        url: str,
        crawler: "AsyncWebCrawler",
        crawler_run_config: Optional["CrawlerRunConfig"] = None,
    ) -> AsyncGenerator[CrawlResult, None]:
        """Traverse the given URL using the specified crawler.

        Args:
            url (str): The starting URL for the traversal.
            crawler (AsyncWebCrawler): The crawler instance to use for traversal.
            crawler_run_config (CrawlerRunConfig, optional): The configuration for the crawler.

        Returns:
            AsyncGenerator[CrawlResult, None]: An async generator yielding crawl results.
        """
        pass

    @abstractmethod
    async def shutdown(self):
        """Clean up resources used by the strategy"""
        pass
