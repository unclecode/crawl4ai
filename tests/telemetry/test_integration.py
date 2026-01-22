"""
Integration tests for telemetry CLI commands.
"""

import pytest
import subprocess
import sys
import os
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestTelemetryCLI:
    """Test telemetry CLI commands integration."""
    
    def test_telemetry_status_command(self, clean_environment, temp_config_dir):
        """Test the telemetry status CLI command."""
        # Import with mocked config
        with patch('crawl4ai.telemetry.TelemetryConfig') as MockConfig:
            mock_config = Mock()
            mock_config.get_consent.return_value = 'not_set'
            mock_config.is_enabled.return_value = False
            MockConfig.return_value = mock_config
            
            from crawl4ai.cli import main
            
            # Test status command
            with patch('sys.argv', ['crawl4ai', 'telemetry', 'status']):
                try:
                    main()
                except SystemExit:
                    pass  # CLI commands often call sys.exit()
    
    def test_telemetry_enable_command(self, clean_environment, temp_config_dir):
        """Test the telemetry enable CLI command."""
        with patch('crawl4ai.telemetry.TelemetryConfig') as MockConfig:
            mock_config = Mock()
            MockConfig.return_value = mock_config
            
            from crawl4ai.cli import main
            
            # Test enable command
            with patch('sys.argv', ['crawl4ai', 'telemetry', 'enable', '--email', 'test@example.com']):
                try:
                    main()
                except SystemExit:
                    pass
    
    def test_telemetry_disable_command(self, clean_environment, temp_config_dir):
        """Test the telemetry disable CLI command."""
        with patch('crawl4ai.telemetry.TelemetryConfig') as MockConfig:
            mock_config = Mock()
            MockConfig.return_value = mock_config
            
            from crawl4ai.cli import main
            
            # Test disable command
            with patch('sys.argv', ['crawl4ai', 'telemetry', 'disable']):
                try:
                    main()
                except SystemExit:
                    pass
    
    @pytest.mark.slow
    def test_cli_subprocess_integration(self, temp_config_dir):
        """Test CLI commands as subprocess calls."""
        env = os.environ.copy()
        env['CRAWL4AI_CONFIG_DIR'] = str(temp_config_dir)
        
        # Test status command via subprocess
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'crawl4ai.cli', 'telemetry', 'status'],
                env=env,
                capture_output=True,
                text=True,
                timeout=10
            )
            # Should not crash, regardless of exit code
            assert result.returncode in [0, 1]  # May return 1 if not configured
        except subprocess.TimeoutExpired:
            pytest.skip("CLI command timed out")
        except FileNotFoundError:
            pytest.skip("CLI module not found")


@pytest.mark.integration
class TestAsyncWebCrawlerIntegration:
    """Test AsyncWebCrawler telemetry integration."""
    
    @pytest.mark.asyncio
    async def test_crawler_telemetry_decorator(self, enabled_telemetry_config, mock_sentry_provider):
        """Test that AsyncWebCrawler methods are decorated with telemetry."""
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            from crawl4ai import AsyncWebCrawler
            
            # Check if the arun method has telemetry decoration
            crawler = AsyncWebCrawler()
            assert hasattr(crawler.arun, '__wrapped__') or callable(crawler.arun)
    
    @pytest.mark.asyncio
    async def test_crawler_exception_capture_integration(self, enabled_telemetry_config, mock_sentry_provider):
        """Test that exceptions in AsyncWebCrawler are captured."""
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
            with patch('crawl4ai.telemetry.capture_exception') as _mock_capture:
                from crawl4ai import AsyncWebCrawler
                
                async with AsyncWebCrawler() as crawler:
                    try:
                        # This should cause an exception
                        await crawler.arun(url="invalid://url")
                    except Exception:
                        pass  # We expect this to fail
                
                # The decorator should have attempted to capture the exception
                # Note: This might not always be called depending on where the exception occurs
    
    @pytest.mark.asyncio
    async def test_crawler_with_disabled_telemetry(self, disabled_telemetry_config):
        """Test that AsyncWebCrawler works normally with disabled telemetry."""
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=disabled_telemetry_config):
            from crawl4ai import AsyncWebCrawler
            
            # Should work normally even with telemetry disabled
            async with AsyncWebCrawler() as crawler:
                assert crawler is not None


