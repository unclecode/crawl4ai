# __init__.py
"""Crawl4AI Agent - Browser automation agent powered by OpenAI Agents SDK."""

# Import only the components needed for library usage
# Don't import agent_crawl here to avoid warning when running with python -m
from .crawl_tools import CRAWL_TOOLS
from .crawl_prompts import SYSTEM_PROMPT
from .browser_manager import BrowserManager
from .terminal_ui import TerminalUI

__all__ = [
    "CRAWL_TOOLS",
    "SYSTEM_PROMPT",
    "BrowserManager",
    "TerminalUI",
]
