# agent_crawl.py
"""Crawl4AI Agent CLI - Browser automation agent powered by Claude Code SDK."""

import asyncio
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
from claude_agent_sdk import AssistantMessage, TextBlock, ResultMessage

from .c4ai_tools import CRAWL_TOOLS
from .c4ai_prompts import SYSTEM_PROMPT
from .terminal_ui import TerminalUI
from .chat_mode import ChatMode


class SessionStorage:
    """Manage session storage in ~/.crawl4ai/agents/projects/"""

    def __init__(self, cwd: Optional[str] = None):
        self.cwd = Path(cwd) if cwd else Path.cwd()
        self.base_dir = Path.home() / ".crawl4ai" / "agents" / "projects"
        self.project_dir = self.base_dir / self._sanitize_path(str(self.cwd.resolve()))
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = str(uuid.uuid4())
        self.log_file = self.project_dir / f"{self.session_id}.jsonl"

    @staticmethod
    def _sanitize_path(path: str) -> str:
        """Convert /Users/unclecode/devs/test to -Users-unclecode-devs-test"""
        return path.replace("/", "-").replace("\\", "-")

    def log(self, event_type: str, data: dict):
        """Append event to JSONL log."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "session_id": self.session_id,
            "data": data
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_session_path(self) -> str:
        """Return path to current session log."""
        return str(self.log_file)


class CrawlAgent:
    """Crawl4AI agent wrapper."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.storage = SessionStorage(args.add_dir[0] if args.add_dir else None)
        self.client: Optional[ClaudeSDKClient] = None

        # Create MCP server with crawl tools
        self.crawler_server = create_sdk_mcp_server(
            name="crawl4ai",
            version="1.0.0",
            tools=CRAWL_TOOLS
        )

        # Build options
        self.options = ClaudeAgentOptions(
            mcp_servers={"crawler": self.crawler_server},
            allowed_tools=[
                # Crawl4AI tools
                "mcp__crawler__quick_crawl",
                "mcp__crawler__start_session",
                "mcp__crawler__navigate",
                "mcp__crawler__extract_data",
                "mcp__crawler__execute_js",
                "mcp__crawler__screenshot",
                "mcp__crawler__close_session",
                # Claude Code SDK built-in tools
                "Read",
                "Write",
                "Edit",
                "Glob",
                "Grep",
                "Bash",
                "NotebookEdit"
            ],
            system_prompt=SYSTEM_PROMPT if not args.system_prompt else args.system_prompt,
            permission_mode=args.permission_mode or "acceptEdits",
            cwd=args.add_dir[0] if args.add_dir else str(Path.cwd()),
            model=args.model,
        )

    async def run(self, prompt: str):
        """Execute crawl task."""

        self.storage.log("session_start", {
            "prompt": prompt,
            "cwd": self.options.cwd,
            "model": self.options.model
        })

        print(f"\n🕷️  Crawl4AI Agent")
        print(f"📁 Session: {self.storage.session_id}")
        print(f"💾 Log: {self.storage.get_session_path()}")
        print(f"🎯 Task: {prompt}\n")

        async with ClaudeSDKClient(options=self.options) as client:
            self.client = client
            await client.query(prompt)

            turn = 0
            async for message in client.receive_messages():
                turn += 1

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"\n💭 [{turn}] {block.text}")
                            self.storage.log("assistant_message", {"turn": turn, "text": block.text})

                elif isinstance(message, ResultMessage):
                    print(f"\n✅ Completed in {message.duration_ms/1000:.2f}s")
                    print(f"💰 Cost: ${message.total_cost_usd:.4f}" if message.total_cost_usd else "")
                    print(f"🔄 Turns: {message.num_turns}")

                    self.storage.log("session_end", {
                        "duration_ms": message.duration_ms,
                        "cost_usd": message.total_cost_usd,
                        "turns": message.num_turns,
                        "success": not message.is_error
                    })
                    break

        print(f"\n📊 Session log: {self.storage.get_session_path()}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Crawl4AI Agent - Browser automation powered by Claude Code SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("prompt", nargs="?", help="Your crawling task prompt (not used in --chat mode)")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat mode")
    parser.add_argument("--system-prompt", help="Custom system prompt")
    parser.add_argument("--permission-mode", choices=["acceptEdits", "bypassPermissions", "default", "plan"],
                       help="Permission mode for tool execution")
    parser.add_argument("--model", help="Model to use (e.g., 'sonnet', 'opus')")
    parser.add_argument("--add-dir", nargs="+", help="Additional directories for file access")
    parser.add_argument("--session-id", help="Use specific session ID (UUID)")
    parser.add_argument("-v", "--version", action="version", version="Crawl4AI Agent 1.0.0")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Chat mode - interactive
    if args.chat:
        try:
            agent = CrawlAgent(args)
            ui = TerminalUI()
            chat = ChatMode(agent.options, ui, agent.storage)
            asyncio.run(chat.run())
        except KeyboardInterrupt:
            print("\n\n⚠️  Chat interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if args.debug:
                raise
            sys.exit(1)
        return

    # Single-shot mode - requires prompt
    if not args.prompt:
        parser.print_help()
        print("\nExample usage:")
        print('  # Single-shot mode:')
        print('  crawl-agent "Scrape all products from example.com with price > $10"')
        print('  crawl-agent --add-dir ~/projects "Find all Python files and analyze imports"')
        print()
        print('  # Interactive chat mode:')
        print('  crawl-agent --chat')
        sys.exit(1)

    try:
        agent = CrawlAgent(args)
        asyncio.run(agent.run(args.prompt))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
