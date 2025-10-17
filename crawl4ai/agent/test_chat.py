#!/usr/bin/env python
"""Test script to verify chat mode setup (non-interactive)."""

import sys
import asyncio
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawl4ai.agent.browser_manager import BrowserManager
from crawl4ai.agent.terminal_ui import TerminalUI
from crawl4ai.agent.chat_mode import ChatMode
from crawl4ai.agent.c4ai_tools import CRAWL_TOOLS
from crawl4ai.agent.c4ai_prompts import SYSTEM_PROMPT

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server


class MockStorage:
    """Mock storage for testing."""

    def log(self, event_type: str, data: dict):
        print(f"[LOG] {event_type}: {data}")

    def get_session_path(self):
        return "/tmp/test_session.jsonl"


async def test_components():
    """Test individual components."""

    print("="*60)
    print("CHAT MODE COMPONENT TESTS")
    print("="*60)

    # Test 1: BrowserManager
    print("\n[TEST 1] BrowserManager singleton")
    try:
        browser1 = await BrowserManager.get_browser()
        browser2 = await BrowserManager.get_browser()
        assert browser1 is browser2, "Browser instances should be same (singleton)"
        print("✓ BrowserManager singleton works")
        await BrowserManager.close_browser()
    except Exception as e:
        print(f"✗ BrowserManager failed: {e}")
        return False

    # Test 2: TerminalUI
    print("\n[TEST 2] TerminalUI rendering")
    try:
        ui = TerminalUI()
        ui.show_header("test-123", "/tmp/test.log")
        ui.print_agent_text("Hello from agent")
        ui.print_markdown("# Test\nThis is **bold**")
        ui.print_success("Test success message")
        print("✓ TerminalUI renders correctly")
    except Exception as e:
        print(f"✗ TerminalUI failed: {e}")
        return False

    # Test 3: MCP Server Setup
    print("\n[TEST 3] MCP Server with tools")
    try:
        crawler_server = create_sdk_mcp_server(
            name="crawl4ai",
            version="1.0.0",
            tools=CRAWL_TOOLS
        )
        print(f"✓ MCP server created with {len(CRAWL_TOOLS)} tools")
    except Exception as e:
        print(f"✗ MCP Server failed: {e}")
        return False

    # Test 4: ChatMode instantiation
    print("\n[TEST 4] ChatMode instantiation")
    try:
        options = ClaudeAgentOptions(
            mcp_servers={"crawler": crawler_server},
            allowed_tools=[
                "mcp__crawler__quick_crawl",
                "mcp__crawler__start_session",
                "mcp__crawler__navigate",
                "mcp__crawler__extract_data",
                "mcp__crawler__execute_js",
                "mcp__crawler__screenshot",
                "mcp__crawler__close_session",
            ],
            system_prompt=SYSTEM_PROMPT,
            permission_mode="acceptEdits"
        )

        ui = TerminalUI()
        storage = MockStorage()
        chat = ChatMode(options, ui, storage)
        print("✓ ChatMode instance created successfully")
    except Exception as e:
        print(f"✗ ChatMode failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*60)
    print("ALL COMPONENT TESTS PASSED ✓")
    print("="*60)
    print("\nTo test interactive chat mode, run:")
    print("  python -m crawl4ai.agent.agent_crawl --chat")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_components())
    sys.exit(0 if success else 1)
