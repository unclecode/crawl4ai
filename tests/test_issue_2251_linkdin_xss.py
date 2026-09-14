"""
Tests for issue #2251: DOM XSS via unescaped innerHTML interpolation in the
LinkedIn Data Discovery example app's graph view template (5 sinks).

docs/apps/linkdin/templates/graph_view_template.html interpolated
crawled/uploaded fields (company name, person name, profile URLs, AI chat
markdown, ...) directly into innerHTML without escaping. A crafted
company_graph.json, org_chart_*.json, or crawled page content could execute
arbitrary JavaScript in the app's origin.

Fix: escape every untrusted field with a new escapeHtml() helper before
interpolation, and sanitize the AI chat markdown output with DOMPurify.
href/src sinks (profile_url, avatar_url, id) additionally go through a
safeUrl() helper that only allows http(s) schemes through, since entity
escaping alone does not stop a `javascript:` URL reaching setAttribute.
"""

import re
import subprocess
from pathlib import Path

import pytest

TEMPLATE = (
    Path(__file__).parent.parent
    / "docs"
    / "apps"
    / "linkdin"
    / "templates"
    / "graph_view_template.html"
)


def _html() -> str:
    return TEMPLATE.read_text()


def _extract_main_script() -> str:
    scripts = re.findall(r"<script>(.*?)</script>", _html(), re.S)
    assert scripts, "no inline <script> block found in template"
    return scripts[-1]


def _extract_escape_html_fn() -> str:
    match = re.search(
        r"function escapeHtml\(value\) \{.*?\n        \}", _extract_main_script(), re.S
    )
    assert match, "escapeHtml() helper not found in template script"
    return match.group(0)


def _extract_safe_url_fn() -> str:
    match = re.search(
        r"function safeUrl\(value, fallback = '#'\) \{.*?\n        \}",
        _extract_main_script(),
        re.S,
    )
    assert match, "safeUrl() helper not found in template script"
    return match.group(0)


