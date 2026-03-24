"""Tests for TokenUsage accumulation in generate_schema / agenerate_schema.

Covers:
- Backward compatibility (usage=None, the default)
- Single-shot schema generation accumulates usage
- Validation retry loop accumulates across all LLM calls
- _infer_target_json accumulates its own LLM call
- Sync wrapper forwards usage correctly
- JSON parse failure retry also accumulates usage
- usage object receives correct cumulative totals
"""

import asyncio
import json
import pytest
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch, MagicMock

from crawl4ai.extraction_strategy import JsonElementExtractionStrategy, JsonCssExtractionStrategy
from crawl4ai.models import TokenUsage

# The functions are imported lazily inside method bodies via `from .utils import ...`
# so we must patch at the source module.
PATCH_TARGET = "crawl4ai.utils.aperform_completion_with_backoff"


# ---------------------------------------------------------------------------
# Helpers: fake LLM response builder
# ---------------------------------------------------------------------------

def _make_llm_response(content: str, prompt_tokens: int = 100, completion_tokens: int = 50):
    """Build a fake litellm-style response with .usage and .choices."""
    return SimpleNamespace(
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            completion_tokens_details=None,
            prompt_tokens_details=None,
        ),
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ],
    )


# A valid CSS schema that will pass validation against SAMPLE_HTML
VALID_SCHEMA = {
    "name": "products",
    "baseSelector": ".product",
    "fields": [
        {"name": "title", "selector": ".title", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
    ],
}

SAMPLE_HTML = """
<div class="products">
    <div class="product">
        <span class="title">Widget</span>
        <span class="price">$10</span>
    </div>
    <div class="product">
        <span class="title">Gadget</span>
        <span class="price">$20</span>
    </div>
</div>
"""

# A schema with a bad baseSelector — will fail validation and trigger retry
BAD_SCHEMA = {
    "name": "products",
    "baseSelector": ".nonexistent-selector",
    "fields": [
        {"name": "title", "selector": ".title", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
    ],
}

# Fake LLMConfig
@dataclass
class FakeLLMConfig:
    provider: str = "fake/model"
    api_token: str = "fake-token"
    base_url: str = None
    backoff_base_delay: float = 0
    backoff_max_attempts: int = 1
    backoff_exponential_factor: int = 2


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerateSchemaUsage:
    """Test suite for usage tracking in generate_schema / agenerate_schema."""

    @pytest.mark.asyncio
    async def test_backward_compat_usage_none(self):
        """When usage is not passed (default None), everything works as before."""
        mock_response = _make_llm_response(json.dumps(VALID_SCHEMA))

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=False,
            )

        assert isinstance(result, dict)
        assert result["name"] == "products"

    @pytest.mark.asyncio
    async def test_single_shot_no_validate(self):
        """Single LLM call with validate=False populates usage correctly."""
        usage = TokenUsage()
        mock_response = _make_llm_response(
            json.dumps(VALID_SCHEMA), prompt_tokens=200, completion_tokens=80
        )

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=False,
                usage=usage,
            )

        assert result["name"] == "products"
        assert usage.prompt_tokens == 200
        assert usage.completion_tokens == 80
        assert usage.total_tokens == 280

    @pytest.mark.asyncio
    async def test_validation_success_first_try(self):
        """With validate=True and schema passes validation on first try, usage reflects 1 call."""
        usage = TokenUsage()
        mock_response = _make_llm_response(
            json.dumps(VALID_SCHEMA), prompt_tokens=300, completion_tokens=120
        )

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=True,
                max_refinements=3,
                usage=usage,
                # Provide target_json_example to skip _infer_target_json
                target_json_example='{"title": "x", "price": "y"}',
            )

        assert result["name"] == "products"
        # Only 1 LLM call since validation passed
        assert usage.prompt_tokens == 300
        assert usage.completion_tokens == 120
        assert usage.total_tokens == 420

    @pytest.mark.asyncio
    async def test_validation_retries_accumulate_usage(self):
        """When validation fails, retry calls accumulate into the same usage object."""
        usage = TokenUsage()

        # First call returns bad schema (fails validation), second returns good schema
        responses = [
            _make_llm_response(json.dumps(BAD_SCHEMA), prompt_tokens=300, completion_tokens=100),
            _make_llm_response(json.dumps(VALID_SCHEMA), prompt_tokens=350, completion_tokens=120),
        ]
        call_count = 0

        async def mock_completion(*args, **kwargs):
            nonlocal call_count
            idx = min(call_count, len(responses) - 1)
            call_count += 1
            return responses[idx]

        with patch(
            PATCH_TARGET,
            side_effect=mock_completion,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=True,
                max_refinements=3,
                usage=usage,
                target_json_example='{"title": "x", "price": "y"}',
            )

        assert result["name"] == "products"
        # Two LLM calls: 300+350=650 prompt, 100+120=220 completion
        assert usage.prompt_tokens == 650
        assert usage.completion_tokens == 220
        assert usage.total_tokens == 870

    @pytest.mark.asyncio
    async def test_infer_target_json_accumulates_usage(self):
        """When validate=True and no target_json_example, _infer_target_json makes an extra LLM call."""
        usage = TokenUsage()

        infer_response = _make_llm_response(
            '{"title": "Widget", "price": "$10"}',
            prompt_tokens=50,
            completion_tokens=30,
        )
        schema_response = _make_llm_response(
            json.dumps(VALID_SCHEMA),
            prompt_tokens=300,
            completion_tokens=120,
        )

        call_count = 0

        async def mock_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # First call is _infer_target_json, second is schema generation
            if call_count == 1:
                return infer_response
            return schema_response

        with patch(
            PATCH_TARGET,
            side_effect=mock_completion,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                query="extract product title and price",
                llm_config=FakeLLMConfig(),
                validate=True,
                max_refinements=3,
                usage=usage,
                # No target_json_example — triggers _infer_target_json
            )

        assert result["name"] == "products"
        # _infer_target_json: 50+30 = 80
        # schema generation: 300+120 = 420
        # Total: 350 prompt, 150 completion, 500 total
        assert usage.prompt_tokens == 350
        assert usage.completion_tokens == 150
        assert usage.total_tokens == 500

    @pytest.mark.asyncio
    async def test_infer_plus_retries_accumulate(self):
        """Full pipeline: infer + bad schema + good schema = 3 calls accumulated."""
        usage = TokenUsage()

        infer_resp = _make_llm_response(
            '{"title": "x", "price": "y"}',
            prompt_tokens=50, completion_tokens=20,
        )
        bad_resp = _make_llm_response(
            json.dumps(BAD_SCHEMA),
            prompt_tokens=300, completion_tokens=100,
        )
        good_resp = _make_llm_response(
            json.dumps(VALID_SCHEMA),
            prompt_tokens=400, completion_tokens=150,
        )

        call_count = 0

        async def mock_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return infer_resp
            elif call_count == 2:
                return bad_resp
            else:
                return good_resp

        with patch(
            PATCH_TARGET,
            side_effect=mock_completion,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                query="extract products",
                llm_config=FakeLLMConfig(),
                validate=True,
                max_refinements=3,
                usage=usage,
            )

        # 3 calls total
        assert call_count == 3
        assert usage.prompt_tokens == 750    # 50 + 300 + 400
        assert usage.completion_tokens == 270  # 20 + 100 + 150
        assert usage.total_tokens == 1020    # 70 + 400 + 550

    @pytest.mark.asyncio
    async def test_json_parse_failure_retry_accumulates(self):
        """When LLM returns invalid JSON, the retry also accumulates usage."""
        usage = TokenUsage()

        # First response is not valid JSON, second is valid
        bad_json_resp = _make_llm_response(
            "this is not json {{{",
            prompt_tokens=200, completion_tokens=60,
        )
        good_resp = _make_llm_response(
            json.dumps(VALID_SCHEMA),
            prompt_tokens=250, completion_tokens=80,
        )

        call_count = 0

        async def mock_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return bad_json_resp
            return good_resp

        with patch(
            PATCH_TARGET,
            side_effect=mock_completion,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=True,
                max_refinements=3,
                usage=usage,
                target_json_example='{"title": "x", "price": "y"}',
            )

        assert result["name"] == "products"
        # Both calls tracked: even the one that returned bad JSON
        assert usage.prompt_tokens == 450   # 200 + 250
        assert usage.completion_tokens == 140  # 60 + 80
        assert usage.total_tokens == 590

    @pytest.mark.asyncio
    async def test_usage_none_does_not_crash(self):
        """Explicitly passing usage=None should not raise any errors."""
        mock_response = _make_llm_response(json.dumps(VALID_SCHEMA))

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=False,
                usage=None,
            )

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_preexisting_usage_values_are_added_to(self):
        """If usage already has values, new tokens are ADDED, not replaced."""
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)

        mock_response = _make_llm_response(
            json.dumps(VALID_SCHEMA), prompt_tokens=200, completion_tokens=80
        )

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=False,
                usage=usage,
            )

        assert usage.prompt_tokens == 1200    # 1000 + 200
        assert usage.completion_tokens == 580  # 500 + 80
        assert usage.total_tokens == 1780     # 1500 + 280

    def test_sync_wrapper_passes_usage(self):
        """The sync generate_schema forwards usage to agenerate_schema."""
        usage = TokenUsage()
        mock_response = _make_llm_response(
            json.dumps(VALID_SCHEMA), prompt_tokens=200, completion_tokens=80
        )

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = JsonElementExtractionStrategy.generate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=False,
                usage=usage,
            )

        assert result["name"] == "products"
        assert usage.prompt_tokens == 200
        assert usage.completion_tokens == 80
        assert usage.total_tokens == 280

    def test_sync_wrapper_usage_none_backward_compat(self):
        """Sync wrapper with no usage arg (default) still works."""
        mock_response = _make_llm_response(json.dumps(VALID_SCHEMA))

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = JsonElementExtractionStrategy.generate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=False,
            )

        assert isinstance(result, dict)
        assert result["name"] == "products"

    @pytest.mark.asyncio
    async def test_max_refinements_zero_single_call(self):
        """max_refinements=0 with validate=True means exactly 1 attempt, 1 usage entry."""
        usage = TokenUsage()
        mock_response = _make_llm_response(
            json.dumps(BAD_SCHEMA), prompt_tokens=300, completion_tokens=100
        )

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=True,
                max_refinements=0,
                usage=usage,
                target_json_example='{"title": "x", "price": "y"}',
            )

        # Even though validation fails, only 1 attempt (0 refinements)
        assert usage.prompt_tokens == 300
        assert usage.completion_tokens == 100
        assert usage.total_tokens == 400

    @pytest.mark.asyncio
    async def test_css_subclass_inherits_usage(self):
        """JsonCssExtractionStrategy.agenerate_schema also supports usage."""
        usage = TokenUsage()
        mock_response = _make_llm_response(
            json.dumps(VALID_SCHEMA), prompt_tokens=150, completion_tokens=60
        )

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonCssExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=False,
                usage=usage,
            )

        assert result["name"] == "products"
        assert usage.total_tokens == 210

    @pytest.mark.asyncio
    async def test_infer_target_json_failure_still_tracks_nothing(self):
        """If _infer_target_json raises (and catches), usage should not break.

        When the inference LLM call itself throws an exception before we get
        response.usage, no tokens should be added (graceful degradation).
        """
        usage = TokenUsage()

        call_count = 0

        async def mock_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # _infer_target_json call — simulate exception
                raise ConnectionError("LLM is down")
            # Schema generation call
            return _make_llm_response(
                json.dumps(VALID_SCHEMA),
                prompt_tokens=300,
                completion_tokens=100,
            )

        with patch(
            PATCH_TARGET,
            side_effect=mock_completion,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                query="extract products",
                llm_config=FakeLLMConfig(),
                validate=True,
                max_refinements=0,
                usage=usage,
            )

        # Only the schema call counted; infer call failed before tracking
        assert usage.prompt_tokens == 300
        assert usage.completion_tokens == 100
        assert usage.total_tokens == 400

    @pytest.mark.asyncio
    async def test_multiple_bad_retries_then_best_effort(self):
        """All retries fail validation, usage still accumulates for every attempt."""
        usage = TokenUsage()

        # Every call returns bad schema — validation will always fail
        mock_response = _make_llm_response(
            json.dumps(BAD_SCHEMA), prompt_tokens=200, completion_tokens=80
        )

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonElementExtractionStrategy.agenerate_schema(
                html=SAMPLE_HTML,
                llm_config=FakeLLMConfig(),
                validate=True,
                max_refinements=2,  # 1 initial + 2 retries = 3 calls
                usage=usage,
                target_json_example='{"title": "x", "price": "y"}',
            )

        # Returns best-effort (last schema), but all 3 calls tracked
        assert usage.prompt_tokens == 600    # 200 * 3
        assert usage.completion_tokens == 240  # 80 * 3
        assert usage.total_tokens == 840     # 280 * 3


