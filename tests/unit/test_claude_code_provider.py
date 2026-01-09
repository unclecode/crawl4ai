"""
Unit tests for Claude Code Provider (TDD - RED Phase)

These tests are written BEFORE the implementation to follow TDD methodology.
All tests should FAIL initially until the provider is implemented.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestClaudeCodeProviderImport:
    """Test that the provider module can be imported."""

    def test_provider_module_exists(self):
        """The provider module should exist and be importable."""
        from crawl4ai.providers import claude_code_provider
        assert claude_code_provider is not None

    def test_provider_class_exists(self):
        """The ClaudeCodeProvider class should exist."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        assert ClaudeCodeProvider is not None

    def test_provider_inherits_from_custom_llm(self):
        """ClaudeCodeProvider should inherit from LiteLLM's CustomLLM."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        from litellm import CustomLLM
        assert issubclass(ClaudeCodeProvider, CustomLLM)


class TestModelExtraction:
    """Test model name extraction from provider string."""

    def test_extracts_model_from_provider_string(self):
        """Should extract 'claude-sonnet-4' from 'claude-code/claude-sonnet-4'."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        provider = ClaudeCodeProvider()

        result = provider._extract_model("claude-code/claude-sonnet-4-20250514")
        assert result == "claude-sonnet-4-20250514"

    def test_extracts_model_with_opus(self):
        """Should extract opus model correctly."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        provider = ClaudeCodeProvider()

        result = provider._extract_model("claude-code/claude-opus-4-20250514")
        assert result == "claude-opus-4-20250514"

    def test_extracts_model_with_haiku(self):
        """Should extract haiku model correctly."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        provider = ClaudeCodeProvider()

        result = provider._extract_model("claude-code/claude-haiku-3-5-latest")
        assert result == "claude-haiku-3-5-latest"

    def test_handles_model_without_prefix(self):
        """Should return model as-is if no prefix."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        provider = ClaudeCodeProvider()

        result = provider._extract_model("claude-sonnet-4-20250514")
        assert result == "claude-sonnet-4-20250514"


class TestMessageConversion:
    """Test conversion from LiteLLM message format to prompt string."""

    def test_single_user_message(self):
        """Should convert single user message to prompt."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        provider = ClaudeCodeProvider()

        messages = [{"role": "user", "content": "Hello"}]
        result = provider._convert_messages_to_prompt(messages)

        assert "Hello" in result

    def test_system_and_user_messages(self):
        """Should include both system and user messages."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        provider = ClaudeCodeProvider()

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        result = provider._convert_messages_to_prompt(messages)

        assert "You are helpful" in result
        assert "Hello" in result

    def test_multi_turn_conversation(self):
        """Should handle multi-turn conversations."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        provider = ClaudeCodeProvider()

        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]
        result = provider._convert_messages_to_prompt(messages)

        assert "Be helpful" in result
        assert "Hello" in result
        assert "Hi there" in result
        assert "How are you?" in result

    def test_empty_messages(self):
        """Should handle empty message list."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        provider = ClaudeCodeProvider()

        messages = []
        result = provider._convert_messages_to_prompt(messages)

        assert result == ""


class TestCompletionMethods:
    """Test completion and acompletion methods."""

    @pytest.mark.asyncio
    async def test_acompletion_returns_model_response(self):
        """acompletion should return a LiteLLM ModelResponse."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        from litellm.types.utils import ModelResponse

        provider = ClaudeCodeProvider()

        # Mock the _collect_response method instead of the SDK directly
        async def mock_collect_response(prompt, model):
            return ("Test response", {"session_id": "test-session", "input_tokens": 10, "output_tokens": 5})

        with patch.object(provider, '_collect_response', mock_collect_response):
            result = await provider.acompletion(
                model="claude-code/claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": "Hello"}]
            )

            assert isinstance(result, ModelResponse)

    @pytest.mark.asyncio
    async def test_acompletion_extracts_text_content(self):
        """acompletion should extract text from Claude SDK response."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider

        provider = ClaudeCodeProvider()

        async def mock_collect_response(prompt, model):
            return ("The capital of France is Paris.", {"session_id": "test-session", "input_tokens": 10, "output_tokens": 5})

        with patch.object(provider, '_collect_response', mock_collect_response):
            result = await provider.acompletion(
                model="claude-code/claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": "What is the capital of France?"}]
            )

            assert "Paris" in result.choices[0].message.content

    def test_completion_calls_acompletion(self):
        """Sync completion should internally call acompletion."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider

        provider = ClaudeCodeProvider()

        with patch.object(provider, 'acompletion', new_callable=AsyncMock) as mock_acompletion:
            mock_response = MagicMock()
            mock_acompletion.return_value = mock_response

            result = provider.completion(
                model="claude-code/claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": "Hello"}]
            )

            mock_acompletion.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_import_error_when_sdk_not_installed(self):
        """Should raise ImportError with helpful message if SDK not installed."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider

        provider = ClaudeCodeProvider()

        with patch.dict('sys.modules', {'claude_agent_sdk': None}):
            with pytest.raises(ImportError) as exc_info:
                await provider.acompletion(
                    model="claude-code/claude-sonnet-4-20250514",
                    messages=[{"role": "user", "content": "Hello"}]
                )

            assert "claude-agent-sdk" in str(exc_info.value).lower() or \
                   "pip install" in str(exc_info.value).lower()


class TestProviderRegistration:
    """Test that the provider is registered correctly with LiteLLM."""

    def test_registration_function_exists(self):
        """register_custom_providers function should exist."""
        from crawl4ai.providers import register_custom_providers
        assert callable(register_custom_providers)

    def test_provider_registered_after_import(self):
        """Provider should be registered after calling register_custom_providers."""
        import litellm
        from crawl4ai.providers import register_custom_providers

        # Call registration
        register_custom_providers()

        # Check if claude-code is in custom_provider_map
        providers = [p.get("provider") for p in (litellm.custom_provider_map or [])]
        assert "claude-code" in providers


class TestConfigIntegration:
    """Test integration with Crawl4AI's config system."""

    def test_provider_prefix_in_config(self):
        """claude-code should be in PROVIDER_MODELS_PREFIXES."""
        from crawl4ai.config import PROVIDER_MODELS_PREFIXES

        assert "claude-code" in PROVIDER_MODELS_PREFIXES

    def test_provider_prefix_value_is_no_token_needed(self):
        """claude-code should require no token (uses local auth)."""
        from crawl4ai.config import PROVIDER_MODELS_PREFIXES

        assert PROVIDER_MODELS_PREFIXES.get("claude-code") == "no-token-needed"


class TestLLMConfigIntegration:
    """Test integration with LLMConfig class."""

    def test_llm_config_accepts_claude_code_provider(self):
        """LLMConfig should accept claude-code provider without error."""
        from crawl4ai.async_configs import LLMConfig

        config = LLMConfig(provider="claude-code/claude-sonnet-4-20250514")

        assert config.provider == "claude-code/claude-sonnet-4-20250514"

    def test_llm_config_resolves_no_token_needed(self):
        """LLMConfig should resolve api_token to 'no-token-needed' for claude-code."""
        from crawl4ai.async_configs import LLMConfig

        config = LLMConfig(provider="claude-code/claude-sonnet-4-20250514")

        assert config.api_token == "no-token-needed"
