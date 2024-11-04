# __init__.py

from .async_webcrawler import AsyncWebCrawler
from .models import CrawlResult
from ._version import __version__
# __version__ = "0.3.73"

__all__ = [
    "AsyncWebCrawler",
    "CrawlResult",
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
    import warnings
    print("Warning: Synchronous WebCrawler is not available. Install crawl4ai[sync] for synchronous support. However, please note that the synchronous version will be deprecated soon.")