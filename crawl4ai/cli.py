import click
import os
import sys
import time

import humanize
from typing import Dict, Any, Optional, List
import json
import yaml
import anyio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from crawl4ai import (
    CacheMode,
    AsyncWebCrawler, 
    CrawlResult,
    BrowserConfig, 
    CrawlerRunConfig,
    LLMExtractionStrategy, 
    LXMLWebScrapingStrategy,
    JsonCssExtractionStrategy,
    JsonXPathExtractionStrategy,
    BM25ContentFilter, 
    PruningContentFilter,
    BrowserProfiler,
    DefaultMarkdownGenerator,
    LLMConfig
)
from crawl4ai.config import USER_SETTINGS
from litellm import completion
from pathlib import Path


# Initialize rich console
console = Console()

def get_global_config() -> dict:
    config_dir = Path.home() / ".crawl4ai"
    config_file = config_dir / "global.yml"
    
    if not config_file.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        return {}
        
    with open(config_file) as f:
        return yaml.safe_load(f) or {}

def save_global_config(config: dict):
    config_file = Path.home() / ".crawl4ai" / "global.yml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)

def setup_llm_config() -> tuple[str, str]:
    config = get_global_config()
    provider = config.get("DEFAULT_LLM_PROVIDER")
    token = config.get("DEFAULT_LLM_PROVIDER_TOKEN")
    
    if not provider:
        click.echo("\nNo default LLM provider configured.")
        click.echo("Provider format: 'company/model' (e.g., 'openai/gpt-4o', 'anthropic/claude-3-sonnet')")
        click.echo("See available providers at: https://docs.litellm.ai/docs/providers")
        provider = click.prompt("Enter provider")
        
    if not provider.startswith("ollama/"):
        if not token:
            token = click.prompt("Enter API token for " + provider, hide_input=True)
    else:
        token = "no-token"
    
    if not config.get("DEFAULT_LLM_PROVIDER") or not config.get("DEFAULT_LLM_PROVIDER_TOKEN"):
        config["DEFAULT_LLM_PROVIDER"] = provider
        config["DEFAULT_LLM_PROVIDER_TOKEN"] = token
        save_global_config(config)
        click.echo("\nConfiguration saved to ~/.crawl4ai/global.yml")
    
    return provider, token

async def stream_llm_response(url: str, markdown: str, query: str, provider: str, token: str):
    response = completion(
        model=provider,
        api_key=token,
        messages=[
            {
                "content": f"You are Crawl4ai assistant, answering user question based on the provided context which is crawled from {url}.",
                "role": "system"
            },
            {
                "content": f"<|start of context|>\n{markdown}\n<|end of context|>\n\n{query}",
                "role": "user"
            },
        ],
        stream=True,
    )
    
    for chunk in response:
        if content := chunk["choices"][0]["delta"].get("content"):
            print(content, end="", flush=True)
    print()  # New line at end



def parse_key_values(ctx, param, value) -> Dict[str, Any]:
    if not value:
        return {}
    result = {}
    pairs = value.split(',')
    for pair in pairs:
        try:
            k, v = pair.split('=', 1)
            # Handle common value types 
            if v.lower() == 'true': v = True
            elif v.lower() == 'false': v = False
            elif v.isdigit(): v = int(v)
            elif v.replace('.','',1).isdigit(): v = float(v)
            elif v.startswith('[') and v.endswith(']'):
                v = [x.strip() for x in v[1:-1].split(',') if x.strip()]
            elif v.startswith('{') and v.endswith('}'):
                try:
                    v = json.loads(v)
                except json.JSONDecodeError:
                    raise click.BadParameter(f'Invalid JSON object: {v}')
            result[k.strip()] = v
        except ValueError:
            raise click.BadParameter(f'Invalid key=value pair: {pair}')
    return result

def load_config_file(path: Optional[str]) -> dict:
    if not path:
        return {}
    
    try:
        with open(path) as f:
            if path.endswith((".yaml", ".yml")):
                return yaml.safe_load(f)
            return json.load(f)
    except Exception as e:
        raise click.BadParameter(f'Error loading config file {path}: {str(e)}')

def load_schema_file(path: Optional[str]) -> dict:
    if not path:
        return None
    return load_config_file(path)

async def run_crawler(url: str, browser_cfg: BrowserConfig, crawler_cfg: CrawlerRunConfig, verbose: bool):
    if verbose:
        click.echo("Starting crawler with configurations:")
        click.echo(f"Browser config: {browser_cfg.dump()}")
        click.echo(f"Crawler config: {crawler_cfg.dump()}")

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        try:
            result = await crawler.arun(url=url, config=crawler_cfg)
            return result
        except Exception as e:
            raise click.ClickException(f"Crawling failed: {str(e)}")

