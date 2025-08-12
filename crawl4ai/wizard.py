import yaml
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt

console = Console()

def generate_config():
    """
    Runs an interactive wizard to generate a configuration file for crawl4ai.
    """
    console.print("\n[bold cyan]Crawl4AI Interactive Configuration Wizard[/bold cyan]")
    console.print("This wizard will generate a `config.yml` file for your crawl.")
    console.print("Press Ctrl+C at any time to exit.")

    config = {}

    try:
        # 0. Choose Mode
        advanced_mode = Confirm.ask("\n[bold]Enable Advanced Mode for more options?[/bold]", default=False)
        config['advanced_mode'] = advanced_mode

        # 1. Get URL
        config['url'] = Prompt.ask("\n[bold]1. Enter the starting URL to crawl[/bold]")

        # 2. Choose Crawl Type
        console.print("\n[bold]2. Choose your crawl type:[/bold]")
        crawl_type = Prompt.ask(
            "   ",
            choices=["Single Page", "Deep Crawl (follow links)"],
            default="Single Page"
        )

        if crawl_type == "Deep Crawl (follow links)":
            config['deep_crawl'] = {}
            console.print("\n   [bold]Configuring Deep Crawl:[/bold]")
            config['deep_crawl']['strategy'] = Prompt.ask(
                "   Select a crawling strategy",
                choices=["bfs", "dfs"],
                default="bfs"
            )
            config['deep_crawl']['max_pages'] = IntPrompt.ask(
                "   Enter the maximum number of pages to crawl",
                default=10
            )
            config['deep_crawl']['max_depth'] = IntPrompt.ask(
                "   Enter the maximum crawl depth (how many links deep to follow)",
                default=2
            )

        if advanced_mode:
            config['browser'] = {}
            console.print("\n[bold]Advanced: Browser Settings[/bold]")
            config['browser']['headless'] = Confirm.ask("   Run in headless mode (no browser window)?", default=True)
            if Confirm.ask("   Set a custom viewport size?", default=False):
                config['browser']['viewport_width'] = IntPrompt.ask("      Enter viewport width", default=1280)
                config['browser']['viewport_height'] = IntPrompt.ask("      Enter viewport height", default=720)

            if Confirm.ask("   Use a proxy server?", default=False):
                config['browser']['proxy'] = Prompt.ask("      Enter proxy server URL (e.g., http://user:pass@host:port)")

            console.print("\n[bold]Advanced: Crawler Settings[/bold]")
            config['crawler'] = {}
            if Confirm.ask("   Add a delay before extracting content (e.g., for animations)?", default=False):
                config['crawler']['delay_before_return_html'] = IntPrompt.ask("      Enter delay in seconds", default=2)


        # 3. Choose Extraction Mode
        console.print("\n[bold]3. Choose what to extract:[/bold]")
        extraction_mode = Prompt.ask(
            "   ",
            choices=["Clean Markdown Content", "Structured Data (JSON)"],
            default="Clean Markdown Content"
        )

        if extraction_mode == "Structured Data (JSON)":
            config['extraction'] = {}
            console.print("\n   [bold]Configuring Structured Data Extraction:[/bold]")
            config['extraction']['type'] = "llm"  # For now, only support LLM extraction in wizard

            console.print("   You'll use an LLM to extract the data. See docs for CSS/XPath.")
            config['extraction']['instruction'] = Prompt.ask(
                "   Enter the instruction for the LLM (e.g., 'Extract all product names and prices')"
            )

            if Confirm.ask("\n   Do you want to configure the LLM provider now?", default=True):
                config['llm'] = {}
                config['llm']['provider'] = Prompt.ask("   Enter LLM provider (e.g., openai/gpt-4o)")
                config['llm']['api_key'] = Prompt.ask("   Enter your API key", password=True)
            else:
                 console.print("   [yellow]Skipping LLM config. The crawler will use the global default.[/yellow]")


        # 4. Output Configuration
        config['output'] = {}
        console.print("\n[bold]4. How do you want the output?[/bold]")
        if Confirm.ask("   Save the output to a file?", default=True):
            default_filename = "output.md" if extraction_mode == "Clean Markdown Content" else "output.json"
            config['output']['file'] = Prompt.ask("   Enter the output filename", default=default_filename)
        else:
            config['output']['file'] = None # This will mean print to console

        # 5. Save Configuration
        output_filename = Prompt.ask("\n[bold]5. Enter a name for your configuration file[/bold]", default="config.yml")

        with open(output_filename, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        console.print(f"\n[bold green]✅ Configuration saved to `{output_filename}`![/bold green]")
        console.print(f"   You can now run the crawl using: [bold]crwl run {output_filename}[/bold]")

    except (KeyboardInterrupt, EOFError):
        console.print("\n\n[bold red]Wizard cancelled. No configuration file created.[/bold red]")


if __name__ == '__main__':
    generate_config()
