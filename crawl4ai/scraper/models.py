from pydantic import BaseModel
from typing import List, Dict

class ScraperResult(BaseModel):
    url: str
    crawled_urls: List[str]
    extracted_data: Dict