def show_examples():
    examples = """
🚀 Crawl4AI CLI Examples

1️⃣  Basic Usage:
    # Simple crawl with default settings
    crwl https://example.com

    # Get markdown output
    crwl https://example.com -o markdown

    # Verbose JSON output with cache bypass
    crwl https://example.com -o json -v --bypass-cache

2️⃣  Using Config Files:
    # Using browser and crawler configs
    crwl https://example.com -B browser.yml -C crawler.yml

    # CSS-based extraction
    crwl https://example.com -e extract_css.yml -s css_schema.json -o json

    # LLM-based extraction with config file
    crwl https://example.com -e extract_llm.yml -s llm_schema.json -o json
    
    # Quick LLM-based JSON extraction (prompts for LLM provider first time)
    crwl https://example.com -j  # Auto-extracts structured data
    crwl https://example.com -j "Extract product details including name, price, and features"  # With specific instructions

3️⃣  Direct Parameters:
    # Browser settings
    crwl https://example.com -b "headless=true,viewport_width=1280,user_agent_mode=random"

    # Crawler settings
    crwl https://example.com -c "css_selector=#main,delay_before_return_html=2,scan_full_page=true"

4️⃣  Profile Management for Identity-Based Crawling:
    # Launch interactive profile manager
    crwl profiles

    # Create, list, and delete browser profiles for identity-based crawling
    # Use a profile for crawling (keeps you logged in)
    crwl https://example.com -p my-profile-name

    # Example: Crawl a site that requires login
    # 1. First create a profile and log in:
    crwl profiles
    # 2. Then use that profile to crawl the authenticated site:
    crwl https://site-requiring-login.com/dashboard -p my-profile-name

5️⃣  CDP Mode for Browser Automation:
    # Launch browser with CDP debugging on default port 9222
    crwl cdp

    # Use a specific profile and custom port
    crwl cdp -p my-profile -P 9223

    # Launch headless browser with CDP enabled
    crwl cdp --headless

    # Launch in incognito mode (ignores profile)
    crwl cdp --incognito

    # Use the CDP URL with other tools (Puppeteer, Playwright, etc.)
    # The URL will be displayed in the terminal when the browser starts

    
6️⃣  Sample Config Files:

browser.yml:
    headless: true
    viewport_width: 1280
    user_agent_mode: "random"
    verbose: true
    ignore_https_errors: true

extract_css.yml:
    type: "json-css"
    params:
        verbose: true

css_schema.json:
    {
      "name": "ArticleExtractor",
      "baseSelector": ".article",
      "fields": [
        {
          "name": "title",
          "selector": "h1.title",
          "type": "text"
        },
        {
          "name": "link",
          "selector": "a.read-more",
          "type": "attribute",
          "attribute": "href"
        }
      ]
    }

extract_llm.yml:
    type: "llm"
    provider: "openai/gpt-4"
    instruction: "Extract all articles with their titles and links"
    api_token: "your-token"
    params:
        temperature: 0.3
        max_tokens: 1000

llm_schema.json:
    {
      "title": "Article",
      "type": "object",
      "properties": {
        "title": {
          "type": "string",
          "description": "The title of the article"
        },
        "link": {
          "type": "string",
          "description": "URL to the full article"
        }
      }
    }

7️⃣  Advanced Usage:
    # Combine configs with direct parameters
    crwl https://example.com -B browser.yml -b "headless=false,viewport_width=1920"

    # Full extraction pipeline with config files
    crwl https://example.com \\
        -B browser.yml \\
        -C crawler.yml \\
        -e extract_llm.yml \\
        -s llm_schema.json \\
        -o json \\
        -v
        
    # Quick LLM-based extraction with specific instructions
    crwl https://amazon.com/dp/B01DFKC2SO \\
        -j "Extract product title, current price, original price, rating, and all product specifications" \\
        -b "headless=true,viewport_width=1280" \\
        -v

    # Content filtering with BM25
    crwl https://example.com \\
        -f filter_bm25.yml \\
        -o markdown-fit

    # Authenticated crawling with profile
    crwl https://login-required-site.com \\
        -p my-authenticated-profile \\
        -c "css_selector=.dashboard-content" \\
        -o markdown

For more documentation visit: https://github.com/unclecode/crawl4ai

8️⃣  Q&A with LLM:
    # Ask a question about the content
    crwl https://example.com -q "What is the main topic discussed?"

    # First view content, then ask questions
    crwl https://example.com -o markdown  # See the crawled content first
    crwl https://example.com -q "Summarize the key points"
    crwl https://example.com -q "What are the conclusions?"

    # Advanced crawling with Q&A
    crwl https://example.com \\
        -B browser.yml \\
        -c "css_selector=article,scan_full_page=true" \\
        -q "What are the pros and cons mentioned?"

    Note: First time using -q will prompt for LLM provider and API token.
    These will be saved in ~/.crawl4ai/global.yml for future use.
    
    Supported provider format: 'company/model'
    Examples:
      - ollama/llama3.3
      - openai/gpt-4
      - anthropic/claude-3-sonnet
      - cohere/command
      - google/gemini-pro
    
    See full list of providers: https://docs.litellm.ai/docs/providers
    
    # Set default LLM provider and token in advance
    crwl config set DEFAULT_LLM_PROVIDER "anthropic/claude-3-sonnet"
    crwl config set DEFAULT_LLM_PROVIDER_TOKEN "your-api-token-here"
    
    # Set default browser behavior
    crwl config set BROWSER_HEADLESS false  # Always show browser window
    crwl config set USER_AGENT_MODE random  # Use random user agent

9️⃣ Profile Management:
    # Launch interactive profile manager
    crwl profiles

    # Create a profile and use it for crawling
    crwl profiles  # Create and set up your profile interactively
    crwl https://example.com -p my-profile-name  # Use profile for crawling

    # Example workflow for authenticated site
    # 1. First create a profile and log in to the site:
    crwl profiles  # Select "Create new profile" option
    # 2. Then use that profile to crawl authenticated content:
    crwl https://site-requiring-login.com/dashboard -p my-profile-name

🔄 Builtin Browser Management:
    # Start a builtin browser (runs in the background)
    crwl browser start
    
    # Check builtin browser status
    crwl browser status
    
    # Open a visible window to see the browser
    crwl browser view --url https://example.com
    
    # Stop the builtin browser
    crwl browser stop
    
    # Restart with different options
    crwl browser restart --browser-type chromium --port 9223 --no-headless
    
    # Use the builtin browser in your code
    # (Just set browser_mode="builtin" in your BrowserConfig)
    browser_config = BrowserConfig(
        browser_mode="builtin", 
        headless=True
    )
    
    # Usage via CLI:
    crwl https://example.com -b "browser_mode=builtin"
"""
    click.echo(examples)