class TestInferTargetJsonUsage:
    """Isolated tests for _infer_target_json usage tracking."""

    @pytest.mark.asyncio
    async def test_infer_tracks_usage(self):
        """Direct call to _infer_target_json with usage accumulator."""
        usage = TokenUsage()
        mock_response = _make_llm_response(
            '{"name": "test", "value": "123"}',
            prompt_tokens=80,
            completion_tokens=25,
        )

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonElementExtractionStrategy._infer_target_json(
                query="extract names and values",
                html_snippet="<div>test</div>",
                llm_config=FakeLLMConfig(),
                usage=usage,
            )

        assert result == {"name": "test", "value": "123"}
        assert usage.prompt_tokens == 80
        assert usage.completion_tokens == 25
        assert usage.total_tokens == 105

    @pytest.mark.asyncio
    async def test_infer_usage_none_backward_compat(self):
        """_infer_target_json with usage=None (default) still works."""
        mock_response = _make_llm_response('{"name": "test"}')

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonElementExtractionStrategy._infer_target_json(
                query="extract names",
                html_snippet="<div>test</div>",
                llm_config=FakeLLMConfig(),
            )

        assert result == {"name": "test"}

    @pytest.mark.asyncio
    async def test_infer_exception_no_usage_side_effect(self):
        """When _infer_target_json fails, usage is untouched (exception before tracking)."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            side_effect=RuntimeError("API down"),
        ):
            result = await JsonElementExtractionStrategy._infer_target_json(
                query="extract names",
                html_snippet="<div>test</div>",
                llm_config=FakeLLMConfig(),
                usage=usage,
            )

        # Returns None on failure
        assert result is None
        # Usage unchanged — exception happened before tracking
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    @pytest.mark.asyncio
    async def test_infer_empty_response_still_tracks(self):
        """When LLM returns empty content, usage is still tracked (response was received)."""
        usage = TokenUsage()
        mock_response = _make_llm_response("", prompt_tokens=80, completion_tokens=5)

        with patch(
            PATCH_TARGET,
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await JsonElementExtractionStrategy._infer_target_json(
                query="extract names",
                html_snippet="<div>test</div>",
                llm_config=FakeLLMConfig(),
                usage=usage,
            )

        # Returns None because content is empty
        assert result is None
        # But usage was tracked because we got a response
        assert usage.prompt_tokens == 80
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 85
