"""Empty provider responses must not be exposed as successful extracted records."""

from unittest.mock import AsyncMock, Mock

import pytest
from litellm import ModelResponse

from crawl4ai import LLMConfig, LLMExtractionStrategy


def make_response(content, finish_reason="stop"):
    return ModelResponse(
        choices=[
            {
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }
        ],
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )


async def extract_response(monkeypatch, response, async_mode, json_mode):
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(provider="openai/test-model", api_token="test-only"),
        force_json_response=json_mode,
    )
    if async_mode:
        completion = AsyncMock(return_value=response)
        monkeypatch.setattr(
            "crawl4ai.utils.aperform_completion_with_backoff", completion
        )
        blocks = await strategy.aextract("https://example.com", 7, "page text")
        completion.assert_awaited_once()
    else:
        completion = Mock(return_value=response)
        monkeypatch.setattr(
            "crawl4ai.extraction_strategy.perform_completion_with_backoff", completion
        )
        blocks = strategy.extract("https://example.com", 7, "page text")
        completion.assert_called_once()
    return blocks, strategy


@pytest.mark.asyncio
@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("json_mode", [False, True], ids=["blocks", "json"])
@pytest.mark.parametrize("content", [None, "", " \n\t"])
@pytest.mark.parametrize("finish_reason", ["stop", "length", "content_filter"])
async def test_empty_response_is_an_error(
    monkeypatch, async_mode, json_mode, content, finish_reason
):
    blocks, strategy = await extract_response(
        monkeypatch, make_response(content, finish_reason), async_mode, json_mode
    )

    assert len(blocks) == 1
    assert blocks[0]["error"] is True
    assert blocks[0]["index"] == 7
    assert blocks[0]["tags"] == ["error"]
    assert finish_reason in blocks[0]["content"]
    # A failed extraction still consumes the usage reported by the provider.
    assert len(strategy.usages) == 1
    assert strategy.total_usage.prompt_tokens == 10
    assert strategy.total_usage.completion_tokens == 5
    assert strategy.total_usage.total_tokens == 15


@pytest.mark.asyncio
@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("json_mode", [False, True], ids=["blocks", "json"])
@pytest.mark.parametrize("empty_list", [False, True])
async def test_valid_response_keeps_success_semantics(
    monkeypatch, async_mode, json_mode, empty_list
):
    content = "[]" if empty_list else '[{"title": "A useful page"}]'
    if not json_mode:
        content = f"<blocks>{content}</blocks>"
    blocks, strategy = await extract_response(
        monkeypatch, make_response(content), async_mode, json_mode
    )

    assert blocks == (
        [] if empty_list else [{"title": "A useful page", "error": False}]
    )
    assert strategy.total_usage.total_tokens == 15
