"""
Crawl4AI Cloud Module - Integration with Crawl4AI Cloud service.

This module provides:
- CLI commands for cloud profile management
- API client for cloud operations (future)
- Cloud configuration utilities
"""

from .cli import cloud_cmd, get_cloud_config, require_auth

__all__ = [
    "cloud_cmd",
    "get_cloud_config",
    "require_auth",
]
