"""
Crawl4AI Server CLI Commands

Provides `cnode` command group for Docker orchestration.
"""

import click
import anyio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from cnode_pkg.server_manager import ServerManager


console = Console()


@click.group()
def cli():
    """Manage Crawl4AI Docker server instances

    \b
    One-command deployment with automatic scaling:
      • Single container for development (N=1)
      • Docker Swarm for production with built-in load balancing (N>1)
      • Docker Compose + Nginx as fallback (N>1)

    \b
    Examples:
      cnode start                    # Single container on port 11235
      cnode start --replicas 3       # Auto-detect Swarm or Compose
      cnode start -r 5 --port 8080   # 5 replicas on custom port
      cnode status                   # Check current deployment
      cnode scale 10                 # Scale to 10 replicas
      cnode stop                     # Stop and cleanup
    """
    pass


@cli.command("start")
@click.option(
    "--replicas", "-r",
    type=int,
    default=1,
    help="Number of container replicas (default: 1)"
)
@click.option(
    "--mode",
    type=click.Choice(["auto", "single", "swarm", "compose"]),
    default="auto",
    help="Deployment mode (default: auto-detect)"
)
@click.option(
    "--port", "-p",
    type=int,
    default=11235,
    help="External port to expose (default: 11235)"
)
@click.option(
    "--env-file",
    type=click.Path(exists=True),
    help="Path to environment file"
)
@click.option(
    "--image",
    default="unclecode/crawl4ai:latest",
    help="Docker image to use (default: unclecode/crawl4ai:latest)"
)
def start_cmd(replicas: int, mode: str, port: int, env_file: str, image: str):
    """Start Crawl4AI server with automatic orchestration.

    Deployment modes:
    - auto: Automatically choose best mode (default)
    - single: Single container (N=1 only)
    - swarm: Docker Swarm with built-in load balancing
    - compose: Docker Compose + Nginx reverse proxy

    The server will:
    1. Check if Docker is running
    2. Validate port availability
    3. Pull image if needed
    4. Start container(s) with health checks
    5. Save state for management

    Examples:
        # Development: single container
        cnode start

        # Production: 5 replicas with Swarm
        cnode start --replicas 5

        # Custom configuration
        cnode start -r 3 --port 8080 --env-file .env.prod
    """
    manager = ServerManager()

    console.print(Panel(
        f"[cyan]Starting Crawl4AI Server[/cyan]\n\n"
        f"Replicas: [yellow]{replicas}[/yellow]\n"
        f"Mode: [yellow]{mode}[/yellow]\n"
        f"Port: [yellow]{port}[/yellow]\n"
        f"Image: [yellow]{image}[/yellow]",
        title="Server Start",
        border_style="cyan"
    ))

    with console.status("[cyan]Starting server..."):
        async def _start():
            return await manager.start(
                replicas=replicas,
                mode=mode,
                port=port,
                env_file=env_file,
                image=image
            )
        result = anyio.run(_start)

    if result["success"]:
        console.print(Panel(
            f"[green]✓ Server started successfully![/green]\n\n"
            f"Mode: [cyan]{result.get('state_data', {}).get('mode', mode)}[/cyan]\n"
            f"URL: [bold]http://localhost:{port}[/bold]\n"
            f"Health: [bold]http://localhost:{port}/health[/bold]\n"
            f"Monitor: [bold]http://localhost:{port}/monitor[/bold]",
            title="Server Running",
            border_style="green"
        ))
    else:
        error_msg = result.get("error", result.get("message", "Unknown error"))
        console.print(Panel(
            f"[red]✗ Failed to start server[/red]\n\n"
            f"{error_msg}",
            title="Error",
            border_style="red"
        ))

        if "already running" in error_msg.lower():
            console.print("\n[yellow]Hint: Use 'cnode status' to check current deployment[/yellow]")
            console.print("[yellow]      Use 'cnode stop' to stop existing server[/yellow]")


