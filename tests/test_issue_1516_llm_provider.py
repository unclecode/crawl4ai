"""
Tests for #1516: /llm endpoint provider/temperature/base_url override.

The GET /llm endpoint should accept per-request LLM configuration,
matching the /md and /llm/job endpoints.
"""

import inspect
import pytest


# ── server.py: endpoint signature ─────────────────────────────


def _read_server_source():
    with open("deploy/docker/server.py") as f:
        return f.read()


def test_llm_endpoint_has_provider_param():
    """GET /llm should accept provider query param."""
    src = _read_server_source()
    assert "provider: Optional[str] = Query(None)" in src


def test_llm_endpoint_has_temperature_param():
    """GET /llm should accept temperature query param."""
    src = _read_server_source()
    assert "temperature: Optional[float] = Query(None)" in src


def test_llm_endpoint_has_base_url_param():
    """GET /llm should accept base_url query param."""
    src = _read_server_source()
    assert "base_url: Optional[str] = Query(None)" in src


def test_llm_endpoint_passes_params_to_handler():
    """GET /llm should pass all three params to handle_llm_qa."""
    src = _read_server_source()
    assert "provider=provider" in src
    assert "temperature=temperature" in src
    assert "base_url=base_url" in src


# ── api.py: handler signature ─────────────────────────────────


def _read_api_source():
    with open("deploy/docker/api.py") as f:
        return f.read()


def test_handle_llm_qa_accepts_provider():
    """handle_llm_qa should accept provider kwarg."""
    src = _read_api_source()
    assert "provider: Optional[str] = None" in src


def test_handle_llm_qa_accepts_temperature():
    """handle_llm_qa should accept temperature kwarg."""
    src = _read_api_source()
    assert "temperature: Optional[float] = None" in src


def test_handle_llm_qa_accepts_base_url():
    """handle_llm_qa should accept base_url kwarg."""
    src = _read_api_source()
    assert "base_url: Optional[str] = None" in src


# ── api.py: provider override logic ──────────────────────────


def test_provider_validated():
    """handle_llm_qa should validate the provider."""
    src = _read_api_source()
    assert "validate_llm_provider(config, provider)" in src


def test_provider_override_in_completion():
    """Provider override should be passed to perform_completion_with_backoff."""
    src = _read_api_source()
    assert 'provider=provider or config["llm"]["provider"]' in src


def test_api_key_uses_provider_override():
    """get_llm_api_key should receive the provider override."""
    src = _read_api_source()
    assert "get_llm_api_key(config, provider)" in src


def test_temperature_uses_override():
    """Temperature should use override with fallback."""
    src = _read_api_source()
    assert "temperature=temperature or get_llm_temperature(config, provider)" in src


def test_base_url_uses_override():
    """Base URL should use override with fallback."""
    src = _read_api_source()
    assert "base_url=base_url or get_llm_base_url(config, provider)" in src


# ── parity checks ────────────────────────────────────────────


def test_md_endpoint_already_has_provider():
    """The /md endpoint should already accept provider (for comparison)."""
    src = _read_server_source()
    # /md uses body.provider via MarkdownRequest
    assert "body.provider" in src


def test_no_hardcoded_api_key_comment():
    """Old commented-out api_token line should be removed."""
    src = _read_api_source()
    # The old comment was: # api_token=os.environ.get(config["llm"].get("api_key_env", ""))
    assert 'api_token=os.environ.get(config["llm"]' not in src
