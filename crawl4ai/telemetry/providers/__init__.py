"""
Telemetry providers for Crawl4AI.
"""

from ..base import TelemetryProvider, NullProvider

__all__ = ['TelemetryProvider', 'NullProvider']

# Try to import Sentry provider if available
try:
    from .sentry import SentryProvider
    __all__.append('SentryProvider')
except ImportError:
    # Sentry SDK not installed
    pass