
"""
Crawl4AI Models Module

This module contains Pydantic models used throughout the Crawl4AI library.

Key Features:
- ORJSONModel: Base model with ORJSON serialization support
- DeprecatedPropertiesMixin: Global system for handling deprecated properties
- CrawlResult: Main result model with backward compatibility support

Deprecated Properties System:
The DeprecatedPropertiesMixin provides a global way to handle deprecated properties
across all models. Instead of manually excluding deprecated properties in each
model_dump() call, you can simply override the get_deprecated_properties() method:

Example:
    class MyModel(ORJSONModel):
        name: str
        old_field: Optional[str] = None
        
        def get_deprecated_properties(self) -> set[str]:
            return {'old_field', 'another_deprecated_field'}
        
        @property
        def old_field(self):
            raise AttributeError("old_field is deprecated, use name instead")

The system automatically excludes these properties from serialization, preventing
property objects from appearing in JSON output.
"""

from pydantic import BaseModel, ConfigDict,HttpUrl, PrivateAttr, Field
from typing import List, Dict, Optional, Callable, Awaitable, Union, Any
from typing import AsyncGenerator
from typing import Generic, TypeVar
from enum import Enum
from dataclasses import dataclass
from .ssl_certificate import SSLCertificate
from datetime import datetime
from datetime import timedelta

import orjson
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
    retry_count: int = 0
    wait_time: float = 0.0
    
    @property
    def success(self) -> bool:
        return self.result.success

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
    start_time: Optional[Union[datetime, float]] = None
    end_time: Optional[Union[datetime, float]] = None
    memory_usage: float = 0.0
    peak_memory: float = 0.0
    error_message: str = ""
    wait_time: float = 0.0
    retry_count: int = 0
    counted_requeue: bool = False

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


def orjson_default(obj):
    # Handle datetime (if not already handled by orjson)
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Handle property objects (convert to string or something else)
    if isinstance(obj, property):
        return str(obj)

    # Last resort: convert to string
    return str(obj)


class DeprecatedPropertiesMixin:
    """
    Mixin to handle deprecated properties in Pydantic models.
    
    Classes that inherit from this mixin can define deprecated properties
    that will be automatically excluded from serialization.
    
    Usage:
    1. Override the get_deprecated_properties() method to return a set of deprecated property names
    2. The model_dump method will automatically exclude these properties
    
    Example:
        class MyModel(ORJSONModel):
            def get_deprecated_properties(self) -> set[str]:
                return {'old_field', 'legacy_property'}
            
            name: str
            old_field: Optional[str] = None  # Field definition
            
            @property
            def old_field(self):  # Property that overrides the field
                raise AttributeError("old_field is deprecated, use name instead")
    """
    
    def get_deprecated_properties(self) -> set[str]:
        """
        Get deprecated property names for this model.
        Override this method in subclasses to define deprecated properties.
        
        Returns:
            set[str]: Set of deprecated property names
        """
        return set()
    
    @classmethod
    def get_all_deprecated_properties(cls) -> set[str]:
        """
        Get all deprecated properties from this class and all parent classes.
        
        Returns:
            set[str]: Set of all deprecated property names
        """
        deprecated_props = set()
        # Create an instance to call the instance method
        try:
            # Try to create a dummy instance to get deprecated properties
            dummy_instance = cls.__new__(cls)
            deprecated_props.update(dummy_instance.get_deprecated_properties())
        except Exception:
            # If we can't create an instance, check for class-level definitions
            pass
            
        # Also check parent classes
        for klass in cls.__mro__:
            if hasattr(klass, 'get_deprecated_properties') and klass != DeprecatedPropertiesMixin:
                try:
                    dummy_instance = klass.__new__(klass)
                    deprecated_props.update(dummy_instance.get_deprecated_properties())
                except Exception:
                    pass
        return deprecated_props
    
    def model_dump(self, *args, **kwargs):
        """
        Override model_dump to automatically exclude deprecated properties.
        
        This method:
        1. Gets the existing exclude set from kwargs
        2. Adds all deprecated properties defined in get_deprecated_properties()
        3. Calls the parent model_dump with the updated exclude set
        """
        # Get the default exclude set, or create empty set if None
        exclude = kwargs.get('exclude', set())
        if exclude is None:
            exclude = set()
        elif not isinstance(exclude, set):
            exclude = set(exclude) if exclude else set()
        
        # Add deprecated properties for this instance
        exclude.update(self.get_deprecated_properties())
        kwargs['exclude'] = exclude
        
        return super().model_dump(*args, **kwargs)


class ORJSONModel(DeprecatedPropertiesMixin, BaseModel):
    model_config = ConfigDict(
        ser_json_timedelta="iso8601",  # Optional: format timedelta
        ser_json_bytes="utf8",         # Optional: bytes → UTF-8 string
    )
    
    def model_dump_json(self, **kwargs) -> bytes:
        """Custom JSON serialization using orjson"""
        return orjson.dumps(self.model_dump(**kwargs), default=orjson_default)
    
    @classmethod
    def model_validate_json(cls, json_data: Union[str, bytes], **kwargs):
        """Custom JSON deserialization using orjson"""
        if isinstance(json_data, str):
            json_data = json_data.encode()
        return cls.model_validate(orjson.loads(json_data), **kwargs)
class UrlModel(ORJSONModel):
    url: HttpUrl
    forced: bool = False



@dataclass
class TraversalStats:
    """Statistics for the traversal process"""

    start_time: datetime = datetime.now()
    urls_processed: int = 0
    urls_failed: int = 0
    urls_skipped: int = 0
    total_depth_reached: int = 0
    current_depth: int = 0

