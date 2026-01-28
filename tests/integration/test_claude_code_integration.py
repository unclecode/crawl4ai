"""
Integration tests for Claude Code Provider.

These tests require Claude Code CLI to be installed and authenticated,
AND the claude-agent-sdk package to be installed.
They will be skipped if either is not available.
"""
import pytest
import shutil
import asyncio

# Check if claude-agent-sdk is installed
def _sdk_available():
    try:
        import claude_agent_sdk
        return True
    except ImportError:
        return False

# Mark for tests that need both CLI and SDK
requires_claude_code = pytest.mark.skipif(
    not shutil.which("claude") or not _sdk_available(),
    reason="Claude Code CLI or claude-agent-sdk not installed"
)


class TestClaudeCodeIntegration:
    """Integration tests with real Claude Code CLI."""

    @requires_claude_code
    @pytest.mark.asyncio
    async def test_basic_completion_with_claude_code(self):
        """Test basic completion using Claude Code provider."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        from litellm.types.utils import ModelResponse

        provider = ClaudeCodeProvider()

        # Simple prompt that should get a quick response
        result = await provider.acompletion(
            model="claude-code/claude-haiku-3-5-latest",  # Use Haiku for speed
            messages=[{"role": "user", "content": "Reply with only the word 'hello'"}]
        )

        assert isinstance(result, ModelResponse)
        assert result.choices[0].message.content is not None
        assert len(result.choices[0].message.content) > 0

    def test_llm_config_with_claude_code(self):
        """Test LLMConfig works with claude-code provider."""
        from crawl4ai.async_configs import LLMConfig

        config = LLMConfig(provider="claude-code/claude-haiku-3-5-latest")

        assert config.provider == "claude-code/claude-haiku-3-5-latest"
        assert config.api_token == "no-token-needed"

    @requires_claude_code
    @pytest.mark.asyncio
    async def test_extraction_strategy_with_claude_code(self):
        """Test LLMExtractionStrategy with Claude Code provider."""
        from crawl4ai.async_configs import LLMConfig
        from crawl4ai.extraction_strategy import LLMExtractionStrategy

        config = LLMConfig(provider="claude-code/claude-haiku-3-5-latest")

        strategy = LLMExtractionStrategy(
            llm_config=config,
            instruction="Extract the main heading text"
        )

        # Simple HTML to extract from
        html = "<html><body><h1>Test Heading</h1><p>Some content</p></body></html>"

        # Run extraction
        result = await strategy.aextract(
            url="https://example.com",
            ix=0,
            html=html
        )

        # Should get some result (exact format depends on extraction)
        assert result is not None

    @requires_claude_code
    @pytest.mark.asyncio
    async def test_model_selection_sonnet(self):
        """Test that Sonnet model can be used."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider
        from litellm.types.utils import ModelResponse

        provider = ClaudeCodeProvider()

        result = await provider.acompletion(
            model="claude-code/claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Say 'test' only"}]
        )

        assert isinstance(result, ModelResponse)
        assert result.model == "claude-sonnet-4-20250514"

    @requires_claude_code
    @pytest.mark.asyncio
    async def test_system_prompt_handling(self):
        """Test that system prompts are properly included."""
        from crawl4ai.providers.claude_code_provider import ClaudeCodeProvider

        provider = ClaudeCodeProvider()

        result = await provider.acompletion(
            model="claude-code/claude-haiku-3-5-latest",
            messages=[
                {"role": "system", "content": "You only respond with the word 'CONFIRMED'"},
                {"role": "user", "content": "Hello"}
            ]
        )

        # System prompt should influence the response
        assert result.choices[0].message.content is not None


class TestBackwardCompatibility:
    """Test that existing providers still work alongside claude-code."""

    def test_existing_providers_still_in_config(self):
        """Ensure existing providers weren't removed."""
        from crawl4ai.config import PROVIDER_MODELS_PREFIXES

        # Original providers should still exist
        assert "ollama" in PROVIDER_MODELS_PREFIXES
        assert "openai" in PROVIDER_MODELS_PREFIXES
        assert "anthropic" in PROVIDER_MODELS_PREFIXES
        assert "gemini" in PROVIDER_MODELS_PREFIXES
        assert "deepseek" in PROVIDER_MODELS_PREFIXES

        # New provider should also exist
        assert "claude-code" in PROVIDER_MODELS_PREFIXES

    def test_llm_config_still_works_with_openai(self):
        """LLMConfig should still work with OpenAI provider."""
        from crawl4ai.async_configs import LLMConfig
        import os

        # Set a dummy key for testing
        original = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-key"

        try:
            config = LLMConfig(provider="openai/gpt-4o")
            assert config.provider == "openai/gpt-4o"
        finally:
            if original:
                os.environ["OPENAI_API_KEY"] = original
            else:
                os.environ.pop("OPENAI_API_KEY", None)

    def test_llm_config_still_works_with_anthropic(self):
        """LLMConfig should still work with Anthropic provider."""
        from crawl4ai.async_configs import LLMConfig
        import os

        # Set a dummy key for testing
        original = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        try:
            config = LLMConfig(provider="anthropic/claude-3-5-sonnet-20240620")
            assert config.provider == "anthropic/claude-3-5-sonnet-20240620"
        finally:
            if original:
                os.environ["ANTHROPIC_API_KEY"] = original
            else:
                os.environ.pop("ANTHROPIC_API_KEY", None)
