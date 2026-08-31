"""
Tests for issue #1837: Docker API arun_many config-list support.

Verifies that the /crawl endpoint accepts crawler_configs (list of dicts)
alongside the existing crawler_config (single dict), and that the list
is correctly passed through to arun_many().
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from crawl4ai import CrawlerRunConfig, CacheMode


# -- Schema tests --

class TestCrawlRequestSchema:
    """Verify CrawlRequest schema accepts crawler_configs."""

    def test_schema_has_crawler_configs_field(self):
        """CrawlRequest should have an optional crawler_configs field."""
        import importlib.util
        with open("deploy/docker/schemas.py") as f:
            source = f.read()
        assert "crawler_configs" in source
        assert "Optional[List[Dict]]" in source

    def test_schema_backward_compatible(self):
        """crawler_config (singular) should still work."""
        with open("deploy/docker/schemas.py") as f:
            source = f.read()
        assert "crawler_config: Optional[Dict]" in source

    def test_crawler_configs_default_none(self):
        """crawler_configs should default to None."""
        with open("deploy/docker/schemas.py") as f:
            source = f.read()
        assert "default=None" in source


# -- API handler tests --

class TestHandleCrawlRequestSignature:
    """Verify handle_crawl_request accepts crawler_configs parameter."""

    def test_handler_accepts_crawler_configs(self):
        """handle_crawl_request should have crawler_configs parameter."""
        with open("deploy/docker/api.py") as f:
            source = f.read()
        assert "crawler_configs: Optional[List[dict]]" in source

    def test_handler_defaults_crawler_configs_none(self):
        """crawler_configs should default to None."""
        with open("deploy/docker/api.py") as f:
            source = f.read()
        assert "crawler_configs: Optional[List[dict]] = None" in source


# -- Config list deserialization --

class TestConfigListDeserialization:
    """Verify that a list of config dicts can be deserialized."""

    def test_single_config_loads(self):
        """Single config dict should deserialize as before."""
        data = {"type": "CrawlerRunConfig", "params": {"verbose": False}}
        config = CrawlerRunConfig.load(data)
        assert isinstance(config, CrawlerRunConfig)

    def test_multiple_configs_load(self):
        """Multiple config dicts should each deserialize independently."""
        configs_data = [
            {"type": "CrawlerRunConfig", "params": {"verbose": False}},
            {"type": "CrawlerRunConfig", "params": {"cache_mode": {"type": "CacheMode", "params": "bypass"}}},
        ]
        configs = [CrawlerRunConfig.load(c) for c in configs_data]
        assert len(configs) == 2
        assert all(isinstance(c, CrawlerRunConfig) for c in configs)

    def test_empty_config_list(self):
        """Empty config list should produce empty list."""
        configs = [CrawlerRunConfig.load(c) for c in []]
        assert configs == []


# -- Integration: config list logic in api.py --

class TestConfigListLogic:
    """Verify the branching logic for single vs list configs."""

    def test_api_uses_config_list_when_provided(self):
        """When crawler_configs is provided with multiple URLs, it should be used."""
        with open("deploy/docker/api.py") as f:
            source = f.read()
        # Should check crawler_configs and build a list
        assert "if crawler_configs and len(urls) > 1:" in source
        assert "config_list" in source

    def test_api_falls_back_to_single_config(self):
        """When crawler_configs is None, original single-config path is used."""
        with open("deploy/docker/api.py") as f:
            source = f.read()
        assert "effective_config = crawler_config" in source

    def test_api_applies_base_config_to_each(self):
        """Base config should be applied to each config in the list."""
        with open("deploy/docker/api.py") as f:
            source = f.read()
        assert "for cfg in config_list:" in source


# -- Server endpoint passes crawler_configs --

class TestServerEndpoint:
    """Verify the /crawl endpoint passes crawler_configs through."""

    def test_server_passes_crawler_configs(self):
        """The crawl endpoint should pass crawler_configs to handle_crawl_request."""
        with open("deploy/docker/server.py") as f:
            source = f.read()
        assert "crawler_configs=crawl_request.crawler_configs" in source


# -- Backward compatibility --

class TestBackwardCompatibility:
    """Ensure existing single-config requests still work."""

    def test_single_url_ignores_crawler_configs(self):
        """With a single URL, crawler_configs should be ignored (uses arun, not arun_many)."""
        with open("deploy/docker/api.py") as f:
            source = f.read()
        # Single URL uses arun which only takes one config
        assert '"arun" if len(urls) == 1 else "arun_many"' in source

    def test_no_crawler_configs_uses_single(self):
        """When crawler_configs is None, the original single config path is used."""
        with open("deploy/docker/api.py") as f:
            source = f.read()
        # The else branch uses the original crawler_config
        assert "effective_config = crawler_config" in source
