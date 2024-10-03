from .scraper_strategy import ScraperStrategy
from .filters import FilterChain
from .scorers import URLScorer
from .models import ScraperResult
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
logging.basicConfig(level=logging.DEBUG)

rate_limiter = AsyncLimiter(1, 1)  # 1 request per second

class BFSScraperStrategy(ScraperStrategy):
    def __init__(self, max_depth: int, filter_chain: FilterChain, url_scorer: URLScorer, max_concurrent: int = 5):
        self.max_depth = max_depth
        self.filter_chain = filter_chain
        self.url_scorer = url_scorer
        self.max_concurrent = max_concurrent
        # 9. Crawl Politeness
        self.last_crawl_time = defaultdict(float)
        self.min_crawl_delay = 1  # 1 second delay between requests to the same domain
        # 5. Robots.txt Compliance
        self.robot_parsers = {}
    
    # Robots.txt Parser
    def get_robot_parser(self, url: str) -> RobotFileParser:
        domain = urlparse(url).netloc
        if domain not in self.robot_parsers:
            rp = RobotFileParser()
            rp.set_url(f"https://{domain}/robots.txt")
            rp.read()
            self.robot_parsers[domain] = rp
        return self.robot_parsers[domain]
    
    # Retry with exponential backoff
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def retry_crawl(self, crawler: AsyncWebCrawler, url: str) -> CrawlResult:
        return await crawler.arun(url)
    
    async def process_url(self, url: str, depth: int, crawler: AsyncWebCrawler, queue: asyncio.PriorityQueue, visited: set) -> CrawlResult:
        def normalize_url(url: str) -> str:
            parsed = urlparse(url)
            return urlunparse(parsed._replace(fragment=""))
        
        # URL Validation
        if not validators.url(url):
            logging.warning(f"Invalid URL: {url}")
            return None
        
        # Robots.txt Compliance
        if not self.get_robot_parser(url).can_fetch("YourUserAgent", url):
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
        
        # Content Type Checking
        # if 'text/html' not in crawl_result.response_header.get('Content-Type', ''):
        #     logging.info(f"Skipping non-HTML content: {url}")
        #     return crawl_result

        visited.add(url)

        # Process links
        for link_type in ["internal", "external"]:
            for link in crawl_result.links[link_type]:
                absolute_link = urljoin(url, link['href'])
                normalized_link = normalize_url(absolute_link)
                if self.filter_chain.apply(normalized_link) and normalized_link not in visited:
                    new_depth = depth + 1
                    if new_depth <= self.max_depth:
                        # URL Scoring
                        score = self.url_scorer.score(normalized_link)
                        await queue.put((score, new_depth, normalized_link))

        return crawl_result

    async def ascrape(self, start_url: str, crawler: AsyncWebCrawler) -> ScraperResult:
        queue = asyncio.PriorityQueue()
        queue.put_nowait((0, 0, start_url))
        visited = set()
        crawled_urls = []
        extracted_data = {}

        while not queue.empty():
            tasks = []
            while not queue.empty() and len(tasks) < self.max_concurrent:
                _, depth, url = await queue.get()
                if url not in visited:
                    task = asyncio.create_task(self.process_url(url, depth, crawler, queue, visited))
                    tasks.append(task)

            if tasks:
                results = await asyncio.gather(*tasks)
                for result in results:
                    if result:
                        crawled_urls.append(result.url)
                        extracted_data[result.url] = result

        return ScraperResult(url=start_url, crawled_urls=crawled_urls, extracted_data=extracted_data)