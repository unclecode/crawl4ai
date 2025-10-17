"""Chat mode implementation with streaming message generator for Claude SDK."""

import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock, ResultMessage, ToolUseBlock

from .terminal_ui import TerminalUI
from .browser_manager import BrowserManager


class ChatMode:
    """Interactive chat mode with streaming input/output."""

    def __init__(self, options: ClaudeAgentOptions, ui: TerminalUI, storage):
        self.options = options
        self.ui = ui
        self.storage = storage
        self._exit_requested = False
        self._current_streaming_text = ""

    async def message_generator(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate user messages as async generator (streaming input mode per cc_stream.md).

        Yields messages in the format:
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": "user input text"
            }
        }
        """
        while not self._exit_requested:
            try:
                # Get user input
                user_input = await asyncio.to_thread(self.ui.get_user_input)

                # Handle commands
                if user_input.startswith('/'):
                    await self._handle_command(user_input)
                    if self._exit_requested:
                        break
                    continue

                # Skip empty input
                if not user_input.strip():
                    continue

                # Log user message
                self.storage.log("user_message", {"text": user_input})

                # Yield user message for agent
                yield {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": user_input
                    }
                }

            except KeyboardInterrupt:
                self._exit_requested = True
                break
            except Exception as e:
                self.ui.print_error(f"Input error: {e}")

    async def _handle_command(self, command: str):
        """Handle special chat commands."""
        cmd = command.lower().strip()

        if cmd == '/exit' or cmd == '/quit':
            self._exit_requested = True
            self.ui.print_info("Exiting chat mode...")

        elif cmd == '/clear':
            self.ui.clear_screen()

        elif cmd == '/help':
            self.ui.show_commands()

        elif cmd == '/browser':
            # Show browser status
            if BrowserManager.is_browser_active():
                config = BrowserManager.get_current_config()
                self.ui.print_info(f"Browser active: {config}")
            else:
                self.ui.print_info("No browser instance active")

        else:
            self.ui.print_error(f"Unknown command: {command}")

    async def run(self):
        """Run the interactive chat loop with streaming responses."""
        # Show header
        self.ui.show_header(
            session_id=str(self.options.session_id or "chat"),
            log_path=self.storage.get_session_path() if hasattr(self.storage, 'get_session_path') else "N/A"
        )
        self.ui.show_commands()

        try:
            async with ClaudeSDKClient(options=self.options) as client:
                # Start streaming input mode
                await client.query(self.message_generator())

                # Process streaming responses
                turn = 0
                async for message in client.receive_messages():
                    turn += 1

                    if isinstance(message, AssistantMessage):
                        # Clear "thinking" line if we printed it
                        if self._current_streaming_text:
                            self.ui.console.print()  # New line after streaming

                        self._current_streaming_text = ""

                        # Process message content blocks
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                # Stream text as it arrives
                                self.ui.print_agent_text(block.text)
                                self._current_streaming_text += block.text

                                # Log assistant message
                                self.storage.log("assistant_message", {
                                    "turn": turn,
                                    "text": block.text
                                })

                            elif isinstance(block, ToolUseBlock):
                                # Show tool usage
                                self.ui.print_tool_use(block.name)

                    elif isinstance(message, ResultMessage):
                        # Session completed (user exited or error)
                        if message.is_error:
                            self.ui.print_error(f"Agent error: {message.result}")
                        else:
                            self.ui.print_session_summary(
                                duration_s=message.duration_ms / 1000 if message.duration_ms else 0,
                                turns=message.num_turns,
                                cost_usd=message.total_cost_usd
                            )

                        # Log session end
                        self.storage.log("session_end", {
                            "duration_ms": message.duration_ms,
                            "cost_usd": message.total_cost_usd,
                            "turns": message.num_turns,
                            "success": not message.is_error
                        })
                        break

        except KeyboardInterrupt:
            self.ui.print_info("\nChat interrupted by user")

        except Exception as e:
            self.ui.print_error(f"Chat error: {e}")
            raise

        finally:
            # Cleanup browser on exit
            await BrowserManager.close_browser()
            self.ui.print_info("Browser closed")
