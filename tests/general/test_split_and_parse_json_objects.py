"""Regression tests for split_and_parse_json_objects brace tracking."""

from crawl4ai.utils import split_and_parse_json_objects


def test_braces_inside_string_values_do_not_split_the_object():
    parsed, unparsed = split_and_parse_json_objects('[{"snippet": "if (x) { y() }"}, {"n": 2}]')
    assert parsed == [{"snippet": "if (x) { y() }"}, {"n": 2}]
    assert unparsed == []


def test_closing_brace_inside_a_string_keeps_the_rest_of_the_payload():
    # The scanner used to count the "}" inside the string value as the end of the
    # object: the first segment became invalid and the second object was dropped.
    parsed, unparsed = split_and_parse_json_objects('[{"a": "x}y"}, {"b": 2}]')
    assert parsed == [{"a": "x}y"}, {"b": 2}]
    assert unparsed == []


def test_escaped_quotes_do_not_end_the_string_early():
    parsed, unparsed = split_and_parse_json_objects('[{"q": "say \\"hi}\\" now"}, {"n": 1}]')
    assert parsed == [{"q": 'say "hi}" now'}, {"n": 1}]
    assert unparsed == []


def test_nested_objects_still_parse():
    parsed, unparsed = split_and_parse_json_objects('[{"nested": {"x": {"y": 1}}}, {"b": 2}]')
    assert parsed == [{"nested": {"x": {"y": 1}}}, {"b": 2}]
    assert unparsed == []


def test_plain_payload_is_unchanged():
    parsed, unparsed = split_and_parse_json_objects('[{"a": 1}, {"b": 2}]')
    assert parsed == [{"a": 1}, {"b": 2}]
    assert unparsed == []


def test_truncated_payload_keeps_the_complete_objects():
    parsed, unparsed = split_and_parse_json_objects('[{"a": 1}, {"broken": ]')
    assert parsed == [{"a": 1}]
    assert unparsed == []
