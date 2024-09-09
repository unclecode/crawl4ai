from .scraper_strategy import ScraperStrategy
from .filters import FilterChain
from .scorers import URLScorer
from .models import ScraperResult
from ..models import CrawlResult
from ..async_webcrawler import AsyncWebCrawler
import asyncio
from urllib.parse import urljoin

class BFSScraperStrategy(ScraperStrategy):
    def __init__(self, max_depth: int, filter_chain: FilterChain, url_scorer: URLScorer):
        self.max_depth = max_depth
        self.filter_chain = filter_chain
        self.url_scorer = url_scorer

    async def ascrape(self, start_url: str, initial_crawl_result: CrawlResult, crawler: AsyncWebCrawler) -> ScraperResult:
        queue = asyncio.PriorityQueue()
        queue.put_nowait((0, 0, start_url))  # (score, depth, url)
        visited = set()
        crawled_urls = []
        extracted_data = {}

        while not queue.empty():
            _, depth, url = await queue.get()
            if depth > self.max_depth or url in visited:
                continue
            crawl_result = initial_crawl_result if url == start_url else await crawler.arun(url)
            visited.add(url)
            crawled_urls.append(url)
            extracted_data[url]=crawl_result
            if crawl_result.success == False:
                print(f"failed to crawl -- {url}")
                continue
            for internal in crawl_result.links["internal"]:
                link = internal['href']
                is_special_uri = any(link.startswith(scheme) for scheme in ('tel:', 'mailto:', 'sms:', 'geo:', 'fax:', 'file:', 'data:', 'sip:', 'ircs:', 'magnet:'))
                is_fragment = '#' in link
                if not (is_fragment or is_special_uri):
                    # To fix partial links: eg:'/support' to 'https://example.com/support'
                    absolute_link = urljoin(url, link)
                    if self.filter_chain.apply(absolute_link) and absolute_link not in visited:
                        score = self.url_scorer.score(absolute_link)
                        await queue.put((1 / score, depth + 1, absolute_link))
            for external in crawl_result.links["external"]:
                link = external['href']
                if self.filter_chain.apply(link) and link not in visited:
                    score = self.url_scorer.score(link)
                    await queue.put((1 / score, depth + 1, link))

        return ScraperResult(url=start_url, crawled_urls=crawled_urls, extracted_data=extracted_data)