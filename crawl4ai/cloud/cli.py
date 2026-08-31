"""
Crawl4AI Cloud CLI - Commands for interacting with Crawl4AI Cloud service.

Commands:
  crwl cloud auth          - Authenticate with API key
  crwl cloud profiles upload - Upload a profile to cloud
  crwl cloud profiles list   - List cloud profiles
  crwl cloud profiles delete - Delete a cloud profile
"""

import click
import httpx
import os
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from crawl4ai import BrowserProfiler
from crawl4ai.browser_profiler import ShrinkLevel, _format_size

console = Console()

# Default cloud API URL
DEFAULT_CLOUD_API_URL = "https://api.crawl4ai.com"


def get_global_config() -> dict:
    """Load global config from ~/.crawl4ai/global.yml"""
    config_file = Path.home() / ".crawl4ai" / "global.yml"
    if not config_file.exists():
        return {}
    with open(config_file) as f:
        return yaml.safe_load(f) or {}


def save_global_config(config: dict):
    """Save global config to ~/.crawl4ai/global.yml"""
    config_dir = Path.home() / ".crawl4ai"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "global.yml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)


def get_cloud_config() -> tuple[str, str]:
    """Get cloud API key and URL from config."""
    config = get_global_config()
    api_key = config.get("CLOUD_API_KEY")
    api_url = config.get("CLOUD_API_URL", DEFAULT_CLOUD_API_URL)
    return api_key, api_url


def require_auth() -> tuple[str, str]:
    """Require authentication, exit if not configured."""
    api_key, api_url = get_cloud_config()
    if not api_key:
        console.print("[red]Not authenticated with Crawl4AI Cloud.[/red]")
        console.print("\nRun [cyan]crwl cloud auth[/cyan] to authenticate.")
        sys.exit(1)
    return api_key, api_url


# ==================== Cloud Command Group ====================

@click.group("cloud")
def cloud_cmd():
    """Crawl4AI Cloud commands - manage cloud profiles and authentication.

    Use browser profiles for authenticated crawling in the cloud.

    Getting started:
      1. Get an API key at https://api.crawl4ai.com/dashboard
      2. Run: crwl cloud auth
      3. Create a local profile: crwl profiles
      4. Upload to cloud: crwl cloud profiles upload my_profile
    """
    pass


# ==================== Auth Commands ====================

@cloud_cmd.command("auth")
@click.option("--api-key", "-k", help="API key (will prompt if not provided)")
@click.option("--api-url", "-u", help=f"API URL (default: {DEFAULT_CLOUD_API_URL})")
@click.option("--logout", is_flag=True, help="Remove saved credentials")
@click.option("--status", is_flag=True, help="Show current auth status")
def auth_cmd(api_key: str, api_url: str, logout: bool, status: bool):
    """Authenticate with Crawl4AI Cloud.

    Your API key is saved locally in ~/.crawl4ai/global.yml

    To get an API key:
      1. Go to https://api.crawl4ai.com/dashboard
      2. Sign in or create an account
      3. Navigate to API Keys section
      4. Create a new key and copy it

    Examples:
      crwl cloud auth                    # Interactive authentication
      crwl cloud auth --api-key sk_...   # Provide key directly
      crwl cloud auth --status           # Check current status
      crwl cloud auth --logout           # Remove saved credentials
    """
    config = get_global_config()

    if status:
        current_key = config.get("CLOUD_API_KEY")
        current_url = config.get("CLOUD_API_URL", DEFAULT_CLOUD_API_URL)

        if current_key:
            # Mask the key for display
            masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
            console.print(Panel(
                f"[green]Authenticated[/green]\n\n"
                f"API Key: [cyan]{masked}[/cyan]\n"
                f"API URL: [blue]{current_url}[/blue]",
                title="Cloud Auth Status",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[yellow]Not authenticated[/yellow]\n\n"
                "Run [cyan]crwl cloud auth[/cyan] to authenticate.\n\n"
                "Get your API key at:\n"
                "[blue]https://api.crawl4ai.com/dashboard[/blue]",
                title="Cloud Auth Status",
                border_style="yellow"
            ))
        return

    if logout:
        if "CLOUD_API_KEY" in config:
            del config["CLOUD_API_KEY"]
            save_global_config(config)
            console.print("[green]Logged out successfully.[/green]")
        else:
            console.print("[yellow]Not currently authenticated.[/yellow]")
        return

    # Interactive auth
    if not api_key:
        console.print(Panel(
            "[cyan]Crawl4AI Cloud Authentication[/cyan]\n\n"
            "To get your API key:\n"
            "  1. Go to [blue]https://api.crawl4ai.com/dashboard[/blue]\n"
            "  2. Sign in or create an account\n"
            "  3. Navigate to API Keys section\n"
            "  4. Create a new key and paste it below",
            title="Setup",
            border_style="cyan"
        ))
        api_key = click.prompt("\nEnter your API key", hide_input=True)

    if not api_key:
        console.print("[red]API key is required.[/red]")
        sys.exit(1)

    # Validate the key by making a test request
    test_url = api_url or config.get("CLOUD_API_URL", DEFAULT_CLOUD_API_URL)

    console.print("\n[dim]Validating API key...[/dim]")

    try:
        response = httpx.get(
            f"{test_url}/v1/profiles",
            headers={"X-API-Key": api_key},
            timeout=10.0
        )

        if response.status_code == 401:
            console.print("[red]Invalid API key.[/red]")
            sys.exit(1)
        elif response.status_code != 200:
            console.print(f"[red]Error validating key: {response.status_code}[/red]")
            sys.exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        sys.exit(1)

    # Save to config
    config["CLOUD_API_KEY"] = api_key
    if api_url:
        config["CLOUD_API_URL"] = api_url
    save_global_config(config)

    console.print("[green]Authentication successful![/green]")
    console.print(f"Credentials saved to [cyan]~/.crawl4ai/global.yml[/cyan]")


