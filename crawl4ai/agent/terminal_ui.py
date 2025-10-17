"""Terminal UI components using Rich for beautiful agent output."""

import readline
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule

# Crawl4AI Logo (>X< shape)
CRAWL4AI_LOGO = """
  ██      ██
▓   ██  ██   ▓
 ▓    ██    ▓
▓   ██  ██   ▓
  ██      ██
"""

VERSION = "0.1.0"


class TerminalUI:
    """Rich-based terminal interface for the Crawl4AI agent."""

    def __init__(self):
        self.console = Console()
        self._current_text = ""

        # Configure readline for command history
        # History will persist in memory during session
        readline.parse_and_bind('tab: complete')  # Enable tab completion
        readline.parse_and_bind('set editing-mode emacs')  # Emacs-style editing (Ctrl+A, Ctrl+E, etc.)
        # Up/Down arrows already work by default for history

    def show_header(self, session_id: str = None, log_path: str = None):
        """Display agent session header - Claude Code style with vertical divider."""
        import os

        self.console.print()

        # Get current directory
        current_dir = os.getcwd()

        # Build left and right columns separately to avoid padding issues
        from rich.table import Table
        from rich.text import Text

        # Create a table with two columns
        table = Table.grid(padding=(0, 2))
        table.add_column(width=30, style="")  # Left column
        table.add_column(width=1, style="dim")  # Divider
        table.add_column(style="")  # Right column

        # Row 1: Welcome / Tips header (centered)
        table.add_row(
            Text("Welcome back!", style="bold white", justify="center"),
            "│",
            Text("Tips", style="bold white")
        )

        # Row 2: Empty / Tip 1
        table.add_row(
            "",
            "│",
            Text("• Press ", style="dim") + Text("Enter", style="cyan") + Text(" to send", style="dim")
        )

        # Row 3: Logo line 1 / Tip 2
        table.add_row(
            Text("      ██      ██", style="bold cyan"),
            "│",
            Text("• Press ", style="dim") + Text("Option+Enter", style="cyan") + Text(" or ", style="dim") + Text("Ctrl+J", style="cyan") + Text(" for new line", style="dim")
        )

        # Row 4: Logo line 2 / Tip 3
        table.add_row(
            Text("    ▓   ██  ██   ▓", style="bold cyan"),
            "│",
            Text("• Use ", style="dim") + Text("/exit", style="cyan") + Text(", ", style="dim") + Text("/clear", style="cyan") + Text(", ", style="dim") + Text("/help", style="cyan") + Text(", ", style="dim") + Text("/browser", style="cyan")
        )

        # Row 5: Logo line 3 / Empty
        table.add_row(
            Text("     ▓    ██    ▓", style="bold cyan"),
            "│",
            ""
        )

        # Row 6: Logo line 4 / Session header
        table.add_row(
            Text("    ▓   ██  ██   ▓", style="bold cyan"),
            "│",
            Text("Session", style="bold white")
        )

        # Row 7: Logo line 5 / Session ID
        session_name = os.path.basename(session_id) if session_id else "unknown"
        table.add_row(
            Text("      ██      ██", style="bold cyan"),
            "│",
            Text(session_name, style="dim")
        )

        # Row 8: Empty
        table.add_row("", "│", "")

        # Row 9: Version (centered)
        table.add_row(
            Text(f"Version {VERSION}", style="dim", justify="center"),
            "│",
            ""
        )

        # Row 10: Path (centered)
        table.add_row(
            Text(current_dir, style="dim", justify="center"),
            "│",
            ""
        )

        # Create panel with title
        panel = Panel(
            table,
            title=f"[bold cyan]─── Crawl4AI Agent v{VERSION} ───[/bold cyan]",
            title_align="left",
            border_style="cyan",
            padding=(1, 1),
            expand=True
        )

        self.console.print(panel)
        self.console.print()

    def show_commands(self):
        """Display available commands."""
        self.console.print("\n[dim]Commands:[/dim]")
        self.console.print("  [cyan]/exit[/cyan] - Exit chat")
        self.console.print("  [cyan]/clear[/cyan] - Clear screen")
        self.console.print("  [cyan]/help[/cyan] - Show this help")
        self.console.print("  [cyan]/browser[/cyan] - Show browser status\n")

    def get_user_input(self) -> str:
        """Get user input with multi-line support and paste handling.

        Usage:
        - Press Enter to submit
        - Press Option+Enter (or Ctrl+J) for new line
        - Paste multi-line text works perfectly
        """
        from prompt_toolkit import prompt
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.keys import Keys
        from prompt_toolkit.formatted_text import HTML

        # Create custom key bindings
        bindings = KeyBindings()

        # Enter to submit (reversed from default multiline behavior)
        @bindings.add(Keys.Enter)
        def _(event):
            """Submit the input when Enter is pressed."""
            event.current_buffer.validate_and_handle()

        # Option+Enter for newline (sends Esc+Enter when iTerm2 configured with "Esc+")
        @bindings.add(Keys.Escape, Keys.Enter)
        def _(event):
            """Insert newline with Option+Enter (or Esc then Enter)."""
            event.current_buffer.insert_text("\n")

        # Ctrl+J as alternative for newline (works everywhere)
        @bindings.add(Keys.ControlJ)
        def _(event):
            """Insert newline with Ctrl+J."""
            event.current_buffer.insert_text("\n")

        try:
            # Tips are now in header, no need for extra hint

            # Use prompt_toolkit with HTML formatting (no ANSI codes)
            user_input = prompt(
                HTML("\n<ansigreen><b>You:</b></ansigreen> "),
                multiline=True,
                key_bindings=bindings,
                enable_open_in_editor=False,
            )
            return user_input.strip()

        except (EOFError, KeyboardInterrupt):
            raise EOFError()

    def print_separator(self):
        """Print a visual separator."""
        self.console.print(Rule(style="dim"))

    def print_thinking(self):
        """Show thinking indicator."""
        self.console.print("\n[cyan]Agent:[/cyan] [dim]thinking...[/dim]", end="")

    def print_agent_text(self, text: str, stream: bool = False):
        """
        Print agent response text.

        Args:
            text: Text to print
            stream: If True, append to current streaming output
        """
        if stream:
            # For streaming, just print without newline
            self.console.print(f"\r[cyan]Agent:[/cyan] {text}", end="")
        else:
            # For complete messages
            self.console.print(f"\n[cyan]Agent:[/cyan] {text}")

    def print_markdown(self, markdown_text: str):
        """Render markdown content."""
        self.console.print()
        self.console.print(Markdown(markdown_text))

    def print_code(self, code: str, language: str = "python"):
        """Render code with syntax highlighting."""
        self.console.print()
        self.console.print(Syntax(code, language, theme="monokai", line_numbers=True))

    def print_error(self, error_msg: str):
        """Display error message."""
        self.console.print(f"\n[bold red]Error:[/bold red] {error_msg}")

    def print_success(self, msg: str):
        """Display success message."""
        self.console.print(f"\n[bold green]✓[/bold green] {msg}")

    def print_info(self, msg: str):
        """Display info message."""
        self.console.print(f"\n[bold blue]ℹ[/bold blue] {msg}")

    def clear_screen(self):
        """Clear the terminal screen."""
        self.console.clear()

    def print_session_summary(self, duration_s: float, turns: int, cost_usd: float = None):
        """Display session completion summary."""
        self.console.print()
        self.console.print(Panel(
            f"[green]✅ Completed[/green]\n"
            f"⏱ Duration: {duration_s:.2f}s\n"
            f"🔄 Turns: {turns}\n"
            + (f"💰 Cost: ${cost_usd:.4f}" if cost_usd else ""),
            border_style="green"
        ))

    def print_tool_use(self, tool_name: str, tool_input: dict = None):
        """Indicate tool usage with parameters."""
        # Shorten crawl4ai tool names for readability
        display_name = tool_name.replace("mcp__crawler__", "")

        if tool_input:
            # Show key parameters only
            params = []
            if "url" in tool_input:
                url = tool_input["url"]
                # Truncate long URLs
                if len(url) > 50:
                    url = url[:47] + "..."
                params.append(f"[dim]url=[/dim]{url}")
            if "session_id" in tool_input:
                params.append(f"[dim]session=[/dim]{tool_input['session_id']}")
            if "file_path" in tool_input:
                params.append(f"[dim]file=[/dim]{tool_input['file_path']}")
            if "output_format" in tool_input:
                params.append(f"[dim]format=[/dim]{tool_input['output_format']}")

            param_str = ", ".join(params) if params else ""
            self.console.print(f"  [yellow]🔧 {display_name}[/yellow]({param_str})")
        else:
            self.console.print(f"  [yellow]🔧 {display_name}[/yellow]")

    def with_spinner(self, text: str = "Processing..."):
        """
        Context manager for showing a spinner.

        Usage:
            with ui.with_spinner("Crawling page..."):
                # do work
        """
        return self.console.status(f"[cyan]{text}[/cyan]", spinner="dots")
