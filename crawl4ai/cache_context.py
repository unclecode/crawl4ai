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

    Attributes:
        url (str): The URL being processed.
        cache_mode (CacheMode): The cache mode for the current operation.
        always_bypass (bool): If True, bypasses caching for this operation.
        is_cacheable (bool): True if the URL is cacheable, False otherwise.
        is_web_url (bool): True if the URL is a web URL, False otherwise.
        is_local_file (bool): True if the URL is a local file, False otherwise.
        is_raw_html (bool): True if the URL is raw HTML, False otherwise.
        _url_display (str): The display name for the URL (web, local file, or raw HTML).
    """

    def __init__(self, url: str, cache_mode: CacheMode, always_bypass: bool = False):
        """
        Initializes the CacheContext with the provided URL and cache mode.

        Args:
            url (str): The URL being processed.
            cache_mode (CacheMode): The cache mode for the current operation.
            always_bypass (bool): If True, bypasses caching for this operation.
        """
        self.url = url
        self.cache_mode = cache_mode
        self.always_bypass = always_bypass
        self.is_cacheable = url.startswith(("http://", "https://", "file://"))
        self.is_web_url = url.startswith(("http://", "https://"))
        self.is_local_file = url.startswith("file://")
        self.is_raw_html = url.startswith("raw:")
        self._url_display = url if not self.is_raw_html else "Raw HTML"

    def should_read(self) -> bool:
        """
        Determines if cache should be read based on context.

        How it works:
        1. If always_bypass is True or is_cacheable is False, return False.
        2. If cache_mode is ENABLED or READ_ONLY, return True.

        Returns:
            bool: True if cache should be read, False otherwise.
        """
        if self.always_bypass or not self.is_cacheable:
            return False
        return self.cache_mode in [CacheMode.ENABLED, CacheMode.READ_ONLY]

    def should_write(self) -> bool:
        """
        Determines if cache should be written based on context.

        How it works:
        1. If always_bypass is True or is_cacheable is False, return False.
        2. If cache_mode is ENABLED or WRITE_ONLY, return True.

        Returns:
            bool: True if cache should be written, False otherwise.
        """
        if self.always_bypass or not self.is_cacheable:
            return False
        return self.cache_mode in [CacheMode.ENABLED, CacheMode.WRITE_ONLY]

    @property
    def display_url(self) -> str:
        """Returns the URL in display format."""
        return self._url_display