# ==================== Profiles Command Group ====================

@cloud_cmd.group("profiles")
def profiles_cmd():
    """Manage cloud browser profiles.

    Upload local browser profiles to Crawl4AI Cloud for authenticated crawling.

    Workflow:
      1. Create a local profile: crwl profiles
      2. Shrink it (optional): crwl shrink my_profile
      3. Upload to cloud: crwl cloud profiles upload my_profile
      4. Use in API: {"browser_config": {"profile_id": "..."}}
    """
    pass


@profiles_cmd.command("upload")
@click.argument("profile_name")
@click.option("--name", "-n", help="Cloud profile name (defaults to local name)")
@click.option("--level", "-l",
              type=click.Choice(["light", "medium", "aggressive", "minimal"]),
              default="aggressive",
              help="Shrink level before upload (default: aggressive)")
@click.option("--no-shrink", is_flag=True, help="Skip shrinking (upload as-is)")
def upload_cmd(profile_name: str, name: str, level: str, no_shrink: bool):
    """Upload a browser profile to Crawl4AI Cloud.

    The profile will be shrunk to remove caches before uploading.
    Use --no-shrink to upload the profile as-is.

    Examples:
      crwl cloud profiles upload my_profile
      crwl cloud profiles upload my_profile --name github-auth
      crwl cloud profiles upload my_profile --level minimal
      crwl cloud profiles upload my_profile --no-shrink
    """
    api_key, api_url = require_auth()

    # Find the profile
    profiler = BrowserProfiler()
    profile_path = profiler.get_profile_path(profile_name)

    if not profile_path:
        console.print(f"[red]Profile not found: {profile_name}[/red]")
        console.print("\nAvailable profiles:")
        for p in profiler.list_profiles():
            console.print(f"  - {p['name']}")
        sys.exit(1)

    cloud_name = name or profile_name

    console.print(f"\n[cyan]Uploading profile:[/cyan] {profile_name}")
    console.print(f"[cyan]Cloud name:[/cyan] {cloud_name}")

    # Step 1: Shrink (unless --no-shrink)
    if not no_shrink:
        console.print(f"\n[dim][1/4] Shrinking profile ({level})...[/dim]")
        try:
            result = profiler.shrink(profile_name, ShrinkLevel(level), dry_run=False)
            console.print(f"      Freed: {_format_size(result['bytes_freed'])}")
            if result.get("size_after"):
                console.print(f"      Size: {_format_size(result['size_after'])}")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not shrink profile: {e}[/yellow]")
    else:
        console.print("\n[dim][1/4] Skipping shrink...[/dim]")

    # Step 2: Package as tar.gz
    console.print("[dim][2/4] Packaging profile...[/dim]")

    temp_dir = Path(tempfile.mkdtemp(prefix="crawl4ai_upload_"))
    tar_path = temp_dir / f"{cloud_name}.tar.gz"

    try:
        with tarfile.open(tar_path, "w:gz") as tar:
            # Add profile contents (not the directory itself)
            for item in Path(profile_path).iterdir():
                tar.add(item, arcname=item.name)

        size_bytes = tar_path.stat().st_size
        console.print(f"      Created: {tar_path.name} ({_format_size(size_bytes)})")

        # Step 3: Upload
        console.print("[dim][3/4] Uploading to cloud...[/dim]")

        with open(tar_path, "rb") as f:
            response = httpx.post(
                f"{api_url}/v1/profiles",
                headers={"X-API-Key": api_key},
                files={"file": (f"{cloud_name}.tar.gz", f, "application/gzip")},
                data={"name": cloud_name},
                timeout=120.0
            )

        if response.status_code == 409:
            console.print(f"[red]Profile '{cloud_name}' already exists in cloud.[/red]")
            console.print("Use --name to specify a different name, or delete the existing profile first.")
            sys.exit(1)
        elif response.status_code == 400:
            error = response.json().get("detail", "Unknown error")
            console.print(f"[red]Upload rejected: {error}[/red]")
            sys.exit(1)
        elif response.status_code != 200:
            console.print(f"[red]Upload failed: {response.status_code}[/red]")
            console.print(response.text)
            sys.exit(1)

        result = response.json()
        profile_id = result["id"]

        console.print("[dim][4/4] Done![/dim]")

        # Success output
        console.print(Panel(
            f"[green]Profile uploaded successfully![/green]\n\n"
            f"Profile ID: [cyan]{profile_id}[/cyan]\n"
            f"Name: [blue]{cloud_name}[/blue]\n"
            f"Size: {_format_size(size_bytes)}\n\n"
            f"[dim]Use in API:[/dim]\n"
            f'  {{"browser_config": {{"profile_id": "{profile_id}"}}}}',
            title="Upload Complete",
            border_style="green"
        ))

        if result.get("scan_warnings"):
            console.print("\n[yellow]Scan warnings:[/yellow]")
            for warning in result["scan_warnings"]:
                console.print(f"  - {warning}")

    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


