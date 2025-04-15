import pytest
from litellm.exceptions import RateLimitError

from crawl4ai.utils import perform_completion_with_backoff


def test_perform_completion_with_backoff_rate_limit():
    with pytest.raises(RateLimitError):
        perform_completion_with_backoff(
            provider="openai/gpt-4o",
            prompt_with_variables="Test prompt",
            api_token="test_token",
            extra_args={  # Force the rate limit error.
                "mock_response": RateLimitError(
                    message="Rate limit exceeded",
                    llm_provider="openai",
                    model="gpt-4o",
                ),
            },
        )
