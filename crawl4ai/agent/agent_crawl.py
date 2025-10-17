# agent_crawl.py
"""Crawl4AI Agent CLI - Browser automation agent powered by OpenAI Agents SDK."""

import asyncio
import sys
import os
import argparse
from pathlib import Path

from agents import Agent, Runner, set_default_openai_key

from .crawl_tools import CRAWL_TOOLS
from .crawl_prompts import SYSTEM_PROMPT
from .browser_manager import BrowserManager
from .terminal_ui import TerminalUI


class CrawlAgent:
    """Crawl4AI agent wrapper using OpenAI Agents SDK."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.ui = TerminalUI()

        # Set API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        set_default_openai_key(api_key)

        # Create agent
        self.agent = Agent(
            name="Crawl4AI Agent",
            instructions=SYSTEM_PROMPT,
            model=args.model or "gpt-4.1",
            tools=CRAWL_TOOLS,
            tool_use_behavior="run_llm_again",  # CRITICAL: Run LLM again after tools to generate response
        )

    async def run_single_shot(self, prompt: str):
        """Execute a single crawl task."""
        self.ui.console.print(f"\n🕷️  [bold cyan]Crawl4AI Agent[/bold cyan]")
        self.ui.console.print(f"🎯 Task: {prompt}\n")

        try:
            result = await Runner.run(
                starting_agent=self.agent,
                input=prompt,
                context=None,
                max_turns=100,  # Allow up to 100 turns for complex tasks
            )

            self.ui.console.print(f"\n[bold green]Result:[/bold green]")
            self.ui.console.print(result.final_output)

            if hasattr(result, 'usage'):
                self.ui.console.print(f"\n[dim]Tokens: {result.usage}[/dim]")

        except Exception as e:
            self.ui.print_error(f"Error: {e}")
            if self.args.debug:
                raise

    async def run_chat_mode(self):
        """Run interactive chat mode with streaming visibility."""
        from .chat_mode import ChatMode

        chat = ChatMode(self.agent, self.ui)
        await chat.run()


def main():
    parser = argparse.ArgumentParser(
        description="Crawl4AI Agent - Browser automation powered by OpenAI Agents SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("prompt", nargs="?", help="Your crawling task prompt (not used in --chat mode)")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat mode")
    parser.add_argument("--model", help="Model to use (e.g., 'gpt-4.1', 'gpt-5-nano')", default="gpt-4.1")
    parser.add_argument("-v", "--version", action="version", version="Crawl4AI Agent 2.0.0")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Chat mode - interactive
    if args.chat:
        try:
            agent = CrawlAgent(args)
            asyncio.run(agent.run_chat_mode())
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
        print('  python -m crawl4ai.agent.agent_crawl "Scrape products from example.com"')
        print()
        print('  # Interactive chat mode:')
        print('  python -m crawl4ai.agent.agent_crawl --chat')
        sys.exit(1)

    try:
        agent = CrawlAgent(args)
        asyncio.run(agent.run_single_shot(args.prompt))
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
