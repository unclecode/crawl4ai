from pydantic import BaseModel, HttpUrl
from typing import List, Dict

class UrlModel(BaseModel):
    url: HttpUrl
    forced: bool = False

class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: str = None
    media: Dict[str, List[Dict]] = {}
    markdown: str = None
    extracted_content: str = None
    metadata: dict = None
    error_message: str = None