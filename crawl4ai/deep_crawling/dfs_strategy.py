# dfs_deep_crawl_strategy.py
from typing import AsyncGenerator, Optional, Set, Dict, List, Tuple

from ..models import CrawlResult
from .bfs_strategy import BFSDeepCrawlStrategy  # noqa
from ..types import AsyncWebCrawler, CrawlerRunConfig
from ..utils import normalize_url_for_deep_crawl

class DFSDeepCrawlStrategy(BFSDeepCrawlStrategy):
    """
    Depth-First Search (DFS) deep crawling strategy.

    Inherits URL validation and link discovery from BFSDeepCrawlStrategy.
    Overrides _arun_batch and _arun_stream to use a stack (LIFO) for DFS traversal.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dfs_seen: Set[str] = set()

    def _reset_seen(self, start_url: str) -> None:
        self._dfs_seen = {start_url}

    async def _arun_batch(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> List[CrawlResult]:
        """
        Batch (non-streaming) DFS mode.
        Uses a stack to traverse URLs in DFS order, aggregating CrawlResults into a list.
        """
        visited: Set[str] = set()
        # Stack items: (url, parent_url, depth)
        stack: List[Tuple[str, Optional[str], int]] = [(start_url, None, 0)]
        depths: Dict[str, int] = {start_url: 0}
        results: List[CrawlResult] = []
        self._reset_seen(start_url)

        while stack and not self._cancel_event.is_set():
            url, parent, depth = stack.pop()
            if url in visited or depth > self.max_depth:
                continue
            visited.add(url)

            # Clone config to disable recursive deep crawling.
            batch_config = config.clone(deep_crawl_strategy=None, stream=False)
            url_results = await crawler.arun_many(urls=[url], config=batch_config)
            
            for result in url_results:
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                result.metadata["parent_url"] = parent
                if self.url_scorer:
                    result.metadata["score"] = self.url_scorer.score(url)
                results.append(result)
                
                # Count only successful crawls toward max_pages limit
                if result.success:
                    self._pages_crawled += 1
                    # Check if we've reached the limit during batch processing
                    if self._pages_crawled >= self.max_pages:
                        self.logger.info(f"Max pages limit ({self.max_pages}) reached during batch, stopping crawl")
                        break  # Exit the generator
                    
                    # Only discover links from successful crawls
                    new_links: List[Tuple[str, Optional[str]]] = []
                    await self.link_discovery(result, url, depth, visited, new_links, depths)
                    
                    # Push new links in reverse order so the first discovered is processed next.
                    for new_url, new_parent in reversed(new_links):
                        new_depth = depths.get(new_url, depth + 1)
                        stack.append((new_url, new_parent, new_depth))
        return results

    async def _arun_stream(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlResult, None]:
        """
        Streaming DFS mode.
        Uses a stack to traverse URLs in DFS order and yields CrawlResults as they become available.
        """
        visited: Set[str] = set()
        stack: List[Tuple[str, Optional[str], int]] = [(start_url, None, 0)]
        depths: Dict[str, int] = {start_url: 0}
        self._reset_seen(start_url)

        while stack and not self._cancel_event.is_set():
            url, parent, depth = stack.pop()
            if url in visited or depth > self.max_depth:
                continue
            visited.add(url)

            stream_config = config.clone(deep_crawl_strategy=None, stream=True)
            stream_gen = await crawler.arun_many(urls=[url], config=stream_config)
            async for result in stream_gen:
                result.metadata = result.metadata or {}
                result.metadata["depth"] = depth
                result.metadata["parent_url"] = parent
                if self.url_scorer:
                    result.metadata["score"] = self.url_scorer.score(url)
                yield result

                # Only count successful crawls toward max_pages limit
                # and only discover links from successful crawls
                if result.success:
                    self._pages_crawled += 1
                    # Check if we've reached the limit during batch processing
                    if self._pages_crawled >= self.max_pages:
                        self.logger.info(f"Max pages limit ({self.max_pages}) reached during batch, stopping crawl")
                        break  # Exit the generator
                    
                    new_links: List[Tuple[str, Optional[str]]] = []
                    await self.link_discovery(result, url, depth, visited, new_links, depths)
                    for new_url, new_parent in reversed(new_links):
                        new_depth = depths.get(new_url, depth + 1)
                        stack.append((new_url, new_parent, new_depth))

    async def link_discovery(
        self,
        result: CrawlResult,
        source_url: str,
        current_depth: int,
        _visited: Set[str],
        next_level: List[Tuple[str, Optional[str]]],
        depths: Dict[str, int],
    ) -> None:
        """
        DFS-specific link discovery that avoids mutating the traversal
        'visited' set, preventing premature skips.
        """
        next_depth = current_depth + 1
        if next_depth > self.max_depth:
            return

        remaining_capacity = self.max_pages - self._pages_crawled
        if remaining_capacity <= 0:
            self.logger.info(
                f"Max pages limit ({self.max_pages}) reached, stopping link discovery"
            )
            return

        links = result.links.get("internal", [])
        if self.include_external:
            links += result.links.get("external", [])

        seen = self._dfs_seen
        valid_links: List[Tuple[str, float]] = []

        for link in links:
            raw_url = link.get("href")
            if not raw_url:
                continue

            normalized_url = normalize_url_for_deep_crawl(raw_url, source_url)
            if not normalized_url or normalized_url in seen:
                continue

            if not await self.can_process_url(raw_url, next_depth):
                self.stats.urls_skipped += 1
                continue

            score = self.url_scorer.score(normalized_url) if self.url_scorer else 0
            if score < self.score_threshold:
                self.logger.debug(
                    f"URL {normalized_url} skipped: score {score} below threshold {self.score_threshold}"
                )
                self.stats.urls_skipped += 1
                continue

            seen.add(normalized_url)
            valid_links.append((normalized_url, score))

        if len(valid_links) > remaining_capacity:
            if self.url_scorer:
                valid_links.sort(key=lambda x: x[1], reverse=True)
            valid_links = valid_links[:remaining_capacity]
            self.logger.info(
                f"Limiting to {remaining_capacity} URLs due to max_pages limit"
            )

        for url, score in valid_links:
            if score:
                result.metadata = result.metadata or {}
                result.metadata["score"] = score
            next_level.append((url, source_url))
            depths[url] = next_depth
