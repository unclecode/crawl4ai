"""
Test configuration and utilities for telemetry testing.
"""

import os
import pytest


def pytest_configure(config):  # noqa: ARG001
    """Configure pytest for telemetry tests."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "privacy: Privacy compliance tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(config, items):  # noqa: ARG001
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test location and name
        if "telemetry" in str(item.fspath):
            if "integration" in item.name or "test_integration" in str(item.fspath):
                item.add_marker(pytest.mark.integration)
            elif "privacy" in item.name or "performance" in item.name:
                if "privacy" in item.name:
                    item.add_marker(pytest.mark.privacy)
                if "performance" in item.name:
                    item.add_marker(pytest.mark.performance)
            else:
                item.add_marker(pytest.mark.unit)
            
            # Mark slow tests
            if "slow" in item.name or any(mark.name == "slow" for mark in item.iter_markers()):
                item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Ensure we're in test mode
    os.environ['CRAWL4AI_TEST_MODE'] = '1'
    
    # Disable actual telemetry during tests unless explicitly enabled
    if 'CRAWL4AI_TELEMETRY_TEST_REAL' not in os.environ:
        os.environ['CRAWL4AI_TELEMETRY'] = '0'
    
    yield
    
    # Clean up after tests
    test_vars = ['CRAWL4AI_TEST_MODE', 'CRAWL4AI_TELEMETRY_TEST_REAL']
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]


def pytest_report_header(config):  # noqa: ARG001
    """Add information to pytest header."""
    return [
        "Crawl4AI Telemetry Tests",
        f"Test mode: {'ENABLED' if os.environ.get('CRAWL4AI_TEST_MODE') else 'DISABLED'}",
        f"Real telemetry: {'ENABLED' if os.environ.get('CRAWL4AI_TELEMETRY_TEST_REAL') else 'DISABLED'}"
    ]