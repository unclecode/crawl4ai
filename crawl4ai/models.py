from pydantic import BaseModel, HttpUrl
from typing import List

class UrlModel(BaseModel):
    url: HttpUrl
    forced: bool = False

class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: str = None
    markdown: str = None
    extracted_content: str = None
    metadata: dict = None
    error_message: str = None