from crawl4ai import BrowserConfig, CrawlerRunConfig, PruningContentFilter, DefaultMarkdownGenerator
from crawl4ai.deep_crawling.filters import ContentTypeFilter, DomainFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer, PathDepthScorer
from crawl4ai.cache_context import CacheMode
from crawl4ai.deep_crawling.bfs_strategy import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain
from crawl4ai.deep_crawling.scorers import CompositeScorer
from crawl4ai.docker_client import Crawl4aiDockerClient
import json
from rich.console import Console
from rich.syntax import Syntax

console = Console()

def print_json(data: dict, title: str = None):
    """Helper to print JSON prettily with syntax highlighting"""
    if title:
        console.print(f"\n[bold blue]{title}[/bold blue]")
    json_str = json.dumps(data, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
    console.print(syntax)

async def part1_basic_config():
    """PART 1: Understanding Basic Configuration Objects
    
    Here we create simple configuration objects and examine their structure.
    This helps understand the basic type-params pattern used throughout the API.
    """
    console.print("\n[bold green]Explanation:[/bold green] Configuration objects like BrowserConfig and CrawlerRunConfig are the foundation of Crawl4AI. They define how the crawler behaves—e.g., whether it runs headless or how it processes content. These objects use a 'type-params' pattern: 'type' identifies the object class, and 'params' holds its settings. This structure is key because it’s reusable and can be serialized into JSON for API calls.")
    
    # Create a simple browser config
    browser_config = BrowserConfig(
        headless=False,
        viewport_width=500,
        headers = {"User-Agent": "Mozilla/5.0"}
    )
    
    # Show its structure
    print_json(browser_config.dump(), "Simple Browser Config Structure")
    
    # Create a more complex config with nested objects
    crawler_config = CrawlerRunConfig(
        word_count_threshold=200,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.5)
        )
    )
    
    print_json(crawler_config.dump(), "Complex Config with Nested Objects")

async def part2_manual_json():
    """PART 2: Building JSON Manually
    
    Learn how to construct the JSON structure by hand.
    This demonstrates deep understanding of the configuration format.
    """
    console.print("\n[bold green]Explanation:[/bold green] Manually building JSON configurations mirrors how the API expects data. It’s a hands-on way to learn the exact structure—each object has a 'type' and 'params' section. This is useful when you’re troubleshooting or working without the SDK, as it forces you to understand every detail of the config format.")
    
    # Manual browser config
    manual_browser = {
        "type": "BrowserConfig",
        "params": {
            "headless": True,
            "viewport": {
                "type": "dict",
                "value": {
                    "width": 1200,
                    "height": 800
                }
            }
        }
    }
    
    # Validate by loading into BrowserConfig
    loaded_config = BrowserConfig.load(manual_browser)
    print_json(loaded_config.dump(), "Manually Created -> Loaded -> Dumped")
    
    # Show they're equivalent
    original = BrowserConfig(headless=True, viewport={"width": 1200, "height": 800})
    assert loaded_config.dump() == original.dump(), "Configs are equivalent!"
    
async def part3_complex_structures():
    """PART 3: Working with Complex Nested Structures
    
    Explore more complex configurations with multiple levels of nesting.
    This shows how the type-params pattern scales to complex scenarios.
    """
    console.print("\n[bold green]Explanation:[/bold green] Real-world crawling often requires detailed settings—like filtering content or customizing output. Here, we nest objects (e.g., a markdown generator with a content filter) using the same 'type-params' pattern. This nesting lets you fine-tune the crawler’s behavior at multiple levels, making it powerful and flexible.")
    
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter()
        ),
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=5,
            filter_chain=FilterChain(
                filters=[
                    ContentTypeFilter(allowed_types=["text/html"]),
                    DomainFilter(allowed_domains=["example.com"])
                ]
            ),
            url_scorer=CompositeScorer(
                scorers=[
                    KeywordRelevanceScorer(keywords=["data", "analysis"]),
                    PathDepthScorer(optimal_depth=3)
                ]
            )
        )
    )
    
    print_json(config.dump(), "Deep Nested Configuration")