@cli.command("status")
def status_cmd():
    """Show current server status and deployment info.

    Displays:
    - Running state (up/down)
    - Deployment mode (single/swarm/compose)
    - Number of replicas
    - Port mapping
    - Uptime
    - Image version

    Example:
        cnode status
    """
    manager = ServerManager()

    async def _status():
        return await manager.status()
    result = anyio.run(_status)

    if result["running"]:
        table = Table(title="Crawl4AI Server Status", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Status", "🟢 Running")
        table.add_row("Mode", result["mode"])
        table.add_row("Replicas", str(result.get("replicas", 1)))
        table.add_row("Port", str(result.get("port", 11235)))
        table.add_row("Image", result.get("image", "unknown"))
        table.add_row("Uptime", result.get("uptime", "unknown"))
        table.add_row("Started", result.get("started_at", "unknown"))

        console.print(table)
        console.print(f"\n[green]✓ Server is healthy[/green]")
        console.print(f"[dim]Access: http://localhost:{result.get('port', 11235)}[/dim]")
    else:
        console.print(Panel(
            f"[yellow]No server is currently running[/yellow]\n\n"
            f"Use 'cnode start' to launch a server",
            title="Server Status",
            border_style="yellow"
        ))


@cli.command("stop")
@click.option(
    "--remove-volumes",
    is_flag=True,
    help="Remove associated volumes (WARNING: deletes data)"
)
def stop_cmd(remove_volumes: bool):
    """Stop running Crawl4AI server and cleanup resources.

    This will:
    1. Stop all running containers/services
    2. Remove containers
    3. Optionally remove volumes (--remove-volumes)
    4. Clean up state files

    WARNING: Use --remove-volumes with caution as it will delete
    persistent data including Redis databases and logs.

    Examples:
        # Stop server, keep volumes
        cnode stop

        # Stop and remove all data
        cnode stop --remove-volumes
    """
    manager = ServerManager()

    # Confirm if removing volumes
    if remove_volumes:
        if not Confirm.ask(
            "[red]⚠️  This will delete all server data including Redis databases. Continue?[/red]"
        ):
            console.print("[yellow]Cancelled[/yellow]")
            return

    with console.status("[cyan]Stopping server..."):
        async def _stop():
            return await manager.stop(remove_volumes=remove_volumes)
        result = anyio.run(_stop)

    if result["success"]:
        console.print(Panel(
            f"[green]✓ Server stopped successfully[/green]\n\n"
            f"{result.get('message', 'All resources cleaned up')}",
            title="Server Stopped",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]✗ Error stopping server[/red]\n\n"
            f"{result.get('error', result.get('message', 'Unknown error'))}",
            title="Error",
            border_style="red"
        ))


@cli.command("scale")
@click.argument("replicas", type=int)
def scale_cmd(replicas: int):
    """Scale server to specified number of replicas.

    Only works with Swarm or Compose modes. Single container
    mode cannot be scaled (must stop and restart with --replicas).

    Scaling is live and does not require downtime. The load
    balancer will automatically distribute traffic to new replicas.

    Examples:
        # Scale up to 10 replicas
        cnode scale 10

        # Scale down to 2 replicas
        cnode scale 2

        # Scale to 1 (minimum)
        cnode scale 1
    """
    if replicas < 1:
        console.print("[red]Error: Replicas must be at least 1[/red]")
        return

    manager = ServerManager()

    with console.status(f"[cyan]Scaling to {replicas} replicas..."):
        async def _scale():
            return await manager.scale(replicas=replicas)
        result = anyio.run(_scale)

    if result["success"]:
        console.print(Panel(
            f"[green]✓ Scaled successfully[/green]\n\n"
            f"New replica count: [bold]{replicas}[/bold]\n"
            f"Mode: [cyan]{result.get('mode')}[/cyan]",
            title="Scaling Complete",
            border_style="green"
        ))
    else:
        error_msg = result.get("error", result.get("message", "Unknown error"))
        console.print(Panel(
            f"[red]✗ Scaling failed[/red]\n\n"
            f"{error_msg}",
            title="Error",
            border_style="red"
        ))

        if "single container" in error_msg.lower():
            console.print("\n[yellow]Hint: For single container mode:[/yellow]")
            console.print("[yellow]  1. cnode stop[/yellow]")
            console.print(f"[yellow]  2. cnode start --replicas {replicas}[/yellow]")


@cli.command("logs")
@click.option(
    "--follow", "-f",
    is_flag=True,
    help="Follow log output (like tail -f)"
)
@click.option(
    "--tail",
    type=int,
    default=100,
    help="Number of lines to show (default: 100)"
)
def logs_cmd(follow: bool, tail: int):
    """View server logs.

    Shows logs from running containers/services. Use --follow
    to stream logs in real-time.

    Examples:
        # Show last 100 lines
        cnode logs

        # Show last 500 lines
        cnode logs --tail 500

        # Follow logs in real-time
        cnode logs --follow

        # Combine options
        cnode logs -f --tail 50
    """
    manager = ServerManager()

    async def _logs():
        return await manager.logs(follow=follow, tail=tail)
    output = anyio.run(_logs)
    console.print(output)


