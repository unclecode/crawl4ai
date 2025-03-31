from __future__ import annotations

from abc import ABC, abstractmethod
from contextvars import ContextVar
from functools import wraps
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Set, Awaitable
from typing_extensions import Concatenate

from ..types import AsyncWebCrawler, CrawlerRunConfig, CrawlResult
from ..models import CrawlResultContainer

class DeepCrawlDecorator:
    """Decorator that adds deep crawling capability to arun method."""
    deep_crawl_active = ContextVar("deep_crawl_active", default=False)
    
    def __init__(self, crawler: AsyncWebCrawler): 
        self.crawler = crawler

    def __call__(self, original_arun: Callable[Concatenate[str, Optional[CrawlerRunConfig], ...], Awaitable[CrawlResultContainer]]):
        @wraps(original_arun)
        async def wrapped_arun(
            url: str, config: Optional[CrawlerRunConfig] = None, **kwargs
        ) -> CrawlResultContainer:
            # If deep crawling is already active, call the original method to avoid recursion.
            if config and config.deep_crawl_strategy and not self.deep_crawl_active.get():
                token = self.deep_crawl_active.set(True)
                # Await the arun call to get the actual result object.
                result_obj: CrawlResultContainer = await config.deep_crawl_strategy.arun(
                    crawler=self.crawler,
                    start_url=url,
                    config=config
                )
                if config.stream:
                    # Streaming mode.
                    async def result_wrapper() -> AsyncGenerator[CrawlResult, Any]:
                        try:
                            async for result in result_obj:
                                yield result
                        finally:
                            self.deep_crawl_active.reset(token)
                    return CrawlResultContainer(result_wrapper())

                # Batch mode.
                try:
                    return result_obj
                finally:
                    self.deep_crawl_active.reset(token)

            return await original_arun(url, config, **kwargs)
        return wrapped_arun

class DeepCrawlStrategy(ABC):
    """
    Abstract base class for deep crawling strategies.
    
    Core functions:
      - arun: Main entry point that returns an async generator of CrawlResults.
      - shutdown: Clean up resources.
      - can_process_url: Validate a URL and decide whether to process it.
      - _process_links: Extract and process links from a CrawlResult.
    """

    @abstractmethod
    async def _arun_batch(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> List[CrawlResult]:
        """
        Batch (non-streaming) mode:
        Processes one BFS level at a time, then yields all the results.
        """
        pass

    # Not async because it returns an AsyncGenerator but does not yield.
    # See the following issue from pyright for more information:
    # https://github.com/microsoft/pyright/issues/9949
    @abstractmethod
    def _arun_stream(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        Streaming mode:
        Processes one BFS level at a time and yields results immediately as they arrive.
        """
        pass
    
    async def arun(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: Optional[CrawlerRunConfig] = None,
    ) -> CrawlResultContainer:
        """
        Traverse the given URL using the specified crawler.
        
        Args:
            start_url (str): The URL from which to start crawling.
            crawler (AsyncWebCrawler): The crawler instance to use.
            crawler_run_config (Optional[CrawlerRunConfig]): Crawler configuration.
        
        Returns:
            CrawlResultContainer
        """
        if config is None:
            raise ValueError("CrawlerRunConfig must be provided")

        if config.stream:
            return CrawlResultContainer(self._arun_stream(start_url, crawler, config))

        return CrawlResultContainer(await self._arun_batch(start_url, crawler, config))

    def __call__(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig):
        return self.arun(start_url, crawler, config)

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Clean up resources used by the deep crawl strategy.
        """
        pass

    @abstractmethod
    async def can_process_url(self, url: str, depth: int) -> bool:
        """
        Validate the URL format and apply custom filtering logic.
        
        Args:
            url (str): The URL to validate.
            depth (int): The current depth in the crawl.
        
        Returns:
            bool: True if the URL should be processed, False otherwise.
        """
        pass

    @abstractmethod
    async def link_discovery(
        self,
        result: CrawlResult,
        source_url: str,
        current_depth: int,
        visited: Set[str],
        next_level: List[tuple],
        depths: Dict[str, int],
    ) -> None:
        """
        Extract and process links from the given crawl result.
        
        This method should:
          - Validate each extracted URL using can_process_url.
          - Optionally score URLs.
          - Append valid URLs (and their parent references) to the next_level list.
          - Update the depths dictionary with the new depth for each URL.
        
        Args:
            result (CrawlResult): The result from a crawl operation.
            source_url (str): The URL from which this result was obtained.
            current_depth (int): The depth at which the source URL was processed.
            visited (Set[str]): Set of already visited URLs.
            next_level (List[tuple]): List of tuples (url, parent_url) for the next BFS level.
            depths (Dict[str, int]): Mapping of URLs to their current depth.
        """
        pass

