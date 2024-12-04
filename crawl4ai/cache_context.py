from enum import Enum


class CacheMode(Enum):
    """
    Defines the caching behavior for web crawling operations.
    
    Modes:
    - ENABLED: Normal caching behavior (read and write)
    - DISABLED: No caching at all
    - READ_ONLY: Only read from cache, don't write
    - WRITE_ONLY: Only write to cache, don't read
    - BYPASS: Bypass cache for this operation
    """
    ENABLED = "enabled"
    DISABLED = "disabled"
    READ_ONLY = "read_only"
    WRITE_ONLY = "write_only"
    BYPASS = "bypass"


class CacheContext:
    """
    Encapsulates cache-related decisions and URL handling.
    
    This class centralizes all cache-related logic and URL type checking,
    making the caching behavior more predictable and maintainable.
    """
    def __init__(self, url: str, cache_mode: CacheMode, always_bypass: bool = False):
        self.url = url
        self.cache_mode = cache_mode
        self.always_bypass = always_bypass
        self.is_cacheable = url.startswith(('http://', 'https://', 'file://'))
        self.is_web_url = url.startswith(('http://', 'https://'))
        self.is_local_file = url.startswith("file://")
        self.is_raw_html = url.startswith("raw:")
        self._url_display = url if not self.is_raw_html else "Raw HTML"
    
    def should_read(self) -> bool:
        """Determines if cache should be read based on context."""
        if self.always_bypass or not self.is_cacheable:
            return False
        return self.cache_mode in [CacheMode.ENABLED, CacheMode.READ_ONLY]
    
    def should_write(self) -> bool:
        """Determines if cache should be written based on context."""
        if self.always_bypass or not self.is_cacheable:
            return False
        return self.cache_mode in [CacheMode.ENABLED, CacheMode.WRITE_ONLY]
    
    @property
    def display_url(self) -> str:
        """Returns the URL in display format."""
        return self._url_display


def _legacy_to_cache_mode(
    disable_cache: bool = False,
    bypass_cache: bool = False,
    no_cache_read: bool = False,
    no_cache_write: bool = False
) -> CacheMode:
    """
    Converts legacy cache parameters to the new CacheMode enum.
    
    This is an internal function to help transition from the old boolean flags
    to the new CacheMode system.
    """
    if disable_cache:
        return CacheMode.DISABLED
    if bypass_cache:
        return CacheMode.BYPASS
    if no_cache_read and no_cache_write:
        return CacheMode.DISABLED
    if no_cache_read:
        return CacheMode.WRITE_ONLY
    if no_cache_write:
        return CacheMode.READ_ONLY
    return CacheMode.ENABLED
