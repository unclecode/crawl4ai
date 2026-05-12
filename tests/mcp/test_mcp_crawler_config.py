"""
Tests that each MCP tool correctly accepts and honours crawler_config.

Common crawler_config used in every test:
  wait_until               = "domcontentloaded"
  delay_before_return_html = 0.5
  cache_mode               = "bypass"

Run:
    source .venv/bin/activate
    python tests/mcp/test_mcp_crawler_config.py
"""

import anyio, json, time
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

SSE_URL = "http://localhost:11235/mcp/sse"
TARGET_URL = "https://example.com"

# Delay we assert is actually observed in every timed test.
# Kept at 2 s so it's large enough to be unambiguous even with network variance.
DELAY = 2.0

COMMON_CRAWLER_CONFIG = {
    "wait_until": "domcontentloaded",
    "delay_before_return_html": DELAY,
    "cache_mode": "bypass",
}

# ── helpers ───────────────────────────────────────────────────────────────────

def _ok(name: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"  ✓  {name}{suffix}")

def _fail(name: str, reason: str) -> None:
    print(f"  ✗  {name} FAILED: {reason}")

def _parse(res) -> dict | list:
    return json.loads(res.content[0].text)

def _assert_delay(elapsed: float, name: str) -> None:
    """Assert that elapsed time is at least DELAY, proving the server waited."""
    if elapsed < DELAY:
        raise AssertionError(
            f"delay_before_return_html={DELAY}s was NOT honoured: "
            f"response returned in {elapsed:.2f}s (expected >= {DELAY}s)"
        )

# ── individual tests ──────────────────────────────────────────────────────────

async def test_schema_exposes_crawler_config(s: ClientSession) -> bool:
    """All MCP tools we changed must advertise crawler_config in their inputSchema."""
    name = "schema check"
    expected = {"md", "html", "screenshot", "pdf", "execute_js", "crawl"}
    missing = []
    try:
        tools = (await s.list_tools()).tools
        tool_map = {t.name: t for t in tools}
        for tool_name in expected:
            tool = tool_map.get(tool_name)
            if tool is None:
                missing.append(f"{tool_name}(not found)")
                continue
            props = (tool.inputSchema or {}).get("properties", {})
            if "crawler_config" not in props:
                missing.append(f"{tool_name}(no crawler_config in schema)")
        if missing:
            _fail(name, ", ".join(missing))
            return False
        _ok(name, f"all {len(expected)} tools expose crawler_config")
        return True
    except Exception as e:
        _fail(name, str(e))
        return False


async def test_md(s: ClientSession) -> bool:
    name = "md"
    try:
        t0 = time.monotonic()
        res = _parse(await s.call_tool(name, {
            "url": TARGET_URL,
            "f": "fit",
            "crawler_config": COMMON_CRAWLER_CONFIG,
        }))
        elapsed = time.monotonic() - t0
        assert res.get("success"), f"success=False: {res}"

        md = res.get("markdown", "")
        assert md, "markdown field is empty"
        # Must look like markdown — at minimum contain a heading or a link
        assert any(tok in md for tok in ("#", "[", "*", "---")), \
            f"content does not look like markdown: {md[:200]!r}"

        _assert_delay(elapsed, name)
        _ok(name, f"len={len(md)}, elapsed={elapsed:.2f}s, preview={md[:60]!r}")
        return True
    except Exception as e:
        _fail(name, str(e))
        return False


async def test_html(s: ClientSession) -> bool:
    name = "html"
    try:
        t0 = time.monotonic()
        res = _parse(await s.call_tool(name, {
            "url": TARGET_URL,
            "crawler_config": COMMON_CRAWLER_CONFIG,
        }))
        elapsed = time.monotonic() - t0
        assert res.get("success"), f"success=False: {res}"

        html = res.get("html", "")
        assert html, "html field is empty"
        # Must contain real HTML tags
        assert "<" in html and ">" in html, \
            f"content does not look like HTML: {html[:200]!r}"
        assert any(tag in html.lower() for tag in ("<html", "<body", "<div", "<p", "<h")), \
            f"no block-level HTML tags found: {html[:200]!r}"

        _assert_delay(elapsed, name)
        _ok(name, f"len={len(html)}, elapsed={elapsed:.2f}s, first_tag={html[:40]!r}")
        return True
    except Exception as e:
        _fail(name, str(e))
        return False


