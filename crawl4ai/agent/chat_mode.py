# chat_mode.py
"""Interactive chat mode with streaming visibility for Crawl4AI Agent."""

import asyncio
from typing import Optional
from agents import Agent, Runner

from .terminal_ui import TerminalUI
from .browser_manager import BrowserManager


class ChatMode:
    """Interactive chat mode with real-time status updates and tool visibility."""

    def __init__(self, agent: Agent, ui: TerminalUI):
        self.agent = agent
        self.ui = ui
        self._exit_requested = False
        self.conversation_history = []  # Track full conversation for context

        # Generate unique session ID
        import time
        self.session_id = f"session_{int(time.time())}"

    async def _handle_command(self, command: str) -> bool:
        """Handle special chat commands.

        Returns:
            True if command was /exit, False otherwise
        """
        cmd = command.lower().strip()

        if cmd == '/exit' or cmd == '/quit':
            self._exit_requested = True
            self.ui.print_info("Exiting chat mode...")
            return True

        elif cmd == '/clear':
            self.ui.clear_screen()
            self.ui.show_header(session_id=self.session_id)
            return False

        elif cmd == '/help':
            self.ui.show_commands()
            return False

        elif cmd == '/browser':
            # Show browser status
            if BrowserManager.is_browser_active():
                config = BrowserManager.get_current_config()
                self.ui.print_info(f"Browser active: headless={config.headless if config else 'unknown'}")
            else:
                self.ui.print_info("No browser instance active")
            return False

        else:
            self.ui.print_error(f"Unknown command: {command}")
            self.ui.print_info("Available commands: /exit, /clear, /help, /browser")
            return False

    async def run(self):
        """Run the interactive chat loop with streaming responses and visibility."""
        # Show header with session ID (tips are now inside)
        self.ui.show_header(session_id=self.session_id)

        try:
            while not self._exit_requested:
                # Get user input
                try:
                    user_input = await asyncio.to_thread(self.ui.get_user_input)
                except EOFError:
                    break

                # Handle commands
                if user_input.startswith('/'):
                    should_exit = await self._handle_command(user_input)
                    if should_exit:
                        break
                    continue

                # Skip empty input
                if not user_input.strip():
                    continue

                # Add user message to conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })

                # Show thinking indicator
                self.ui.console.print("\n[cyan]Agent:[/cyan] [dim italic]thinking...[/dim italic]")

                try:
                    # Run agent with streaming, passing conversation history for context
                    result = Runner.run_streamed(
                        self.agent,
                        input=self.conversation_history,  # Pass full conversation history
                        context=None,
                        max_turns=100,  # Allow up to 100 turns for complex multi-step tasks
                    )

                    # Track what we've seen
                    response_text = []
                    tools_called = []
                    current_tool = None

                    # Process streaming events
                    async for event in result.stream_events():
                        # DEBUG: Print all event types
                        # self.ui.console.print(f"[dim]DEBUG: event type={event.type}[/dim]")

                        # Agent switched
                        if event.type == "agent_updated_stream_event":
                            self.ui.console.print(f"\n[dim]→ Agent: {event.new_agent.name}[/dim]")

                        # Items generated (tool calls, outputs, text)
                        elif event.type == "run_item_stream_event":
                            item = event.item

                            # Tool call started
                            if item.type == "tool_call_item":
                                # Get tool name from raw_item
                                current_tool = item.raw_item.name if hasattr(item.raw_item, 'name') else "unknown"
                                tools_called.append(current_tool)

                                # Show tool name and args clearly
                                tool_display = current_tool
                                self.ui.console.print(f"\n[yellow]🔧 Calling:[/yellow] [bold]{tool_display}[/bold]")

                                # Show tool arguments if present
                                if hasattr(item.raw_item, 'arguments'):
                                    try:
                                        import json
                                        args_str = item.raw_item.arguments
                                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                                        # Show key args only
                                        key_args = {k: v for k, v in args.items() if k in ['url', 'session_id', 'output_format']}
                                        if key_args:
                                            params_str = ", ".join(f"{k}={v}" for k, v in key_args.items())
                                            self.ui.console.print(f"  [dim]({params_str})[/dim]")
                                    except:
                                        pass

                            # Tool output received
                            elif item.type == "tool_call_output_item":
                                if current_tool:
                                    self.ui.console.print(f"  [green]✓[/green] [dim]completed[/dim]")
                                    current_tool = None

                            # Agent text response (multiple types)
                            elif item.type == "text_item":
                                # Clear "thinking..." line if this is first text
                                if not response_text:
                                    self.ui.console.print("\r[cyan]Agent:[/cyan] ", end="")

                                # Stream the text
                                self.ui.console.print(item.text, end="")
                                response_text.append(item.text)

                            # Message output (final response)
                            elif item.type == "message_output_item":
                                # This is the final formatted response
                                if not response_text:
                                    self.ui.console.print("\n[cyan]Agent:[/cyan] ", end="")

                                # Extract text from content blocks
                                if hasattr(item.raw_item, 'content') and item.raw_item.content:
                                    for content_block in item.raw_item.content:
                                        if hasattr(content_block, 'text'):
                                            text = content_block.text
                                            self.ui.console.print(text, end="")
                                            response_text.append(text)

                        # Text deltas (real-time streaming)
                        elif event.type == "text_delta_stream_event":
                            # Clear "thinking..." if this is first delta
                            if not response_text:
                                self.ui.console.print("\r[cyan]Agent:[/cyan] ", end="")

                            # Stream character by character for responsiveness
                            self.ui.console.print(event.delta, end="", markup=False)
                            response_text.append(event.delta)

                    # Newline after response
                    self.ui.console.print()

                    # Show summary after response
                    if tools_called:
                        self.ui.console.print(f"\n[dim]Tools used: {', '.join(set(tools_called))}[/dim]")

                    # Add agent response to conversation history
                    if response_text:
                        agent_response = "".join(response_text)
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": agent_response
                        })

                except Exception as e:
                    self.ui.print_error(f"Error during agent execution: {e}")
                    import traceback
                    traceback.print_exc()

        except KeyboardInterrupt:
            self.ui.print_info("\n\nChat interrupted by user")

        finally:
            # Cleanup browser on exit
            self.ui.console.print("\n[dim]Cleaning up...[/dim]")
            await BrowserManager.close_browser()
            self.ui.print_info("Browser closed")
            self.ui.console.print("[bold green]Goodbye![/bold green]\n")
