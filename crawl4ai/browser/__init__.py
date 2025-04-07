"""Browser management module for Crawl4AI.

This module provides browser management capabilities using different strategies
for browser creation and interaction.
"""

from .manager import BrowserManager
from .profiles import BrowserProfileManager
from .models import DockerConfig
from .docker_registry import DockerRegistry
from .docker_utils import DockerUtils
from .browser_hub import BrowserHub
from .strategies import (
    BaseBrowserStrategy,
    PlaywrightBrowserStrategy,
    CDPBrowserStrategy,
    BuiltinBrowserStrategy,
    DockerBrowserStrategy
)

__all__ = ['BrowserManager', 'BrowserProfileManager', 'DockerConfig', 'DockerRegistry', 'DockerUtils', 'BaseBrowserStrategy',
           'PlaywrightBrowserStrategy', 'CDPBrowserStrategy', 'BuiltinBrowserStrategy',
           'DockerBrowserStrategy', 'BrowserHub']