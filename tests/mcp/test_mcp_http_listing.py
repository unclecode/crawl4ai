"""Minimal MCP HTTP listing smoke test.

Run with ``python tests/mcp/test_mcp_http_listing.py`` while the server is
running to verify that the HTTP transport exposes tools and resources.
"""


import os

import anyio

from fastmcp.client import Client

MCP_URL = os.getenv("MCP_URL", f"http://127.0.0.1:{os.getenv('HOST_PORT', '11235')}/mcp")


async def main() -> None:
    async with Client(MCP_URL) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()

        print("tools      :", [tool.name for tool in tools])
        print("resources  :", [resource.name for resource in resources])
        print("templates  :", [template.name for template in templates])


if __name__ == "__main__":
    anyio.run(main)
