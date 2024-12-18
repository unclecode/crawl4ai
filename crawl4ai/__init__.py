# __init__.py

from .async_webcrawler import AsyncWebCrawler, CacheMode
from .async_configs import BrowserConfig, CrawlerRunConfig
from .extraction_strategy import ExtractionStrategy, LLMExtractionStrategy, CosineStrategy, JsonCssExtractionStrategy
from .chunking_strategy import ChunkingStrategy, RegexChunking
from .markdown_generation_strategy import DefaultMarkdownGenerator
from .content_filter_strategy import PruningContentFilter, BM25ContentFilter
from .models import CrawlResult
from .__version__ import __version__

__all__ = [
    "AsyncWebCrawler",
    "CrawlResult",
    "CacheMode",
    'BrowserConfig',
    'CrawlerRunConfig',
    'ExtractionStrategy',
    'LLMExtractionStrategy',
    'CosineStrategy',
    'JsonCssExtractionStrategy',
    'ChunkingStrategy',
    'RegexChunking',
    'DefaultMarkdownGenerator',
    'PruningContentFilter',
    'BM25ContentFilter',
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
        import warnings
        print("Warning: Failed to import WebCrawler even though selenium is installed. This might be due to other missing dependencies.")
else:
    WebCrawler = None
    # import warnings
    # print("Warning: Synchronous WebCrawler is not available. Install crawl4ai[sync] for synchronous support. However, please note that the synchronous version will be deprecated soon.")