class DispatchResult(ORJSONModel):
    task_id: str
    memory_usage: float
    peak_memory: float
    start_time: Union[datetime, float]
    end_time: Union[datetime, float]
    error_message: str = ""

class MarkdownGenerationResult(ORJSONModel):
    raw_markdown: str
    markdown_with_citations: str
    references_markdown: str
    fit_markdown: Optional[str] = None
    fit_html: Optional[str] = None

    def __str__(self):
        return self.raw_markdown
    
class CrawlResult(ORJSONModel):
    url: str
    html: str
    fit_html: Optional[str] = None
    success: bool
    cleaned_html: Optional[str] = None
    media: Dict[str, List[Dict]] = {}
    links: Dict[str, List[Dict]] = {}
    downloaded_files: Optional[List[str]] = None
    js_execution_result: Optional[Dict[str, Any]] = None
    screenshot: Optional[str] = None
    pdf: Optional[bytes] = None
    mhtml: Optional[str] = None
    _markdown: Optional[MarkdownGenerationResult] = PrivateAttr(default=None)
    extracted_content: Optional[str] = None
    metadata: Optional[dict] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    response_headers: Optional[dict] = None
    status_code: Optional[int] = None
    ssl_certificate: Optional[SSLCertificate] = None
    dispatch_result: Optional[DispatchResult] = None
    redirected_url: Optional[str] = None
    network_requests: Optional[List[Dict[str, Any]]] = None
    console_messages: Optional[List[Dict[str, Any]]] = None
    tables: List[Dict] = Field(default_factory=list)  # NEW – [{headers,rows,caption,summary}]

    class Config:
        arbitrary_types_allowed = True

    def get_deprecated_properties(self) -> set[str]:
        """Define deprecated properties that should be excluded from serialization."""
        return {'fit_html', 'fit_markdown', 'markdown_v2'}

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
        3. Uses the DeprecatedPropertiesMixin to automatically exclude deprecated properties
        
        Future developers: This method ensures that the markdown content is properly
        serialized despite being stored in a private attribute. The deprecated properties
        are automatically handled by the mixin.
        """
        # Use the parent class method which handles deprecated properties automatically
        result = super().model_dump(*args, **kwargs)
        
        # Add the markdown content if it exists
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

CrawlResultT = TypeVar('CrawlResultT', bound=CrawlResult)

class CrawlResultContainer(Generic[CrawlResultT]):
    def __init__(self, results: Union[CrawlResultT, List[CrawlResultT]]):
        # Normalize to a list
        if isinstance(results, list):
            self._results = results
        else:
            self._results = [results]

    def __iter__(self):
        return iter(self._results)

    def __getitem__(self, index):
        return self._results[index]

    def __len__(self):
        return len(self._results)

    def __getattr__(self, attr):
        # Delegate attribute access to the first element.
        if self._results:
            return getattr(self._results[0], attr)
        raise AttributeError(f"{self.__class__.__name__} object has no attribute '{attr}'")

    def __repr__(self):
        return f"{self.__class__.__name__}({self._results!r})"

RunManyReturn = Union[
    CrawlResultContainer[CrawlResultT],
    AsyncGenerator[CrawlResultT, None]
]


# END of backward compatibility code for markdown/markdown_v2.
# When removing this code in the future, make sure to:
# 1. Replace the private attribute and property with a standard field
# 2. Update any serialization logic that might depend on the current behavior

class AsyncCrawlResponse(ORJSONModel):
    html: str
    response_headers: Dict[str, str]
    js_execution_result: Optional[Dict[str, Any]] = None
    status_code: int
    screenshot: Optional[str] = None
    pdf_data: Optional[bytes] = None
    mhtml_data: Optional[str] = None
    get_delayed_content: Optional[Callable[[Optional[float]], Awaitable[str]]] = None
    downloaded_files: Optional[List[str]] = None
    ssl_certificate: Optional[SSLCertificate] = None
    redirected_url: Optional[str] = None
    network_requests: Optional[List[Dict[str, Any]]] = None
    console_messages: Optional[List[Dict[str, Any]]] = None

    class Config:
        arbitrary_types_allowed = True

###############################
# Scraping Models
###############################
class MediaItem(ORJSONModel):
    src: Optional[str] = ""
    data: Optional[str] = ""
    alt: Optional[str] = ""
    desc: Optional[str] = ""
    score: Optional[int] = 0
    type: str = "image"
    group_id: Optional[int] = 0
    format: Optional[str] = None
    width: Optional[int] = None


class Link(ORJSONModel):
    href: Optional[str] = ""
    text: Optional[str] = ""
    title: Optional[str] = ""
    base_domain: Optional[str] = ""
    head_data: Optional[Dict[str, Any]] = None  # Head metadata extracted from link target
    head_extraction_status: Optional[str] = None  # "success", "failed", "skipped"
    head_extraction_error: Optional[str] = None  # Error message if extraction failed
    intrinsic_score: Optional[float] = None  # Quality score based on URL structure, text, and context
    contextual_score: Optional[float] = None  # BM25 relevance score based on query and head content
    total_score: Optional[float] = None  # Combined score from intrinsic and contextual scores


class Media(ORJSONModel):
    images: List[MediaItem] = []
    videos: List[
        MediaItem
    ] = []  # Using MediaItem model for now, can be extended with Video model if needed
    audios: List[
        MediaItem
    ] = []  # Using MediaItem model for now, can be extended with Audio model if needed
    tables: List[Dict] = []  # Table data extracted from HTML tables


class Links(ORJSONModel):
    internal: List[Link] = []
    external: List[Link] = []


class ScrapingResult(ORJSONModel):
    cleaned_html: str
    success: bool
    media: Media = Media()
    links: Links = Links()
    metadata: Dict[str, Any] = {}
