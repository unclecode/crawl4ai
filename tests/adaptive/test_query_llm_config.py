"""
E2E tests for separate embedding and query LLM configs (issue #1682).

Tests that AdaptiveConfig.query_llm_config flows correctly through
AdaptiveCrawler → EmbeddingStrategy → map_query_semantic_space,
and that the right config is used for embeddings vs query expansion.
"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))

from crawl4ai import AdaptiveConfig, LLMConfig
from crawl4ai.adaptive_crawler import EmbeddingStrategy, AdaptiveCrawler


# ---------------------------------------------------------------------------
# Test 1: Config plumbing — AdaptiveConfig → AdaptiveCrawler → EmbeddingStrategy
# ---------------------------------------------------------------------------

def test_config_plumbing():
    """query_llm_config flows from AdaptiveConfig through _create_strategy."""
    config = AdaptiveConfig(
        strategy="embedding",
        embedding_llm_config=LLMConfig(provider="openai/text-embedding-3-small", api_token="emb-key"),
        query_llm_config=LLMConfig(provider="openai/gpt-4o-mini", api_token="query-key"),
    )

    # Simulate what AdaptiveCrawler.__init__ does
    with patch("crawl4ai.adaptive_crawler.AsyncWebCrawler"):
        crawler_mock = MagicMock()
        adaptive = AdaptiveCrawler(crawler=crawler_mock, config=config)

    strategy = adaptive.strategy
    assert isinstance(strategy, EmbeddingStrategy)

    # Strategy should have both configs
    assert strategy.query_llm_config is not None
    query_dict = strategy._get_query_llm_config_dict()
    assert query_dict["provider"] == "openai/gpt-4o-mini"
    assert query_dict["api_token"] == "query-key"

    emb_dict = strategy._get_embedding_llm_config_dict()
    assert emb_dict["provider"] == "openai/text-embedding-3-small"
    assert emb_dict["api_token"] == "emb-key"

    print("PASS: test_config_plumbing")


# ---------------------------------------------------------------------------
# Test 2: Backward compat — no query_llm_config falls back to llm_config
# ---------------------------------------------------------------------------

def test_backward_compat_fallback():
    """When query_llm_config is not set, falls back to llm_config (legacy)."""
    strategy = EmbeddingStrategy(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        llm_config={"provider": "openai/gpt-4o-mini", "api_token": "shared-key"},
        query_llm_config=None,
    )
    # No AdaptiveConfig attached → should fall back to llm_config
    result = strategy._get_query_llm_config_dict()
    assert result["provider"] == "openai/gpt-4o-mini"
    assert result["api_token"] == "shared-key"
    print("PASS: test_backward_compat_fallback")


def test_backward_compat_no_config():
    """When nothing is set, returns None (caller uses hardcoded defaults)."""
    strategy = EmbeddingStrategy()
    result = strategy._get_query_llm_config_dict()
    assert result is None
    print("PASS: test_backward_compat_no_config")


# ---------------------------------------------------------------------------
# Test 3: Fallback priority chain
# ---------------------------------------------------------------------------

def test_fallback_priority():
    """Explicit query_llm_config beats AdaptiveConfig beats llm_config."""
    config = AdaptiveConfig(
        strategy="embedding",
        query_llm_config={"provider": "config-level", "api_token": "cfg"},
    )
    strategy = EmbeddingStrategy(
        llm_config={"provider": "legacy-level", "api_token": "leg"},
        query_llm_config={"provider": "strategy-level", "api_token": "strat"},
    )
    strategy.config = config

    # Strategy-level should win
    result = strategy._get_query_llm_config_dict()
    assert result["provider"] == "strategy-level"

    # Remove strategy-level → config-level should win
    strategy.query_llm_config = None
    result = strategy._get_query_llm_config_dict()
    assert result["provider"] == "config-level"

    # Remove config-level → legacy llm_config should win
    config.query_llm_config = None
    result = strategy._get_query_llm_config_dict()
    assert result["provider"] == "legacy-level"

    # Remove everything → None
    strategy.llm_config = None
    result = strategy._get_query_llm_config_dict()
    assert result is None

    print("PASS: test_fallback_priority")


# ---------------------------------------------------------------------------
# Test 4: E2E — map_query_semantic_space uses query config, not embedding config
# ---------------------------------------------------------------------------

async def test_map_query_uses_query_config():
    """map_query_semantic_space should call perform_completion_with_backoff
    with the query LLM config (chat model), NOT the embedding config."""

    config = AdaptiveConfig(
        strategy="embedding",
        embedding_llm_config=LLMConfig(
            provider="openai/text-embedding-3-small",
            api_token="emb-key",
            base_url="https://emb.example.com",
        ),
        query_llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token="query-key",
            base_url="https://query.example.com",
        ),
    )

    strategy = EmbeddingStrategy(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        llm_config=config.embedding_llm_config,
        query_llm_config=config.query_llm_config,
    )
    strategy.config = config

    # Mock perform_completion_with_backoff to capture its arguments
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "queries": [f"variation {i}" for i in range(13)]
    })

    captured_kwargs = {}

    def mock_completion(**kwargs):
        # Also accept positional-style
        captured_kwargs.update(kwargs)
        return mock_response

    # Also mock _get_embeddings to avoid real embedding calls
    fake_embeddings = np.random.rand(11, 384).astype(np.float32)

    with patch("crawl4ai.utils.perform_completion_with_backoff", side_effect=mock_completion):
        with patch.object(strategy, "_get_embeddings", new_callable=AsyncMock, return_value=fake_embeddings):
            await strategy.map_query_semantic_space("test query", n_synthetic=10)

    # Verify the query config was used, NOT the embedding config
    assert captured_kwargs["provider"] == "openai/gpt-4o-mini", \
        f"Expected query model, got {captured_kwargs['provider']}"
    assert captured_kwargs["api_token"] == "query-key", \
        f"Expected query-key, got {captured_kwargs['api_token']}"
    assert captured_kwargs["base_url"] == "https://query.example.com", \
        f"Expected query base_url, got {captured_kwargs['base_url']}"

    # Verify backoff params are passed (bug fix)
    assert "base_delay" in captured_kwargs
    assert "max_attempts" in captured_kwargs
    assert "exponential_factor" in captured_kwargs

    print("PASS: test_map_query_uses_query_config")


# ---------------------------------------------------------------------------
# Test 5: E2E — legacy single-config still works for query expansion
# ---------------------------------------------------------------------------

async def test_legacy_single_config_for_query():
    """When only embedding_llm_config is set (old usage), query expansion
    falls back to it via llm_config → still works."""

    single_config = LLMConfig(
        provider="openai/gpt-4o-mini",
        api_token="single-key",
    )

    config = AdaptiveConfig(
        strategy="embedding",
        embedding_llm_config=single_config,
        # No query_llm_config — legacy usage
    )

    strategy = EmbeddingStrategy(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        llm_config=config.embedding_llm_config,  # This is how _create_strategy passes it
        # No query_llm_config
    )
    strategy.config = config

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "queries": [f"variation {i}" for i in range(13)]
    })

    captured_kwargs = {}

    def mock_completion(**kwargs):
        captured_kwargs.update(kwargs)
        return mock_response

    fake_embeddings = np.random.rand(11, 384).astype(np.float32)

    with patch("crawl4ai.utils.perform_completion_with_backoff", side_effect=mock_completion):
        with patch.object(strategy, "_get_embeddings", new_callable=AsyncMock, return_value=fake_embeddings):
            await strategy.map_query_semantic_space("test query", n_synthetic=10)

    # Should fall back to llm_config (the single shared config)
    assert captured_kwargs["provider"] == "openai/gpt-4o-mini"
    assert captured_kwargs["api_token"] == "single-key"

    print("PASS: test_legacy_single_config_for_query")


# ---------------------------------------------------------------------------
# Test 6: LLMConfig.to_dict() includes backoff params (bug fix verification)
# ---------------------------------------------------------------------------

def test_to_dict_includes_backoff():
    """_embedding_llm_config_dict now uses to_dict() which includes backoff params."""
    config = AdaptiveConfig(
        embedding_llm_config=LLMConfig(
            provider="openai/text-embedding-3-small",
            api_token="test",
            backoff_base_delay=5,
            backoff_max_attempts=10,
            backoff_exponential_factor=3,
        ),
    )
    d = config._embedding_llm_config_dict
    assert d["backoff_base_delay"] == 5
    assert d["backoff_max_attempts"] == 10
    assert d["backoff_exponential_factor"] == 3
    print("PASS: test_to_dict_includes_backoff")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print("=" * 60)
    print("E2E Tests: Separate Embedding & Query LLM Configs (#1682)")
    print("=" * 60)

    # Sync tests
    test_config_plumbing()
    test_backward_compat_fallback()
    test_backward_compat_no_config()
    test_fallback_priority()
    test_to_dict_includes_backoff()

    # Async tests
    await test_map_query_uses_query_config()
    await test_legacy_single_config_for_query()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
