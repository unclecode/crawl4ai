from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional, Callable, Awaitable, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from .ssl_certificate import SSLCertificate

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from datetime import timedelta



###############################
# Dispatcher Models
###############################
@dataclass
class DomainState:
    last_request_time: float = 0
    current_delay: float = 0
    fail_count: int = 0

@dataclass
class CrawlerTaskResult:
    task_id: str
    url: str
    result: "CrawlResult"
    memory_usage: float
    peak_memory: float
    start_time: datetime
    end_time: datetime
    error_message: str = ""

class CrawlStatus(Enum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class CrawlStats:
    task_id: str
    url: str
    status: CrawlStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    memory_usage: float = 0.0
    peak_memory: float = 0.0
    error_message: str = ""
    
    @property
    def duration(self) -> str:
        if not self.start_time:
            return "0:00"
        end = self.end_time or datetime.now()
        duration = end - self.start_time
        return str(timedelta(seconds=int(duration.total_seconds())))

class DisplayMode(Enum):
    DETAILED = "DETAILED"
    AGGREGATED = "AGGREGATED"

###############################
# Crawler Models
###############################
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

class DispatchResult(BaseModel):
    task_id: str
    memory_usage: float
    peak_memory: float
    start_time: datetime
    end_time: datetime
    error_message: str = ""
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
    dispatch_result: Optional[DispatchResult] = None
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
