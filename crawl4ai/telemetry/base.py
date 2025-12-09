"""
Base telemetry provider interface for Crawl4AI.
Provides abstraction for different telemetry backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
import traceback


class TelemetryProvider(ABC):
    """Abstract base class for telemetry providers."""
    
    def __init__(self, **kwargs):
        """Initialize the provider with optional configuration."""
        self.config = kwargs
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the telemetry provider.
        Returns True if initialization successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def send_exception(
        self, 
        exc: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an exception to the telemetry backend.
        
        Args:
            exc: The exception to report
            context: Optional context data (email, environment, etc.)
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_event(
        self, 
        event_name: str, 
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a generic telemetry event.
        
        Args:
            event_name: Name of the event
            payload: Optional event data
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush any pending telemetry data."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Clean shutdown of the provider."""
        pass
    
    def sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive information from telemetry data.
        Override in subclasses for custom sanitization.
        
        Args:
            data: Raw data dictionary
            
        Returns:
            Sanitized data dictionary
        """
        # Default implementation - remove common sensitive fields
        sensitive_keys = {
            'password', 'token', 'api_key', 'secret', 'credential',
            'auth', 'authorization', 'cookie', 'session'
        }
        
        def _sanitize_dict(d: Dict) -> Dict:
            sanitized = {}
            for key, value in d.items():
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in sensitive_keys):
                    sanitized[key] = '[REDACTED]'
                elif isinstance(value, dict):
                    sanitized[key] = _sanitize_dict(value)
                elif isinstance(value, list):
                    sanitized[key] = [
                        _sanitize_dict(item) if isinstance(item, dict) else item 
                        for item in value
                    ]
                else:
                    sanitized[key] = value
            return sanitized
        
        return _sanitize_dict(data) if isinstance(data, dict) else data


class NullProvider(TelemetryProvider):
    """No-op provider for when telemetry is disabled."""
    
    def initialize(self) -> bool:
        """No initialization needed for null provider."""
        self._initialized = True
        return True
    
    def send_exception(
        self, 
        exc: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """No-op exception sending."""
        return True
    
    def send_event(
        self, 
        event_name: str, 
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """No-op event sending."""
        return True
    
    def flush(self) -> None:
        """No-op flush."""
        pass
    
    def shutdown(self) -> None:
        """No-op shutdown."""
        pass