"""
Shared pytest fixtures for Crawl4AI tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from crawl4ai.telemetry.config import TelemetryConfig, TelemetryConsent
from crawl4ai.telemetry.environment import Environment


@pytest.fixture
def temp_config_dir():
    """Provide a temporary directory for telemetry config testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_telemetry_config(temp_config_dir):
    """Provide a mocked telemetry config for testing."""
    config = TelemetryConfig(config_dir=temp_config_dir)
    yield config


@pytest.fixture
def clean_environment():
    """Clean environment variables before and after test."""
    # Store original environment
    original_env = os.environ.copy()
    
    # Clean telemetry-related env vars
    telemetry_vars = [
        'CRAWL4AI_TELEMETRY',
        'CRAWL4AI_DOCKER', 
        'CRAWL4AI_API_SERVER',
        'CRAWL4AI_TEST_MODE'
    ]
    
    for var in telemetry_vars:
        if var in os.environ:
            del os.environ[var]
    
    # Set test mode
    os.environ['CRAWL4AI_TEST_MODE'] = '1'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_sentry_provider():
    """Provide a mocked Sentry provider for testing."""
    with patch('crawl4ai.telemetry.providers.sentry.SentryProvider') as mock:
        provider_instance = Mock()
        provider_instance.initialize.return_value = True
        provider_instance.send_exception.return_value = True
        provider_instance.is_initialized = True
        mock.return_value = provider_instance
        yield provider_instance


@pytest.fixture
def enabled_telemetry_config(temp_config_dir):  # noqa: F811
    """Provide a telemetry config with telemetry enabled."""
    config = Mock()
    config.get_consent.return_value = TelemetryConsent.ALWAYS
    config.is_enabled.return_value = True
    config.should_send_current.return_value = True
    config.get_email.return_value = "test@example.com"
    config.update_from_env.return_value = None
    yield config


@pytest.fixture
def disabled_telemetry_config(temp_config_dir):  # noqa: F811
    """Provide a telemetry config with telemetry disabled."""
    config = Mock()
    config.get_consent.return_value = TelemetryConsent.DENIED
    config.is_enabled.return_value = False
    config.should_send_current.return_value = False
    config.update_from_env.return_value = None
    yield config


@pytest.fixture
def docker_environment():
    """Mock Docker environment detection."""
    with patch('crawl4ai.telemetry.environment.EnvironmentDetector.detect', return_value=Environment.DOCKER):
        yield


@pytest.fixture
def cli_environment():
    """Mock CLI environment detection."""
    with patch('crawl4ai.telemetry.environment.EnvironmentDetector.detect', return_value=Environment.CLI):
        with patch('sys.stdin.isatty', return_value=True):
            yield


@pytest.fixture
def jupyter_environment():
    """Mock Jupyter environment detection."""
    with patch('crawl4ai.telemetry.environment.EnvironmentDetector.detect', return_value=Environment.JUPYTER):
        yield


@pytest.fixture(autouse=True)
def reset_telemetry_singleton():
    """Reset telemetry singleton between tests."""
    from crawl4ai.telemetry import TelemetryManager
    # Reset the singleton instance
    if hasattr(TelemetryManager, '_instance'):
        TelemetryManager._instance = None  # noqa: SLF001
    yield
    # Clean up after test
    if hasattr(TelemetryManager, '_instance'):
        TelemetryManager._instance = None  # noqa: SLF001


@pytest.fixture
def sample_exception():
    """Provide a sample exception for testing."""
    try:
        raise ValueError("Test exception for telemetry")
    except ValueError as e:
        return e


@pytest.fixture
def privacy_test_data():
    """Provide test data that should NOT be captured by telemetry."""
    return {
        'url': 'https://example.com/private-page',
        'content': 'This is private content that should not be sent',
        'user_data': {
            'email': 'user@private.com',
            'password': 'secret123',
            'api_key': 'sk-1234567890abcdef'
        },
        'pii': {
            'ssn': '123-45-6789',
            'phone': '+1-555-123-4567',
            'address': '123 Main St, Anytown, USA'
        }
    }