@profiles_cmd.command("list")
def list_cmd():
    """List all cloud profiles.

    Shows all profiles uploaded to your Crawl4AI Cloud account.
    """
    api_key, api_url = require_auth()

    console.print("\n[dim]Fetching profiles...[/dim]")

    try:
        response = httpx.get(
            f"{api_url}/v1/profiles",
            headers={"X-API-Key": api_key},
            timeout=30.0
        )

        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/red]")
            console.print(response.text)
            sys.exit(1)

        data = response.json()
        profiles = data.get("profiles", [])

        if not profiles:
            console.print(Panel(
                "[yellow]No cloud profiles found.[/yellow]\n\n"
                "Upload a profile with:\n"
                "  [cyan]crwl cloud profiles upload <profile_name>[/cyan]",
                title="Cloud Profiles",
                border_style="yellow"
            ))
            return

        # Create table
        table = Table(title="Cloud Profiles")
        table.add_column("Name", style="cyan")
        table.add_column("Profile ID", style="dim")
        table.add_column("Size", justify="right")
        table.add_column("Created", style="green")
        table.add_column("Last Used", style="blue")

        for p in profiles:
            size = _format_size(p.get("size_bytes", 0)) if p.get("size_bytes") else "-"
            created = p.get("created_at", "-")[:10] if p.get("created_at") else "-"
            last_used = p.get("last_used_at", "-")[:10] if p.get("last_used_at") else "Never"

            table.add_row(
                p["name"],
                p["id"][:8] + "...",
                size,
                created,
                last_used
            )

        console.print(table)
        console.print(f"\nTotal: {len(profiles)} profile(s)")

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        sys.exit(1)


@profiles_cmd.command("delete")
@click.argument("profile_name_or_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete_cmd(profile_name_or_id: str, yes: bool):
    """Delete a cloud profile.

    You can specify either the profile name or ID.

    Examples:
      crwl cloud profiles delete my_profile
      crwl cloud profiles delete abc123...
      crwl cloud profiles delete my_profile --yes
    """
    api_key, api_url = require_auth()

    # First, try to find the profile
    console.print("\n[dim]Finding profile...[/dim]")

    try:
        # List profiles to find by name
        response = httpx.get(
            f"{api_url}/v1/profiles",
            headers={"X-API-Key": api_key},
            timeout=30.0
        )

        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/red]")
            sys.exit(1)

        profiles = response.json().get("profiles", [])

        # Find matching profile
        profile = None
        for p in profiles:
            if p["name"] == profile_name_or_id or p["id"] == profile_name_or_id or p["id"].startswith(profile_name_or_id):
                profile = p
                break

        if not profile:
            console.print(f"[red]Profile not found: {profile_name_or_id}[/red]")
            console.print("\nAvailable profiles:")
            for p in profiles:
                console.print(f"  - {p['name']} ({p['id'][:8]}...)")
            sys.exit(1)

        # Confirm deletion
        console.print(f"\nProfile: [cyan]{profile['name']}[/cyan]")
        console.print(f"ID: [dim]{profile['id']}[/dim]")

        if not yes:
            if not click.confirm("\nAre you sure you want to delete this profile?"):
                console.print("[yellow]Cancelled.[/yellow]")
                return

        # Delete
        console.print("\n[dim]Deleting...[/dim]")

        response = httpx.delete(
            f"{api_url}/v1/profiles/{profile['id']}",
            headers={"X-API-Key": api_key},
            timeout=30.0
        )

        if response.status_code == 404:
            console.print("[red]Profile not found (may have been already deleted).[/red]")
            sys.exit(1)
        elif response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/red]")
            console.print(response.text)
            sys.exit(1)

        console.print(f"[green]Profile '{profile['name']}' deleted successfully.[/green]")

    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        sys.exit(1)
