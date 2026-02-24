"""Pytest fixtures for cache validation tests."""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require network)"
    )


@pytest.fixture
def sample_head_html():
    """Sample HTML head section for testing."""
    return '''
    <head>
        <meta charset="utf-8">
        <title>Test Page Title</title>
        <meta name="description" content="This is a test page description">
        <meta property="og:title" content="OG Test Title">
        <meta property="og:description" content="OG Description">
        <meta property="og:image" content="https://example.com/image.jpg">
        <meta property="article:modified_time" content="2024-12-01T00:00:00Z">
        <link rel="stylesheet" href="style.css">
        <script src="app.js"></script>
    </head>
    '''


@pytest.fixture
def minimal_head_html():
    """Minimal head with just a title."""
    return '<head><title>Minimal</title></head>'


@pytest.fixture
def empty_head_html():
    """Empty head section."""
    return '<head></head>'
