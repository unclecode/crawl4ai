from abc import ABC, abstractmethod
from typing import AsyncGenerator

from ..async_configs import CrawlerRunConfig
from ..models import CrawlResult


class TraversalStrategy(ABC):
    @abstractmethod
    async def deep_crawl(
        self,
        url: str,
        crawler: "AsyncWebCrawler",
        crawler_run_config: CrawlerRunConfig = None,
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
