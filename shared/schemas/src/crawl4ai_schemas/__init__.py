"""Crawl4AI Schemas - API request/response models for all services."""

__version__ = "0.1.0"

from .browser import BrowserRequest, BrowserResponse, PageAction
from .scraping import ScrapingRequest, ScrapingResponse
from .extraction import ExtractionRequest, ExtractionResponse, ExtractionSchema
from .filtering import FilteringRequest, FilteringResponse, FilterType

__all__ = [
    "BrowserRequest",
    "BrowserResponse",
    "PageAction",
    "ScrapingRequest",
    "ScrapingResponse",
    "ExtractionRequest",
    "ExtractionResponse",
    "ExtractionSchema",
    "FilteringRequest",
    "FilteringResponse",
    "FilterType",
]
