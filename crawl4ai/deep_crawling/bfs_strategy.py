# bfs_deep_crawl_strategy.py
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Set, Dict, List, Tuple
from urllib.parse import urlparse

from ..models import TraversalStats
from .filters import FilterChain
from .scorers import URLScorer
from . import DeepCrawlStrategy  
from ..types import AsyncWebCrawler, CrawlerRunConfig, CrawlResult
from ..utils import normalize_url_for_deep_crawl, efficient_normalize_url_for_deep_crawl
from math import inf as infinity

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
        filter_chain: FilterChain = FilterChain(),
        url_scorer: Optional[URLScorer] = None,        
        include_external: bool = False,
        score_threshold: float = -infinity,
        max_pages: int = infinity,
        logger: Optional[logging.Logger] = None,
    ):
        self.max_depth = max_depth
        self.filter_chain = filter_chain
        self.url_scorer = url_scorer
        self.include_external = include_external
        self.score_threshold = score_threshold
        self.max_pages = max_pages
        self.logger = logger or logging.getLogger(__name__)
        self.stats = TraversalStats(start_time=datetime.now())
        self._cancel_event = asyncio.Event()
        self._pages_crawled = 0

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

        if depth != 0 and not await self.filter_chain.apply(url):
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

        # If we've reached the max pages limit, don't discover new links
        remaining_capacity = self.max_pages - self._pages_crawled
        if remaining_capacity <= 0:
            self.logger.info(f"Max pages limit ({self.max_pages}) reached, stopping link discovery")
            return

        # Get internal links and, if enabled, external links.
        links = result.links.get("internal", [])
        if self.include_external:
            links += result.links.get("external", [])

        valid_links = []
        
        # First collect all valid links
        for link in links:
            url = link.get("href")
            # Strip URL fragments to avoid duplicate crawling
            # base_url = url.split('#')[0] if url else url
            base_url = normalize_url_for_deep_crawl(url, source_url)
            if base_url in visited:
                continue
            if not await self.can_process_url(url, next_depth):
                self.stats.urls_skipped += 1
                continue

            # Score the URL if a scorer is provided
            score = self.url_scorer.score(base_url) if self.url_scorer else 0
            
            # Skip URLs with scores below the threshold
            if score < self.score_threshold:
                self.logger.debug(f"URL {url} skipped: score {score} below threshold {self.score_threshold}")
                self.stats.urls_skipped += 1
                continue

            visited.add(base_url)
            valid_links.append((base_url, score))
        
        # If we have more valid links than capacity, sort by score and take the top ones
        if len(valid_links) > remaining_capacity:
            if self.url_scorer:
                # Sort by score in descending order
                valid_links.sort(key=lambda x: x[1], reverse=True)
            # Take only as many as we have capacity for
            valid_links = valid_links[:remaining_capacity]
            self.logger.info(f"Limiting to {remaining_capacity} URLs due to max_pages limit")
            
        # Process the final selected links
        for url, score in valid_links:
            # attach the score to metadata if needed
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
            # Check if we've already reached max_pages before starting a new level
            if self._pages_crawled >= self.max_pages:
                self.logger.info(f"Max pages limit ({self.max_pages}) reached, stopping crawl")
                break
            
            next_level: List[Tuple[str, Optional[str]]] = []
            urls = [url for url, _ in current_level]

            # Clone the config to disable deep crawling recursion and enforce batch mode.
            batch_config = config.clone(deep_crawl_strategy=None, stream=False)
            batch_results = await crawler.arun_many(urls=urls, config=batch_config)
            
            # Update pages crawled counter - count only successful crawls
            successful_results = [r for r in batch_results if r.success]
            self._pages_crawled += len(successful_results)
            
            for result in batch_results:
                url = result.url
                depth = depths.get(url, 0)
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                parent_url = next((parent for (u, parent) in current_level if u == url), None)
                result.metadata["parent_url"] = parent_url
                results.append(result)
                
                # Only discover links from successful crawls
                if result.success:
                    # Link discovery will handle the max pages limit internally
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
            
            # Keep track of processed results for this batch
            results_count = 0
            async for result in stream_gen:
                url = result.url
                depth = depths.get(url, 0)
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                parent_url = next((parent for (u, parent) in current_level if u == url), None)
                result.metadata["parent_url"] = parent_url
                
                # Count only successful crawls
                if result.success:
                    self._pages_crawled += 1
                    # Check if we've reached the limit during batch processing
                    if self._pages_crawled >= self.max_pages:
                        self.logger.info(f"Max pages limit ({self.max_pages}) reached during batch, stopping crawl")
                        break  # Exit the generator
                
                results_count += 1
                yield result
                
                # Only discover links from successful crawls
                if result.success:
                    # Link discovery will handle the max pages limit internally
                    await self.link_discovery(result, url, depth, visited, next_level, depths)
            
            # If we didn't get results back (e.g. due to errors), avoid getting stuck in an infinite loop
            # by considering these URLs as visited but not counting them toward the max_pages limit
            if results_count == 0 and urls:
                self.logger.warning(f"No results returned for {len(urls)} URLs, marking as visited")
                
            current_level = next_level

    async def shutdown(self) -> None:
        """
        Clean up resources and signal cancellation of the crawl.
        """
        self._cancel_event.set()
        self.stats.end_time = datetime.now()
