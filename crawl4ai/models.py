from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional, Callable, Awaitable, Union, Any
from dataclasses import dataclass
from .ssl_certificate import SSLCertificate

@dataclass
class TokenUsage:
    completion_tokens: int = 0
    prompt_tokens: int = 0 
    total_tokens: int = 0
    completion_tokens_details: Optional[dict] = None
    prompt_tokens_details: Optional[dict] = None
    

class UrlModel(BaseModel):
    url: HttpUrl
    forced: bool = False

class MarkdownGenerationResult(BaseModel):
    raw_markdown: str
    markdown_with_citations: str
    references_markdown: str
    fit_markdown: Optional[str] = None
    fit_html: Optional[str] = None

class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: Optional[str] = None
    media: Dict[str, List[Dict]] = {}
    links: Dict[str, List[Dict]] = {}
    downloaded_files: Optional[List[str]] = None
    screenshot: Optional[str] = None
    pdf : Optional[bytes] = None
    markdown: Optional[Union[str, MarkdownGenerationResult]] = None
    markdown_v2: Optional[MarkdownGenerationResult] = None
    fit_markdown: Optional[str] = None
    fit_html: Optional[str] = None
    extracted_content: Optional[str] = None
    metadata: Optional[dict] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    response_headers: Optional[dict] = None
    status_code: Optional[int] = None
    ssl_certificate: Optional[SSLCertificate] = None
    class Config:
        arbitrary_types_allowed = True

class AsyncCrawlResponse(BaseModel):
    html: str
    response_headers: Dict[str, str]
    status_code: int
    screenshot: Optional[str] = None
    pdf_data: Optional[bytes] = None
    get_delayed_content: Optional[Callable[[Optional[float]], Awaitable[str]]] = None
    downloaded_files: Optional[List[str]] = None
    ssl_certificate: Optional[SSLCertificate] = None

    class Config:
        arbitrary_types_allowed = True
