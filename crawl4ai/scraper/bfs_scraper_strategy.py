from abc import ABC, abstractmethod
from typing import Union, AsyncGenerator, Optional, Dict, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
import validators
import time
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential
from collections import defaultdict

from .models import ScraperResult, CrawlResult
from .filters import FilterChain
from .scorers import URLScorer
from ..async_webcrawler import AsyncWebCrawler

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

class ScraperStrategy(ABC):
    """Base class for scraping strategies"""
    
    @abstractmethod
    async def ascrape(
        self, 
        url: str, 
        crawler: AsyncWebCrawler, 
        parallel_processing: bool = True,
        stream: bool = False
    ) -> Union[AsyncGenerator[CrawlResult, None], ScraperResult]:
        """Abstract method for scraping implementation"""
        pass

    @abstractmethod
    async def can_process_url(self, url: str) -> bool:
        """Check if URL can be processed based on strategy rules"""
        pass

    @abstractmethod
    async def shutdown(self):
        """Clean up resources used by the strategy"""
        pass

class BFSScraperStrategy(ScraperStrategy):
    """Breadth-First Search scraping strategy with politeness controls"""

    def __init__(
        self,
        max_depth: int,
        filter_chain: FilterChain,
        url_scorer: URLScorer,
        max_concurrent: int = 5,
        min_crawl_delay: int = 1,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        self.max_depth = max_depth
        self.filter_chain = filter_chain
        self.url_scorer = url_scorer
        self.max_concurrent = max_concurrent
        self.min_crawl_delay = min_crawl_delay
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        
        # Crawl control
        self.stats = CrawlStats(start_time=datetime.now())
        self._cancel_event = asyncio.Event()
        self.process_external_links = False
        
        # Rate limiting and politeness
        self.rate_limiter = AsyncLimiter(1, 1)
        self.last_crawl_time = defaultdict(float)
        self.robot_parsers: Dict[str, RobotFileParser] = {}
        self.domain_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)

    async def can_process_url(self, url: str) -> bool:
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

        return self.filter_chain.apply(url)

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

    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _crawl_with_retry(
        self, 
        crawler: AsyncWebCrawler, 
        url: str
    ) -> CrawlResult:
        """Crawl URL with retry logic"""
        try:
            async with asyncio.timeout(self.timeout):
                return await crawler.arun(url)
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout crawling {url}")
            raise

    async def process_url(
        self,
        url: str,
        depth: int,
        crawler: AsyncWebCrawler,
        queue: asyncio.PriorityQueue,
        visited: Set[str],
        depths: Dict[str, int]
    ) -> Optional[CrawlResult]:
        """Process a single URL and extract links.
        This is our main URL processing workhorse that:
            - Checks for cancellation
            - Validates URLs through can_process_url
            - Implements politeness delays per domain
            - Applies rate limiting
            - Handles crawling with retries
            - Updates various statistics
            - Processes extracted links
            - Returns the crawl result or None on failure
        """
        
        if self._cancel_event.is_set():
            return None
            
        if not await self.can_process_url(url):
            self.stats.urls_skipped += 1
            return None

        # Politeness delay
        domain = urlparse(url).netloc
        time_since_last = time.time() - self.last_crawl_time[domain]
        if time_since_last < self.min_crawl_delay:
            await asyncio.sleep(self.min_crawl_delay - time_since_last)
        self.last_crawl_time[domain] = time.time()

        # Crawl with rate limiting
        try:
            async with self.rate_limiter:
                result = await self._crawl_with_retry(crawler, url)
                self.stats.urls_processed += 1
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {e}")
            self.stats.urls_failed += 1
            return None

        # Process links
        await self._process_links(result, url, depth, queue, visited, depths)
        
        return result

    async def _process_links(
        self,
        result: CrawlResult,
        source_url: str,
        depth: int,
        queue: asyncio.PriorityQueue,
        visited: Set[str],
        depths: Dict[str, int]
    ):
        """Process extracted links from crawl result.
        This is our link processor that:
            Handles both internal and external links
            Normalizes URLs (removes fragments)
            Checks depth limits
            Scores URLs for priority
            Updates depth tracking
            Adds valid URLs to the queue
            Updates maximum depth statistics
        """
        links_ro_process = result.links["internal"]
        if self.process_external_links:
            links_ro_process += result.links["external"]
        for link_type in links_ro_process:
            for link in result.links[link_type]:
                url = link['href']
                # url = urljoin(source_url, link['href'])
                # url = urlunparse(urlparse(url)._replace(fragment=""))
                
                if url not in visited and await self.can_process_url(url):
                    new_depth = depths[source_url] + 1
                    if new_depth <= self.max_depth:
                        score = self.url_scorer.score(url)
                        await queue.put((score, new_depth, url))
                        depths[url] = new_depth
                        self.stats.total_depth_reached = max(
                            self.stats.total_depth_reached, 
                            new_depth
                        )

    async def ascrape(
        self,
        start_url: str,
        crawler: AsyncWebCrawler,
        parallel_processing: bool = True
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
        pending_tasks: Tracks currently running crawl tasks        
        """
        queue = asyncio.PriorityQueue()
        await queue.put((0, 0, start_url))
        visited: Set[str] = set()
        depths = {start_url: 0}
        pending_tasks = set()
        
        try:
            while (not queue.empty() or pending_tasks) and not self._cancel_event.is_set():
                """
                This sets up our main control loop which:
                    - Continues while there are URLs to process (not queue.empty())
                    - Or while there are tasks still running (pending_tasks)
                    - Can be interrupted via cancellation (not self._cancel_event.is_set())
                """
                # Start new tasks up to max_concurrent
                while not queue.empty() and len(pending_tasks) < self.max_concurrent:
                    """
                    This section manages task creation:
                        Checks if we can start more tasks (under max_concurrent limit)
                        Gets the next URL from the priority queue
                        Marks URLs as visited immediately to prevent duplicates
                        Updates current depth in stats
                        Either:
                            Creates a new async task (parallel mode)
                            Processes URL directly (sequential mode)
                    """
                    _, depth, url = await queue.get()
                    if url not in visited:
                        visited.add(url)
                        self.stats.current_depth = depth
                        
                        if parallel_processing:
                            task = asyncio.create_task(
                                self.process_url(url, depth, crawler, queue, visited, depths)
                            )
                            pending_tasks.add(task)
                        else:
                            result = await self.process_url(
                                url, depth, crawler, queue, visited, depths
                            )
                            if result:
                                yield result

                # Process completed tasks
                """
                This section manages completed tasks:
                    Waits for any task to complete using asyncio.wait
                    Uses FIRST_COMPLETED to handle results as soon as they're ready
                    Yields successful results to the caller
                    Updates pending_tasks to remove completed ones
                """
                if pending_tasks:
                    done, pending_tasks = await asyncio.wait(
                        pending_tasks,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in done:
                        result = await task
                        if result:
                            yield result
                            
        except Exception as e:
            self.logger.error(f"Error in crawl process: {e}")
            raise
            
        finally:
            # Clean up any remaining tasks
            for task in pending_tasks:
                task.cancel()
            self.stats.end_time = datetime.now()

    async def shutdown(self):
        """Clean up resources and stop crawling"""
        self._cancel_event.set()
        # Clear caches and close connections
        self.robot_parsers.clear()
        self.domain_queues.clear()