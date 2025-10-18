"""Utility functions shared across Crawl4AI services."""

import uuid
from datetime import datetime
from urllib.parse import urlparse, urlunparse
from typing import Optional


def generate_id() -> str:
    """Generate a unique identifier.

    Returns:
        A unique UUID string.
    """
    return str(uuid.uuid4())


def sanitize_url(url: str) -> str:
    """Sanitize and normalize a URL.

    Args:
        url: The URL to sanitize.

    Returns:
        The sanitized URL.
    """
    parsed = urlparse(url)

    # Ensure scheme
    if not parsed.scheme:
        parsed = parsed._replace(scheme="https")

    # Remove fragment
    parsed = parsed._replace(fragment="")

    # Normalize path
    path = parsed.path
    if path and not path.startswith("/"):
        path = "/" + path
    parsed = parsed._replace(path=path)

    return urlunparse(parsed)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime as ISO 8601 string.

    Args:
        dt: The datetime to format. If None, uses current time.

    Returns:
        ISO 8601 formatted timestamp string.
    """
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat() + "Z"


def calculate_duration(start: datetime, end: Optional[datetime] = None) -> float:
    """Calculate duration in seconds between two timestamps.

    Args:
        start: Start timestamp.
        end: End timestamp. If None, uses current time.

    Returns:
        Duration in seconds.
    """
    if end is None:
        end = datetime.utcnow()
    return (end - start).total_seconds()
