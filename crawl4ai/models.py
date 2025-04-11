from __future__ import annotations
from pydantic import BaseModel, HttpUrl, PrivateAttr, Field
from typing import List, Dict, Optional, Callable, Awaitable, Union, Any, AsyncGenerator, Iterator, AsyncIterator
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
    result: CrawlResultContainer
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

        duration = end - start # pyright: ignore[reportOperatorIssue]
        return str(timedelta(seconds=int(duration.total_seconds()))) # pyright: ignore[reportAttributeAccessIssue]


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
    raw_markdown: str = ""
    markdown_with_citations: str = ""
    references_markdown: str = ""
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
    url: str
    html: str
    success: bool
    cleaned_html: Optional[str] = None
    media: Dict[str, List[Dict]] = Field(default_factory=dict)
    links: Dict[str, List[Dict]] = Field(default_factory=dict)
    downloaded_files: Optional[List[str]] = None
    js_execution_result: Optional[Dict[str, Any]] = None
    screenshot: Optional[str] = None
    pdf: Optional[bytes] = None
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

    def __init__(
        self,
        url: str,
        html: str,
        success: bool,
        cleaned_html: Optional[str] = None,
        media: Optional[Dict[str, List[Dict]]] = None,
        links: Optional[Dict[str, List[Dict]]] = None,
        downloaded_files: Optional[List[str]] = None,
        js_execution_result: Optional[Dict[str, Any]] = None,
        screenshot: Optional[str] = None,
        pdf: Optional[bytes] = None,
        markdown: Optional[Union[MarkdownGenerationResult, dict]] = None,
        extracted_content: Optional[str] = None,
        metadata: Optional[dict] = None,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
        response_headers: Optional[dict] = None,
        status_code: Optional[int] = None,
        ssl_certificate: Optional[SSLCertificate] = None,
        dispatch_result: Optional[DispatchResult] = None,
        redirected_url: Optional[str] = None
    ):
        super().__init__(
            url=url,
            html=html,
            success=success,
            cleaned_html=cleaned_html,
            media=media if media is not None else {},
            links=links if links is not None else {},
            downloaded_files=downloaded_files,
            js_execution_result=js_execution_result,
            screenshot=screenshot,
            pdf=pdf,
            extracted_content=extracted_content,
            metadata=metadata,
            error_message=error_message,
            session_id=session_id,
            response_headers=response_headers,
            status_code=status_code,
            ssl_certificate=ssl_certificate,
            dispatch_result=dispatch_result,
            redirected_url=redirected_url
        )
        if markdown is not None:
            self._markdown = (
                MarkdownGenerationResult(**markdown)
                if isinstance(markdown, dict)
                else markdown
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

CrawlResultsT = Union[
   CrawlResult, List[CrawlResult], AsyncGenerator[CrawlResult, None]
]

class CrawlResultContainer(CrawlResult):
    """A container class for crawl results.

    Provides a consistent interface for synchronous and asynchronous iteration
    as well as direct access to fields of first result and the length of the
    results.
    """
    # We use private attributes and a property for source to simplify the
    # implementation of __getattribute__.
    _source: CrawlResultsT = PrivateAttr()
    _results: List[CrawlResult] = PrivateAttr()

    def __init__(
        self,
        results: CrawlResultsT,
    ) -> None:
        result_list: List[CrawlResult]
        if isinstance(results, AsyncGenerator):
            result_list = []
        elif isinstance(results, List):
            result_list = results
        else:
            result_list = [results]

        if len(result_list) == 0:
            super().__init__(url="", html="", success=False)
        else:
            super().__init__(**result_list[0].model_dump())

        self._source = results
        self._results = result_list

    @property
    def source(self) -> CrawlResultsT:
        """Returns the source of the crawl results.

        :return: The source of the crawl results.
        :rtype: CrawlResultsT
        """
        return self._source

    def _raise_if_async_generator(self):
        """Raises a TypeError if the source is an AsyncGenerator.

        This is to prevent synchronous operations over an asynchronous source.

        :raises TypeError: If source is an AsyncGenerator.
        """
        if isinstance(self._source, AsyncGenerator):
            raise TypeError(
                "CrawlResultContainer source is an AsyncGenerator. Use __aiter__() to iterate over it."
            )

    def __iter__(self) -> Iterator[CrawlResult]: # pyright: ignore[reportIncompatibleMethodOverride]
        """Returns an iterator for the crawl results.

        This method is used for synchronous iteration.

        :return: An iterator for the crawl results.
        :rtype: Iterator[CrawlResult]
        :raises TypeError: If the source is an AsyncGenerator.
        """
        self._raise_if_async_generator()

        return iter(self._results)

    def __aiter__(self) -> AsyncIterator[CrawlResult]:
        """Returns an asynchronous iterator for the crawl results."""
        if isinstance(self._source, AsyncIterator):
            return self._source.__aiter__()

        async def async_iterator() -> AsyncIterator[CrawlResult]:
            for result in self._results:
                yield result

        return async_iterator()

    def __getitem__(self, index: int) -> CrawlResult:
        """Return the result at a given index.

        :param index: The index of the result to retrieve.
        :type index: int
        :return: The crawl result at the specified index.
        :rtype: CrawlResult
        :raises TypeError: If the source is an AsyncGenerator.
        :raises IndexError: If the index is out of range.
        """
        self._raise_if_async_generator()

        return self._results[index]

    def __len__(self) -> int:
        """Return the number of results in the container.

        :return: The number of results.
        :rtype: int
        :raises TypeError: If the source is an AsyncGenerator.
        """
        self._raise_if_async_generator()

        return len(self._results)

    def __getattribute__(self, attr: str) -> Any:
        """Return an attribute from the first result.

        :param attr: The name of the attribute to retrieve.
        :type attr: str
        :return: The attribute value from the first result if present.
        :rtype: Any
        :raises TypeError: If the source is an AsyncGenerator.
        :raises AttributeError: If the attribute does not exist.
        """
        if attr.startswith("_") or attr == "source":
            # Private attribute or known local field so just delegate to the parent class.
            return super().__getattribute__(attr)

        try:
            source: CrawlResultsT = self._source
        except (AttributeError, TypeError):
            # _source is not defined yet so we're in the __init__ method.
            # Just delegate to the parent class.
            return super().__getattribute__(attr)

        # We have a CrawlResult field.
        # Local test to avoid the additional lookups from calling _raise_if_async_generator.
        if isinstance(source, AsyncGenerator):
            raise TypeError(
                "CrawlResultContainer source is an AsyncGenerator. Use __aiter__() to iterate over it."
            )

        if not source:
            # Empty source so we can't return the attribute.
            raise AttributeError(f"{self.__class__.__name__} object has no results")

        # Delegate to the first result.
        return super().__getattribute__(attr)

    def __repr__(self) -> str:
        """Get a string representation of the container.

        The representation will be incomplete if the source is an AsyncIterator.
        :return: String representation of the container.
        :rtype: str
        """

        return f"{self.__class__.__name__}({self._results!r})"

class StringCompatibleMarkdown(str):
    """A string subclass that also provides access to MarkdownGenerationResult attributes"""
    def __new__(cls, markdown_result):
        return super().__new__(cls, markdown_result.raw_markdown)
    
    def __init__(self, markdown_result):
        self.markdown_result = markdown_result

    def __getattr__(self, name):
        return getattr(self.markdown_result, name)


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

    def __init__(self, **data):
        if "width" in data and data["width"] == "undefined":
            data["width"] = None

        super().__init__(**data)


class Link(BaseModel):
    href: Optional[str] = ""
    text: Optional[str] = ""
    title: Optional[str] = ""
    base_domain: Optional[str] = ""


class Media(BaseModel):
    images: List[MediaItem] = Field(default_factory=list)
    videos: List[MediaItem] = Field(
        default_factory=list
    )  # Using MediaItem model for now, can be extended with Video model if needed
    audios: List[MediaItem] = Field(
        default_factory=list
    )  # Using MediaItem model for now, can be extended with Audio model if needed
    tables: List[Dict] = Field(default_factory=list)  # Table data extracted from HTML tables


class Links(BaseModel):
    internal: List[Link] = Field(default_factory=list)
    external: List[Link] = Field(default_factory=list)


class ScrapingResult(BaseModel):
    cleaned_html: str
    success: bool
    media: Media = Media()
    links: Links = Links()
    metadata: Dict[str, Any] = Field(default_factory=dict)
