#!/usr/bin/env python3
"""
MCP protocol tests focusing on MCP-specific functionality.

Tests MCP tool registration, schemas, and protocol compliance.
Tool execution is covered by test_e2e_api.py (no need to duplicate).
"""

import json
import pytest
import pytest_asyncio

try:
    from fastmcp import Client as MCPClient
    HAVE_FASTMCP = True
except ImportError:
    HAVE_FASTMCP = False


@pytest.fixture(scope="module")
def mcp_server():
    """Get FastMCP server instance for protocol testing."""
    if not HAVE_FASTMCP:
        pytest.skip("fastmcp not installed")

    from deploy.docker.server import mcp_service
    return mcp_service.mcp_server


@pytest_asyncio.fixture
async def mcp_client(mcp_server):
    """Async MCP client using in-memory transport."""
    async with MCPClient(mcp_server) as client:
        yield client


# ---- MCP Protocol Tests ----------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_list_tools(mcp_client):
    """Test MCP server exposes expected tools via protocol."""
    tools = await mcp_client.list_tools()
    names = {t.name for t in tools}
    expected = {"md", "html", "screenshot", "pdf", "execute_js", "crawl", "ask"}
    assert expected.issubset(names), f"Missing tools: {expected - names}"


@pytest.mark.asyncio
async def test_mcp_tool_schemas(mcp_client):
    """Test MCP tools have valid schemas."""
    tools = await mcp_client.list_tools()

    for tool in tools:
        assert tool.name, f"Tool missing name"
        assert tool.description, f"Tool {tool.name} missing description"
        assert tool.inputSchema, f"Tool {tool.name} missing inputSchema"
        # Verify inputSchema is valid JSON schema
        assert "type" in tool.inputSchema, f"Tool {tool.name} schema missing type"
        assert tool.inputSchema["type"] == "object", f"Tool {tool.name} schema type should be object"


@pytest.mark.asyncio
async def test_mcp_tool_parameters(mcp_client):
    """Test MCP tool schemas have required parameters."""
    tools = await mcp_client.list_tools()
    tool_dict = {t.name: t for t in tools}

    # Verify key tools have expected parameters
    md_tool = tool_dict.get("md")
    assert md_tool, "md tool not found"
    assert "properties" in md_tool.inputSchema
    assert "url" in md_tool.inputSchema["properties"]
    assert "filter" in md_tool.inputSchema["properties"]

    crawl_tool = tool_dict.get("crawl")
    assert crawl_tool, "crawl tool not found"
    assert "properties" in crawl_tool.inputSchema
    assert "urls" in crawl_tool.inputSchema["properties"]

    ask_tool = tool_dict.get("ask")
    assert ask_tool, "ask tool not found"
    assert "properties" in ask_tool.inputSchema
    assert "context_type" in ask_tool.inputSchema["properties"]


@pytest.mark.asyncio
async def test_mcp_required_parameters(mcp_client):
    """Test MCP tool schemas properly mark required parameters."""
    tools = await mcp_client.list_tools()
    tool_dict = {t.name: t for t in tools}

    # Verify md tool has required url parameter
    md_tool = tool_dict.get("md")
    assert md_tool, "md tool not found"
    url_prop = md_tool.inputSchema["properties"].get("url")
    assert url_prop, "md tool missing url property"
    assert url_prop.get("type") == "string", "url should be string type"
    # url should be required
    required = md_tool.inputSchema.get("required", [])
    assert "url" in required, "url should be required parameter"

    # Verify crawl tool has urls parameter as array type
    crawl_tool = tool_dict.get("crawl")
    assert crawl_tool, "crawl tool not found"
    urls_prop = crawl_tool.inputSchema["properties"].get("urls")
    assert urls_prop, "crawl tool missing urls property"
    assert urls_prop.get("type") == "array", "urls should be array type"
    assert urls_prop.get("items"), "urls array should define item type"
    # urls should be required
    required = crawl_tool.inputSchema.get("required", [])
    assert "urls" in required, "urls should be required parameter"