def get_directory_size(path: str) -> int:
    """Calculate the total size of a directory in bytes"""
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def display_profiles_table(profiles: List[Dict[str, Any]]):
    """Display a rich table of browser profiles"""
    if not profiles:
        console.print(Panel("[yellow]No profiles found. Create one with the 'create' command.[/yellow]", 
                          title="Browser Profiles", border_style="blue"))
        return
    
    table = Table(title="Browser Profiles", show_header=True, header_style="bold cyan", border_style="blue")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Path", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("Browser", style="magenta")
    table.add_column("Size", style="blue", justify="right")
    
    for i, profile in enumerate(profiles):
        # Calculate folder size
        size = get_directory_size(profile["path"])
        human_size = humanize.naturalsize(size)
        
        # Format creation date
        created = profile["created"].strftime("%Y-%m-%d %H:%M")
        
        # Add row to table
        table.add_row(
            str(i+1), 
            profile["name"], 
            profile["path"], 
            created, 
            profile["type"].capitalize(), 
            human_size
        )
    
    console.print(table)

async def create_profile_interactive(profiler: BrowserProfiler):
    """Interactive profile creation wizard"""
    console.print(Panel("[bold cyan]Create Browser Profile[/bold cyan]\n"
                      "This will open a browser window for you to set up your identity.\n"
                      "Log in to sites, adjust settings, then press 'q' to save.",
                      border_style="cyan"))
    
    profile_name = Prompt.ask("[cyan]Enter profile name[/cyan]", default=f"profile_{int(time.time())}")
    
    console.print("[cyan]Creating profile...[/cyan]")
    console.print("[yellow]A browser window will open. After logging in to sites, press 'q' in this terminal to save.[/yellow]")
    
    # Create the profile
    try:
        profile_path = await profiler.create_profile(profile_name)
        
        if profile_path:
            console.print(f"[green]Profile successfully created at:[/green] {profile_path}")
        else:
            console.print("[red]Failed to create profile.[/red]")
    except Exception as e:
        console.print(f"[red]Error creating profile: {str(e)}[/red]")

def delete_profile_interactive(profiler: BrowserProfiler):
    """Interactive profile deletion"""
    profiles = profiler.list_profiles()
    
    if not profiles:
        console.print("[yellow]No profiles found to delete.[/yellow]")
        return
    
    # Display profiles
    display_profiles_table(profiles)
    
    # Get profile selection
    idx = Prompt.ask(
        "[red]Enter number of profile to delete[/red]", 
        console=console,
        choices=[str(i+1) for i in range(len(profiles))],
        show_choices=False
    )
    
    try:
        idx = int(idx) - 1
        profile = profiles[idx]
        
        # Confirm deletion
        if Confirm.ask(f"[red]Are you sure you want to delete profile '{profile['name']}'?[/red]"):
            success = profiler.delete_profile(profile["path"])
            
            if success:
                console.print(f"[green]Profile '{profile['name']}' deleted successfully.[/green]")
            else:
                console.print(f"[red]Failed to delete profile '{profile['name']}'.[/red]")
    except (ValueError, IndexError):
        console.print("[red]Invalid selection.[/red]")
        
async def crawl_with_profile_cli(profile_path, url):
    """Use a profile to crawl a website via CLI"""
    console.print(f"[cyan]Crawling [bold]{url}[/bold] using profile at [bold]{profile_path}[/bold][/cyan]")
    
    # Create browser config with the profile
    browser_cfg = BrowserConfig(
        headless=False,  # Set to False to see the browser in action
        use_managed_browser=True,
        user_data_dir=profile_path
    )
    
    # Default crawler config
    crawler_cfg = CrawlerRunConfig()
    
    # Ask for output format
    output_format = Prompt.ask(
        "[cyan]Output format[/cyan]",
        choices=["all", "json", "markdown", "md", "title"],
        default="markdown"
    )
    
    try:
        # Run the crawler
        result = await run_crawler(url, browser_cfg, crawler_cfg, True)
        
        # Handle output
        if output_format == "all":
            console.print(json.dumps(result.model_dump(), indent=2))
        elif output_format == "json":
            console.print(json.dumps(json.loads(result.extracted_content), indent=2))
        elif output_format in ["markdown", "md"]:
            console.print(result.markdown.raw_markdown)
        elif output_format == "title":
            console.print(result.metadata.get("title", "No title found"))
        
        console.print(f"[green]Successfully crawled[/green] {url}")
        return result
    except Exception as e:
        console.print(f"[red]Error crawling:[/red] {str(e)}")
        return None
        
async def use_profile_to_crawl():
    """Interactive profile selection for crawling"""
    profiler = BrowserProfiler()
    profiles = profiler.list_profiles()
    
    if not profiles:
        console.print("[yellow]No profiles found. Create one first.[/yellow]")
        return
        
    # Display profiles
    display_profiles_table(profiles)
    
    # Get profile selection
    idx = Prompt.ask(
        "[cyan]Enter number of profile to use[/cyan]", 
        console=console,
        choices=[str(i+1) for i in range(len(profiles))],
        show_choices=False
    )
    
    try:
        idx = int(idx) - 1
        profile = profiles[idx]
        
        # Get URL
        url = Prompt.ask("[cyan]Enter URL to crawl[/cyan]")
        if url:
            # Crawl with the selected profile
            await crawl_with_profile_cli(profile["path"], url)
        else:
            console.print("[red]No URL provided[/red]")
    except (ValueError, IndexError):
        console.print("[red]Invalid selection[/red]")

