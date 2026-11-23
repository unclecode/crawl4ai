from fastapi import FastAPI, Query
from fastapi.testclient import TestClient
from mcp_bridge import attach_mcp, mcp_tool


def test_query_tool_schema_includes_properties():
    app = FastAPI()

    @app.get("/ask")
    @mcp_tool("ask")
    async def ask(
        query: str | None = Query(None, description="Search query"),
        max_results: int = Query(20, ge=1),
    ):
        return {}

    attach_mcp(app, base_url="http://127.0.0.1:8020")
    tools = TestClient(app).get("/mcp/schema").json()["tools"]
    schema = next(tool for tool in tools if tool["name"] == "ask")["inputSchema"]

    assert set(schema["properties"]) == {"query", "max_results"}
    assert schema["properties"]["max_results"]["minimum"] == 1