async def test_screenshot(s: ClientSession) -> bool:
    name = "screenshot"
    try:
        t0 = time.monotonic()
        res = _parse(await s.call_tool(name, {
            "url": TARGET_URL,
            "screenshot_wait_for": 1.0,
            "crawler_config": COMMON_CRAWLER_CONFIG,
        }))
        elapsed = time.monotonic() - t0
        assert res.get("success"), f"success=False: {res}"

        shot_b64 = res.get("screenshot", "")
        assert shot_b64, "screenshot field is empty"
        # Decode and verify PNG magic bytes (\x89PNG\r\n\x1a\n)
        import base64
        raw = base64.b64decode(shot_b64)
        assert raw[:4] == b"\x89PNG", \
            f"screenshot is not a PNG — magic bytes: {raw[:8]!r}"
        assert len(raw) > 1000, f"PNG suspiciously small: {len(raw)} bytes"

        _assert_delay(elapsed, name)
        _ok(name, f"PNG {len(raw)//1024}KB, elapsed={elapsed:.2f}s")
        return True
    except Exception as e:
        _fail(name, str(e))
        return False


async def test_pdf(s: ClientSession) -> bool:
    name = "pdf"
    try:
        t0 = time.monotonic()
        res = _parse(await s.call_tool(name, {
            "url": TARGET_URL,
            "crawler_config": COMMON_CRAWLER_CONFIG,
        }))
        elapsed = time.monotonic() - t0
        assert res.get("success"), f"success=False: {res}"

        pdf_b64 = res.get("pdf", "")
        assert pdf_b64, "pdf field is empty"
        # Decode and verify PDF magic bytes (%PDF-)
        import base64
        raw = base64.b64decode(pdf_b64)
        assert raw[:4] == b"%PDF", \
            f"response is not a PDF — magic bytes: {raw[:8]!r}"
        assert len(raw) > 500, f"PDF suspiciously small: {len(raw)} bytes"

        _assert_delay(elapsed, name)
        _ok(name, f"PDF {len(raw)//1024}KB, elapsed={elapsed:.2f}s")
        return True
    except Exception as e:
        _fail(name, str(e))
        return False


async def test_execute_js(s: ClientSession) -> bool:
    name = "execute_js"
    try:
        t0 = time.monotonic()
        # Ask for the page title — example.com always returns "Example Domain"
        res = _parse(await s.call_tool(name, {
            "url": TARGET_URL,
            "scripts": ["document.title"],
            "crawler_config": COMMON_CRAWLER_CONFIG,
        }))
        elapsed = time.monotonic() - t0
        assert res.get("success"), f"success=False: {res}"

        # Full CrawlResult must be present
        assert res.get("html"), "CrawlResult missing html"
        assert res.get("url"), "CrawlResult missing url"

        _assert_delay(elapsed, name)
        _ok(name, f"html len={len(res['html'])}, url={res['url']}, elapsed={elapsed:.2f}s")
        return True
    except Exception as e:
        _fail(name, str(e))
        return False


async def test_crawl(s: ClientSession) -> bool:
    name = "crawl"
    try:
        t0 = time.monotonic()
        res = _parse(await s.call_tool(name, {
            "urls": [TARGET_URL],
            "browser_config": {},
            "crawler_config": {
                **COMMON_CRAWLER_CONFIG,
                "wait_until": "networkidle",
            },
        }))
        elapsed = time.monotonic() - t0

        results = res.get("results", [])
        assert results, "no results list"
        r0 = results[0]
        assert r0.get("success"), f"result[0] not successful: {r0}"

        # Must have the full crawl payload
        assert r0.get("html"), "result missing html"
        assert r0.get("url"), "result missing url"
        assert r0.get("status_code") == 200, \
            f"unexpected status_code: {r0.get('status_code')}"

        _assert_delay(elapsed, name)
        _ok(name, f"html len={len(r0['html'])}, status={r0['status_code']}, elapsed={elapsed:.2f}s")
        return True
    except Exception as e:
        _fail(name, str(e))
        return False


# ── runner ────────────────────────────────────────────────────────────────────

async def main() -> None:
    print(f"\nConnecting to {SSE_URL} …")
    async with sse_client(SSE_URL) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = [t.name for t in (await s.list_tools()).tools]
            print(f"Available tools: {tools}\n")

            tests = [
                ("schema check",   test_schema_exposes_crawler_config),
                ("md",             test_md),
                ("html",           test_html),
                ("screenshot",     test_screenshot),
                ("pdf",            test_pdf),
                ("execute_js",     test_execute_js),
                ("crawl",          test_crawl),
            ]

            passed = 0
            failed = 0
            for label, fn in tests:
                ok = await fn(s)
                if ok:
                    passed += 1
                else:
                    failed += 1

            print(f"\n{'='*50}")
            print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
            if failed:
                raise SystemExit(1)

anyio.run(main)
