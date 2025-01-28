from typing import AsyncGenerator, Optional, Dict, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from urllib.parse import urlparse

from ..async_webcrawler import AsyncWebCrawler
from ..async_configs import BrowserConfig, CrawlerRunConfig
from .models import CrawlResult, ScraperPageResult
from .filters import FilterChain
from .scorers import URLScorer
from .scraper_strategy import ScraperStrategy
from ..config import SCRAPER_BATCH_SIZE


@dataclass
class CrawlStats:
    """Statistics for the crawling process"""

    start_time: datetime
    urls_processed: int = 0
    urls_failed: int = 0
    urls_skipped: int = 0
    total_depth_reached: int = 0
    current_depth: int = 0


class BFSScraperStrategy(ScraperStrategy):
    """Breadth-First Search scraping strategy with politeness controls"""

    def __init__(
        self,
        max_depth: int,
        filter_chain: FilterChain,
        url_scorer: URLScorer,
        process_external_links: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self.max_depth = max_depth
        self.filter_chain = filter_chain
        self.url_scorer = url_scorer
        self.logger = logger or logging.getLogger(__name__)

        # Crawl control
        self.stats = CrawlStats(start_time=datetime.now())
        self._cancel_event = asyncio.Event()
        self.process_external_links = process_external_links

    async def can_process_url(self, url: str, depth: int) -> bool:
        """Check if URL can be processed based on filters
        This is our gatekeeper method that determines if a URL should be processed. It:
            - Validates URL format using a robust built-in method
            - Applies custom filters from the filter chain
            - Updates statistics for blocked URLs
            - Returns False early if any check fails
        """
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL")
            if result.scheme not in ("http", "https"):
                raise ValueError("URL must be HTTP or HTTPS")
            if not result.netloc or "." not in result.netloc:
                raise ValueError("Invalid domain")
        except Exception as e:
            self.logger.warning(f"Invalid URL: {url}. Error: {str(e)}")
            return False

        # Apply the filter chain if it's not start page
        if depth != 0 and not self.filter_chain.apply(url):
            return False

        return True

    async def _process_links(
        self,
        result: CrawlResult,
        source_url: str,
        queue: asyncio.PriorityQueue,
        visited: Set[str],
        depths: Dict[str, int],
    ):
        """Process extracted links from crawl result.
        This is our link processor that:
            Checks depth limits
            Handles both internal and external links
            Checks if URL is visited already
            Checks if URL can be processed - validates URL, applies Filters with can_process_url
            Scores URLs for priority
            Updates depth tracking dictionary
            Adds valid URLs to the queue
            Updates maximum depth statistics
        """
        next_depth = depths[source_url] + 1
        # If depth limit reached, exit without processing links
        if next_depth > self.max_depth:
            return
        links_to_process = result.links["internal"]
        if self.process_external_links:
            links_to_process += result.links["external"]
        for link in links_to_process:
            url = link["href"]
            if url in visited:
                continue
            if not await self.can_process_url(url, next_depth):
                self.stats.urls_skipped += 1
                continue
            score = self.url_scorer.score(url) if self.url_scorer else 0
            await queue.put((score, next_depth, url))
            depths[url] = next_depth
            self.stats.total_depth_reached = max(
                self.stats.total_depth_reached, next_depth
            )

    async def ascrape(
        self,
        start_url: str,
        crawler_config: Optional[CrawlerRunConfig] = None,
        browser_config: Optional[BrowserConfig] = None,
    ) -> AsyncGenerator[CrawlResult, None]:
        """Implement BFS crawling strategy"""

        # Initialize crawl state
        """
        queue: A priority queue where items are tuples of (score, depth, url)
            Score: Determines crawling priority (lower = higher priority)
            Depth: Current distance from start_url
            URL: The actual URL to crawl
        visited: Keeps track of URLs we've already seen to avoid cycles
        depths: Maps URLs to their depths from the start URL
        active_crawls: Tracks currently running crawl tasks        
        """
        queue = asyncio.PriorityQueue()
        await queue.put((0, 0, start_url))
        visited: Set[str] = set()
        depths = {start_url: 0}
        active_crawls = {}  # Track URLs currently being processed with depth and score
        active_crawls_lock = asyncio.Lock()  # Create the lock within the same event loop

        # Update crawler_config to stream back results to scraper
        crawler_config = crawler_config.clone(stream=True) if crawler_config else CrawlerRunConfig(stream=True)

        async with AsyncWebCrawler(
            config=browser_config,
            verbose=True,
        ) as crawler:
            try:
                while (
                    not queue.empty() or active_crawls
                ) and not self._cancel_event.is_set():
                    """
                    This sets up our main control loop which:
                        - Continues while there are URLs to process (not queue.empty())
                        - Or while there are active crawls still running (arun_many)
                        - Can be interrupted via cancellation (not self._cancel_event.is_set())
                    """
                    # Collect batch of URLs into active_crawls to process
                    async with active_crawls_lock:
                        while len(active_crawls) < SCRAPER_BATCH_SIZE and not queue.empty():
                            score, depth, url = await queue.get()
                            active_crawls[url] = {"depth": depth, "score": score}
                            self.stats.current_depth = depth

                    if not active_crawls:
                        # If no active crawls exist, wait a bit and continue
                        await asyncio.sleep(0.1)
                        continue
                    # Process batch
                    try:
                        async for result in await crawler.arun_many(
                            urls=list(active_crawls.keys()),
                            config=crawler_config.clone(stream=True),
                        ):
                            source_url = result.url
                            depth = active_crawls[source_url]["depth"]
                            score=active_crawls[source_url]["score"]
                            async with active_crawls_lock:
                                active_crawls.pop(source_url, None)

                            if result.success:
                                await self._process_links(
                                    result, source_url, queue, visited, depths
                                )
                                yield ScraperPageResult(
                                    result = result,
                                    depth=depth,
                                    score=score,
                                )
                            else:
                                self.logger.warning(
                                    f"Failed to crawl {result.url}: {result.error_message}"
                                )
                    except Exception as e:
                        self.logger.error(f"Batch processing error: {e}")
                        # Continue processing other batches
                        continue

            except Exception as e:
                self.logger.error(f"Error in crawl process: {e}")
                raise

            finally:
                self.stats.end_time = datetime.now()
                await crawler.close()

    async def shutdown(self):
        """Clean up resources and stop crawling"""
        self._cancel_event.set()
