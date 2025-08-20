"""
Tests for Crawl4AI telemetry functionality.
"""

import pytest
import os
import tempfile
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock

from crawl4ai.telemetry import (
    TelemetryManager,
    capture_exception,
    enable,
    disable,
    status
)
from crawl4ai.telemetry.config import TelemetryConfig, TelemetryConsent
from crawl4ai.telemetry.environment import Environment, EnvironmentDetector
from crawl4ai.telemetry.base import NullProvider
from crawl4ai.telemetry.consent import ConsentManager


class TestTelemetryConfig:
    """Test telemetry configuration management."""
    
    def test_config_initialization(self):
        """Test config initialization with custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TelemetryConfig(config_dir=Path(tmpdir))
            assert config.config_dir == Path(tmpdir)
            assert config.get_consent() == TelemetryConsent.NOT_SET
    
    def test_consent_persistence(self):
        """Test that consent is saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TelemetryConfig(config_dir=Path(tmpdir))
            
            # Set consent
            config.set_consent(TelemetryConsent.ALWAYS, email="test@example.com")
            
            # Create new config instance to test persistence
            config2 = TelemetryConfig(config_dir=Path(tmpdir))
            assert config2.get_consent() == TelemetryConsent.ALWAYS
            assert config2.get_email() == "test@example.com"
    
    def test_environment_variable_override(self):
        """Test that environment variables override config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TelemetryConfig(config_dir=Path(tmpdir))
            config.set_consent(TelemetryConsent.ALWAYS)
            
            # Set environment variable to disable
            os.environ['CRAWL4AI_TELEMETRY'] = '0'
            try:
                config.update_from_env()
                assert config.get_consent() == TelemetryConsent.DENIED
            finally:
                del os.environ['CRAWL4AI_TELEMETRY']


class TestEnvironmentDetection:
    """Test environment detection functionality."""
    
    def test_cli_detection(self):
        """Test CLI environment detection."""
        # Mock sys.stdin.isatty
        with patch('sys.stdin.isatty', return_value=True):
            env = EnvironmentDetector.detect()
            # Should detect as CLI in most test environments
            assert env in [Environment.CLI, Environment.UNKNOWN]
    
    def test_docker_detection(self):
        """Test Docker environment detection."""
        # Mock Docker environment
        with patch.dict(os.environ, {'CRAWL4AI_DOCKER': 'true'}):
            env = EnvironmentDetector.detect()
            assert env == Environment.DOCKER
    
    def test_api_server_detection(self):
        """Test API server detection."""
        with patch.dict(os.environ, {'CRAWL4AI_API_SERVER': 'true', 'CRAWL4AI_DOCKER': 'true'}):
            env = EnvironmentDetector.detect()
            assert env == Environment.API_SERVER


class TestTelemetryManager:
    """Test the main telemetry manager."""
    
    def test_singleton_pattern(self):
        """Test that TelemetryManager is a singleton."""
        manager1 = TelemetryManager.get_instance()
        manager2 = TelemetryManager.get_instance()
        assert manager1 is manager2
    
    def test_exception_capture(self):
        """Test exception capture functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manager with custom config dir
            with patch('crawl4ai.telemetry.TelemetryConfig') as MockConfig:
                mock_config = Mock()
                mock_config.get_consent.return_value = TelemetryConsent.ALWAYS
                mock_config.is_enabled.return_value = True
                mock_config.should_send_current.return_value = True
                mock_config.get_email.return_value = "test@example.com"
                mock_config.update_from_env.return_value = None
                MockConfig.return_value = mock_config
                
                # Mock the provider setup
                with patch('crawl4ai.telemetry.providers.sentry.SentryProvider') as MockSentryProvider:
                    mock_provider = Mock()
                    mock_provider.initialize.return_value = True
                    mock_provider.send_exception.return_value = True
                    MockSentryProvider.return_value = mock_provider
                    
                    manager = TelemetryManager()
                    
                    # Test exception capture
                    test_exception = ValueError("Test error")
                    result = manager.capture_exception(test_exception, {'test': 'context'})
                    
                    # Verify the exception was processed
                    assert mock_config.should_send_current.called
    
    def test_null_provider_when_disabled(self):
        """Test that NullProvider is used when telemetry is disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('crawl4ai.telemetry.TelemetryConfig') as MockConfig:
                mock_config = Mock()
                mock_config.get_consent.return_value = TelemetryConsent.DENIED
                mock_config.is_enabled.return_value = False
                MockConfig.return_value = mock_config
                
                manager = TelemetryManager()
                assert isinstance(manager._provider, NullProvider)


class TestConsentManager:
    """Test consent management functionality."""
    
    def test_docker_default_enabled(self):
        """Test that Docker environment has telemetry enabled by default."""
        with patch('crawl4ai.telemetry.consent.EnvironmentDetector.detect', return_value=Environment.DOCKER):
            config = Mock()
            config.get_consent.return_value = TelemetryConsent.NOT_SET
            
            consent_manager = ConsentManager(config)
            consent = consent_manager.check_and_prompt()
            
            # Should be enabled by default in Docker
            assert config.set_consent.called
            assert config.set_consent.call_args[0][0] == TelemetryConsent.ALWAYS
    
    def test_docker_disabled_by_env(self):
        """Test that Docker telemetry can be disabled via environment variable."""
        with patch('crawl4ai.telemetry.consent.EnvironmentDetector.detect', return_value=Environment.DOCKER):
            with patch.dict(os.environ, {'CRAWL4AI_TELEMETRY': '0'}):
                config = Mock()
                config.get_consent.return_value = TelemetryConsent.NOT_SET
                
                consent_manager = ConsentManager(config)
                consent = consent_manager.check_and_prompt()
                
                # Should be disabled
                assert config.set_consent.called
                assert config.set_consent.call_args[0][0] == TelemetryConsent.DENIED


class TestPublicAPI:
    """Test the public API functions."""
    
    @patch('crawl4ai.telemetry.get_telemetry')
    def test_enable_function(self, mock_get_telemetry):
        """Test the enable() function."""
        mock_manager = Mock()
        mock_get_telemetry.return_value = mock_manager
        
        enable(email="test@example.com", always=True)
        
        mock_manager.enable.assert_called_once_with(
            email="test@example.com",
            always=True,
            once=False
        )
    
    @patch('crawl4ai.telemetry.get_telemetry')
    def test_disable_function(self, mock_get_telemetry):
        """Test the disable() function."""
        mock_manager = Mock()
        mock_get_telemetry.return_value = mock_manager
        
        disable()
        
        mock_manager.disable.assert_called_once()
    
    @patch('crawl4ai.telemetry.get_telemetry')
    def test_status_function(self, mock_get_telemetry):
        """Test the status() function."""
        mock_manager = Mock()
        mock_manager.status.return_value = {
            'enabled': True,
            'consent': 'always',
            'email': 'test@example.com'
        }
        mock_get_telemetry.return_value = mock_manager
        
        result = status()
        
        assert result['enabled'] is True
        assert result['consent'] == 'always'
        assert result['email'] == 'test@example.com'


class TestIntegration:
    """Integration tests for telemetry with AsyncWebCrawler."""
    
    @pytest.mark.asyncio
    async def test_crawler_exception_capture(self):
        """Test that AsyncWebCrawler captures exceptions."""
        from crawl4ai import AsyncWebCrawler
        
        with patch('crawl4ai.telemetry.capture_exception') as mock_capture:
            # This should trigger an exception for invalid URL
            async with AsyncWebCrawler() as crawler:
                try:
                    # Use an invalid URL that will cause an error
                    result = await crawler.arun(url="not-a-valid-url")
                except Exception:
                    pass
            
            # Check if exception was captured (may not be called if error is handled)
            # This is more of a smoke test to ensure the integration doesn't break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])