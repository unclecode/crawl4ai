"""Regression tests for ``split_and_parse_json_objects``.

The helper splits a JSON array string into individual object segments by
tracking brace depth. Brace characters that appear *inside* JSON string
values must not affect the depth count, otherwise objects get split at the
wrong position and fail to parse.
"""

from crawl4ai.utils import split_and_parse_json_objects


def test_plain_objects_parse():
    parsed, unparsed = split_and_parse_json_objects('[{"a": 1}, {"b": 2}]')
    assert parsed == [{"a": 1}, {"b": 2}]
    assert unparsed == []


def test_closing_brace_inside_string_value():
    # A lone "}" inside a string value must not terminate the object early.
    parsed, unparsed = split_and_parse_json_objects('[{"a": "x}y"}, {"b": 2}]')
    assert parsed == [{"a": "x}y"}, {"b": 2}]
    assert unparsed == []


def test_opening_brace_inside_string_value():
    parsed, unparsed = split_and_parse_json_objects('[{"a": "x{y"}, {"b": 2}]')
    assert parsed == [{"a": "x{y"}, {"b": 2}]
    assert unparsed == []


def test_escaped_quote_inside_string_value():
    # An escaped quote must not be treated as the end of the string, so the
    # "}" that follows still counts as being inside the string.
    parsed, unparsed = split_and_parse_json_objects('[{"a": "he said \\"}\\""}]')
    assert parsed == [{"a": 'he said "}"'}]
    assert unparsed == []


def test_balanced_braces_inside_string_still_work():
    parsed, unparsed = split_and_parse_json_objects('[{"text": "see {this}", "n": 1}]')
    assert parsed == [{"text": "see {this}", "n": 1}]
    assert unparsed == []
