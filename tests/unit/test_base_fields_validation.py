"""Schema validation must account for fields extracted from the base element."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from crawl4ai.extraction_strategy import (
    JsonCssExtractionStrategy,
    JsonElementExtractionStrategy,
    JsonXPathExtractionStrategy,
)

HTML = '<a class="blog-post-card" href="/post"><h2>Post title</h2></a>'


@pytest.fixture(params=["CSS", "XPATH"])
def schema_type(request):
    return request.param


@pytest.fixture(params=[False, True], ids=["base-only", "base-and-child"])
def with_child(request):
    return request.param


def make_schema(schema_type, with_child):
    return {
        "name": "Blog posts",
        "baseSelector": "//a" if schema_type == "XPATH" else "a",
        "baseFields": [{"name": "post_url", "type": "attribute", "attribute": "href"}],
        "fields": (
            [
                {
                    "name": "title",
                    "selector": ".//h2" if schema_type == "XPATH" else "h2",
                    "type": "text",
                }
            ]
            if with_child
            else []
        ),
    }


def expected_names(with_child):
    return ["post_url", "title"] if with_child else ["post_url"]


@pytest.mark.parametrize("strict", [False, True], ids=["fuzzy", "strict"])
def test_populated_base_fields_are_in_validation(schema_type, with_child, strict):
    schema = make_schema(schema_type, with_child)
    strategy_class = (
        JsonXPathExtractionStrategy
        if schema_type == "XPATH"
        else JsonCssExtractionStrategy
    )
    expected_item = {"post_url": "/post"}
    if with_child:
        expected_item["title"] = "Post title"
    assert strategy_class(schema).extract("", HTML) == [expected_item]

    result = JsonElementExtractionStrategy._validate_schema(
        schema,
        HTML,
        schema_type,
        expected_fields=expected_names(with_child) if strict else None,
    )

    assert result["success"] is True
    assert result["total_fields"] == len(expected_item)
    assert result["populated_fields"] == len(expected_item)
    assert result["field_coverage"] == 1.0
    assert result["issues"] == []
    assert [field["name"] for field in result["field_details"]] == list(expected_item)
    assert all(field["populated_count"] == 1 for field in result["field_details"])


@pytest.mark.parametrize("strict", [False, True], ids=["fuzzy", "strict"])
@pytest.mark.parametrize("href", ["", ' href=""'], ids=["missing", "empty"])
def test_unpopulated_base_fields_stay_unpopulated(
    schema_type, with_child, strict, href
):
    schema = make_schema(schema_type, with_child)
    html = f"<a{href}><h2>Post title</h2></a>"
    result = JsonElementExtractionStrategy._validate_schema(
        schema,
        html,
        schema_type,
        expected_fields=expected_names(with_child) if strict else None,
    )

    assert result["success"] is (with_child and not strict)
    assert result["total_fields"] == len(expected_names(with_child))
    assert result["populated_fields"] == int(with_child)
    assert (
        next(field for field in result["field_details"] if field["name"] == "post_url")[
            "populated_count"
        ]
        == 0
    )
    assert not any("missing from schema" in issue for issue in result["issues"])


def test_truly_missing_expected_field_is_rejected(schema_type):
    result = JsonElementExtractionStrategy._validate_schema(
        make_schema(schema_type, True),
        HTML,
        schema_type,
        expected_fields=["post_url", "title", "author"],
    )

    assert result["success"] is False
    assert "Expected fields missing from schema: author" in result["issues"]


def test_child_only_schema_validation_is_unchanged(schema_type):
    schema = make_schema(schema_type, True)
    del schema["baseFields"]
    result = JsonElementExtractionStrategy._validate_schema(
        schema, HTML, schema_type, expected_fields=["title"]
    )

    assert result["success"] is True
    assert result["total_fields"] == result["populated_fields"] == 1
    assert result["issues"] == []


@pytest.mark.parametrize("strict", [False, True], ids=["fuzzy", "strict"])
@pytest.mark.parametrize(
    ("child_html", "expected_value"),
    [("<h2>Child value</h2>", "Child value"), ("", "/post"), ("<h2></h2>", "")],
    ids=[
        "child-overrides-base",
        "missing-child-retains-base",
        "empty-child-overrides-base",
    ],
)
def test_same_named_base_and_child_fields_count_final_output_once(
    schema_type, strict, child_html, expected_value
):
    """Existing extraction precedence determines one final value per field name."""
    schema = make_schema(schema_type, True)
    schema["fields"][0]["name"] = "post_url"
    html = f'<a href="/post">{child_html}</a>'
    strategy_class = (
        JsonXPathExtractionStrategy
        if schema_type == "XPATH"
        else JsonCssExtractionStrategy
    )
    assert strategy_class(schema).extract("", html) == [{"post_url": expected_value}]

    result = JsonElementExtractionStrategy._validate_schema(
        schema,
        html,
        schema_type,
        expected_fields=["post_url"] if strict else None,
    )

    assert result["success"] is bool(expected_value)
    assert result["total_fields"] == 1
    assert result["populated_fields"] == int(bool(expected_value))
    assert len(result["field_details"]) == 1
    assert result["field_details"][0]["populated_count"] == int(bool(expected_value))
    assert result["field_details"][0]["sample_value"] == (expected_value or None)


def test_generate_schema_does_not_refine_a_valid_base_field_schema(
    monkeypatch, schema_type, with_child
):
    """Exercise the public lifecycle with only the remote completion replaced."""
    schema = make_schema(schema_type, with_child)
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(schema)))]
    )
    completion = AsyncMock(return_value=response)
    monkeypatch.setattr("crawl4ai.utils.aperform_completion_with_backoff", completion)
    config = SimpleNamespace(
        provider="test/model", api_token="test-token", base_url=None
    )

    result = JsonCssExtractionStrategy.generate_schema(
        html=HTML,
        schema_type=schema_type,
        target_json_example=json.dumps(
            {name: "expected" for name in expected_names(with_child)}
        ),
        llm_config=config,
        validate=True,
        max_refinements=2,
    )

    assert result == schema
    assert completion.await_count == 1
