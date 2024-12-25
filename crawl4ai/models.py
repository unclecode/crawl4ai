from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional, Callable, Awaitable, Union
from typing_extensions import TypedDict



class UrlModel(BaseModel):
    url: HttpUrl
    forced: bool = False

class MarkdownGenerationResult(BaseModel):
    raw_markdown: str
    markdown_with_citations: str
    references_markdown: str
    fit_markdown: Optional[str] = None
    fit_html: Optional[str] = None

class SecurityDetails(TypedDict):
    issuer: Optional[str]
    protocol: Optional[str]
    subjectName: Optional[str]
    validFrom: Optional[float]
    validTo: Optional[float]

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
    ssl_certificate: Optional[SecurityDetails] = None
    status_code: Optional[int] = None


class AsyncCrawlResponse(BaseModel):
    html: str
    response_headers: Dict[str, str]
    status_code: int
    ssl_certificate: Optional[SecurityDetails] = None
    screenshot: Optional[str] = None
    pdf_data: Optional[bytes] = None
    get_delayed_content: Optional[Callable[[Optional[float]], Awaitable[str]]] = None
    downloaded_files: Optional[List[str]] = None

    class Config:
        arbitrary_types_allowed = True


