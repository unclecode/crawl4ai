"""Tests for the named OrcaRouter provider integration.

OrcaRouter (https://www.orcarouter.ai) is an OpenAI-compatible gateway. The
pinned ``unclecode-litellm`` build has no native ``orcarouter/`` provider prefix,
so crawl4ai routes ``orcarouter/<model>`` through the ``openai`` provider while
keeping the full model id intact and pointing ``base_url`` at the gateway.
"""

import os
import sys

# Env vars are read by crawl4ai.config.PROVIDER_MODELS_PREFIXES at import time
# (same as OPENAI_API_KEY / DEEPSEEK_API_KEY), so set them before importing.
os.environ.setdefault("ORCAROUTER_API_KEY", "sk-orca-env")

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.config import ORCAROUTER_BASE_URL, orcarouter_litellm_params
from crawl4ai import LLMConfig


class TestOrcarouterLitellmParams:
    def test_routes_orcarouter_models(self):
        params = orcarouter_litellm_params("orcarouter/auto", "sk-orca-test", None)
        assert params["custom_llm_provider"] == "openai"
        assert params["api_key"] == "sk-orca-test"
        assert params["base_url"] == ORCAROUTER_BASE_URL

    def test_defaults_base_url_to_gateway(self):
        params = orcarouter_litellm_params("orcarouter/free", "sk-orca-test", None)
        assert params["base_url"] == "https://api.orcarouter.ai/v1"

    def test_honors_custom_base_url(self):
        params = orcarouter_litellm_params(
            "orcarouter/auto", "sk-orca-test", "https://example.com/v1"
        )
        assert params["base_url"] == "https://example.com/v1"

    def test_ignores_non_orcarouter_providers(self):
        assert orcarouter_litellm_params("openai/gpt-4o", "key", None) == {}
        assert orcarouter_litellm_params("groq/llama3-70b-8192", "key", None) == {}
        assert orcarouter_litellm_params(None, "key", None) == {}

    def test_keeps_full_model_id(self):
        # The helper never rewrites the provider string; litellm receives
        # `model="orcarouter/auto"` with custom_llm_provider="openai".
        params = orcarouter_litellm_params("orcarouter/auto", "sk-orca-test", None)
        assert "model" not in params
        assert params["custom_llm_provider"] == "openai"


class TestLLMConfigOrcarouter:
    def test_api_token_auto_resolved(self):
        config = LLMConfig(provider="orcarouter/auto")
        assert config.api_token == "sk-orca-env"
        assert config.base_url == ORCAROUTER_BASE_URL

    def test_explicit_api_token_wins(self):
        config = LLMConfig(provider="orcarouter/auto", api_token="sk-orca-explicit")
        assert config.api_token == "sk-orca-explicit"

    def test_explicit_base_url_wins(self):
        config = LLMConfig(
            provider="orcarouter/auto", base_url="https://example.com/v1"
        )
        assert config.base_url == "https://example.com/v1"

    def test_non_orcarouter_unchanged(self):
        config = LLMConfig(provider="openai/gpt-4o")
        assert config.base_url is None
