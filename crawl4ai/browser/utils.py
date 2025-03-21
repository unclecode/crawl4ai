"""Browser utilities module for Crawl4AI.

This module provides utility functions for browser management,
including process management, CDP connection utilities,
and Playwright instance management.
"""

import asyncio
import os
import sys
import platform
import tempfile
from typing import Optional, Any

from playwright.async_api import async_playwright

from ..async_logger import AsyncLogger
from ..utils import get_chromium_path

_playwright_instance = None

async def get_playwright():
    """Get or create the Playwright instance (singleton pattern).
    
    Returns:
        Playwright: The Playwright instance
    """
    global _playwright_instance
    if _playwright_instance is None or True:
        _playwright_instance = await async_playwright().start()
    return _playwright_instance

def get_browser_executable(browser_type: str) -> str:
    """Get the path to browser executable, with platform-specific handling.
    
    Args:
        browser_type: Type of browser (chromium, firefox, webkit)
        
    Returns:
        Path to browser executable
    """
    return get_chromium_path(browser_type)

def create_temp_directory(prefix="browser-profile-") -> str:
    """Create a temporary directory for browser data.
    
    Args:
        prefix: Prefix for the temporary directory name
        
    Returns:
        Path to the created temporary directory
    """
    return tempfile.mkdtemp(prefix=prefix)

def is_windows() -> bool:
    """Check if the current platform is Windows.
    
    Returns:
        True if Windows, False otherwise
    """
    return sys.platform == "win32"

def is_macos() -> bool:
    """Check if the current platform is macOS.
    
    Returns:
        True if macOS, False otherwise
    """
    return sys.platform == "darwin"

def is_linux() -> bool:
    """Check if the current platform is Linux.
    
    Returns:
        True if Linux, False otherwise
    """
    return not (is_windows() or is_macos())

def get_browser_disable_options() -> list:
    """Get standard list of browser disable options for performance.
    
    Returns:
        List of command-line options to disable various browser features
    """
    return [
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-breakpad",
        "--disable-client-side-phishing-detection",
        "--disable-component-extensions-with-background-pages",
        "--disable-default-apps",
        "--disable-extensions",
        "--disable-features=TranslateUI",
        "--disable-hang-monitor",
        "--disable-ipc-flooding-protection",
        "--disable-popup-blocking",
        "--disable-prompt-on-repost",
        "--disable-sync",
        "--force-color-profile=srgb",
        "--metrics-recording-only",
        "--no-first-run",
        "--password-store=basic",
        "--use-mock-keychain",
    ]