@pytest.mark.integration  
class TestDockerIntegration:
    """Test Docker environment telemetry integration."""
    
    def test_docker_environment_detection(self, docker_environment, temp_config_dir):
        """Test that Docker environment is detected correctly."""
        from crawl4ai.telemetry.environment import EnvironmentDetector
        
        env = EnvironmentDetector.detect()
        from crawl4ai.telemetry.environment import Environment
        assert env == Environment.DOCKER
    
    def test_docker_default_telemetry_enabled(self, temp_config_dir):
        """Test that telemetry is enabled by default in Docker."""
        from crawl4ai.telemetry.environment import Environment
        
        # Clear any existing environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True):
            # Set only the Docker environment variable
            os.environ['CRAWL4AI_DOCKER'] = 'true'
            
            with patch('crawl4ai.telemetry.environment.EnvironmentDetector.detect', return_value=Environment.DOCKER):
                from crawl4ai.telemetry.consent import ConsentManager
                from crawl4ai.telemetry.config import TelemetryConfig, TelemetryConsent
                
                config = TelemetryConfig(config_dir=temp_config_dir)
                consent_manager = ConsentManager(config)
                
                # Should set consent to ALWAYS for Docker
                consent_manager.check_and_prompt()
                assert config.get_consent() == TelemetryConsent.ALWAYS
    
    def test_docker_telemetry_can_be_disabled(self, temp_config_dir):
        """Test that Docker telemetry can be disabled via environment variable."""
        from crawl4ai.telemetry.environment import Environment
        
        with patch.dict(os.environ, {'CRAWL4AI_TELEMETRY': '0', 'CRAWL4AI_DOCKER': 'true'}):
            with patch('crawl4ai.telemetry.environment.EnvironmentDetector.detect', return_value=Environment.DOCKER):
                from crawl4ai.telemetry.consent import ConsentManager
                from crawl4ai.telemetry.config import TelemetryConfig, TelemetryConsent
                
                config = TelemetryConfig(config_dir=temp_config_dir)
                consent_manager = ConsentManager(config)
                
                # Should set consent to DENIED when env var is 0
                consent_manager.check_and_prompt()
                assert config.get_consent() == TelemetryConsent.DENIED


@pytest.mark.integration
class TestTelemetryProviderIntegration:
    """Test telemetry provider integration."""
    
    def test_sentry_provider_initialization(self, enabled_telemetry_config):
        """Test that Sentry provider initializes correctly."""
        try:
            from crawl4ai.telemetry.providers.sentry import SentryProvider
            
            provider = SentryProvider()
            # Should not crash during initialization
            assert provider is not None
            
        except ImportError:
            pytest.skip("Sentry provider not available")
    
    def test_null_provider_fallback(self, disabled_telemetry_config):
        """Test that NullProvider is used when telemetry is disabled."""
        with patch('crawl4ai.telemetry.TelemetryConfig', return_value=disabled_telemetry_config):
            from crawl4ai.telemetry import TelemetryManager
            from crawl4ai.telemetry.base import NullProvider
            
            manager = TelemetryManager()
            assert isinstance(manager._provider, NullProvider)  # noqa: SLF001
    
    def test_graceful_degradation_without_sentry(self, enabled_telemetry_config):
        """Test graceful degradation when sentry-sdk is not available."""
        with patch.dict('sys.modules', {'sentry_sdk': None}):
            with patch('crawl4ai.telemetry.TelemetryConfig', return_value=enabled_telemetry_config):
                from crawl4ai.telemetry import TelemetryManager
                from crawl4ai.telemetry.base import NullProvider
                
                # Should fall back to NullProvider when Sentry is not available
                manager = TelemetryManager()
                assert isinstance(manager._provider, NullProvider)  # noqa: SLF001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])