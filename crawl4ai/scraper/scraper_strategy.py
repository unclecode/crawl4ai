from abc import ABC, abstractmethod
from .models import ScraperResult
from ..models import CrawlResult
from ..async_webcrawler import AsyncWebCrawler

class ScraperStrategy(ABC):
    @abstractmethod
    async def ascrape(self, url: str, crawl_result: CrawlResult, crawler: AsyncWebCrawler) -> ScraperResult:
        pass