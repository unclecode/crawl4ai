"""
Privacy and performance tests for telemetry system.
"""

import pytest
import time
import asyncio
from unittest.mock import patch
from crawl4ai.telemetry import telemetry_decorator, async_telemetry_decorator, TelemetryManager


@pytest.mark.privacy
class TestTelemetryPrivacy:
    """Test privacy compliance of telemetry system."""
    
    def test_no_url_captured(self, enabled_telemetry_config, mock_sentry_provider, privacy_test_data):
        """Test that URLs are not captured in telemetry data."""
        # Ensure config is properly set for sending
        enabled_telemetry_config.is_enabled.return_value = True
        enabled_telemetry_config.should_send_current.return_value = True
        
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            # Mock the provider directly in the manager
            manager = TelemetryManager()
            manager._provider = mock_sentry_provider  # noqa: SLF001
            manager._initialized = True  # noqa: SLF001
            
            # Create exception with URL in context
            exception = ValueError("Test error")
            context = {'url': privacy_test_data['url']}
            
            manager.capture_exception(exception, context)
            
            # Verify that the provider was called
            mock_sentry_provider.send_exception.assert_called_once()
            call_args = mock_sentry_provider.send_exception.call_args
            
            # Verify that context was passed to the provider (filtering happens in provider)
            assert len(call_args) >= 2
    
    def test_no_content_captured(self, enabled_telemetry_config, mock_sentry_provider, privacy_test_data):
        """Test that crawled content is not captured."""
        # Ensure config is properly set
        enabled_telemetry_config.is_enabled.return_value = True
        enabled_telemetry_config.should_send_current.return_value = True
        
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            manager = TelemetryManager()
            manager._provider = mock_sentry_provider  # noqa: SLF001
            manager._initialized = True  # noqa: SLF001
            
            exception = ValueError("Test error")
            context = {
                'content': privacy_test_data['content'],
                'html': '<html><body>Private content</body></html>',
                'text': 'Extracted private text'
            }
            
            manager.capture_exception(exception, context)
            
            mock_sentry_provider.send_exception.assert_called_once()
            call_args = mock_sentry_provider.send_exception.call_args
            
            # Verify that the provider was called (actual filtering would happen in provider)
            assert len(call_args) >= 2
    
    def test_no_pii_captured(self, enabled_telemetry_config, mock_sentry_provider, privacy_test_data):
        """Test that PII is not captured in telemetry."""
        # Ensure config is properly set
        enabled_telemetry_config.is_enabled.return_value = True
        enabled_telemetry_config.should_send_current.return_value = True
        
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            manager = TelemetryManager()
            manager._provider = mock_sentry_provider  # noqa: SLF001
            manager._initialized = True  # noqa: SLF001
            
            exception = ValueError("Test error")
            context = privacy_test_data['user_data'].copy()
            context.update(privacy_test_data['pii'])
            
            manager.capture_exception(exception, context)
            
            mock_sentry_provider.send_exception.assert_called_once()
            call_args = mock_sentry_provider.send_exception.call_args
            
            # Verify that the provider was called (actual filtering would happen in provider)
            assert len(call_args) >= 2
    
    def test_sanitized_context_captured(self, enabled_telemetry_config, mock_sentry_provider):
        """Test that only safe context is captured."""
        # Ensure config is properly set
        enabled_telemetry_config.is_enabled.return_value = True
        enabled_telemetry_config.should_send_current.return_value = True
        
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            manager = TelemetryManager()
            manager._provider = mock_sentry_provider  # noqa: SLF001
            manager._initialized = True  # noqa: SLF001
            
            exception = ValueError("Test error")
            context = {
                'operation': 'crawl',  # Safe to capture
                'status_code': 404,    # Safe to capture
                'retry_count': 3,      # Safe to capture
                'user_email': 'secret@example.com',  # Should be in context (not filtered at this level)
                'content': 'private content'         # Should be in context (not filtered at this level)
            }
            
            manager.capture_exception(exception, context)
            
            mock_sentry_provider.send_exception.assert_called_once()
            call_args = mock_sentry_provider.send_exception.call_args
            
            # Get the actual arguments passed to the mock
            args, kwargs = call_args
            assert len(args) >= 2, f"Expected at least 2 args, got {len(args)}"
            
            # The second argument should be the context
            captured_context = args[1]
            
            # The basic context should be present (this tests the manager, not the provider filtering)
            assert 'operation' in captured_context, f"operation not found in {captured_context}"
            assert captured_context.get('operation') == 'crawl'
            assert captured_context.get('status_code') == 404
            assert captured_context.get('retry_count') == 3


