"""The default LLM must still work after OpenAI shuts down gpt-4o (#2584).

gpt-6-luna, the new default, rejects any temperature but 1, so no default
temperature may be sent; a temperature the caller sets must still go through.
"""

import asyncio

import litellm
import pytest

from crawl4ai import LLMConfig
from crawl4ai.config import DEFAULT_PROVIDER
from crawl4ai.utils import aperform_completion_with_backoff, perform_completion_with_backoff


def test_default_provider_is_not_shut_down():
    assert "gpt-4o" not in DEFAULT_PROVIDER
    assert LLMConfig().provider == DEFAULT_PROVIDER


@pytest.fixture
def sent(monkeypatch):
    calls = []

    def completion(**kwargs):
        calls.append(kwargs)
        return "response"

    async def acompletion(**kwargs):
        return completion(**kwargs)

    monkeypatch.setattr(litellm, "completion", completion)
    monkeypatch.setattr(litellm, "acompletion", acompletion)
    return calls


def _call(is_async, extra_args=None):
    args = ("openai/gpt-6-luna", "prompt", "key")
    if is_async:
        return asyncio.run(aperform_completion_with_backoff(*args, extra_args=extra_args))
    return perform_completion_with_backoff(*args, extra_args=extra_args)


@pytest.mark.parametrize("is_async", [False, True])
def test_no_default_temperature_is_sent(sent, is_async):
    _call(is_async)
    assert "temperature" not in sent[0]


@pytest.mark.parametrize("is_async", [False, True])
def test_caller_temperature_is_sent(sent, is_async):
    _call(is_async, extra_args={"temperature": 0.2})
    assert sent[0]["temperature"] == 0.2
