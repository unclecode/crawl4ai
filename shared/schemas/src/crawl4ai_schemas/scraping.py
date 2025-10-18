"""Content scraping service API schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScrapingRequest(BaseModel):
    """Request to content scraping service."""

    html: str = Field(description="HTML content to scrape")
    extract_links: bool = Field(default=False, description="Extract all links")
    extract_images: bool = Field(default=False, description="Extract all images")
    extract_media: bool = Field(default=False, description="Extract media elements")
    extract_metadata: bool = Field(default=False, description="Extract page metadata")
    base_url: Optional[str] = Field(
        default=None, description="Base URL for relative links"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ScrapingResponse(BaseModel):
    """Response from content scraping service."""

    success: bool = Field(description="Whether scraping was successful")
    text: Optional[str] = Field(default=None, description="Extracted plain text")
    links: List[str] = Field(default_factory=list, description="Extracted links")
    images: List[Dict[str, str]] = Field(
        default_factory=list, description="Extracted images with metadata"
    )
    media: List[Dict[str, str]] = Field(
        default_factory=list, description="Extracted media elements"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Page metadata")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    duration_ms: float = Field(description="Processing duration in milliseconds")
