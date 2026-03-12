"""
Unit tests for fixes #1678, #1574, #1516.

These tests verify the logic changes without requiring a running Docker
server, Redis, or external LLM APIs.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass
from typing import Optional


# ── #1678: MCP WebSocket SessionMessage wrapping ──────────────────────


class TestMCPWebSocketSessionMessage:
    """Verify that the WebSocket transport wraps/unwraps SessionMessage."""

    def test_session_message_import(self):
        """SessionMessage should be importable from mcp.shared.message."""
        from mcp.shared.message import SessionMessage
        assert SessionMessage is not None

    def test_wrap_jsonrpc_in_session_message(self):
        """JSONRPCMessage should be wrappable in SessionMessage."""
        from mcp.types import JSONRPCMessage
        from mcp.shared.message import SessionMessage
        from pydantic import TypeAdapter

        adapter = TypeAdapter(JSONRPCMessage)
        raw = {"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {}}
        json_msg = adapter.validate_python(raw)
        session_msg = SessionMessage(message=json_msg)

        assert hasattr(session_msg, "message")
        assert session_msg.message is json_msg

    def test_unwrap_session_message(self):
        """Unwrapping SessionMessage should yield the original JSONRPCMessage."""
        from mcp.types import JSONRPCMessage
        from mcp.shared.message import SessionMessage
        from pydantic import TypeAdapter

        adapter = TypeAdapter(JSONRPCMessage)
        raw = {"jsonrpc": "2.0", "method": "ping", "id": 2}
        json_msg = adapter.validate_python(raw)
        session_msg = SessionMessage(message=json_msg)

        # The srv_to_ws function does this unwrap
        unwrapped = session_msg.message if isinstance(session_msg, SessionMessage) else session_msg
        assert unwrapped is json_msg
        # Should be serializable
        dumped = unwrapped.model_dump()
        assert dumped["jsonrpc"] == "2.0"

    def test_raw_jsonrpc_passthrough(self):
        """If msg is already a JSONRPCMessage (not SessionMessage), passthrough works."""
        from mcp.types import JSONRPCMessage
        from mcp.shared.message import SessionMessage
        from pydantic import TypeAdapter

        adapter = TypeAdapter(JSONRPCMessage)
        raw = {"jsonrpc": "2.0", "method": "test", "id": 3}
        json_msg = adapter.validate_python(raw)

        # Simulate the isinstance check in srv_to_ws
        result = json_msg.message if isinstance(json_msg, SessionMessage) else json_msg
        assert result is json_msg


# ── #1574: EmbeddingStrategy config fallback ──────────────────────────


class TestEmbeddingStrategyConfigFallback:
    """Verify that map_query_semantic_space uses _get_query_llm_config_dict."""

    def test_query_config_used_over_embedding_config(self):
        """query_llm_config should take priority over llm_config for query generation."""
        from crawl4ai.adaptive_crawler import EmbeddingStrategy

        query_cfg = {"provider": "openai/gpt-4o-mini", "api_token": "qkey", "base_url": None}
        embed_cfg = {"provider": "openai/text-embedding-3-small", "api_token": "ekey"}

        strategy = EmbeddingStrategy(
            llm_config=embed_cfg,
            query_llm_config=query_cfg,
        )

        result = strategy._get_query_llm_config_dict()
        assert result["provider"] == "openai/gpt-4o-mini"
        assert result["api_token"] == "qkey"

    def test_fallback_to_llm_config_when_no_query_config(self):
        """When query_llm_config is None, fall back to llm_config."""
        from crawl4ai.adaptive_crawler import EmbeddingStrategy

        embed_cfg = {"provider": "openai/gpt-4o-mini", "api_token": "shared_key"}

        strategy = EmbeddingStrategy(llm_config=embed_cfg)
        result = strategy._get_query_llm_config_dict()
        assert result["provider"] == "openai/gpt-4o-mini"
        assert result["api_token"] == "shared_key"

    def test_returns_none_when_no_config(self):
        """When no config is provided, return None."""
        from crawl4ai.adaptive_crawler import EmbeddingStrategy

        strategy = EmbeddingStrategy()
        result = strategy._get_query_llm_config_dict()
        assert result is None

    def test_no_mock_data_in_source(self):
        """The commented-out 'fried rice' mock data should be removed."""
        import inspect
        from crawl4ai.adaptive_crawler import EmbeddingStrategy

        source = inspect.getsource(EmbeddingStrategy.map_query_semantic_space)
        assert "fried rice" not in source
        assert "vegetable fried rice" not in source

    def test_base_url_extracted_from_config(self):
        """base_url should be extracted from the query config dict."""
        from crawl4ai.adaptive_crawler import EmbeddingStrategy

        query_cfg = {
            "provider": "openai/gpt-4o-mini",
            "api_token": "key",
            "base_url": "https://custom.api.example.com",
        }
        strategy = EmbeddingStrategy(query_llm_config=query_cfg)
        result = strategy._get_query_llm_config_dict()
        assert result["base_url"] == "https://custom.api.example.com"


# ── #1516: /llm endpoint provider override ────────────────────────────


class TestLlmEndpointProviderOverride:
    """Verify handle_llm_qa accepts provider/temperature/base_url params."""

    def test_handle_llm_qa_signature(self):
        """handle_llm_qa should accept provider, temperature, base_url kwargs."""
        import inspect
        import importlib.util

        spec = importlib.util.spec_from_file_location("api", "deploy/docker/api.py")
        # Just check the source contains the right signature
        with open("deploy/docker/api.py") as f:
            source = f.read()

        assert "provider: Optional[str] = None" in source
        assert "temperature: Optional[float] = None" in source
        assert "base_url: Optional[str] = None" in source
        # Should use provider override in perform_completion_with_backoff
        assert "provider=provider or config" in source
        assert "get_llm_api_key(config, provider)" in source

    def test_llm_endpoint_signature(self):
        """GET /llm endpoint should accept provider, temperature, base_url query params."""
        with open("deploy/docker/server.py") as f:
            source = f.read()

        assert 'provider: Optional[str] = Query(None)' in source
        assert 'temperature: Optional[float] = Query(None)' in source
        assert 'base_url: Optional[str] = Query(None)' in source
        assert "provider=provider, temperature=temperature, base_url=base_url" in source

    def test_provider_validation_added(self):
        """handle_llm_qa should validate the provider before calling LLM."""
        with open("deploy/docker/api.py") as f:
            source = f.read()

        # Should validate provider in handle_llm_qa
        assert "validate_llm_provider(config, provider)" in source
