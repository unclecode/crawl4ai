"""Browser management module for Crawl4AI.

This module provides browser management capabilities using different strategies
for browser creation and interaction.
"""

from .manager import BrowserManager
from .profiles import BrowserProfileManager

__all__ = ['BrowserManager', 'BrowserProfileManager']