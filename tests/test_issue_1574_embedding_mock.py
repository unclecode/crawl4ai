"""
Tests for #1574: EmbeddingStrategy config separation and mock data removal.

Verifies:
- Commented-out "fried rice" mock data is removed
- _get_query_llm_config_dict() fallback chain works correctly
- query_llm_config is kept separate from embedding config
- base_url and backoff params are passed through
"""

import inspect
import pytest
from typing import Dict, Optional
from crawl4ai.adaptive_crawler import EmbeddingStrategy, AdaptiveConfig


# ── mock data removal ─────────────────────────────────────────


def test_no_fried_rice_in_source():
    """The 'fried rice' mock data must be completely removed."""
    source = inspect.getsource(EmbeddingStrategy.map_query_semantic_space)
    assert "fried rice" not in source


def test_no_vegetable_in_source():
    """No 'vegetable fried rice' mock variations should remain."""
    source = inspect.getsource(EmbeddingStrategy.map_query_semantic_space)
    assert "vegetable" not in source


def test_no_async_await_mock_in_source():
    """The 'async and await' mock variations should be removed."""
    source = inspect.getsource(EmbeddingStrategy.map_query_semantic_space)
    assert "How do async and await work" not in source


def test_no_event_loop_mock_in_source():
    """The 'event loop' mock variations should be removed."""
    source = inspect.getsource(EmbeddingStrategy.map_query_semantic_space)
    assert "role of event loops" not in source


def test_no_commented_mock_blocks():
    """No large commented-out mock blocks should remain."""
    source = inspect.getsource(EmbeddingStrategy.map_query_semantic_space)
    mock_indicators = ["Mock data", "# variations =", "# variations = {"]
    for indicator in mock_indicators:
        assert indicator not in source, f"Found leftover mock indicator: {indicator}"


# ── config fallback chain ─────────────────────────────────────


def test_query_config_priority_over_llm_config():
    """query_llm_config should take priority over llm_config."""
    query_cfg = {"provider": "openai/gpt-4o-mini", "api_token": "qkey", "base_url": None}
    embed_cfg = {"provider": "openai/text-embedding-3-small", "api_token": "ekey"}

    strategy = EmbeddingStrategy(
        llm_config=embed_cfg,
        query_llm_config=query_cfg,
    )
    result = strategy._get_query_llm_config_dict()
    assert result["provider"] == "openai/gpt-4o-mini"
    assert result["api_token"] == "qkey"


def test_fallback_to_llm_config():
    """When query_llm_config is None, fall back to llm_config."""
    embed_cfg = {"provider": "openai/gpt-4o-mini", "api_token": "shared"}
    strategy = EmbeddingStrategy(llm_config=embed_cfg)
    result = strategy._get_query_llm_config_dict()
    assert result["provider"] == "openai/gpt-4o-mini"


def test_returns_none_when_no_config():
    """With no config at all, return None (caller uses defaults)."""
    strategy = EmbeddingStrategy()
    result = strategy._get_query_llm_config_dict()
    assert result is None


def test_adaptive_config_fallback():
    """AdaptiveConfig._query_llm_config_dict should be used as fallback."""
    from crawl4ai import LLMConfig
    ac = AdaptiveConfig(
        query_llm_config=LLMConfig(provider="anthropic/claude-3-haiku", api_token="akey")
    )
    strategy = EmbeddingStrategy()
    strategy.config = ac
    result = strategy._get_query_llm_config_dict()
    assert result["provider"] == "anthropic/claude-3-haiku"


def test_base_url_in_query_config():
    """base_url should be available from query config dict."""
    query_cfg = {
        "provider": "openai/gpt-4o",
        "api_token": "key",
        "base_url": "https://custom.example.com/v1",
    }
    strategy = EmbeddingStrategy(query_llm_config=query_cfg)
    result = strategy._get_query_llm_config_dict()
    assert result["base_url"] == "https://custom.example.com/v1"


def test_embedding_config_separate_from_query():
    """_get_embedding_llm_config_dict should NOT return query config."""
    from crawl4ai import LLMConfig
    ac = AdaptiveConfig(
        embedding_llm_config=LLMConfig(provider="openai/text-embedding-3-small", api_token="ekey"),
        query_llm_config=LLMConfig(provider="openai/gpt-4o-mini", api_token="qkey"),
    )
    strategy = EmbeddingStrategy()
    strategy.config = ac

    embed_cfg = strategy._get_embedding_llm_config_dict()
    query_cfg = strategy._get_query_llm_config_dict()
    assert embed_cfg["provider"] == "openai/text-embedding-3-small"
    assert query_cfg["provider"] == "openai/gpt-4o-mini"


def test_llm_config_object_converted_to_dict():
    """LLMConfig objects should be converted to dicts via to_dict()."""
    from crawl4ai import LLMConfig
    cfg = LLMConfig(provider="openai/gpt-4o", api_token="tok123")
    strategy = EmbeddingStrategy(query_llm_config=cfg)
    result = strategy._get_query_llm_config_dict()
    assert isinstance(result, dict)
    assert result["provider"] == "openai/gpt-4o"
    assert result["api_token"] == "tok123"


# ── map_query_semantic_space uses correct config ──────────────


def test_map_query_uses_get_query_llm_config():
    """map_query_semantic_space should call _get_query_llm_config_dict."""
    source = inspect.getsource(EmbeddingStrategy.map_query_semantic_space)
    assert "_get_query_llm_config_dict" in source


def test_map_query_passes_base_url():
    """map_query_semantic_space should pass base_url to perform_completion."""
    source = inspect.getsource(EmbeddingStrategy.map_query_semantic_space)
    assert "base_url=" in source


def test_map_query_passes_backoff_params():
    """map_query_semantic_space should pass backoff params."""
    source = inspect.getsource(EmbeddingStrategy.map_query_semantic_space)
    assert "base_delay=" in source
    assert "max_attempts=" in source
    assert "exponential_factor=" in source
