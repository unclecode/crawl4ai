from typing import AsyncGenerator, Optional, Dict, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import validators

from ..async_configs import CrawlerRunConfig
from .models import CrawlResult
from .filters import FilterChain
from .scorers import URLScorer
from ..async_webcrawler import AsyncWebCrawler
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
    robots_blocked: int = 0


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
        self.robot_parsers: Dict[str, RobotFileParser] = {}

    async def can_process_url(self, url: str, depth: int) -> bool:
        """Check if URL can be processed based on robots.txt and filters
        This is our gatekeeper method that determines if a URL should be processed. It:
            - Validates URL format using the validators library
            - Checks robots.txt permissions for the domain
            - Applies custom filters from the filter chain
            - Updates statistics for blocked URLs
            - Returns False early if any check fails
        """
        if not validators.url(url):
            self.logger.warning(f"Invalid URL: {url}")
            return False

        robot_parser = await self._get_robot_parser(url)
        if robot_parser and not robot_parser.can_fetch("*", url):
            self.stats.robots_blocked += 1
            self.logger.info(f"Blocked by robots.txt: {url}")
            return False

        # Apply the filter chain it's not start page
        if depth != 0 and not self.filter_chain.apply(url):
            return False

        return True

    async def _get_robot_parser(self, url: str) -> Optional[RobotFileParser]:
        """Get or create robots.txt parser for domain.
        This is our robots.txt manager that:
            - Uses domain-level caching of robot parsers
            - Creates and caches new parsers as needed
            - Handles failed robots.txt fetches gracefully
            - Returns None if robots.txt can't be fetched, allowing crawling to proceed
        """
        domain = urlparse(url).netloc
        if domain not in self.robot_parsers:
            parser = RobotFileParser()
            try:
                robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
                parser.set_url(robots_url)
                parser.read()
                self.robot_parsers[domain] = parser
            except Exception as e:
                self.logger.warning(f"Error fetching robots.txt for {domain}: {e}")
                return None
        return self.robot_parsers[domain]

    async def _process_links(
        self,
        result: CrawlResult,
        source_url: str,
        depth: int,
        queue: asyncio.PriorityQueue,
        visited: Set[str],
        depths: Dict[str, int],
    ):
        """Process extracted links from crawl result.
        This is our link processor that:
            Handles both internal and external links
            Checks if URL can be processed - validates URL, applies Filters and tests Robots.txt compliance with can_process_url
            Checks depth limits
            Scores URLs for priority
            Updates depth tracking
            Adds valid URLs to the queue
            Updates maximum depth statistics
        """
        links_to_process = result.links["internal"]
        if self.process_external_links:
            links_to_process += result.links["external"]
        for link in links_to_process:
            url = link["href"]
            if not await self.can_process_url(url, depth):
                self.stats.urls_skipped += 1
                continue
            if url not in visited:
                new_depth = depths[source_url] + 1
                if new_depth <= self.max_depth:
                    if self.url_scorer:
                        score = self.url_scorer.score(url)
                    else:
                        # When no url_scorer is provided all urls will have same score of 0.
                        # Therefore will be process in FIFO order as per URL depth
                        score = 0
                    await queue.put((score, new_depth, url))
                    depths[url] = new_depth
                    self.stats.total_depth_reached = max(
                        self.stats.total_depth_reached, new_depth
                    )

    async def ascrape(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
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
        active_crawls = set()  # Track URLs currently being processed
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
                # Collect batch of jobs to process
                jobs = []
                # Fill batch with available jobs
                while len(jobs) < SCRAPER_BATCH_SIZE and not queue.empty():
                    score, depth, url = await queue.get()
                    if url not in active_crawls:  # Only add if not currently processing
                        jobs.append((score, depth, url))
                        active_crawls.add(url)
                        self.stats.current_depth = depth

                if not jobs:
                    # If no jobs but active crawls exist, wait a bit and continue
                    if active_crawls:
                        await asyncio.sleep(0.1)
                    continue

                # Process batch
                crawler_config = CrawlerRunConfig(cache_mode="BYPASS", stream=True)
                try:
                    async for result in await crawler.arun_many(
                        urls=[url for _, _, url in jobs], config=crawler_config
                    ):
                        source_url, depth = next(
                            (url, depth) for _, depth, url in jobs if url == result.url
                        )
                        active_crawls.remove(source_url)  # Remove from active set

                        if result.success:
                            await self._process_links(
                                result, source_url, depth, queue, visited, depths
                            )
                            yield result
                        else:
                            self.logger.warning(
                                f"Failed to crawl {result.url}: {result.error_message}"
                            )
                except Exception as e:
                    # Remove failed URLs from active set
                    for _, _, url in jobs:
                        active_crawls.discard(url)
                    self.logger.error(f"Batch processing error: {e}")
                    # Continue processing other batches
                    continue

        except Exception as e:
            self.logger.error(f"Error in crawl process: {e}")
            raise

        finally:
            self.stats.end_time = datetime.now()

    async def shutdown(self):
        """Clean up resources and stop crawling"""
        self._cancel_event.set()
        # Clear caches and close connections
        self.robot_parsers.clear()
