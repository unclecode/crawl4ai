"""Crawl4AI Client SDK - HTTP clients for all microservices."""

__version__ = "0.1.0"

from .base import BaseClient
from .browser import BrowserClient
from .scraping import ScrapingClient
from .extraction import ExtractionClient
from .filtering import FilteringClient

__all__ = [
    "BaseClient",
    "BrowserClient",
    "ScrapingClient",
    "ExtractionClient",
    "FilteringClient",
]
