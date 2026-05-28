"""Regression tests for https://github.com/unclecode/crawl4ai/issues/1962

mcp_bridge.py must not escape non-ASCII (CJK/emoji) content when serialising
tool results.  The default json.dumps() uses ensure_ascii=True which replaces
every non-ASCII codepoint with a \\uXXXX escape — a 2.5-3x token overhead
for CJK content.
"""

import json


def test_cjk_not_escaped_in_json_dumps():
    """json.dumps(..., ensure_ascii=False) must preserve CJK characters."""
    cjk_text = "跳转到内容"
    result = json.dumps({"markdown": cjk_text}, ensure_ascii=False)
    # With ensure_ascii=False the characters appear literally in the output.
    assert "跳转到内容" in result, (
        "CJK characters were escaped to \\uXXXX. "
        "Pass ensure_ascii=False to json.dumps() in mcp_bridge.py."
    )
    # Control: ensure_ascii=True (the old behaviour) would have escaped them.
    escaped_result = json.dumps({"markdown": cjk_text}, ensure_ascii=True)
    assert "\\u" in escaped_result, "This test depends on ensure_ascii=True escaping non-ASCII"


def test_mcp_bridge_serialize_uses_ensure_ascii_false():
    """The three json.dumps calls in mcp_bridge.py must all pass ensure_ascii=False."""
    import ast
    import pathlib

    bridge_path = pathlib.Path(__file__).parent.parent.parent / "deploy" / "docker" / "mcp_bridge.py"
    source = bridge_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Check if this is a json.dumps(...) call
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "dumps"):
            continue

        # Look for ensure_ascii keyword argument
        for kw in node.keywords:
            if kw.arg == "ensure_ascii":
                assert isinstance(kw.value, ast.Constant), "ensure_ascii should be a constant"
                assert kw.value.value is False, (
                    f"json.dumps at line {node.lineno} has ensure_ascii={kw.value.value!r}; "
                    "must be False to avoid escaping non-ASCII content."
                )
                break
        else:
            # No ensure_ascii keyword → defaults to True (the bug)
            raise AssertionError(
                f"json.dumps at line {node.lineno} in mcp_bridge.py is missing "
                "ensure_ascii=False, which causes CJK/emoji content to be escaped."
            )
