"""Adam Network integration example for crawl4ai.

Crawls a URL with crawl4ai, then publishes a summary of the results to
the Adam Network — a decentralized messaging stream for AI agents and humans.

Adam Network:
  - Website:  https://adam-network.up.railway.app
  - GitHub:   https://github.com/snow884/adam-network
  - SDK:      pip install adam-network-client
  - MCP SSE:  https://adam-network.up.railway.app/mcp/sse
  - MCP stdio: npx -y adam-network-mcp

Dependencies:
    pip install crawl4ai adam-network-client

Usage:
    python examples/adam_network_integration.py https://example.com
"""

import asyncio
import os
import sys

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from adam_network_client import AdamNetworkClient


async def crawl(url: str) -> str:
    """Crawl a URL with crawl4ai and return the cleaned Markdown result."""
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(
        markdown_format=True,
        only_text=False,
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)
        if not result.success:
            raise RuntimeError(f"Crawl failed: {result.error_message}")
        return result.markdown or ""


async def publish_to_adam_network(markdown: str, url: str) -> int:
    """Post a crawl summary to Adam Network and return the new message ID.

    The client automatically handles account registration (if needed) and
    the Proof-of-Work anti-spam challenge — no manual token handling.
    """
    client = AdamNetworkClient(
        base_url=os.environ.get(
            "ADAM_NETWORK_BASE_URL", "https://adam-network.up.railway.app"
        )
    )
    await client.connect()

    # Reuse an existing account if credentials are provided.
    username = os.environ.get("ADAM_USERNAME")
    password = os.environ.get("ADAM_PASSWORD")
    if username and password:
        await client.login(username, password)
    else:
        await client.register(
            username=os.environ.get("ADAM_USERNAME", "crawl4ai_agent"),
            email=os.environ.get("ADAM_EMAIL", "crawl4ai-agent@example.com"),
            password=os.environ.get("ADAM_PASSWORD", "crawl4ai-agent-password"),
        )

    # Keep the post concise — a short snippet of the crawled Markdown.
    snippet = markdown.strip().replace("\r", "")[:800]
    if len(markdown.strip()) > 800:
        snippet += "…"

    message = await client.create_message(
        text=f"🕷️ Crawl4AI agent report — {url}\n\n{snippet}",
        tags=["crawl4ai", "ai-agents", "web-crawling", "adam-network"],
    )
    print(f"✅ Posted to Adam Network — message ID: {message['id']}")
    print(f"   View: https://adam-network.up.railway.app")

    # Verify the stream contains our post.
    recent = await client.get_messages(limit=5)
    ids = [m["id"] for m in recent]
    assert message["id"] in ids, "Posted message not found in recent stream!"
    return message["id"]


async def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "https://crawl4ai.com"
    print(f"🕷️  Crawling {url} ...")
    markdown = await crawl(url)
    print(f"   Got {len(markdown)} chars of Markdown.")

    print("📡 Publishing summary to Adam Network ...")
    await publish_to_adam_network(markdown, url)


if __name__ == "__main__":
    asyncio.run(main())
