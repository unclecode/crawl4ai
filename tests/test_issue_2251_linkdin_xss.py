"""Regression tests for the LinkedIn Data Discovery DOM XSS fixes (#2251)."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


TEMPLATE = (
    Path(__file__).parents[1]
    / "docs"
    / "apps"
    / "linkdin"
    / "templates"
    / "graph_view_template.html"
)
SOURCE = TEMPLATE.read_text(encoding="utf-8")


def section(start: str, end: str) -> str:
    return SOURCE.split(start, 1)[1].split(end, 1)[0]


def run_node(script: str):
    if not shutil.which("node"):
        pytest.skip("Node.js is required for JavaScript helper tests")
    result = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("data.nodes.forEach(n => {", "// Add search functionality"),
        ("function renderOrg(chart, pane) {", "function colorForScore"),
        ("function showPersonDetails(p) {", "// ───── Chat drawer logic"),
        ("network.on('hoverNode'", "network.on('blurNode'"),
    ],
)
def test_untrusted_data_sinks_use_dom_apis(start, end):
    rendered_section = section(start, end)

    assert ".innerHTML" not in rendered_section
    assert "makeElement(" in rendered_section


def test_markdown_is_sanitized_and_streams_are_appended_as_text():
    chat = section(
        "function appendMsg(sender, text, streaming = false) {", "// Settings modal"
    )

    assert "DOMPurify.sanitize(marked.parse(text))" in chat
    assert "appendTextWithBreaks(el.lastChild, text)" in chat
    assert "innerHTML +=" not in chat
    assert "dompurify@3.4.15/dist/purify.min.js" in SOURCE


def test_url_fields_are_validated_before_dom_assignment():
    assert "safeHttpUrl(person.profile_url)" in SOURCE
    assert "safeHttpUrl(p.avatar_url, avatarFallback)" in SOURCE
    assert "safeHttpUrl(p.id)" in SOURCE

    vulnerable_assignments = (
        'href="${n.profile_url}"',
        'src="${p.avatar_url',
        'href="${p.id}"',
    )
    assert all(pattern not in SOURCE for pattern in vulnerable_assignments)


def test_safe_http_url_rejects_executable_schemes():
    helper = section(
        "function safeHttpUrl(value, fallback = null) {",
        "function appendTextWithBreaks",
    )
    helper = "function safeHttpUrl(value, fallback = null) {" + helper
    payloads = [
        "https://example.com/profile",
        "http://example.com/profile",
        "/relative-profile",
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
        "http://[",
        None,
        "",
    ]
    result = run_node(
        "global.window = { location: { href: 'https://demo.example/app/' } };\n"
        + helper
        + f"\nconsole.log(JSON.stringify({json.dumps(payloads)}.map(value => safeHttpUrl(value, null))));"
    )

    assert result[:3] == [
        "https://example.com/profile",
        "http://example.com/profile",
        "https://demo.example/relative-profile",
    ]
    assert result[3:] == [None, None, None, None, None, None]


def test_make_element_treats_payload_as_text():
    helper = section(
        "function makeElement(tag, className = '', text = null) {",
        "function safeHttpUrl",
    )
    helper = "function makeElement(tag, className = '', text = null) {" + helper
    payload = '<img src=x onerror="globalThis.pwned=true">'
    result = run_node(
        "global.document = { createElement: tag => ({ tag, className: '', textContent: '' }) };\n"
        + helper
        + f"\nconsole.log(JSON.stringify(makeElement('div', 'value', {json.dumps(payload)})));"
    )

    assert result["textContent"] == payload
    assert result["className"] == "value"


def test_streaming_payload_creates_only_text_and_break_nodes():
    match = re.search(
        r"function appendTextWithBreaks\(element, text\) \{.*?\n            \}",
        SOURCE,
        re.DOTALL,
    )
    assert match
    result = run_node(
        "global.document = {"
        "createElement: tag => ({ tag }),"
        "createTextNode: text => ({ text })"
        "};"
        + match.group(0)
        + "\nconst target = { children: [], appendChild(node) { this.children.push(node); } };"
        + "\nappendTextWithBreaks(target, '<img src=x onerror=alert(1)>\\nnext');"
        + "\nconsole.log(JSON.stringify(target.children));"
    )

    assert result == [
        {"text": "<img src=x onerror=alert(1)>"},
        {"tag": "br"},
        {"text": "next"},
    ]