@cli.command("cleanup")
@click.option(
    "--force",
    is_flag=True,
    help="Force cleanup even if state file doesn't exist"
)
def cleanup_cmd(force: bool):
    """Force cleanup of all Crawl4AI Docker resources.

    Stops and removes all containers, networks, and optionally volumes.
    Useful when server is stuck or state is corrupted.

    Examples:
        # Clean up everything
        cnode cleanup

        # Force cleanup (ignore state file)
        cnode cleanup --force
    """
    manager = ServerManager()

    console.print(Panel(
        f"[yellow]⚠️  Cleaning up Crawl4AI Docker resources[/yellow]\n\n"
        f"This will stop and remove:\n"
        f"- All Crawl4AI containers\n"
        f"- Nginx load balancer\n"
        f"- Redis instance\n"
        f"- Docker networks\n"
        f"- State files",
        title="Cleanup",
        border_style="yellow"
    ))

    if not force and not Confirm.ask("[yellow]Continue with cleanup?[/yellow]"):
        console.print("[yellow]Cancelled[/yellow]")
        return

    with console.status("[cyan]Cleaning up resources..."):
        async def _cleanup():
            return await manager.cleanup(force=force)
        result = anyio.run(_cleanup)

    if result["success"]:
        console.print(Panel(
            f"[green]✓ Cleanup completed successfully[/green]\n\n"
            f"Removed: {result.get('removed', 0)} containers\n"
            f"{result.get('message', 'All resources cleaned up')}",
            title="Cleanup Complete",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[yellow]⚠️  Partial cleanup[/yellow]\n\n"
            f"{result.get('message', 'Some resources may still exist')}",
            title="Cleanup Status",
            border_style="yellow"
        ))


@cli.command("restart")
@click.option(
    "--replicas", "-r",
    type=int,
    help="New replica count (optional)"
)
def restart_cmd(replicas: int):
    """Restart server (stop then start with same config).

    Preserves existing configuration unless overridden with options.
    Useful for applying image updates or recovering from errors.

    Examples:
        # Restart with same configuration
        cnode restart

        # Restart and change replica count
        cnode restart --replicas 5
    """
    manager = ServerManager()

    # Get current state
    async def _get_status():
        return await manager.status()
    current = anyio.run(_get_status)

    if not current["running"]:
        console.print("[yellow]No server is running. Use 'cnode start' instead.[/yellow]")
        return

    # Extract current config
    current_replicas = current.get("replicas", 1)
    current_port = current.get("port", 11235)
    current_image = current.get("image", "unclecode/crawl4ai:latest")
    current_mode = current.get("mode", "auto")

    # Override with CLI args
    new_replicas = replicas if replicas is not None else current_replicas

    console.print(Panel(
        f"[cyan]Restarting Crawl4AI Server[/cyan]\n\n"
        f"Replicas: [yellow]{current_replicas}[/yellow] → [green]{new_replicas}[/green]\n"
        f"Port: [yellow]{current_port}[/yellow]\n"
        f"Mode: [yellow]{current_mode}[/yellow]",
        title="Server Restart",
        border_style="cyan"
    ))

    # Stop current
    with console.status("[cyan]Stopping current server..."):
        async def _stop_server():
            return await manager.stop(remove_volumes=False)
        stop_result = anyio.run(_stop_server)

    if not stop_result["success"]:
        console.print(f"[red]Failed to stop server: {stop_result.get('error')}[/red]")
        return

    # Start new
    with console.status("[cyan]Starting server..."):
        async def _start_server():
            return await manager.start(
                replicas=new_replicas,
                mode="auto",
                port=current_port,
                image=current_image
            )
        start_result = anyio.run(_start_server)

    if start_result["success"]:
        console.print(Panel(
            f"[green]✓ Server restarted successfully![/green]\n\n"
            f"URL: [bold]http://localhost:{current_port}[/bold]",
            title="Restart Complete",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]✗ Failed to restart server[/red]\n\n"
            f"{start_result.get('error', 'Unknown error')}",
            title="Error",
            border_style="red"
        ))


def main():
    """Entry point for cnode CLI"""
    cli()


if __name__ == "__main__":
    main()

# Test comment
