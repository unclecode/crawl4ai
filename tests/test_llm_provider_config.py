import os

import pytest

from crawl4ai.async_configs import LLMConfig


class TestAWSBedrockProviderConfig:
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

    def test_provider_config_basic(self):
        config = LLMConfig(
            provider="bedrock/anthropic.claude-v2", provider_config={"aws_region_name": "us-east-1"}
        )
        assert config.provider == "bedrock/anthropic.claude-v2"
        assert config.provider_config == {"aws_region_name": "us-east-1"}

    def test_provider_config_empty_default(self):
        config = LLMConfig(provider="bedrock/anthropic.claude-v2")
        assert config.provider_config == {}

    def test_provider_config_none_becomes_empty(self):
        config = LLMConfig(provider="bedrock/anthropic.claude-v2", provider_config=None)
        assert config.provider_config == {}

    def test_provider_config_aws_credentials(self):
        config = LLMConfig(
            provider="bedrock/anthropic.claude-v2",
            provider_config={
                "aws_region_name": "us-west-2",
                "aws_profile_name": "dev",
                "aws_access_key_id": "AKIA123",
                "aws_secret_access_key": "secret123",
                "aws_session_token": "token123",
            },
        )
        assert config.provider_config == {
            "aws_region_name": "us-west-2",
            "aws_profile_name": "dev",
            "aws_access_key_id": "AKIA123",
            "aws_secret_access_key": "secret123",
            "aws_session_token": "token123",
        }

    def test_to_dict_includes_provider_config(self):
        config = LLMConfig(
            provider="bedrock/anthropic.claude-v2", provider_config={"aws_region_name": "us-east-1"}
        )
        config_dict = config.to_dict()
        assert "provider_config" in config_dict
        assert config_dict["provider_config"] == {"aws_region_name": "us-east-1"}

    def test_from_kwargs_with_provider_config(self):
        kwargs = {
            "provider": "bedrock/anthropic.claude-v2",
            "provider_config": {"aws_region_name": "us-west-2"},
            "temperature": 0.7,
        }
        config = LLMConfig.from_kwargs(kwargs)
        assert config.provider_config == {"aws_region_name": "us-west-2"}
        assert config.temperature == 0.7

    def test_clone_with_provider_config(self):
        config1 = LLMConfig(
            provider="bedrock/anthropic.claude-v2", provider_config={"aws_region_name": "us-east-1"}
        )
        config2 = config1.clone(provider_config={"aws_region_name": "eu-west-1"})
        assert config2.provider_config == {"aws_region_name": "eu-west-1"}
        assert config1.provider_config == {"aws_region_name": "us-east-1"}

    def test_explicit_provider_config_priority(self):
        os.environ["AWS_REGION"] = "us-west-2"
        config = LLMConfig(
            provider="bedrock/anthropic.claude-v2", provider_config={"aws_region_name": "us-east-1"}
        )
        assert config.provider_config["aws_region_name"] == "us-east-1"

    def test_environment_variable_fallback(self):
        os.environ["AWS_REGION"] = "ap-southeast-1"
        os.environ["AWS_ACCESS_KEY_ID"] = "AKIA_FROM_ENV"
        config = LLMConfig(provider="bedrock/anthropic.claude-v2")
        assert config.provider_config == {}

    def test_mixed_explicit_and_env(self):
        os.environ["AWS_ACCESS_KEY_ID"] = "AKIA_FROM_ENV"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "SECRET_FROM_ENV"
        config = LLMConfig(
            provider="bedrock/anthropic.claude-v2", provider_config={"aws_region_name": "us-east-1"}
        )
        assert config.provider_config["aws_region_name"] == "us-east-1"

    def test_llm_extraction_strategy_receives_provider_config(self):
        from crawl4ai.extraction_strategy import LLMExtractionStrategy

        llm_config = LLMConfig(
            provider="bedrock/anthropic.claude-v2",
            provider_config={"aws_region_name": "us-east-1", "aws_access_key_id": "AKIA123"},
        )
        strategy = LLMExtractionStrategy(llm_config=llm_config, instruction="Extract content")
        assert strategy.llm_config.provider_config == {
            "aws_region_name": "us-east-1",
            "aws_access_key_id": "AKIA123",
        }

    def test_bedrock_provider_detected(self):
        providers = [
            "bedrock/anthropic.claude-v2",
            "bedrock/anthropic.claude-instant-v1",
            "bedrock/us.anthropic.claude-sonnet-4-6",
            "bedrock/amazon.titan-text-express-v1",
        ]
        for provider in providers:
            config = LLMConfig(provider=provider, provider_config={"aws_region_name": "us-east-1"})
            assert config.provider.startswith("bedrock/")
            assert config.provider_config["aws_region_name"] == "us-east-1"

    def test_empty_provider_config_values(self):
        config = LLMConfig(
            provider="bedrock/anthropic.claude-v2",
            provider_config={
                "aws_region_name": "",
                "aws_profile_name": None,
                "aws_access_key_id": "",
            },
        )
        assert "aws_region_name" in config.provider_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
