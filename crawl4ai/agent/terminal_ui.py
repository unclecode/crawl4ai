"""Terminal UI components using Rich for beautiful agent output."""

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule


class TerminalUI:
    """Rich-based terminal interface for the Crawl4AI agent."""

    def __init__(self):
        self.console = Console()
        self._current_text = ""

    def show_header(self, session_id: str, log_path: str):
        """Display agent session header."""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]🕷️  Crawl4AI Agent - Chat Mode[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print(f"[dim]📁 Session: {session_id}[/dim]")
        self.console.print(f"[dim]💾 Log: {log_path}[/dim]")
        self.console.print()

    def show_commands(self):
        """Display available commands."""
        self.console.print("\n[dim]Commands:[/dim]")
        self.console.print("  [cyan]/exit[/cyan] - Exit chat")
        self.console.print("  [cyan]/clear[/cyan] - Clear screen")
        self.console.print("  [cyan]/help[/cyan] - Show this help\n")

    def get_user_input(self) -> str:
        """Get user input with styled prompt."""
        return Prompt.ask("\n[bold green]You[/bold green]")

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

    def print_tool_use(self, tool_name: str):
        """Indicate tool usage."""
        self.console.print(f"\n[dim]🔧 Using tool: {tool_name}[/dim]")

    def with_spinner(self, text: str = "Processing..."):
        """
        Context manager for showing a spinner.

        Usage:
            with ui.with_spinner("Crawling page..."):
                # do work
        """
        return self.console.status(f"[cyan]{text}[/cyan]", spinner="dots")
