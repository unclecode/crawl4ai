from pydantic import BaseModel
from typing import List, Dict
from ..models import CrawlResult

class ScraperResult(BaseModel):
    url: str
    crawled_urls: List[str]
    extracted_data: Dict[str,CrawlResult]