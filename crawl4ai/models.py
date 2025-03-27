from re import U
from pydantic import BaseModel, Field, HttpUrl, PrivateAttr
from typing import List, Dict, Optional, Callable, Awaitable, Union, Any
from enum import Enum
from dataclasses import dataclass
from .ssl_certificate import SSLCertificate
from datetime import datetime
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
    start_time: Union[datetime, float]
    end_time: Union[datetime, float]
    error_message: str = ""


class CrawlStatus(Enum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# @dataclass
# class CrawlStats:
#     task_id: str
#     url: str
#     status: CrawlStatus
#     start_time: Optional[datetime] = None
#     end_time: Optional[datetime] = None
#     memory_usage: float = 0.0
#     peak_memory: float = 0.0
#     error_message: str = ""

#     @property
#     def duration(self) -> str:
#         if not self.start_time:
#             return "0:00"
#         end = self.end_time or datetime.now()
#         duration = end - self.start_time
#         return str(timedelta(seconds=int(duration.total_seconds())))


@dataclass
class CrawlStats:
    task_id: str
    url: str
    status: CrawlStatus
    start_time: Optional[Union[datetime, float]] = None
    end_time: Optional[Union[datetime, float]] = None
    memory_usage: float = 0.0
    peak_memory: float = 0.0
    error_message: str = ""

    @property
    def duration(self) -> str:
        if not self.start_time:
            return "0:00"
            
        # Convert start_time to datetime if it's a float
        start = self.start_time
        if isinstance(start, float):
            start = datetime.fromtimestamp(start)
            
        # Get end time or use current time
        end = self.end_time or datetime.now()
        # Convert end_time to datetime if it's a float
        if isinstance(end, float):
            end = datetime.fromtimestamp(end)
            
        duration = end - start
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

    def __str__(self):
        return self.raw_markdown

@dataclass
class TraversalStats:
    """Statistics for the traversal process"""

    start_time: datetime = datetime.now()
    urls_processed: int = 0
    urls_failed: int = 0
    urls_skipped: int = 0
    total_depth_reached: int = 0
    current_depth: int = 0

class DispatchResult(BaseModel):
    task_id: str
    memory_usage: float
    peak_memory: float
    start_time: Union[datetime, float]
    end_time: Union[datetime, float]
    error_message: str = ""

class CrawlResult(BaseModel):
    url: str = Field(
        description="The final or actual URL crawled (in case of redirects).",
    )
    html: str = Field(
        description="Original, unmodified page HTML. Good for debugging or custom processing.",
    )
    success: bool = Field(
        description="True if the crawl completed without major errors, else False.",
    )
    cleaned_html: Optional[str] = Field(
        description="Sanitized HTML with scripts/styles removed; can exclude tags if configured via excluded_tags etc.",
        default=None,
    )
    media: Dict[str, List[Dict]] = Field(
        description="Extracted media info (images, audio, etc.), each with attributes like src, alt, score, etc.",
        default_factory=dict,
    )
    links: Dict[str, List[Dict]] = Field(
        description="Extracted link data, split by internal and external. Each link usually has href, text, etc.",
        default_factory=dict,
    )
    downloaded_files: Optional[List[str]] = Field(
        description="If accept_downloads=True in BrowserConfig, this lists the filepaths of saved downloads.",
        default=None,
    )
    js_execution_result: Optional[Dict[str, Any]] = Field(
        description="The result of executing JavaScript code on the page.",
        default=None,
    )
    screenshot: Optional[str] = Field(
        description="Screenshot of the page (base64-encoded) if screenshot=True.",
        default=None,
    )
    pdf: Optional[bytes] = Field(
        description="PDF of the page if pdf=True.",
        default=None,
    )
    _markdown: Optional[MarkdownGenerationResult] = PrivateAttr(
        default=None,
    )
    extracted_content: Optional[str] = Field(
        description="The output of a structured extraction (CSS/LLM-based) stored as JSON string or other text.",
        default=None,
    )
    metadata: Optional[dict] = Field(
        description="Additional info about the crawl or extracted data.",
        default=None,
    )
    error_message: Optional[str] = Field(
        description="If success=False, contains a short description of what went wrong.",
        default=None,
    )
    session_id: Optional[str] = Field(
        description="The ID of the session used for multi-page or persistent crawling.",
        default=None,
    )
    response_headers: Optional[dict] = Field(
        description="HTTP response headers, if captured.",
        default=None,
    )
    status_code: Optional[int] = Field(
        description="HTTP status code (e.g., 200 for OK).",
        default=None,
    )
    ssl_certificate: Optional[SSLCertificate] = Field(
        description="SSL certificate info if fetch_ssl_certificate=True.",
        default=None,
    )
    dispatch_result: Optional[DispatchResult] = Field(
        description="Object containing dispatch process details.",
        default=None,
    )
    redirected_url: Optional[str] = Field(
        description="The URL the page was redirected to, if any.",
        default=None,
    )

    class Config:
        arbitrary_types_allowed = True

# NOTE: The StringCompatibleMarkdown class, custom __init__ method, property getters/setters,
# and model_dump override all exist to support a smooth transition from markdown as a string
# to markdown as a MarkdownGenerationResult object, while maintaining backward compatibility.
# 
# This allows code that expects markdown to be a string to continue working, while also
# providing access to the full MarkdownGenerationResult object's properties.
# 
# The markdown_v2 property is deprecated and raises an error directing users to use markdown.
# 
# When backward compatibility is no longer needed in future versions, this entire mechanism
# can be simplified to a standard field with no custom accessors or serialization logic.
    
    def __init__(self, **data):
        markdown_result = data.pop('markdown', None)
        super().__init__(**data)
        if markdown_result is not None:
            self._markdown = (
                MarkdownGenerationResult(**markdown_result)
                if isinstance(markdown_result, dict)
                else markdown_result
            )
    
    @property
    def markdown(self):
        """
        Property that returns a StringCompatibleMarkdown object that behaves like
        a string but also provides access to MarkdownGenerationResult attributes.
        
        This approach allows backward compatibility with code that expects 'markdown'
        to be a string, while providing access to the full MarkdownGenerationResult.
        """
        if self._markdown is None:
            return None
        return StringCompatibleMarkdown(self._markdown)
    
    @markdown.setter
    def markdown(self, value):
        """
        Setter for the markdown property.
        """
        self._markdown = value
    
    @property
    def markdown_v2(self):
        """
        Deprecated property that raises an AttributeError when accessed.

        This property exists to inform users that 'markdown_v2' has been
        deprecated and they should use 'markdown' instead.
        """
        raise AttributeError(
            "The 'markdown_v2' attribute is deprecated and has been removed. "
            """Please use 'markdown' instead, which now returns a MarkdownGenerationResult, with
            following properties:
            - raw_markdown: The raw markdown string
            - markdown_with_citations: The markdown string with citations
            - references_markdown: The markdown string with references
            - fit_markdown: The markdown string with fit text
            """
        )
    
    @property
    def fit_markdown(self):
        """
        Deprecated property that raises an AttributeError when accessed.
        """
        raise AttributeError(
            "The 'fit_markdown' attribute is deprecated and has been removed. "
            "Please use 'markdown.fit_markdown' instead."
        )
    
    @property
    def fit_html(self):
        """
        Deprecated property that raises an AttributeError when accessed.
        """
        raise AttributeError(
            "The 'fit_html' attribute is deprecated and has been removed. "
            "Please use 'markdown.fit_html' instead."
        )

    def model_dump(self, *args, **kwargs):
        """
        Override model_dump to include the _markdown private attribute in serialization.
        
        This override is necessary because:
        1. PrivateAttr fields are excluded from serialization by default
        2. We need to maintain backward compatibility by including the 'markdown' field
           in the serialized output
        3. We're transitioning from 'markdown_v2' to enhancing 'markdown' to hold
           the same type of data
        
        Future developers: This method ensures that the markdown content is properly
        serialized despite being stored in a private attribute. If the serialization
        requirements change, this is where you would update the logic.
        """
        result = super().model_dump(*args, **kwargs)
        if self._markdown is not None:
            result["markdown"] = self._markdown.model_dump() 
        return result

class StringCompatibleMarkdown(str):
    """A string subclass that also provides access to MarkdownGenerationResult attributes"""
    def __new__(cls, markdown_result):
        return super().__new__(cls, markdown_result.raw_markdown)
    
    def __init__(self, markdown_result):
        self._markdown_result = markdown_result
    
    def __getattr__(self, name):
        return getattr(self._markdown_result, name)

# END of backward compatibility code for markdown/markdown_v2.
# When removing this code in the future, make sure to:
# 1. Replace the private attribute and property with a standard field
# 2. Update any serialization logic that might depend on the current behavior

class AsyncCrawlResponse(BaseModel):
    html: str
    response_headers: Dict[str, str]
    js_execution_result: Optional[Dict[str, Any]] = None
    status_code: int
    screenshot: Optional[str] = None
    pdf_data: Optional[bytes] = None
    get_delayed_content: Optional[Callable[[Optional[float]], Awaitable[str]]] = None
    downloaded_files: Optional[List[str]] = None
    ssl_certificate: Optional[SSLCertificate] = None
    redirected_url: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


###############################
# Scraping Models
###############################
class MediaItem(BaseModel):
    src: Optional[str] = ""
    data: Optional[str] = ""
    alt: Optional[str] = ""
    desc: Optional[str] = ""
    score: Optional[int] = 0
    type: str = "image"
    group_id: Optional[int] = 0
    format: Optional[str] = None
    width: Optional[int] = None


class Link(BaseModel):
    href: Optional[str] = ""
    text: Optional[str] = ""
    title: Optional[str] = ""
    base_domain: Optional[str] = ""


class Media(BaseModel):
    images: List[MediaItem] = []
    videos: List[
        MediaItem
    ] = []  # Using MediaItem model for now, can be extended with Video model if needed
    audios: List[
        MediaItem
    ] = []  # Using MediaItem model for now, can be extended with Audio model if needed


class Links(BaseModel):
    internal: List[Link] = []
    external: List[Link] = []


class ScrapingResult(BaseModel):
    cleaned_html: str
    success: bool
    media: Media = Media()
    links: Links = Links()
    metadata: Dict[str, Any] = {}
