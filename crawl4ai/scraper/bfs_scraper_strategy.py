from .scraper_strategy import ScraperStrategy
from .filters import FilterChain
from .scorers import URLScorer
from ..models import CrawlResult
from ..async_webcrawler import AsyncWebCrawler
import asyncio
import validators
from urllib.parse import urljoin,urlparse,urlunparse
from urllib.robotparser import RobotFileParser
import time
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential
from collections import defaultdict
import logging
from typing import Dict, AsyncGenerator
logging.basicConfig(level=logging.DEBUG)

rate_limiter = AsyncLimiter(1, 1)  # 1 request per second

class BFSScraperStrategy(ScraperStrategy):
    def __init__(self, max_depth: int, filter_chain: FilterChain, url_scorer: URLScorer, max_concurrent: int = 5, min_crawl_delay: int=1):
        self.max_depth = max_depth
        self.filter_chain = filter_chain
        self.url_scorer = url_scorer
        self.max_concurrent = max_concurrent
        # For Crawl Politeness
        self.last_crawl_time = defaultdict(float)
        self.min_crawl_delay = min_crawl_delay  # 1 second delay between requests to the same domain
        # For Robots.txt Compliance
        self.robot_parsers = {}

    # Robots.txt Parser
    def get_robot_parser(self, url: str) -> RobotFileParser:
        domain = urlparse(url)
        scheme = domain.scheme if domain.scheme else 'http'  # Default to 'http' if no scheme provided
        netloc = domain.netloc
        if netloc not in self.robot_parsers:
            rp = RobotFileParser()
            rp.set_url(f"{scheme}://{netloc}/robots.txt")
            try:
                rp.read()
            except Exception as e:
                # Log the type of error, message, and the URL
                logging.warning(f"Error {type(e).__name__} occurred while fetching robots.txt for {netloc}: {e}")
                return None
            self.robot_parsers[netloc] = rp
        return self.robot_parsers[netloc]

    
    # Retry with exponential backoff
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def retry_crawl(self, crawler: AsyncWebCrawler, url: str) -> CrawlResult:
        return await crawler.arun(url)
    
    async def process_url(self, url: str, depth: int, crawler: AsyncWebCrawler, queue: asyncio.PriorityQueue, visited: set, depths: Dict[str, int]) -> AsyncGenerator[CrawlResult, None]:
        def normalize_url(url: str) -> str:
            parsed = urlparse(url)
            return urlunparse(parsed._replace(fragment=""))
        
        # URL Validation
        if not validators.url(url):
            logging.warning(f"Invalid URL: {url}")
            return None
        
        # Robots.txt Compliance
        robot_parser = self.get_robot_parser(url)
        if robot_parser is None:
            logging.info(f"Could not retrieve robots.txt for {url}, hence proceeding with crawl.")
        else:
            # If robots.txt was fetched, check if crawling is allowed
            if not robot_parser.can_fetch(crawler.crawler_strategy.user_agent, url):
                logging.info(f"Skipping {url} as per robots.txt")
                return None
    
        # Crawl Politeness
        domain = urlparse(url).netloc
        time_since_last_crawl = time.time() - self.last_crawl_time[domain]
        if time_since_last_crawl < self.min_crawl_delay:
            await asyncio.sleep(self.min_crawl_delay - time_since_last_crawl)
        self.last_crawl_time[domain] = time.time()

        # Rate Limiting
        async with rate_limiter:
            # Error Handling
            try:
                crawl_result = await self.retry_crawl(crawler, url)
            except Exception as e:
                logging.error(f"Error crawling {url}: {str(e)}")
                crawl_result = CrawlResult(url=url, html="", success=False, status_code=0, error_message=str(e))
        
        if not crawl_result.success:
            # Logging and Monitoring
            logging.error(f"Failed to crawl URL: {url}. Error: {crawl_result.error_message}")
            # Error Categorization
            if crawl_result.status_code == 404:
                self.remove_from_future_crawls(url)
            elif crawl_result.status_code == 503:
                await self.add_to_retry_queue(url)
            return crawl_result

        # Process links
        for link_type in ["internal", "external"]:
            for link in crawl_result.links[link_type]:
                absolute_link = urljoin(url, link['href'])
                normalized_link = normalize_url(absolute_link)
                if self.filter_chain.apply(normalized_link) and normalized_link not in visited:
                    new_depth = depths[url] + 1
                    if new_depth <= self.max_depth:
                        # URL Scoring
                        score = self.url_scorer.score(normalized_link)
                        await queue.put((score, new_depth, normalized_link))
                        depths[normalized_link] = new_depth
        return crawl_result

    async def ascrape(self, start_url: str, crawler: AsyncWebCrawler, parallel_processing:bool = True) -> AsyncGenerator[CrawlResult,None]:
        queue = asyncio.PriorityQueue()
        queue.put_nowait((0, 0, start_url))
        visited = set()
        depths = {start_url: 0}
        pending_tasks = set()

        while not queue.empty() or pending_tasks:
            while not queue.empty() and len(pending_tasks) < self.max_concurrent:
                _, depth, url = await queue.get()
                if url not in visited:
                    # Adding URL to the visited set here itself, (instead of after result generation)
                    # so that other tasks are not queued for same URL, found at different depth before
                    # crawling and extraction of this task is completed.
                    visited.add(url)
                    if parallel_processing:
                        task = asyncio.create_task(self.process_url(url, depth, crawler, queue, visited, depths))
                        pending_tasks.add(task)
                    else:
                        result = await self.process_url(url, depth, crawler, queue, visited, depths)
                        if result:
                            yield result 

            # Wait for the first task to complete and yield results incrementally as each task is completed
            if pending_tasks:
                done, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    result = await task
                    if result:
                        yield result