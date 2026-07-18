"""Test the MCP Streamable-HTTP transport.

Requires a running Crawl4AI server on port 11235.

Usage:
    pytest tests/mcp/test_mcp_streamable_http.py -v
    # or run directly:
    python tests/mcp/test_mcp_streamable_http.py
"""

from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession


async def main():
    async with streamable_http_client("http://127.0.0.1:11235/mcp") as (read, write, get_sid):
        async with ClientSession(read, write) as session:
            tools = await session.list_tools()
            print("tools:", [t.name for t in tools.tools])

            resources = await session.list_resources()
            print("resources:", [r.name for r in resources.resources])


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
