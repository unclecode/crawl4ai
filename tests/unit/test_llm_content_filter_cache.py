from types import SimpleNamespace

import pytest

from crawl4ai import LLMConfig
from crawl4ai import content_filter_strategy


@pytest.mark.parametrize(
    ("default_ignore_cache", "call_options", "expected_calls"),
    [
        (False, {"ignore_cache": True}, 2),
        (True, {"ignore_cache": False}, 1),
        (False, {}, 1),
        (True, {}, 2),
    ],
)
def test_filter_content_uses_the_per_call_cache_setting(
    monkeypatch, tmp_path, default_ignore_cache, call_options, expected_calls
):
    html = "<p>Documentation</p>"
    calls = []

    def complete(*args, **kwargs):
        calls.append(args)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=f"<content>Response {len(calls)}</content>"
                    )
                )
            ],
            usage=SimpleNamespace(
                completion_tokens=1,
                prompt_tokens=2,
                total_tokens=3,
                completion_tokens_details=None,
                prompt_tokens_details=None,
            ),
        )

    monkeypatch.setattr(content_filter_strategy, "get_home_folder", lambda: tmp_path)
    monkeypatch.setattr(
        content_filter_strategy, "perform_completion_with_backoff", complete
    )
    filter_ = content_filter_strategy.LLMContentFilter(
        llm_config=LLMConfig(provider="openai/test-model", api_token="unused-test-key"),
        ignore_cache=default_ignore_cache,
    )

    assert filter_.filter_content(html) == ["Response 1"]
    assert filter_.filter_content(html, **call_options) == [
        f"Response {expected_calls}"
    ]
    assert len(calls) == expected_calls
