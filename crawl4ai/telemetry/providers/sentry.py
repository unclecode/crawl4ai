"""
Sentry telemetry provider for Crawl4AI.
"""

import os
from typing import Dict, Any, Optional
from ..base import TelemetryProvider

# Hardcoded DSN for Crawl4AI project
# This is safe to embed as it's the public part of the DSN
# TODO: Replace with actual Crawl4AI Sentry project DSN before release
# Format: "https://<public_key>@<organization>.ingest.sentry.io/<project_id>"
DEFAULT_SENTRY_DSN = "https://your-public-key@sentry.io/your-project-id"


class SentryProvider(TelemetryProvider):
    """Sentry implementation of telemetry provider."""
    
    def __init__(self, dsn: Optional[str] = None, **kwargs):
        """
        Initialize Sentry provider.
        
        Args:
            dsn: Optional DSN override (for testing/development)
            **kwargs: Additional Sentry configuration
        """
        super().__init__(**kwargs)
        
        # Allow DSN override via environment variable or parameter
        self.dsn = (
            dsn or 
            os.environ.get('CRAWL4AI_SENTRY_DSN') or 
            DEFAULT_SENTRY_DSN
        )
        
        self._sentry_sdk = None
        self.environment = kwargs.get('environment', 'production')
        self.release = kwargs.get('release', None)
    
    def initialize(self) -> bool:
        """Initialize Sentry SDK."""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.stdlib import StdlibIntegration
            from sentry_sdk.integrations.excepthook import ExcepthookIntegration
            
            # Initialize Sentry with minimal integrations
            sentry_sdk.init(
                dsn=self.dsn,
                
                environment=self.environment,
                release=self.release,
                
                # Performance monitoring disabled by default
                traces_sample_rate=0.0,
                
                # Only capture errors, not transactions
                # profiles_sample_rate=0.0,
                
                # Minimal integrations
                integrations=[
                    StdlibIntegration(),
                    ExcepthookIntegration(always_run=False),
                ],
                
                # Privacy settings
                send_default_pii=False,
                attach_stacktrace=True,
                
                # Before send hook for additional sanitization
                before_send=self._before_send,
                
                # Disable automatic breadcrumbs
                max_breadcrumbs=0,
                
                # Disable request data collection
                # request_bodies='never',
                
                # # Custom transport options
                # transport_options={
                #     'keepalive': True,
                # },
            )

            self._sentry_sdk = sentry_sdk
            self._initialized = True
            return True
            
        except ImportError:
            # Sentry SDK not installed
            return False
        except Exception:
            # Initialization failed silently
            return False
    
    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process event before sending to Sentry.
        Provides additional privacy protection.
        """
        # Remove sensitive data
        if 'request' in event:
            event['request'] = self._sanitize_request(event['request'])
        
        # Remove local variables that might contain sensitive data
        if 'exception' in event and 'values' in event['exception']:
            for exc in event['exception']['values']:
                if 'stacktrace' in exc and 'frames' in exc['stacktrace']:
                    for frame in exc['stacktrace']['frames']:
                        # Remove local variables from frames
                        frame.pop('vars', None)
        
        # Apply general sanitization
        event = self.sanitize_data(event)
        
        return event
    
    def _sanitize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize request data to remove sensitive information."""
        sanitized = request_data.copy()
        
        # Remove sensitive fields
        sensitive_fields = ['cookies', 'headers', 'data', 'query_string', 'env']
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '[REDACTED]'
        
        # Keep only safe fields
        safe_fields = ['method', 'url']
        return {k: v for k, v in sanitized.items() if k in safe_fields}
    
    def send_exception(
        self, 
        exc: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send exception to Sentry.
        
        Args:
            exc: Exception to report
            context: Optional context (email, environment info)
            
        Returns:
            True if sent successfully
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            if self._sentry_sdk:
                with self._sentry_sdk.push_scope() as scope:
                    # Add user context if email provided
                    if context and 'email' in context:
                        scope.set_user({'email': context['email']})
                    
                    # Add additional context
                    if context:
                        for key, value in context.items():
                            if key != 'email':
                                scope.set_context(key, value)
                    
                    # Add tags for filtering
                    scope.set_tag('source', context.get('source', 'unknown'))
                    scope.set_tag('environment_type', context.get('environment_type', 'unknown'))
                    
                    # Capture the exception
                    self._sentry_sdk.capture_exception(exc)
                    
                return True
                
        except Exception:
            # Silently fail - telemetry should never crash the app
            return False
        
        return False
    
    def send_event(
        self, 
        event_name: str, 
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send custom event to Sentry.
        
        Args:
            event_name: Name of the event
            payload: Event data
            
        Returns:
            True if sent successfully
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            if self._sentry_sdk:
                # Sanitize payload
                safe_payload = self.sanitize_data(payload) if payload else {}
                
                # Send as a message with extra data
                self._sentry_sdk.capture_message(
                    event_name,
                    level='info',
                    extras=safe_payload
                )
                return True
                
        except Exception:
            return False
        
        return False
    
    def flush(self) -> None:
        """Flush pending events to Sentry."""
        if self._initialized and self._sentry_sdk:
            try:
                self._sentry_sdk.flush(timeout=2.0)
            except Exception:
                pass
    
    def shutdown(self) -> None:
        """Shutdown Sentry client."""
        if self._initialized and self._sentry_sdk:
            try:
                self._sentry_sdk.flush(timeout=2.0)
                # Note: sentry_sdk doesn't have a shutdown method
                # Flush is sufficient for cleanup
            except Exception:
                pass
            finally:
                self._initialized = False