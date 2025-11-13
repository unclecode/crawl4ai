import yaml
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt

console = Console()

def _ask_llm_extraction():
    config = {'type': 'llm'}
    console.print("\n   [bold]Configuring LLM Data Extraction:[/bold]")
    config['instruction'] = Prompt.ask(
        "   Enter the instruction for the LLM (e.g., 'Extract all product names and prices')"
    )
    if Confirm.ask("\n   Do you want to configure the LLM provider now?", default=True):
        config['llm'] = {}
        config['llm']['provider'] = Prompt.ask("   Enter LLM provider (e.g., openai/gpt-4o)")
        config['llm']['api_key'] = Prompt.ask("   Enter your API key", password=True)
    else:
        console.print("   [yellow]Skipping LLM config. The crawler will use the global default.[/yellow]")
    return config

def _ask_css_extraction():
    config = {'type': 'json-css', 'schema': {'fields': []}}
    console.print("\n   [bold]Configuring CSS Selector Data Extraction:[/bold]")
    console.print("   You will now define a schema to extract structured data.")
    base_selector = Prompt.ask("   [bold]Step 1: Base Selector[/bold]\n   Enter the CSS selector for the repeating element that contains all the fields (e.g., 'div.product-item')")
    config['schema']['baseSelector'] = base_selector
    console.print("\n   [bold]Step 2: Define Fields to Extract[/bold]")
    while True:
        field = {}
        console.print(f"\n   --- Defining Field #{len(config['schema']['fields']) + 1} ---")
        field['name'] = Prompt.ask("   Field Name (e.g., 'product_title')")
        field['selector'] = Prompt.ask(f"   CSS Selector for '{field['name']}' (relative to the base selector)")
        field['type'] = Prompt.ask("   Extraction Type", choices=["text", "attribute"], default="text")
        if field['type'] == 'attribute':
            field['attribute'] = Prompt.ask("   Which attribute to extract (e.g., 'href', 'src')")
        config['schema']['fields'].append(field)
        if not Confirm.ask("\n   Add another field?", default=True):
            break
    return config

def _ask_deep_crawl():
    config = {}
    console.print("\n   [bold]Configuring Deep Crawl:[/bold]")
    config['strategy'] = Prompt.ask(
        "   Select a crawling strategy",
        choices=["bfs", "dfs"],
        default="bfs"
    )
    config['max_pages'] = IntPrompt.ask(
        "   Enter the maximum number of pages to crawl",
        default=10
    )
    config['max_depth'] = IntPrompt.ask(
        "   Enter the maximum crawl depth (how many links deep to follow)",
        default=2
    )
    return config

def generate_config():
    """
    Runs an interactive wizard to generate a configuration file for crawl4ai.
    """
    console.print("\n[bold cyan]Crawl4AI Interactive Configuration Wizard[/bold cyan]")
    console.print("This wizard will generate a `config.yml` file for your crawl.")
    console.print("Press Ctrl+C at any time to exit.")

    config = {}

    try:
        # 0. Choose Goal/Preset
        console.print("\n[bold]1. What is your goal?[/bold]")
        goal = Prompt.ask(
            "   ",
            choices=[
                "Scrape a single article (get clean markdown)",
                "Extract product data from a list (structured JSON)",
                "Crawl an entire website (deep crawl)",
                "Custom crawl (access all advanced options)"
            ],
            default="Scrape a single article (get clean markdown)"
        )

        # 1. Get URL
        config['url'] = Prompt.ask("\n[bold]2. Enter the starting URL to crawl[/bold]")

        if goal == "Scrape a single article (get clean markdown)":
            config['output'] = {'file': Prompt.ask("Enter output filename", default="article.md")}

        elif goal == "Extract product data from a list (structured JSON)":
            console.print("\n   [bold]Choose an extraction method:[/bold]")
            method = Prompt.ask(
                "   ",
                choices=["LLM (more flexible, requires AI model)", "CSS Selectors (faster, for consistent layouts)"],
                default="LLM (more flexible, requires AI model)"
            )
            if "LLM" in method:
                config['extraction'] = _ask_llm_extraction()
            else:
                config['extraction'] = _ask_css_extraction()
            config['output'] = {'file': Prompt.ask("\nEnter output filename", default="products.json")}

        elif goal == "Crawl an entire website (deep crawl)":
            config['deep_crawl'] = _ask_deep_crawl()
            config['output'] = {'file': Prompt.ask("\nEnter output filename for the first page's content", default="crawl_result.md")}

        else: # Custom crawl
            # This path is for the full, advanced experience
            advanced_mode = Confirm.ask("\n[bold]Enable Advanced Mode for more options?[/bold]", default=False)
            config['advanced_mode'] = advanced_mode

            console.print("\n[bold]Custom Crawl Type:[/bold]")
            crawl_type = Prompt.ask(
                "   ",
                choices=["Single Page", "Deep Crawl (follow links)"],
                default="Single Page"
            )
            if crawl_type == "Deep Crawl (follow links)":
                config['deep_crawl'] = _ask_deep_crawl()

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

            console.print("\n[bold]Custom Extraction Mode:[/bold]")
            extraction_mode = Prompt.ask(
                "   ",
                choices=["Clean Markdown Content", "Structured Data (JSON) using LLM", "Structured Data (JSON) using CSS Selectors"],
                default="Clean Markdown Content"
            )
            if "LLM" in extraction_mode:
                config['extraction'] = _ask_llm_extraction()
            elif "CSS" in extraction_mode:
                config['extraction'] = _ask_css_extraction()

            config['output'] = {'file': Prompt.ask("\nEnter output filename", default="custom_output.md")}


        # 5. Save Configuration
        output_filename = Prompt.ask("\n[bold]Last step: Enter a name for your configuration file[/bold]", default="config.yml")

        with open(output_filename, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        console.print(f"\n[bold green]✅ Configuration saved to `{output_filename}`![/bold green]")
        console.print(f"   You can now run the crawl using: [bold]crwl run {output_filename}[/bold]")

    except (KeyboardInterrupt, EOFError):
        console.print("\n\n[bold red]Wizard cancelled. No configuration file created.[/bold red]")


if __name__ == '__main__':
    generate_config()
