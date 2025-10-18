"""Core data models shared across all Crawl4AI microservices."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class CrawlStatus(str, Enum):
    """Status of a crawl job."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlRequest(BaseModel):
    """Request model for crawling a URL."""

    url: HttpUrl
    depth: int = Field(
        default=0, ge=0, le=10, description="Crawl depth (0 = single page)"
    )
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout in seconds")
    headless: bool = Field(default=True, description="Run browser in headless mode")
    user_agent: Optional[str] = Field(default=None, description="Custom user agent")
    wait_time: float = Field(
        default=0, ge=0, le=30, description="Wait time after page load"
    )
    screenshot: bool = Field(default=False, description="Capture screenshot")
    extract_links: bool = Field(default=False, description="Extract all links")
    extract_images: bool = Field(default=False, description="Extract all images")
    css_selector: Optional[str] = Field(
        default=None, description="CSS selector for extraction"
    )
    xpath: Optional[str] = Field(default=None, description="XPath for extraction")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class CrawlResult(BaseModel):
    """Result model for a completed crawl."""

    id: str = Field(description="Unique crawl job ID")
    url: str = Field(description="Crawled URL")
    status: CrawlStatus = Field(description="Crawl status")
    html: Optional[str] = Field(default=None, description="Raw HTML content")
    markdown: Optional[str] = Field(default=None, description="Markdown content")
    text: Optional[str] = Field(default=None, description="Extracted text")
    links: List[str] = Field(default_factory=list, description="Extracted links")
    images: List[str] = Field(default_factory=list, description="Extracted images")
    screenshot_path: Optional[str] = Field(
        default=None, description="Screenshot file path"
    )
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Extracted structured data"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )
    started_at: datetime = Field(description="Crawl start time")
    completed_at: Optional[datetime] = Field(
        default=None, description="Crawl completion time"
    )
    duration_seconds: Optional[float] = Field(
        default=None, description="Duration in seconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ServiceResponse(BaseModel):
    """Generic service response model."""

    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Response message")
    data: Optional[Any] = Field(default=None, description="Response data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
