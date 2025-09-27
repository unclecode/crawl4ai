"""Interactive MCP HTTP smoke test.

These helper coroutines mirror the legacy WebSocket test but target the
FastMCP Streamable HTTP transport exposed at ``/mcp``.
Run with ``python tests/mcp/test_mcp_socket.py`` once the server is up.
"""

import json
import os
from typing import Iterable

import anyio

from fastmcp.client import Client

MCP_URL = os.getenv("MCP_URL", f"http://localhost:{os.getenv('HOST_PORT', '11235')}/mcp")


def _first_text_block(content_blocks: Iterable[object]) -> str:
    """Return the first textual content block emitted by a tool call."""
    for block in content_blocks:
        text = getattr(block, "text", None)
        if isinstance(text, str):
            return text
    raise RuntimeError("Tool response did not include textual content")


async def test_crawl(client: Client) -> None:
    """Hit the @mcp_tool('crawl') endpoint."""
    result = await client.call_tool(
        "crawl",
        {
            "urls": ["https://example.com"],
            "browser_config": {},
            "crawler_config": {},
        },
    )
    print("crawl →", json.loads(_first_text_block(result.content)))


async def test_md(client: Client) -> None:
    """Hit the @mcp_tool('md') endpoint."""
    result = await client.call_tool(
        "md",
        {
            "url": "https://example.com",
            "filter": "fit",  # or raw, bm25, llm
            "query": None,
            "cache": "0",
        },
    )
    markdown = json.loads(_first_text_block(result.content))
    snippet = markdown.get("markdown", "")[:100]
    print("md →", snippet, "...")


async def test_screenshot(client: Client) -> None:
    result = await client.call_tool(
        "screenshot",
        {
            "url": "https://example.com",
            "screenshot_wait_for": 1.0,
        },
    )
    payload = json.loads(_first_text_block(result.content))
    key = "path" if "path" in payload else "screenshot"
    value = payload[key]
    display = value if key == "path" else value[:60] + "… (base64)"
    print("screenshot →", display)


async def test_pdf(client: Client) -> None:
    result = await client.call_tool(
        "pdf",
        {
            "url": "https://example.com",
        },
    )
    payload = json.loads(_first_text_block(result.content))
    key = "path" if "path" in payload else "pdf"
    value = payload[key]
    display = value if key == "path" else value[:60] + "… (base64)"
    print("pdf →", display)


async def test_execute_js(client: Client) -> None:
    result = await client.call_tool(
        "execute_js",
        {
            "url": "https://news.ycombinator.com/news",
            "scripts": [
                "await page.click('a.morelink')",
                "await page.waitForTimeout(1000)",
            ],
        },
    )
    crawl_result = json.loads(_first_text_block(result.content))
    print("execute_js → status", crawl_result.get("success"), "| html len:", len(crawl_result.get("html", "")))


async def test_html(client: Client) -> None:
    result = await client.call_tool(
        "html",
        {
            "url": "https://news.ycombinator.com/news",
        },
    )
    crawl_result = json.loads(_first_text_block(result.content))
    print("html → status", crawl_result.get("success"), "| html len:", len(crawl_result.get("html", "")))


async def test_context(client: Client) -> None:
    result = await client.call_tool(
        "ask",
        {
            "query": "How do I extract internal links when crawling a page?",
            "context_type": "code",
            "score_ratio": 0.4,
        },
    )
    context_result = json.loads(_first_text_block(result.content))
    print("ask → keys", list(context_result.keys()))


async def main() -> None:
    async with Client(MCP_URL) as client:
        tools = await client.list_tools()
        print("tools:", [t.name for t in tools])

        await test_crawl(client)
        await test_md(client)
        await test_screenshot(client)
        await test_pdf(client)
        await test_execute_js(client)
        await test_html(client)
        await test_context(client)


if __name__ == "__main__":
    anyio.run(main)
