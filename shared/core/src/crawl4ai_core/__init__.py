"""Crawl4AI Core - Shared models, utilities, and configuration."""

__version__ = "0.1.0"

from .models import (
    CrawlRequest,
    CrawlResult,
    CrawlStatus,
    ServiceResponse,
    ErrorResponse,
)
from .config import Settings, get_settings
from .utils import sanitize_url, generate_id, format_timestamp

__all__ = [
    "CrawlRequest",
    "CrawlResult",
    "CrawlStatus",
    "ServiceResponse",
    "ErrorResponse",
    "Settings",
    "get_settings",
    "sanitize_url",
    "generate_id",
    "format_timestamp",
]
