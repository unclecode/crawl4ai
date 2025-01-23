# __init__.py

from .async_webcrawler import AsyncWebCrawler, CacheMode
from .async_configs import BrowserConfig, CrawlerRunConfig
from .content_scraping_strategy import (
    ContentScrapingStrategy,
    WebScrapingStrategy,
    LXMLWebScrapingStrategy,
)
from .extraction_strategy import (
    ExtractionStrategy,
    LLMExtractionStrategy,
    CosineStrategy,
    JsonCssExtractionStrategy,
    JsonXPathExtractionStrategy
)
from .chunking_strategy import ChunkingStrategy, RegexChunking
from .markdown_generation_strategy import DefaultMarkdownGenerator
from .content_filter_strategy import PruningContentFilter, BM25ContentFilter, LLMContentFilter, RelevantContentFilter
from .models import CrawlResult, MarkdownGenerationResult
from .async_dispatcher import (
    MemoryAdaptiveDispatcher,
    SemaphoreDispatcher,
    RateLimiter,
    CrawlerMonitor,
    DisplayMode,
    BaseDispatcher
)

__all__ = [
    "AsyncWebCrawler",
    "CrawlResult",
    "CacheMode",
    "ContentScrapingStrategy",
    "WebScrapingStrategy",
    "LXMLWebScrapingStrategy",
    "BrowserConfig",
    "CrawlerRunConfig",
    "ExtractionStrategy",
    "LLMExtractionStrategy",
    "CosineStrategy",
    "JsonCssExtractionStrategy",
    "JsonXPathExtractionStrategy",
    "ChunkingStrategy",
    "RegexChunking",
    "DefaultMarkdownGenerator",
    "RelevantContentFilter",
    "PruningContentFilter",
    "BM25ContentFilter",
    "LLMContentFilter",
    "BaseDispatcher",
    "MemoryAdaptiveDispatcher",
    "SemaphoreDispatcher",
    "RateLimiter",
    "CrawlerMonitor",
    "DisplayMode",
    "MarkdownGenerationResult",
]


def is_sync_version_installed():
    try:
        import selenium

        return True
    except ImportError:
        return False


if is_sync_version_installed():
    try:
        from .web_crawler import WebCrawler

        __all__.append("WebCrawler")
    except ImportError:
        print(
            "Warning: Failed to import WebCrawler even though selenium is installed. This might be due to other missing dependencies."
        )
else:
    WebCrawler = None
    # import warnings
    # print("Warning: Synchronous WebCrawler is not available. Install crawl4ai[sync] for synchronous support. However, please note that the synchronous version will be deprecated soon.")

import warnings
from pydantic import warnings as pydantic_warnings

# Disable all Pydantic warnings
warnings.filterwarnings("ignore", module="pydantic")
# pydantic_warnings.filter_warnings()