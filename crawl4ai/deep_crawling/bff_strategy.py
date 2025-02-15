# best_first_crawling_strategy.py
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Set, Dict, List, Tuple
from urllib.parse import urlparse

from ..models import TraversalStats
from .filters import FilterChain
from .scorers import URLScorer
from . import DeepCrawlStrategy

from ..types import AsyncWebCrawler, CrawlerRunConfig, CrawlResult, RunManyReturn


# Configurable batch size for processing items from the priority queue
BATCH_SIZE = 10


class BestFirstCrawlingStrategy(DeepCrawlStrategy):
    """
    Best-First Crawling Strategy using a priority queue.
    
    This strategy prioritizes URLs based on their score, ensuring that higher-value
    pages are crawled first. It reimplements the core traversal loop to use a priority
    queue while keeping URL validation and link discovery consistent with our design.
    
    Core methods:
      - arun: Returns either a list (batch mode) or an async generator (stream mode).
      - _arun_best_first: Core generator that uses a priority queue to yield CrawlResults.
      - can_process_url: Validates URLs and applies filtering (inherited behavior).
      - link_discovery: Extracts and validates links from a CrawlResult.
    """
    def __init__(
        self,
        max_depth: int,
        filter_chain: FilterChain = FilterChain(),
        url_scorer: Optional[URLScorer] = None,
        include_external: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self.max_depth = max_depth
        self.filter_chain = filter_chain
        self.url_scorer = url_scorer
        self.include_external = include_external
        self.logger = logger or logging.getLogger(__name__)
        self.stats = TraversalStats(start_time=datetime.now())
        self._cancel_event = asyncio.Event()

    async def can_process_url(self, url: str, depth: int) -> bool:
        """
        Validate the URL format and apply filtering.
        For the starting URL (depth 0), filtering is bypassed.
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Missing scheme or netloc")
            if parsed.scheme not in ("http", "https"):
                raise ValueError("Invalid scheme")
            if "." not in parsed.netloc:
                raise ValueError("Invalid domain")
        except Exception as e:
            self.logger.warning(f"Invalid URL: {url}, error: {e}")
            return False

        if depth != 0 and not self.filter_chain.apply(url):
            return False

        return True

    async def link_discovery(
        self,
        result: CrawlResult,
        source_url: str,
        current_depth: int,
        visited: Set[str],
        next_links: List[Tuple[str, Optional[str]]],
        depths: Dict[str, int],
    ) -> None:
        """
        Extract links from the crawl result, validate them, and append new URLs
        (with their parent references) to next_links.
        Also updates the depths dictionary.
        """
        new_depth = current_depth + 1
        if new_depth > self.max_depth:
            return

        # Retrieve internal links; include external links if enabled.
        links = result.links.get("internal", [])
        if self.include_external:
            links += result.links.get("external", [])

        for link in links:
            url = link.get("href")
            if url in visited:
                continue
            if not await self.can_process_url(url, new_depth):
                self.stats.urls_skipped += 1
                continue

            # Record the new depth.
            depths[url] = new_depth
            next_links.append((url, source_url))

    async def _arun_best_first(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        Core best-first crawl method using a priority queue.
        
        The queue items are tuples of (score, depth, url, parent_url). Lower scores
        are treated as higher priority. URLs are processed in batches for efficiency.
        """
        queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        # Push the initial URL with score 0 and depth 0.
        await queue.put((0, 0, start_url, None))
        visited: Set[str] = set()
        depths: Dict[str, int] = {start_url: 0}

        while not queue.empty() and not self._cancel_event.is_set():
            batch: List[Tuple[float, int, str, Optional[str]]] = []
            # Retrieve up to BATCH_SIZE items from the priority queue.
            for _ in range(BATCH_SIZE):
                if queue.empty():
                    break
                item = await queue.get()
                score, depth, url, parent_url = item
                if url in visited:
                    continue
                visited.add(url)
                batch.append(item)

            if not batch:
                continue

            # Process the current batch of URLs.
            urls = [item[2] for item in batch]
            batch_config = config.clone(deep_crawl_strategy=None, stream=True)
            stream_gen = await crawler.arun_many(urls=urls, config=batch_config)
            async for result in stream_gen:
                result_url = result.url
                # Find the corresponding tuple from the batch.
                corresponding = next((item for item in batch if item[2] == result_url), None)
                if not corresponding:
                    continue
                score, depth, url, parent_url = corresponding
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                result.metadata["parent_url"] = parent_url
                result.metadata["score"] = score
                yield result
                # Discover new links from this result.
                new_links: List[Tuple[str, Optional[str]]] = []
                await self.link_discovery(result, result_url, depth, visited, new_links, depths)
                for new_url, new_parent in new_links:
                    new_depth = depths.get(new_url, depth + 1)
                    new_score = self.url_scorer.score(new_url) if self.url_scorer else 0
                    await queue.put((new_score, new_depth, new_url, new_parent))

        # End of crawl.

    async def _arun_batch(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> List[CrawlResult]:
        """
        Best-first crawl in batch mode.
        
        Aggregates all CrawlResults into a list.
        """
        results: List[CrawlResult] = []
        async for result in self._arun_best_first(start_url, crawler, config):
            results.append(result)
        return results

    async def _arun_stream(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        Best-first crawl in streaming mode.
        
        Yields CrawlResults as they become available.
        """
        async for result in self._arun_best_first(start_url, crawler, config):
            yield result

    async def arun(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: Optional[CrawlerRunConfig] = None,
    ) -> "RunManyReturn":
        """
        Main entry point for best-first crawling.
        
        Returns either a list (batch mode) or an async generator (stream mode)
        of CrawlResults.
        """
        if config is None:
            raise ValueError("CrawlerRunConfig must be provided")
        if config.stream:
            return self._arun_stream(start_url, crawler, config)
        else:
            return await self._arun_batch(start_url, crawler, config)

    async def shutdown(self) -> None:
        """
        Signal cancellation and clean up resources.
        """
        self._cancel_event.set()
        self.stats.end_time = datetime.now()
