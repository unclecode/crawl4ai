"""
Tests for issue #1848: ValueError on deserialization of 'Logger' type.

When BFSDeepCrawlStrategy is serialized for the Docker API, its logger field
(a logging.Logger) was serialized as {"type": "Logger", "params": {...}},
which then failed deserialization because Logger is not in the allowlist.

Fix: to_serializable_dict skips non-allowlisted types (returns None),
and from_serializable_dict returns None for unknown types instead of raising.
"""

import logging
import pytest
from crawl4ai.async_configs import (
    to_serializable_dict,
    from_serializable_dict,
    ALLOWED_DESERIALIZE_TYPES,
)
from crawl4ai import (
    BFSDeepCrawlStrategy,
    DFSDeepCrawlStrategy,
    CrawlerRunConfig,
    BrowserConfig,
    CacheMode,
)


# -- Serialization: non-allowlisted types are skipped --

class TestSerializationSkipsNonAllowlisted:
    """to_serializable_dict should return None for types not in the allowlist."""

    def test_logger_serialized_as_none(self):
        logger = logging.getLogger("test")
        result = to_serializable_dict(logger)
        assert result is None

    def test_bfs_strategy_logger_is_none_in_output(self):
        strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=10)
        serialized = to_serializable_dict(strategy)
        assert serialized["type"] == "BFSDeepCrawlStrategy"
        # Logger should be None, not a {"type": "Logger", ...} dict
        logger_val = serialized["params"].get("logger")
        assert logger_val is None or logger_val is None

    def test_dfs_strategy_logger_is_none_in_output(self):
        strategy = DFSDeepCrawlStrategy(max_depth=3, max_pages=5)
        serialized = to_serializable_dict(strategy)
        assert serialized["type"] == "DFSDeepCrawlStrategy"
        logger_val = serialized["params"].get("logger")
        assert logger_val is None

    def test_allowlisted_types_still_serialized(self):
        """Types in the allowlist should serialize normally."""
        strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=10)
        serialized = to_serializable_dict(strategy)
        assert serialized["type"] == "BFSDeepCrawlStrategy"
        assert serialized["params"]["max_depth"] == 2
        assert serialized["params"]["max_pages"] == 10

    def test_callable_serialized_as_none(self):
        """Callables (like on_state_change) should also be skipped."""
        async def callback(state):
            pass
        result = to_serializable_dict(callback)
        assert result is None


# -- Deserialization: unknown types return None instead of raising --

class TestDeserializationSkipsUnknown:
    """from_serializable_dict should return None for unknown types."""

    def test_logger_type_returns_none(self):
        """The exact payload from the bug report should not raise."""
        data = {
            "type": "Logger",
            "params": {"name": "crawl4ai.deep_crawling.bfs_strategy"}
        }
        result = from_serializable_dict(data)
        assert result is None

    def test_arbitrary_unknown_type_returns_none(self):
        data = {"type": "SomeRandomClass", "params": {"foo": "bar"}}
        result = from_serializable_dict(data)
        assert result is None

    def test_known_types_still_deserialize(self):
        data = {
            "type": "BFSDeepCrawlStrategy",
            "params": {"max_depth": 2, "max_pages": 10}
        }
        result = from_serializable_dict(data)
        assert isinstance(result, BFSDeepCrawlStrategy)
        assert result.max_depth == 2

    def test_no_valueerror_raised(self):
        """Must never raise ValueError for unknown types."""
        data = {"type": "Logger", "params": {"name": "test"}}
        # Should NOT raise
        result = from_serializable_dict(data)
        assert result is None


# -- Roundtrip: serialize then deserialize --

class TestSerializationRoundtrip:
    """Full roundtrip should work for strategies with logger."""

    def test_bfs_strategy_roundtrip(self):
        strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=10)
        serialized = to_serializable_dict(strategy)
        restored = from_serializable_dict(serialized)
        assert isinstance(restored, BFSDeepCrawlStrategy)
        assert restored.max_depth == 2
        assert restored.max_pages == 10

    def test_dfs_strategy_serialization_no_logger(self):
        """DFS strategy should not serialize Logger either."""
        strategy = DFSDeepCrawlStrategy(max_depth=3, max_pages=5)
        serialized = to_serializable_dict(strategy)
        assert serialized["type"] == "DFSDeepCrawlStrategy"
        import json
        assert '"type": "Logger"' not in json.dumps(serialized)

    def test_crawler_config_with_deep_crawl_roundtrip(self):
        strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=10)
        config = CrawlerRunConfig(
            deep_crawl_strategy=strategy,
            cache_mode=CacheMode.BYPASS,
            verbose=False,
        )
        serialized = to_serializable_dict(config)
        restored = from_serializable_dict(serialized)
        assert isinstance(restored, CrawlerRunConfig)
        assert isinstance(restored.deep_crawl_strategy, BFSDeepCrawlStrategy)
        assert restored.deep_crawl_strategy.max_depth == 2

    def test_browser_config_roundtrip(self):
        config = BrowserConfig(headless=True)
        serialized = to_serializable_dict(config)
        restored = from_serializable_dict(serialized)
        assert isinstance(restored, BrowserConfig)


# -- Reporter's exact scenario --

class TestReporterScenario:
    """Reproduce the exact scenario from issue #1848."""

    def test_reporter_payload_deserializes(self):
        """The exact JSON from the bug report should work."""
        payload = {
            "type": "CrawlerRunConfig",
            "params": {
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 2,
                        "max_pages": 10,
                        "logger": {
                            "type": "Logger",
                            "params": {
                                "name": "crawl4ai.deep_crawling.bfs_strategy"
                            }
                        }
                    }
                }
            }
        }
        result = from_serializable_dict(payload)
        assert isinstance(result, CrawlerRunConfig)
        assert isinstance(result.deep_crawl_strategy, BFSDeepCrawlStrategy)
        assert result.deep_crawl_strategy.max_depth == 2
        assert result.deep_crawl_strategy.max_pages == 10

    def test_reporter_full_request(self):
        """Full request payload from the bug report."""
        crawler_config = {
            "type": "CrawlerRunConfig",
            "params": {
                "scraping_strategy": {
                    "type": "LXMLWebScrapingStrategy",
                    "params": {}
                },
                "table_extraction": {
                    "type": "DefaultTableExtraction",
                    "params": {}
                },
                "verbose": False,
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 2,
                        "max_pages": 10,
                        "logger": {
                            "type": "Logger",
                            "params": {
                                "name": "crawl4ai.deep_crawling.bfs_strategy"
                            }
                        }
                    }
                }
            }
        }
        result = from_serializable_dict(crawler_config)
        assert isinstance(result, CrawlerRunConfig)
        assert result.deep_crawl_strategy.max_depth == 2

    def test_client_side_serialization_clean(self):
        """New client serialization should not include Logger at all."""
        strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=10)
        config = CrawlerRunConfig(
            deep_crawl_strategy=strategy,
            verbose=False,
        )
        serialized = to_serializable_dict(config)

        # Walk the serialized dict — no "Logger" type should appear
        import json
        serialized_str = json.dumps(serialized)
        assert '"type": "Logger"' not in serialized_str
