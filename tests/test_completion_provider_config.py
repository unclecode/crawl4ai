import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from crawl4ai.utils import aperform_completion_with_backoff, perform_completion_with_backoff


@pytest.fixture
def mock_completion(monkeypatch):
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.usage.completion_tokens = 10
    mock_response.usage.prompt_tokens = 20
    mock_response.usage.total_tokens = 30
    mock_response.usage.completion_tokens_details = None
    mock_response.usage.prompt_tokens_details = None
    mock.return_value = mock_response
    monkeypatch.setattr("litellm.completion", mock)
    return mock


@pytest.fixture
def mock_acompletion(monkeypatch):
    mock = AsyncMock()
    mock_response = MagicMock()
    mock_response.usage.completion_tokens = 10
    mock_response.usage.prompt_tokens = 20
    mock_response.usage.total_tokens = 30
    mock_response.usage.completion_tokens_details = None
    mock_response.usage.prompt_tokens_details = None
    mock.return_value = mock_response
    monkeypatch.setattr("litellm.acompletion", mock)
    return mock


class TestPerformCompletionWithProviderConfig:
    def setup_method(self):
        env_vars = [
            "AWS_REGION",
            "AWS_DEFAULT_REGION",
            "AWS_PROFILE",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
        ]
        for var in env_vars:
            os.environ.pop(var, None)

    def test_bedrock_provider_config_passed_to_litellm(self, mock_completion):
        provider_config = {
            "aws_region_name": "us-west-2",
            "aws_profile_name": "dev",
            "aws_access_key_id": "AKIA123",
            "aws_secret_access_key": "secret123",
            "aws_session_token": "token123",
        }

        perform_completion_with_backoff(
            provider="bedrock/anthropic.claude-v2",
            prompt_with_variables="test prompt",
            api_token=None,
            provider_config=provider_config,
        )

        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs

        assert {k: v for k, v in call_kwargs.items() if k.startswith("aws_")} == {
            "aws_region_name": "us-west-2",
            "aws_profile_name": "dev",
            "aws_access_key_id": "AKIA123",
            "aws_secret_access_key": "secret123",
            "aws_session_token": "token123",
        }

    def test_bedrock_env_var_fallback(self, mock_completion):
        os.environ["AWS_REGION"] = "ap-southeast-1"
        os.environ["AWS_ACCESS_KEY_ID"] = "AKIA_ENV"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "SECRET_ENV"

        perform_completion_with_backoff(
            provider="bedrock/anthropic.claude-v2",
            prompt_with_variables="test prompt",
            api_token=None,
            provider_config=None,
        )

        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs

        assert {k: v for k, v in call_kwargs.items() if k.startswith("aws_")} == {
            "aws_region_name": "ap-southeast-1",
            "aws_access_key_id": "AKIA_ENV",
            "aws_secret_access_key": "SECRET_ENV",
        }

    def test_bedrock_explicit_overrides_env(self, mock_completion):
        os.environ["AWS_REGION"] = "us-east-1"
        os.environ["AWS_ACCESS_KEY_ID"] = "AKIA_ENV"

        provider_config = {"aws_region_name": "us-west-2", "aws_access_key_id": "AKIA_EXPLICIT"}

        perform_completion_with_backoff(
            provider="bedrock/anthropic.claude-v2",
            prompt_with_variables="test prompt",
            api_token=None,
            provider_config=provider_config,
        )

        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs

        assert {k: v for k, v in call_kwargs.items() if k.startswith("aws_")} == {
            "aws_region_name": "us-west-2",
            "aws_access_key_id": "AKIA_EXPLICIT",
        }

    def test_non_bedrock_provider_unaffected(self, mock_completion):
        provider_config = {"aws_region_name": "us-west-2", "aws_access_key_id": "AKIA123"}

        perform_completion_with_backoff(
            provider="openai/gpt-4",
            prompt_with_variables="test prompt",
            api_token="sk-test",
            provider_config=provider_config,
        )

        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs

        assert "aws_region_name" not in call_kwargs
        assert "aws_access_key_id" not in call_kwargs
        assert call_kwargs["api_key"] == "sk-test"


class TestAPerformCompletionWithProviderConfig:
    def setup_method(self):
        env_vars = [
            "AWS_REGION",
            "AWS_DEFAULT_REGION",
            "AWS_PROFILE",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
        ]
        for var in env_vars:
            os.environ.pop(var, None)

    @pytest.mark.asyncio
    async def test_async_bedrock_provider_config_passed(self, mock_acompletion):
        provider_config = {"aws_region_name": "us-west-2", "aws_access_key_id": "AKIA123"}

        await aperform_completion_with_backoff(
            provider="bedrock/anthropic.claude-v2",
            prompt_with_variables="test prompt",
            api_token=None,
            provider_config=provider_config,
        )

        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args.kwargs

        assert {k: v for k, v in call_kwargs.items() if k.startswith("aws_")} == {
            "aws_region_name": "us-west-2",
            "aws_access_key_id": "AKIA123",
        }

    @pytest.mark.asyncio
    async def test_async_bedrock_env_fallback(self, mock_acompletion):
        os.environ["AWS_REGION"] = "eu-west-1"
        os.environ["AWS_ACCESS_KEY_ID"] = "AKIA_ENV"

        await aperform_completion_with_backoff(
            provider="bedrock/anthropic.claude-v2",
            prompt_with_variables="test prompt",
            api_token=None,
            provider_config=None,
        )

        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args.kwargs

        assert {k: v for k, v in call_kwargs.items() if k.startswith("aws_")} == {
            "aws_region_name": "eu-west-1",
            "aws_access_key_id": "AKIA_ENV",
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
