"""
R3 LLM-broker tests: a request selects a provider BY NAME only; base_url and
api_token are always server-derived, so the configured provider key can never
be redirected to an attacker endpoint (the reported credential-exfil gadget).
"""

import pytest

from llm_broker import resolve_llm, allowed_provider_families, LLMProviderNotAllowed

pytestmark = pytest.mark.posture

CONF = {"llm": {"provider": "openai/gpt-4o-mini"}}


class TestProviderAllowlist:
    def test_default_provider_allowed(self):
        out = resolve_llm(CONF, None)
        assert out["provider"] == "openai/gpt-4o-mini"

    def test_same_family_allowed(self):
        out = resolve_llm(CONF, "openai/gpt-4o")
        assert out["provider"] == "openai/gpt-4o"

    def test_other_family_rejected(self):
        with pytest.raises(LLMProviderNotAllowed):
            resolve_llm(CONF, "anthropic/claude-3-opus")

    def test_explicit_allowlist_widens(self):
        conf = {"llm": {"provider": "openai/gpt-4o-mini",
                        "allowed_providers": ["anthropic/claude-3-opus"]}}
        assert resolve_llm(conf, "anthropic/claude-3-opus")["provider"].startswith("anthropic/")


class TestBaseUrlIsServerOnly:
    def test_resolve_has_no_request_base_url_param(self):
        import inspect
        params = list(inspect.signature(resolve_llm).parameters)
        # only (config, requested_provider) - no way to inject base_url/api_token
        assert params == ["config", "requested_provider"]

    def test_base_url_is_canonical_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.example")
        out = resolve_llm(CONF, "openai/gpt-4o-mini")
        assert out["base_url"] == "https://api.openai.example"

    def test_no_base_url_when_unset(self, monkeypatch):
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        out = resolve_llm(CONF, "openai/gpt-4o-mini")
        assert out["base_url"] is None


class TestRequestSurfaceRemoved:
    def test_markdown_request_has_no_base_url(self):
        from schemas import MarkdownRequest
        assert "base_url" not in MarkdownRequest.model_fields

    def test_llm_job_payload_has_no_base_url(self):
        from job import LlmJobPayload
        assert "base_url" not in LlmJobPayload.model_fields

    def test_llm_endpoint_has_no_base_url_query(self, server_module):
        import inspect
        assert "base_url" not in inspect.signature(server_module.llm_endpoint).parameters

    def test_md_endpoint_rejects_disallowed_provider(self, stock_client, server_module):
        from auth import create_access_token
        h = {"Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'})}"}
        # LLM filter + a provider outside the allowed family -> 400 (not a 500,
        # and no LLM call to an attacker endpoint).
        r = stock_client.post(
            "/md",
            json={"url": "https://example.com", "f": "llm", "provider": "attacker/model",
                  "base_url": "http://169.254.169.254"},
            headers=h,
        )
        assert r.status_code == 400, r.status_code