async def manage_profiles():
    """Interactive profile management menu"""
    profiler = BrowserProfiler()
    
    options = {
        "1": "List profiles",
        "2": "Create new profile",
        "3": "Delete profile",
        "4": "Use a profile to crawl a website",
        "5": "Exit",
    }
    
    while True:
        console.print(Panel("[bold cyan]Browser Profile Manager[/bold cyan]", border_style="cyan"))
        
        for key, value in options.items():
            color = "green" if key == "1" else "yellow" if key == "2" else "red" if key == "3" else "blue" if key == "4" else "cyan"
            console.print(f"[{color}]{key}[/{color}]. {value}")
        
        choice = Prompt.ask("Enter choice", choices=list(options.keys()), default="1")
        
        if choice == "1":
            # List profiles
            profiles = profiler.list_profiles()
            display_profiles_table(profiles)
        
        elif choice == "2":
            # Create profile
            await create_profile_interactive(profiler)
        
        elif choice == "3":
            # Delete profile
            delete_profile_interactive(profiler)
            
        elif choice == "4":
            # Use profile to crawl
            await use_profile_to_crawl()
        
        elif choice == "5":
            # Exit
            console.print("[cyan]Exiting profile manager.[/cyan]")
            break
        
        # Add a separator between operations
        console.print("\n")



@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli():
    """Crawl4AI CLI - Web content extraction and browser profile management tool"""
    pass


@cli.group("browser")
def browser_cmd():
    """Manage browser instances for Crawl4AI
    
    Commands to manage browser instances for Crawl4AI, including:
    - status - Check status of the builtin browser
    - start - Start a new builtin browser
    - stop - Stop the running builtin browser
    - restart - Restart the builtin browser
    """
    pass
    
@browser_cmd.command("status")
def browser_status_cmd():
    """Show status of the builtin browser"""
    profiler = BrowserProfiler()
    
    try:
        status = anyio.run(profiler.get_builtin_browser_status)
        
        if status["running"]:
            info = status["info"]
            console.print(Panel(
                f"[green]Builtin browser is running[/green]\n\n"
                f"CDP URL: [cyan]{info['cdp_url']}[/cyan]\n"
                f"Process ID: [yellow]{info['pid']}[/yellow]\n"
                f"Browser type: [blue]{info['browser_type']}[/blue]\n"
                f"User data directory: [magenta]{info['user_data_dir']}[/magenta]\n"
                f"Started: [cyan]{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['start_time']))}[/cyan]",
                title="Builtin Browser Status",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[yellow]Builtin browser is not running[/yellow]\n\n"
                "Use 'crwl browser start' to start a builtin browser",
                title="Builtin Browser Status",
                border_style="yellow"
            ))
            
    except Exception as e:
        console.print(f"[red]Error checking browser status: {str(e)}[/red]")
        sys.exit(1)
        
@browser_cmd.command("start")
@click.option("--browser-type", "-b", type=click.Choice(["chromium", "firefox"]), default="chromium", 
              help="Browser type (default: chromium)")
@click.option("--port", "-p", type=int, default=9222, help="Debugging port (default: 9222)")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
def browser_start_cmd(browser_type: str, port: int, headless: bool):
    """Start a builtin browser instance
    
    This will start a persistent browser instance that can be used by Crawl4AI
    by setting browser_mode="builtin" in BrowserConfig.
    """
    profiler = BrowserProfiler()
    
    # First check if browser is already running
    status = anyio.run(profiler.get_builtin_browser_status)
    if status["running"]:
        console.print(Panel(
            "[yellow]Builtin browser is already running[/yellow]\n\n"
            f"CDP URL: [cyan]{status['cdp_url']}[/cyan]\n\n"
            "Use 'crwl browser restart' to restart the browser",
            title="Builtin Browser Start",
            border_style="yellow"
        ))
        return
    
    try:
        console.print(Panel(
            f"[cyan]Starting builtin browser[/cyan]\n\n"
            f"Browser type: [green]{browser_type}[/green]\n"
            f"Debugging port: [yellow]{port}[/yellow]\n"
            f"Headless: [cyan]{'Yes' if headless else 'No'}[/cyan]",
            title="Builtin Browser Start",
            border_style="cyan"
        ))
        
        cdp_url = anyio.run(
            profiler.launch_builtin_browser,
            browser_type,
            port,
            headless
        )
        
        if cdp_url:
            console.print(Panel(
                f"[green]Builtin browser started successfully[/green]\n\n"
                f"CDP URL: [cyan]{cdp_url}[/cyan]\n\n"
                "This browser will be used automatically when setting browser_mode='builtin'",
                title="Builtin Browser Start",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[red]Failed to start builtin browser[/red]",
                title="Builtin Browser Start",
                border_style="red"
            ))
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error starting builtin browser: {str(e)}[/red]")
        sys.exit(1)
        
@browser_cmd.command("stop")
def browser_stop_cmd():
    """Stop the running builtin browser"""
    profiler = BrowserProfiler()
    
    try:
        # First check if browser is running
        status = anyio.run(profiler.get_builtin_browser_status)
        if not status["running"]:
            console.print(Panel(
                "[yellow]No builtin browser is currently running[/yellow]",
                title="Builtin Browser Stop",
                border_style="yellow"
            ))
            return
            
        console.print(Panel(
            "[cyan]Stopping builtin browser...[/cyan]",
            title="Builtin Browser Stop", 
            border_style="cyan"
        ))
        
        success = anyio.run(profiler.kill_builtin_browser)
        
        if success:
            console.print(Panel(
                "[green]Builtin browser stopped successfully[/green]",
                title="Builtin Browser Stop",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[red]Failed to stop builtin browser[/red]",
                title="Builtin Browser Stop",
                border_style="red"
            ))
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error stopping builtin browser: {str(e)}[/red]")
        sys.exit(1)
        