async def part4_client_sdk():
    """PART 4: Using the Client SDK
    
    Demonstrate how the SDK makes working with the API simple by handling
    all the complex serialization automatically.
    """
    console.print("\n[bold green]Explanation:[/bold green] The Crawl4aiDockerClient SDK is a time-saver—it takes your configuration objects and turns them into API-ready JSON automatically. This means less manual work and fewer mistakes. You just define your settings, pass them to the SDK, and it handles the rest, making crawling easier and faster.")
    
    async with Crawl4aiDockerClient(base_url="http://localhost:8000") as client:
        # You would normally authenticate here if JWT is enabled
        await client.authenticate("user@example.com")
        
        # Create configs
        browser_config = BrowserConfig(headless=True)
        crawler_config = CrawlerRunConfig(stream=False)
        
        # SDK handles all serialization
        result = await client.crawl(
            urls=["https://example.com"],
            browser_config=browser_config,
            crawler_config=crawler_config
        )
        
        console.print("\n[bold green]🚀 Crawl completed successfully![/bold green]")
        console.print(f"Markdown length: {len(result.markdown)} characters")

async def part5_direct_api():
    """PART 5: Using the API Directly
    
    Learn how to make direct API calls without the SDK.
    This demonstrates the raw request structure and gives more control.
    """
    console.print("\n[bold green]Explanation:[/bold green] Skipping the SDK means you’re in full control—you build the JSON payload yourself and send it to the API. This is harder but gives you a deeper understanding of how Crawl4AI works under the hood. It’s also useful if you’re integrating with systems that don’t use the SDK.")
    
    import aiohttp
    from datetime import datetime

    # Prepare the request payload
    payload = {
        "urls": ["https://example.com"],
        "browser_config": {
            "type": "BrowserConfig",
            "params": {
                "headless": True,
                "viewport": {
                    "type": "dict",
                    "value": {
                        "width": 1200,
                        "height": 800
                    }
                }
            }
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "bypass",
                "markdown_generator": {
                    "type": "DefaultMarkdownGenerator",
                    "params": {
                        "content_filter": {
                            "type": "PruningContentFilter",
                            "params": {
                                "threshold": 0.48,
                                "threshold_type": "fixed"
                            }
                        }
                    }
                }
            }
        }
    }

    print_json(payload, "Direct API Request Payload")

    async with aiohttp.ClientSession() as session:
        # If JWT is enabled, get token first
        token_response = await session.post(
            "http://localhost:8000/token",
            json={"email": "user@example.com"}
        )
        token = (await token_response.json())["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Make the crawl request
        start_time = datetime.now()
        async with session.post(
            "http://localhost:8000/crawl",
            json=payload,
            headers=headers  # comment if using JWT
        ) as response:
            result = await response.json()
            duration = (datetime.now() - start_time).total_seconds()

        console.print(f"\n[bold green]✅ API call completed in {duration:.2f}s[/bold green]")
        print_json(result, "API Response")

async def part6_wrap_up():
    """PART 6: Wrap-Up and Key Takeaways
    
    Summarize the key concepts learned in this tutorial.
    """
    console.print("\n[bold yellow]🎓 Tutorial Wrap-Up[/bold yellow]")
    console.print("[italic]Key Takeaways:[/italic]\n")
    console.print("- **Configurations:** Use the type-params pattern to define settings flexibly.")
    console.print("- **Manual JSON:** Build configs by hand to master the structure.")
    console.print("- **Nesting:** Customize deeply with nested objects.")
    console.print("- **SDK:** Simplify API calls with automatic serialization.")
    console.print("- **Direct API:** Gain control by crafting raw requests.")
    console.print("\n[bold green]🚀 You’re ready to crawl with Crawl4AI![/bold green]")

async def main():
    """Main tutorial runner that executes each part in sequence"""
    console.print("\n[bold yellow]🎓 Crawl4AI Docker Tutorial[/bold yellow]")
    console.print("[italic]Learn how to work with configuration objects and the Docker API[/italic]\n")
    
    parts = [
        (part1_basic_config, "Understanding Basic Configurations"),
        (part2_manual_json, "Manual JSON Construction"),
        (part3_complex_structures, "Complex Nested Structures"),
        (part4_client_sdk, "Using the Client SDK"),
        (part5_direct_api, "Direct API Integration"),
        (part6_wrap_up, "Wrap-Up and Key Takeaways")
    ]
    
    for func, title in parts:
        console.print(f"\n[bold cyan]📚 {title}[/bold cyan]")
        console.print("[dim]" + func.__doc__.strip() + "[/dim]\n")
        await func()
        if func != part6_wrap_up:  # No pause after wrap-up
            input("\nPress Enter to continue...\n")

# Run the tutorial
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())