def _has_node() -> bool:
    try:
        return subprocess.run(["node", "--version"], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


@pytest.mark.skipif(not _has_node(), reason="node is required to execute the template's JS")
def test_escape_html_neutralizes_script_payloads():
    """escapeHtml() must exist and strip HTML/attribute-breakout metacharacters."""
    node_src = _extract_escape_html_fn() + (
        "\nconsole.log(escapeHtml(`<img src=x onerror=alert(1)>' \" &`));\n"
    )
    result = subprocess.run(
        ["node", "-e", node_src], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    escaped = result.stdout.strip()

    # No raw HTML metacharacters survive, so the payload can no longer open a
    # tag, an attribute, or break out of one when re-parsed as HTML.
    assert "<" not in escaped and ">" not in escaped
    assert '"' not in escaped and "'" not in escaped
    assert "&lt;img" in escaped and "&amp;" in escaped


@pytest.mark.skipif(not _has_node(), reason="node is required to execute the template's JS")
@pytest.mark.parametrize(
    "payload",
    [
        "javascript:alert(document.cookie)",
        "JaVaScRiPt:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
    ],
)
def test_safe_url_blocks_dangerous_schemes(payload):
    """safeUrl() must fall back instead of letting a non-http(s) scheme through.

    This is the gap the issue's collaborator explicitly flagged: entity
    escaping alone does not stop a `javascript:` URL from reaching
    setAttribute for an href/src sink.
    """
    node_src = (
        _extract_escape_html_fn()
        + "\n"
        + _extract_safe_url_fn()
        + f"\nconsole.log(JSON.stringify(safeUrl({payload!r})));\n"
    )
    result = subprocess.run(
        ["node", "-e", node_src], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    returned = result.stdout.strip()
    assert payload not in returned
    assert returned == '"#"'


@pytest.mark.skipif(not _has_node(), reason="node is required to execute the template's JS")
@pytest.mark.parametrize(
    "payload",
    [
        "https://www.linkedin.com/in/example",
        "http://www.linkedin.com/in/example",
    ],
)
def test_safe_url_allows_http_and_https(payload):
    node_src = (
        _extract_escape_html_fn()
        + "\n"
        + _extract_safe_url_fn()
        + f"\nconsole.log(JSON.stringify(safeUrl({payload!r})));\n"
    )
    result = subprocess.run(
        ["node", "-e", node_src], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f'"{payload}"'


# Each entry is a snippet that must be present in the fixed template, taken
# from one of the five sinks the issue reported. Checking out the pre-fix
# source (HEAD~1) for this file makes every one of these assertions fail,
# since escapeHtml() did not exist and these fields were interpolated raw.
EXPECTED_ESCAPED_SNIPPETS = [
    # 1. Company list (was: ${n.name}, ${n.industry ...}, ${n.about ...}, ${n.handle})
    '<h3 class="font-semibold text-blue-400 cursor-pointer">${escapeHtml(n.name)}</h3>',
    "${escapeHtml(n.industry || 'N/A')}",
    "${escapeHtml(n.about || 'No description available')}",
    "https://www.linkedin.com${escapeHtml(n.handle || '')}",
    # 2. renderOrg (was: ${companyName}, ${n.name}, ${n.title}, ${n.profile_url})
    '<h2 class="font-semibold text-lg text-blue-400">${escapeHtml(companyName)}</h2>',
    '<div class="font-medium">${escapeHtml(n.name)}</div>',
    '<div class="text-xs text-neutral-300">${escapeHtml(n.title)}</div>',
    '<a href="${safeUrl(n.profile_url)}"',
    # 3. showPersonDetails (was: ${p.avatar_url}, ${p.name}, ${p.title}, ${p.dept}, ${p.title_level}, ${p.id})
    "${safeUrl(p.avatar_url, 'https://ui-avatars.com/api/?name=' + encodeURIComponent(p.name))}",
    '<div class="font-semibold text-lg">${escapeHtml(p.name)}</div>',
    "${escapeHtml(p.title || 'Employee')}",
    "${escapeHtml(p.dept || 'Department not specified')}",
    "${escapeHtml(p.title_level || 'Level not specified')}",
    '<a href="${safeUrl(p.id)}"',
    # 4. AI chat drawer (was: raw text += ..., marked.parse(text) unsanitized)
    'el.lastChild.innerHTML += escapeHtml(text).replace(/\\n/g, "<br>")',
    "contentEl.innerHTML = DOMPurify.sanitize(marked.parse(text))",
    # 5. Graph hover tooltip (was: ${node.name}, ${node.industry ...}, ${node.about ...})
    '<div class="font-semibold text-neutral-200">${escapeHtml(node.name)}</div>',
    "${escapeHtml(node.industry || 'Industry: N/A')}",
    '<div class="mt-1">${escapeHtml(node.about || \'\')}</div>',
]


@pytest.mark.parametrize("snippet", EXPECTED_ESCAPED_SNIPPETS)
def test_sink_interpolates_through_escape_html(snippet):
    html = _html()
    assert snippet in html, f"expected escaped interpolation not found: {snippet!r}"


def test_dompurify_is_loaded():
    assert re.search(r'<script src="[^"]*dompurify[^"]*"', _html(), re.I), (
        "DOMPurify must be loaded to sanitize AI-generated markdown before "
        "it is assigned to innerHTML"
    )


UNESCAPED_VULNERABLE_PATTERNS = [
    '>${n.name}</h3>',
    '>${companyName}</h2>',
    '<div class="font-semibold text-lg">${p.name}</div>',
    '>${node.name}</div>',
    'el.lastChild.innerHTML += text.replace(/\\n/g, "<br>")',
    "contentEl.innerHTML = marked.parse(text)",
    # Entity-only escaping on an href/src sink does not block a `javascript:`
    # scheme; these three sinks must go through safeUrl(), not escapeHtml().
    "<a href=\"${escapeHtml(n.profile_url || '')}\"",
    "<a href=\"${escapeHtml(p.id || '')}\"",
    "${p.avatar_url ? escapeHtml(p.avatar_url) : ",
]


@pytest.mark.parametrize("pattern", UNESCAPED_VULNERABLE_PATTERNS)
def test_original_unescaped_pattern_is_gone(pattern):
    assert pattern not in _html(), f"unescaped XSS sink still present: {pattern!r}"