@browser_cmd.command("view")
@click.option("--url", "-u", help="URL to navigate to (defaults to about:blank)")
def browser_view_cmd(url: Optional[str]):
    """
    Open a visible window of the builtin browser
    
    This command connects to the running builtin browser and opens a visible window,
    allowing you to see what the browser is currently viewing or navigate to a URL.
    """
    profiler = BrowserProfiler()
    
    try:
        # First check if browser is running
        status = anyio.run(profiler.get_builtin_browser_status)
        if not status["running"]:
            console.print(Panel(
                "[yellow]No builtin browser is currently running[/yellow]\n\n"
                "Use 'crwl browser start' to start a builtin browser first",
                title="Builtin Browser View",
                border_style="yellow"
            ))
            return
        
        info = status["info"]
        cdp_url = info["cdp_url"]
        
        console.print(Panel(
            f"[cyan]Opening visible window connected to builtin browser[/cyan]\n\n"
            f"CDP URL: [green]{cdp_url}[/green]\n"
            f"URL to load: [yellow]{url or 'about:blank'}[/yellow]",
            title="Builtin Browser View",
            border_style="cyan"
        ))
        
        # Use the CDP URL to launch a new visible window
        import subprocess
        import os
        
        # Determine the browser command based on platform
        if sys.platform == "darwin":  # macOS
            browser_cmd = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
        elif sys.platform == "win32":  # Windows
            browser_cmd = ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"]
        else:  # Linux
            browser_cmd = ["google-chrome"]
        
        # Add arguments
        browser_args = [
            f"--remote-debugging-port={info['debugging_port']}",
            "--remote-debugging-address=localhost",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        
        # Add URL if provided
        if url:
            browser_args.append(url)
        
        # Launch browser
        try:
            subprocess.Popen(browser_cmd + browser_args)
            console.print("[green]Browser window opened. Close it when finished viewing.[/green]")
        except Exception as e:
            console.print(f"[red]Error launching browser: {str(e)}[/red]")
            console.print(f"[yellow]Try connecting manually to {cdp_url} in Chrome or using the '--remote-debugging-port' flag.[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error viewing builtin browser: {str(e)}[/red]")
        sys.exit(1)

@browser_cmd.command("restart")
@click.option("--browser-type", "-b", type=click.Choice(["chromium", "firefox"]), default=None, 
              help="Browser type (defaults to same as current)")
@click.option("--port", "-p", type=int, default=None, help="Debugging port (defaults to same as current)")
@click.option("--headless/--no-headless", default=None, help="Run browser in headless mode")
def browser_restart_cmd(browser_type: Optional[str], port: Optional[int], headless: Optional[bool]):
    """Restart the builtin browser
    
    Stops the current builtin browser if running and starts a new one.
    By default, uses the same configuration as the current browser.
    """
    profiler = BrowserProfiler()
    
    try:
        # First check if browser is running and get its config
        status = anyio.run(profiler.get_builtin_browser_status)
        current_config = {}
        
        if status["running"]:
            info = status["info"]
            current_config = {
                "browser_type": info["browser_type"],
                "port": info["debugging_port"],
                "headless": True  # Default assumption
            }
            
            # Stop the browser
            console.print(Panel(
                "[cyan]Stopping current builtin browser...[/cyan]",
                title="Builtin Browser Restart", 
                border_style="cyan"
            ))
            
            success = anyio.run(profiler.kill_builtin_browser)
            if not success:
                console.print(Panel(
                    "[red]Failed to stop current browser[/red]",
                    title="Builtin Browser Restart",
                    border_style="red"
                ))
                sys.exit(1)
        
        # Use provided options or defaults from current config
        browser_type = browser_type or current_config.get("browser_type", "chromium")
        port = port or current_config.get("port", 9222)
        headless = headless if headless is not None else current_config.get("headless", True)
        
        # Start a new browser
        console.print(Panel(
            f"[cyan]Starting new builtin browser[/cyan]\n\n"
            f"Browser type: [green]{browser_type}[/green]\n"
            f"Debugging port: [yellow]{port}[/yellow]\n"
            f"Headless: [cyan]{'Yes' if headless else 'No'}[/cyan]",
            title="Builtin Browser Restart",
            border_style="cyan"
        ))
        
        cdp_url = anyio.run(
            profiler.launch_builtin_browser,
            browser_type,
            port,
            headless
        )
        
        if cdp_url:
            console.print(Panel(
                f"[green]Builtin browser restarted successfully[/green]\n\n"
                f"CDP URL: [cyan]{cdp_url}[/cyan]",
                title="Builtin Browser Restart",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[red]Failed to restart builtin browser[/red]",
                title="Builtin Browser Restart",
                border_style="red"
            ))
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error restarting builtin browser: {str(e)}[/red]")
        sys.exit(1)

@cli.command("cdp")
@click.option("--user-data-dir", "-d", help="Directory to use for browser data (will be created if it doesn't exist)")
@click.option("--port", "-P", type=int, default=9222, help="Debugging port (default: 9222)")
@click.option("--browser-type", "-b", type=click.Choice(["chromium", "firefox"]), default="chromium", 
              help="Browser type (default: chromium)")
@click.option("--headless", is_flag=True, help="Run browser in headless mode")
@click.option("--incognito", is_flag=True, help="Run in incognito/private mode (ignores user-data-dir)")
def cdp_cmd(user_data_dir: Optional[str], port: int, browser_type: str, headless: bool, incognito: bool):
    """Launch a standalone browser with CDP debugging enabled
    
    This command launches a browser with Chrome DevTools Protocol (CDP) debugging enabled,
    prints the CDP URL, and keeps the browser running until you press 'q'.
    
    The CDP URL can be used for various automation and debugging tasks.
    
    Examples:
        # Launch Chromium with CDP on default port 9222
        crwl cdp
        
        # Use a specific directory for browser data and custom port
        crwl cdp --user-data-dir ~/browser-data --port 9223
        
        # Launch in headless mode
        crwl cdp --headless
        
        # Launch in incognito mode (ignores user-data-dir)
        crwl cdp --incognito
    """
    profiler = BrowserProfiler()
    
    try:
        # Handle data directory
        data_dir = None
        if not incognito and user_data_dir:
            # Expand user path (~/something)
            expanded_path = os.path.expanduser(user_data_dir)
            
            # Create directory if it doesn't exist
            if not os.path.exists(expanded_path):
                console.print(f"[yellow]Directory '{expanded_path}' doesn't exist. Creating it.[/yellow]")
                os.makedirs(expanded_path, exist_ok=True)
            
            data_dir = expanded_path
        
        # Print launch info
        console.print(Panel(
            f"[cyan]Launching browser with CDP debugging[/cyan]\n\n"
            f"Browser type: [green]{browser_type}[/green]\n"
            f"Debugging port: [yellow]{port}[/yellow]\n"
            f"User data directory: [cyan]{data_dir or 'Temporary directory'}[/cyan]\n"
            f"Headless: [cyan]{'Yes' if headless else 'No'}[/cyan]\n"
            f"Incognito: [cyan]{'Yes' if incognito else 'No'}[/cyan]\n\n"
            f"[yellow]Press 'q' to quit when done[/yellow]",
            title="CDP Browser",
            border_style="cyan"
        ))
        
        # Run the browser
        cdp_url = anyio.run(
            profiler.launch_standalone_browser,
            browser_type,
            data_dir,
            port,
            headless
        )
        
        if not cdp_url:
            console.print("[red]Failed to launch browser or get CDP URL[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error launching CDP browser: {str(e)}[/red]")
        sys.exit(1)


@cli.command("crawl")
@click.argument("url", required=True)
@click.option("--browser-config", "-B", type=click.Path(exists=True), help="Browser config file (YAML/JSON)")
@click.option("--crawler-config", "-C", type=click.Path(exists=True), help="Crawler config file (YAML/JSON)")
@click.option("--filter-config", "-f", type=click.Path(exists=True), help="Content filter config file")
@click.option("--extraction-config", "-e", type=click.Path(exists=True), help="Extraction strategy config file")
@click.option("--json-extract", "-j", is_flag=False, flag_value="", default=None, help="Extract structured data using LLM with optional description")
@click.option("--schema", "-s", type=click.Path(exists=True), help="JSON schema for extraction")
@click.option("--browser", "-b", type=str, callback=parse_key_values, help="Browser parameters as key1=value1,key2=value2")
@click.option("--crawler", "-c", type=str, callback=parse_key_values, help="Crawler parameters as key1=value1,key2=value2")
@click.option("--output", "-o", type=click.Choice(["all", "json", "markdown", "md", "markdown-fit", "md-fit"]), default="all")
@click.option("--output-file", "-O", type=click.Path(), help="Output file path (default: stdout)")
@click.option("--bypass-cache", "-bc", is_flag=True, default=True, help="Bypass cache when crawling")
@click.option("--question", "-q", help="Ask a question about the crawled content")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--profile", "-p", help="Use a specific browser profile (by name)")
def crawl_cmd(url: str, browser_config: str, crawler_config: str, filter_config: str, 
           extraction_config: str, json_extract: str, schema: str, browser: Dict, crawler: Dict,
           output: str, output_file: str, bypass_cache: bool, question: str, verbose: bool, profile: str):
    """Crawl a website and extract content
    
    Simple Usage:
        crwl crawl https://example.com
    """
    
    # Handle profile option
    if profile:
        profiler = BrowserProfiler()
        profile_path = profiler.get_profile_path(profile)
        
        if not profile_path:
            profiles = profiler.list_profiles()
            
            if profiles:
                console.print(f"[red]Profile '{profile}' not found. Available profiles:[/red]")
                display_profiles_table(profiles)
            else:
                console.print("[red]No profiles found. Create one with 'crwl profiles'[/red]")
            
            return
        
        # Include the profile in browser config
        if not browser:
            browser = {}
        browser["user_data_dir"] = profile_path
        browser["use_managed_browser"] = True
        
        if verbose:
            console.print(f"[green]Using browser profile:[/green] {profile}")
            
    try:
        # Load base configurations
        browser_cfg = BrowserConfig.load(load_config_file(browser_config))
        crawler_cfg = CrawlerRunConfig.load(load_config_file(crawler_config))
        
        # Override with CLI params
        if browser:
            browser_cfg = browser_cfg.clone(**browser)
        if crawler:
            crawler_cfg = crawler_cfg.clone(**crawler)
            
        # Handle content filter config
        if filter_config or output in ["markdown-fit", "md-fit"]:
            if filter_config:
                filter_conf = load_config_file(filter_config)
            elif not filter_config and output in ["markdown-fit", "md-fit"]:
                filter_conf = {
                    "type": "pruning",
                    "query": "",
                    "threshold": 0.48
                }
            if filter_conf["type"] == "bm25":
                crawler_cfg.markdown_generator = DefaultMarkdownGenerator(
                    content_filter = BM25ContentFilter(
                        user_query=filter_conf.get("query"),
                        bm25_threshold=filter_conf.get("threshold", 1.0),
                        use_stemming=filter_conf.get("use_stemming", True),
                    )
                )
            elif filter_conf["type"] == "pruning":
                crawler_cfg.markdown_generator = DefaultMarkdownGenerator(
                    content_filter = PruningContentFilter(
                        user_query=filter_conf.get("query"),
                        threshold=filter_conf.get("threshold", 0.48)
                    )
                )
        
        # Handle json-extract option (takes precedence over extraction-config)
        if json_extract is not None:
            # Get LLM provider and token
            provider, token = setup_llm_config()
            
            # Default sophisticated instruction for structured data extraction
            default_instruction = """Analyze the web page content and extract structured data as JSON. 
If the page contains a list of items with repeated patterns, extract all items in an array. 
If the page is an article or contains unique content, extract a comprehensive JSON object with all relevant information.
Look at the content, intention of content, what it offers and find the data item(s) in the page.
Always return valid, properly formatted JSON."""
            
            
            default_instruction_with_user_query = """Analyze the web page content and extract structured data as JSON, following the below instruction and explanation of schema and always return valid, properly formatted JSON. \n\nInstruction:\n\n""" + json_extract
            
            # Determine instruction based on whether json_extract is empty or has content
            instruction = default_instruction_with_user_query if json_extract else default_instruction
            
            # Create LLM extraction strategy
            crawler_cfg.extraction_strategy = LLMExtractionStrategy(
                llm_config=LLMConfig(provider=provider, api_token=token),
                instruction=instruction,
                schema=load_schema_file(schema),  # Will be None if no schema is provided
                extraction_type="schema", #if schema else "block",
                apply_chunking=False,
                force_json_response=True,
                verbose=verbose,
            )
            
            # Set output to JSON if not explicitly specified
            if output == "all":
                output = "json"
                
        # Handle extraction strategy from config file (only if json-extract wasn't used)
        elif extraction_config:
            extract_conf = load_config_file(extraction_config)
            schema_data = load_schema_file(schema)
            
            # Check if type does not exist show proper message
            if not extract_conf.get("type"):
                raise click.ClickException("Extraction type not specified")
            if extract_conf["type"] not in ["llm", "json-css", "json-xpath"]:
                raise click.ClickException(f"Invalid extraction type: {extract_conf['type']}")
            
            if extract_conf["type"] == "llm":
                # if no provider show error emssage
                if not extract_conf.get("provider") or not extract_conf.get("api_token"):
                    raise click.ClickException("LLM provider and API token are required for LLM extraction")

                crawler_cfg.extraction_strategy = LLMExtractionStrategy(
                    llm_config=LLMConfig(provider=extract_conf["provider"], api_token=extract_conf["api_token"]),
                    instruction=extract_conf["instruction"],
                    schema=schema_data,
                    **extract_conf.get("params", {})
                )
            elif extract_conf["type"] == "json-css":
                crawler_cfg.extraction_strategy = JsonCssExtractionStrategy(
                    schema=schema_data
                )
            elif extract_conf["type"] == "json-xpath":
                crawler_cfg.extraction_strategy = JsonXPathExtractionStrategy(
                    schema=schema_data
                )
                

        # No cache
        if bypass_cache:
            crawler_cfg.cache_mode = CacheMode.BYPASS

        crawler_cfg.scraping_strategy = LXMLWebScrapingStrategy()    

        config = get_global_config()
        
        browser_cfg.verbose = config.get("VERBOSE", False)
        crawler_cfg.verbose = config.get("VERBOSE", False)
        
        # Run crawler
        result : CrawlResult = anyio.run(
            run_crawler,
            url,
            browser_cfg,
            crawler_cfg,
            verbose
        )

        # Handle question
        if question:
            provider, token = setup_llm_config()
            markdown = result.markdown.raw_markdown
            anyio.run(stream_llm_response, url, markdown, question, provider, token)
            return
        
        # Handle output
        if not output_file:
            if output == "all":
                click.echo(json.dumps(result.model_dump(), indent=2))
            elif output == "json":
                print(result.extracted_content)
                extracted_items = json.loads(result.extracted_content)
                click.echo(json.dumps(extracted_items, indent=2))
                
            elif output in ["markdown", "md"]:
                click.echo(result.markdown.raw_markdown)
            elif output in ["markdown-fit", "md-fit"]:
                click.echo(result.markdown.fit_markdown)
        else:
            if output == "all":
                with open(output_file, "w") as f:
                    f.write(json.dumps(result.model_dump(), indent=2))
            elif output == "json":
                with open(output_file, "w") as f:
                    f.write(result.extracted_content)
            elif output in ["markdown", "md"]:
                with open(output_file, "w") as f:
                    f.write(result.markdown.raw_markdown)
            elif output in ["markdown-fit", "md-fit"]:
                with open(output_file, "w") as f:
                    f.write(result.markdown.fit_markdown)
            
    except Exception as e:
        raise click.ClickException(str(e))

@cli.command("examples")
def examples_cmd():
    """Show usage examples"""
    show_examples()

@cli.group("config")
def config_cmd():
    """Manage global configuration settings
    
    Commands to view and update global configuration settings:
    - list: Display all current configuration settings
    - get: Get the value of a specific setting
    - set: Set the value of a specific setting
    """
    pass

@config_cmd.command("list")
def config_list_cmd():
    """List all configuration settings"""
    config = get_global_config()
    
    table = Table(title="Crawl4AI Configuration", show_header=True, header_style="bold cyan", border_style="blue")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Default", style="yellow")
    table.add_column("Description", style="white")
    
    for key, setting in USER_SETTINGS.items():
        value = config.get(key, setting["default"])
        
        # Handle secret values
        display_value = value
        if setting.get("secret", False) and value:
            display_value = "********"
            
        # Handle boolean values
        if setting["type"] == "boolean":
            display_value = str(value).lower()
            default_value = str(setting["default"]).lower()
        else:
            default_value = str(setting["default"])
        
        table.add_row(
            key,
            str(display_value),
            default_value,
            setting["description"]
        )
    
    console.print(table)

@config_cmd.command("get")
@click.argument("key", required=True)
def config_get_cmd(key: str):
    """Get a specific configuration setting"""
    config = get_global_config()
    
    # Normalize key to uppercase
    key = key.upper()
    
    if key not in USER_SETTINGS:
        console.print(f"[red]Error: Unknown setting '{key}'[/red]")
        return
    
    value = config.get(key, USER_SETTINGS[key]["default"])
    
    # Handle secret values
    display_value = value
    if USER_SETTINGS[key].get("secret", False) and value:
        display_value = "********"
    
    console.print(f"[cyan]{key}[/cyan] = [green]{display_value}[/green]")
    console.print(f"[dim]Description: {USER_SETTINGS[key]['description']}[/dim]")

@config_cmd.command("set")
@click.argument("key", required=True)
@click.argument("value", required=True)
def config_set_cmd(key: str, value: str):
    """Set a configuration setting"""
    config = get_global_config()
    
    # Normalize key to uppercase
    key = key.upper()
    
    if key not in USER_SETTINGS:
        console.print(f"[red]Error: Unknown setting '{key}'[/red]")
        console.print(f"[yellow]Available settings: {', '.join(USER_SETTINGS.keys())}[/yellow]")
        return
    
    setting = USER_SETTINGS[key]
    
    # Type conversion and validation
    if setting["type"] == "boolean":
        if value.lower() in ["true", "yes", "1", "y"]:
            typed_value = True
        elif value.lower() in ["false", "no", "0", "n"]:
            typed_value = False
        else:
            console.print(f"[red]Error: Invalid boolean value. Use 'true' or 'false'.[/red]")
            return
    elif setting["type"] == "string":
        typed_value = value
        
        # Check if the value should be one of the allowed options
        if "options" in setting and value not in setting["options"]:
            console.print(f"[red]Error: Value must be one of: {', '.join(setting['options'])}[/red]")
            return
    
    # Update config
    config[key] = typed_value
    save_global_config(config)
    
    # Handle secret values for display
    display_value = typed_value
    if setting.get("secret", False) and typed_value:
        display_value = "********"
        
    console.print(f"[green]Successfully set[/green] [cyan]{key}[/cyan] = [green]{display_value}[/green]")

@cli.command("profiles")
def profiles_cmd():
    """Manage browser profiles interactively
    
    Launch an interactive browser profile manager where you can:
    - List all existing profiles
    - Create new profiles for authenticated browsing
    - Delete unused profiles
    """
    # Run interactive profile manager
    anyio.run(manage_profiles)

@cli.command(name="")
@click.argument("url", required=False)
@click.option("--example", is_flag=True, help="Show usage examples")
@click.option("--browser-config", "-B", type=click.Path(exists=True), help="Browser config file (YAML/JSON)")
@click.option("--crawler-config", "-C", type=click.Path(exists=True), help="Crawler config file (YAML/JSON)")
@click.option("--filter-config", "-f", type=click.Path(exists=True), help="Content filter config file")
@click.option("--extraction-config", "-e", type=click.Path(exists=True), help="Extraction strategy config file")
@click.option("--json-extract", "-j", is_flag=False, flag_value="", default=None, help="Extract structured data using LLM with optional description")
@click.option("--schema", "-s", type=click.Path(exists=True), help="JSON schema for extraction")
@click.option("--browser", "-b", type=str, callback=parse_key_values, help="Browser parameters as key1=value1,key2=value2")
@click.option("--crawler", "-c", type=str, callback=parse_key_values, help="Crawler parameters as key1=value1,key2=value2")
@click.option("--output", "-o", type=click.Choice(["all", "json", "markdown", "md", "markdown-fit", "md-fit"]), default="all")
@click.option("--bypass-cache", is_flag=True, default=True, help="Bypass cache when crawling")
@click.option("--question", "-q", help="Ask a question about the crawled content")
@click.option("--verbose", "-v", is_flag=True)
@click.option("--profile", "-p", help="Use a specific browser profile (by name)")
def default(url: str, example: bool, browser_config: str, crawler_config: str, filter_config: str, 
        extraction_config: str, json_extract: str, schema: str, browser: Dict, crawler: Dict,
        output: str, bypass_cache: bool, question: str, verbose: bool, profile: str):
    """Crawl4AI CLI - Web content extraction tool

    Simple Usage:
        crwl https://example.com
    
    Run with --example to see detailed usage examples.
    
    Other commands:
        crwl profiles   - Manage browser profiles for identity-based crawling
        crwl crawl      - Crawl a website with advanced options
        crwl cdp        - Launch browser with CDP debugging enabled
        crwl browser    - Manage builtin browser (start, stop, status, restart)
        crwl config     - Manage global configuration settings
        crwl examples   - Show more usage examples
        
    Configuration Examples:
        crwl config list                         - List all configuration settings
        crwl config get DEFAULT_LLM_PROVIDER     - Show current LLM provider
        crwl config set VERBOSE true             - Enable verbose mode globally
        crwl config set BROWSER_HEADLESS false   - Default to visible browser
    """

    if example:
        show_examples()
        return
        
    if not url:
        # Show help without error message
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return
        
    # Forward to crawl command
    ctx = click.get_current_context()
    ctx.invoke(
        crawl_cmd, 
        url=url, 
        browser_config=browser_config,
        crawler_config=crawler_config,
        filter_config=filter_config,
        extraction_config=extraction_config,
        json_extract=json_extract,
        schema=schema,
        browser=browser,
        crawler=crawler,
        output=output,
        bypass_cache=bypass_cache,
        question=question,
        verbose=verbose,
        profile=profile
    )

def main():
    import sys
    if len(sys.argv) < 2 or sys.argv[1] not in cli.commands:
        sys.argv.insert(1, "crawl")
    cli()

if __name__ == "__main__":
    main()