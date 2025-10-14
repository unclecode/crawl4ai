"""
Crawl4AI Telemetry Module.
Provides opt-in error tracking to improve stability.
"""

import os
import sys
import functools
import traceback
from typing import Optional, Any, Dict, Callable, Type
from contextlib import contextmanager, asynccontextmanager

from .base import TelemetryProvider, NullProvider
from .config import TelemetryConfig, TelemetryConsent
from .consent import ConsentManager
from .environment import Environment, EnvironmentDetector


class TelemetryManager:
    """
    Main telemetry manager for Crawl4AI.
    Coordinates provider, config, and consent management.
    """
    
    _instance: Optional['TelemetryManager'] = None
    
    def __init__(self):
        """Initialize telemetry manager."""
        self.config = TelemetryConfig()
        self.consent_manager = ConsentManager(self.config)
        self.environment = EnvironmentDetector.detect()
        self._provider: Optional[TelemetryProvider] = None
        self._initialized = False
        self._error_count = 0
        self._max_errors = 100  # Prevent telemetry spam
        
        # Load provider based on config
        self._setup_provider()
    
    @classmethod
    def get_instance(cls) -> 'TelemetryManager':
        """
        Get singleton instance of telemetry manager.
        
        Returns:
            TelemetryManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _setup_provider(self) -> None:
        """Setup telemetry provider based on configuration."""
        # Update config from environment
        self.config.update_from_env()
        
        # Check if telemetry is enabled
        if not self.config.is_enabled():
            self._provider = NullProvider()
            return
        
        # Try to load Sentry provider
        try:
            from .providers.sentry import SentryProvider
            
            # Get Crawl4AI version for release tracking
            try:
                from crawl4ai import __version__
                release = f"crawl4ai@{__version__}"
            except ImportError:
                release = "crawl4ai@unknown"
            
            self._provider = SentryProvider(
                environment=self.environment.value,
                release=release
            )
            
            # Initialize provider
            if not self._provider.initialize():
                # Fallback to null provider if init fails
                self._provider = NullProvider()
                
        except ImportError:
            # Sentry not installed - use null provider
            self._provider = NullProvider()
        
        self._initialized = True
    
    def capture_exception(
        self, 
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Capture and send an exception.
        
        Args:
            exception: The exception to capture
            context: Optional additional context
            
        Returns:
            True if exception was sent
        """
        # Check error count limit
        if self._error_count >= self._max_errors:
            return False
        
        # Check consent on first error
        if self._error_count == 0:
            consent = self.consent_manager.check_and_prompt()
            
            # Update provider if consent changed
            if consent == TelemetryConsent.DENIED:
                self._provider = NullProvider()
                return False
            elif consent in [TelemetryConsent.ONCE, TelemetryConsent.ALWAYS]:
                if isinstance(self._provider, NullProvider):
                    self._setup_provider()
        
        # Check if we should send this error
        if not self.config.should_send_current():
            return False
        
        # Prepare context
        full_context = EnvironmentDetector.get_environment_context()
        if context:
            full_context.update(context)
        
        # Add user email if available
        email = self.config.get_email()
        if email:
            full_context['email'] = email
        
        # Add source info
        full_context['source'] = 'crawl4ai'
        
        # Send exception
        try:
            if self._provider:
                success = self._provider.send_exception(exception, full_context)
                if success:
                    self._error_count += 1
                return success
        except Exception:
            # Telemetry itself failed - ignore
            pass
        
        return False
    
    def capture_message(
        self,
        message: str,
        level: str = 'info',
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Capture a message event.
        
        Args:
            message: Message to send
            level: Message level (info, warning, error)
            context: Optional context
            
        Returns:
            True if message was sent
        """
        if not self.config.is_enabled():
            return False
        
        payload = {
            'level': level,
            'message': message
        }
        if context:
            payload.update(context)
        
        try:
            if self._provider:
                return self._provider.send_event(message, payload)
        except Exception:
            pass
        
        return False
    
    def enable(
        self,
        email: Optional[str] = None,
        always: bool = True,
        once: bool = False
    ) -> None:
        """
        Enable telemetry.
        
        Args:
            email: Optional email for follow-up
            always: If True, always send errors
            once: If True, send only next error
        """
        if once:
            consent = TelemetryConsent.ONCE
        elif always:
            consent = TelemetryConsent.ALWAYS
        else:
            consent = TelemetryConsent.ALWAYS
        
        self.config.set_consent(consent, email)
        self._setup_provider()
        
        print("✅ Telemetry enabled")
        if email:
            print(f"   Email: {email}")
        print(f"   Mode: {'once' if once else 'always'}")
    
    def disable(self) -> None:
        """Disable telemetry."""
        self.config.set_consent(TelemetryConsent.DENIED)
        self._provider = NullProvider()
        print("✅ Telemetry disabled")
    
    def status(self) -> Dict[str, Any]:
        """
        Get telemetry status.
        
        Returns:
            Dictionary with status information
        """
        return {
            'enabled': self.config.is_enabled(),
            'consent': self.config.get_consent().value,
            'email': self.config.get_email(),
            'environment': self.environment.value,
            'provider': type(self._provider).__name__ if self._provider else 'None',
            'errors_sent': self._error_count
        }
    
    def flush(self) -> None:
        """Flush any pending telemetry data."""
        if self._provider:
            self._provider.flush()
    
    def shutdown(self) -> None:
        """Shutdown telemetry."""
        if self._provider:
            self._provider.shutdown()


# Global instance
_telemetry_manager: Optional[TelemetryManager] = None


def get_telemetry() -> TelemetryManager:
    """
    Get global telemetry manager instance.
    
    Returns:
        TelemetryManager instance
    """
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager.get_instance()
    return _telemetry_manager


def capture_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Capture an exception for telemetry.
    
    Args:
        exception: Exception to capture
        context: Optional context
        
    Returns:
        True if sent successfully
    """
    try:
        return get_telemetry().capture_exception(exception, context)
    except Exception:
        return False


def telemetry_decorator(func: Callable) -> Callable:
    """
    Decorator to capture exceptions from a function.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Capture exception
            capture_exception(e, {
                'function': func.__name__,
                'module': func.__module__
            })
            # Re-raise the exception
            raise
    
    return wrapper


def async_telemetry_decorator(func: Callable) -> Callable:
    """
    Decorator to capture exceptions from an async function.
    
    Args:
        func: Async function to wrap
        
    Returns:
        Wrapped async function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Capture exception
            capture_exception(e, {
                'function': func.__name__,
                'module': func.__module__
            })
            # Re-raise the exception
            raise
    
    return wrapper


@contextmanager
def telemetry_context(operation: str):
    """
    Context manager for capturing exceptions.
    
    Args:
        operation: Name of the operation
        
    Example:
        with telemetry_context("web_crawl"):
            # Your code here
            pass
    """
    try:
        yield
    except Exception as e:
        capture_exception(e, {'operation': operation})
        raise


@asynccontextmanager
async def async_telemetry_context(operation: str):
    """
    Async context manager for capturing exceptions in async code.
    
    Args:
        operation: Name of the operation
        
    Example:
        async with async_telemetry_context("async_crawl"):
            # Your async code here
            await something()
    """
    try:
        yield
    except Exception as e:
        capture_exception(e, {'operation': operation})
        raise


def install_exception_handler():
    """Install global exception handler for uncaught exceptions."""
    original_hook = sys.excepthook
    
    def telemetry_exception_hook(exc_type, exc_value, exc_traceback):
        """Custom exception hook with telemetry."""
        # Don't capture KeyboardInterrupt
        if not issubclass(exc_type, KeyboardInterrupt):
            capture_exception(exc_value, {
                'uncaught': True,
                'type': exc_type.__name__
            })
        
        # Call original hook
        original_hook(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = telemetry_exception_hook


# Public API
def enable(email: Optional[str] = None, always: bool = True, once: bool = False) -> None:
    """
    Enable telemetry.
    
    Args:
        email: Optional email for follow-up
        always: If True, always send errors (default)
        once: If True, send only the next error
    """
    get_telemetry().enable(email=email, always=always, once=once)


def disable() -> None:
    """Disable telemetry."""
    get_telemetry().disable()


def status() -> Dict[str, Any]:
    """
    Get telemetry status.
    
    Returns:
        Dictionary with status information
    """
    return get_telemetry().status()


# Auto-install exception handler on import
# (Only for main library usage, not for Docker/API)
if EnvironmentDetector.detect() not in [Environment.DOCKER, Environment.API_SERVER]:
    install_exception_handler()


__all__ = [
    'TelemetryManager',
    'get_telemetry',
    'capture_exception',
    'telemetry_decorator',
    'async_telemetry_decorator',
    'telemetry_context',
    'async_telemetry_context',
    'enable',
    'disable',
    'status',
]