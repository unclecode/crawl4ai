from pydantic import BaseModel
from typing import List, Dict
from ..models import CrawlResult

class ScraperPageResult(BaseModel):
    result: CrawlResult
    depth: int
    score: float
class ScraperResult(BaseModel):
    url: str
    crawled_urls: List[str]
    extracted_data: Dict[str, ScraperPageResult]
