# bfs_deep_crawl_strategy.py
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Set, Dict, List, Tuple
from urllib.parse import urlparse

from ..models import TraversalStats
from .filters import FastFilterChain
from .scorers import FastURLScorer
from . import DeepCrawlStrategy  
from ..types import AsyncWebCrawler, CrawlerRunConfig, CrawlResult

class BFSDeepCrawlStrategy(DeepCrawlStrategy):
    """
    Breadth-First Search deep crawling strategy.
    
    Core functions:
      - arun: Main entry point; splits execution into batch or stream modes.
      - link_discovery: Extracts, filters, and (if needed) scores the outgoing URLs.
      - can_process_url: Validates URL format and applies the filter chain.
    """
    def __init__(
        self,
        max_depth: int,
        filter_chain: FastFilterChain = FastFilterChain(),
        url_scorer: Optional[FastURLScorer] = None,
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
        Validates the URL and applies the filter chain.
        For the start URL (depth 0) filtering is bypassed.
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
        next_level: List[Tuple[str, Optional[str]]],
        depths: Dict[str, int],
    ) -> None:
        """
        Extracts links from the crawl result, validates and scores them, and
        prepares the next level of URLs.
        Each valid URL is appended to next_level as a tuple (url, parent_url)
        and its depth is tracked.
        """
        next_depth = current_depth + 1
        if next_depth > self.max_depth:
            return

        # Get internal links and, if enabled, external links.
        links = result.links.get("internal", [])
        if self.include_external:
            links += result.links.get("external", [])

        for link in links:
            url = link.get("href")
            if url in visited:
                continue
            if not await self.can_process_url(url, next_depth):
                self.stats.urls_skipped += 1
                continue

            # Score the URL if a scorer is provided. In this simple BFS
            # the score is not used for ordering.
            score = self.url_scorer.score(url) if self.url_scorer else 0
            # attach the score to metadata if needed.
            if score:
                result.metadata = result.metadata or {}
                result.metadata["score"] = score
            next_level.append((url, source_url))
            depths[url] = next_depth

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
        visited: Set[str] = set()
        # current_level holds tuples: (url, parent_url)
        current_level: List[Tuple[str, Optional[str]]] = [(start_url, None)]
        depths: Dict[str, int] = {start_url: 0}

        results: List[CrawlResult] = []

        while current_level and not self._cancel_event.is_set():
            next_level: List[Tuple[str, Optional[str]]] = []
            urls = [url for url, _ in current_level]
            visited.update(urls)

            # Clone the config to disable deep crawling recursion and enforce batch mode.
            batch_config = config.clone(deep_crawl_strategy=None, stream=False)
            batch_results = await crawler.arun_many(urls=urls, config=batch_config)

            for result in batch_results:
                url = result.url
                depth = depths.get(url, 0)
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                parent_url = next((parent for (u, parent) in current_level if u == url), None)
                result.metadata["parent_url"] = parent_url
                results.append(result)
                await self.link_discovery(result, url, depth, visited, next_level, depths)

            current_level = next_level

        return results

    async def _arun_stream(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        Streaming mode:
        Processes one BFS level at a time and yields results immediately as they arrive.
        """
        visited: Set[str] = set()
        current_level: List[Tuple[str, Optional[str]]] = [(start_url, None)]
        depths: Dict[str, int] = {start_url: 0}

        while current_level and not self._cancel_event.is_set():
            next_level: List[Tuple[str, Optional[str]]] = []
            urls = [url for url, _ in current_level]
            visited.update(urls)

            stream_config = config.clone(deep_crawl_strategy=None, stream=True)
            stream_gen = await crawler.arun_many(urls=urls, config=stream_config)
            async for result in stream_gen:
                url = result.url
                depth = depths.get(url, 0)
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                parent_url = next((parent for (u, parent) in current_level if u == url), None)
                result.metadata["parent_url"] = parent_url
                yield result
                await self.link_discovery(result, url, depth, visited, next_level, depths)

            current_level = next_level

    async def shutdown(self) -> None:
        """
        Clean up resources and signal cancellation of the crawl.
        """
        self._cancel_event.set()
        self.stats.end_time = datetime.now()