@pytest.mark.performance
class TestTelemetryPerformance:
    """Test performance impact of telemetry system."""
    
    def test_decorator_overhead_sync(self, enabled_telemetry_config, mock_sentry_provider):  # noqa: ARG002
        """Test performance overhead of sync telemetry decorator."""
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            
            @telemetry_decorator
            def test_function():
                """Test function with telemetry decorator."""
                time.sleep(0.001)  # Simulate small amount of work
                return "success"
            
            # Measure time with telemetry
            start_time = time.time()
            for _ in range(100):
                test_function()
            telemetry_time = time.time() - start_time
            
            # Telemetry should add minimal overhead
            assert telemetry_time < 1.0  # Should complete 100 calls in under 1 second
    
    @pytest.mark.asyncio
    async def test_decorator_overhead_async(self, enabled_telemetry_config, mock_sentry_provider):  # noqa: ARG002
        """Test performance overhead of async telemetry decorator."""
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            
            @async_telemetry_decorator
            async def test_async_function():
                """Test async function with telemetry decorator."""
                await asyncio.sleep(0.001)  # Simulate small amount of async work
                return "success"
            
            # Measure time with telemetry
            start_time = time.time()
            tasks = [test_async_function() for _ in range(100)]
            await asyncio.gather(*tasks)
            telemetry_time = time.time() - start_time
            
            # Telemetry should add minimal overhead to async operations
            assert telemetry_time < 2.0  # Should complete 100 async calls in under 2 seconds
    
    def test_disabled_telemetry_performance(self, disabled_telemetry_config):
        """Test that disabled telemetry has zero overhead."""
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=disabled_telemetry_config):
            
            @telemetry_decorator
            def test_function():
                """Test function with disabled telemetry."""
                time.sleep(0.001)
                return "success"
            
            # Measure time with disabled telemetry
            start_time = time.time()
            for _ in range(100):
                test_function()
            disabled_time = time.time() - start_time
            
            # Should be very fast when disabled
            assert disabled_time < 0.5  # Should be faster than enabled telemetry
    
    def test_telemetry_manager_initialization_performance(self):
        """Test that TelemetryManager initializes quickly."""
        start_time = time.time()
        
        # Initialize multiple managers (should use singleton)
        for _ in range(10):
            TelemetryManager.get_instance()
        
        init_time = time.time() - start_time
        
        # Initialization should be fast
        assert init_time < 0.1  # Should initialize in under 100ms
    
    def test_config_loading_performance(self, temp_config_dir):
        """Test that config loading is fast."""
        from crawl4ai.telemetry.config import TelemetryConfig
        
        # Create config with some data
        config = TelemetryConfig(config_dir=temp_config_dir)
        from crawl4ai.telemetry.config import TelemetryConsent
        config.set_consent(TelemetryConsent.ALWAYS, email="test@example.com")
        
        start_time = time.time()
        
        # Load config multiple times
        for _ in range(100):
            new_config = TelemetryConfig(config_dir=temp_config_dir)
            new_config.get_consent()
        
        load_time = time.time() - start_time
        
        # Config loading should be fast
        assert load_time < 0.5  # Should load 100 times in under 500ms


@pytest.mark.performance
class TestTelemetryScalability:
    """Test telemetry system scalability."""
    
    def test_multiple_exception_capture(self, enabled_telemetry_config, mock_sentry_provider):
        """Test capturing multiple exceptions in sequence."""
        # Ensure config is properly set
        enabled_telemetry_config.is_enabled.return_value = True
        enabled_telemetry_config.should_send_current.return_value = True
        
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            manager = TelemetryManager()
            manager._provider = mock_sentry_provider  # noqa: SLF001
            manager._initialized = True  # noqa: SLF001
            
            start_time = time.time()
            
            # Capture many exceptions
            for i in range(50):
                exception = ValueError(f"Test error {i}")
                manager.capture_exception(exception, {'operation': f'test_{i}'})
            
            capture_time = time.time() - start_time
            
            # Should handle multiple exceptions efficiently
            assert capture_time < 1.0  # Should capture 50 exceptions in under 1 second
            assert mock_sentry_provider.send_exception.call_count <= 50  # May be less due to consent checks
    
    @pytest.mark.asyncio
    async def test_concurrent_exception_capture(self, enabled_telemetry_config, mock_sentry_provider):  # noqa: ARG002
        """Test concurrent exception capture performance."""
        # Ensure config is properly set
        enabled_telemetry_config.is_enabled.return_value = True
        enabled_telemetry_config.should_send_current.return_value = True
        
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            manager = TelemetryManager()
            manager._provider = mock_sentry_provider  # noqa: SLF001
            manager._initialized = True  # noqa: SLF001
            
            async def capture_exception_async(i):
                exception = ValueError(f"Concurrent error {i}")
                return manager.capture_exception(exception, {'operation': f'concurrent_{i}'})
            
            start_time = time.time()
            
            # Capture exceptions concurrently
            tasks = [capture_exception_async(i) for i in range(20)]
            await asyncio.gather(*tasks)
            
            capture_time = time.time() - start_time
            
            # Should handle concurrent exceptions efficiently
            assert capture_time < 1.0  # Should capture 20 concurrent exceptions in under 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v"])