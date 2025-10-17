"""Browser session management with singleton pattern for persistent browser instances."""

from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig


class BrowserManager:
    """Singleton browser manager for persistent browser sessions across agent operations."""

    _instance: Optional['BrowserManager'] = None
    _crawler: Optional[AsyncWebCrawler] = None
    _config: Optional[BrowserConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def get_browser(cls, config: Optional[BrowserConfig] = None) -> AsyncWebCrawler:
        """
        Get or create the singleton browser instance.

        Args:
            config: Optional browser configuration. Only used if no browser exists yet.
                   To change config, use reconfigure_browser() instead.

        Returns:
            AsyncWebCrawler instance
        """
        # Create new browser if needed
        if cls._crawler is None:
            # Create default config if none provided
            if config is None:
                config = BrowserConfig(headless=True, verbose=False)

            cls._crawler = AsyncWebCrawler(config=config)
            await cls._crawler.start()
            cls._config = config

        return cls._crawler

    @classmethod
    async def reconfigure_browser(cls, new_config: BrowserConfig) -> AsyncWebCrawler:
        """
        Close current browser and create a new one with different configuration.

        Args:
            new_config: New browser configuration

        Returns:
            New AsyncWebCrawler instance
        """
        await cls.close_browser()
        return await cls.get_browser(new_config)

    @classmethod
    async def close_browser(cls):
        """Close the current browser instance and cleanup."""
        if cls._crawler is not None:
            await cls._crawler.close()
            cls._crawler = None
            cls._config = None

    @classmethod
    def is_browser_active(cls) -> bool:
        """Check if browser is currently active."""
        return cls._crawler is not None

    @classmethod
    def get_current_config(cls) -> Optional[BrowserConfig]:
        """Get the current browser configuration."""
        return cls._config
