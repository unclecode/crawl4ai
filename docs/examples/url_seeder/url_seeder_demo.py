"""
URL Seeder Demo - Interactive showcase of Crawl4AI's URL discovery capabilities

This demo shows:
1. Basic URL discovery from sitemaps and Common Crawl
2. Cache management and forced refresh
3. Live URL validation and metadata extraction
4. BM25 relevance scoring for intelligent filtering
5. Integration with AsyncWebCrawler for the complete pipeline
6. Multi-domain discovery across multiple sites

Note: The AsyncUrlSeeder now supports context manager protocol for automatic cleanup.
"""

import asyncio
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    AsyncUrlSeeder,
    SeedingConfig
)

console = Console()

console.rule("[bold green]🌐 Crawl4AI URL Seeder: Interactive Demo")

DOMAIN = "crawl4ai.com"

# Utils

def print_head_info(head_data):
    table = Table(title="<head> Metadata", expand=True)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    
    if not head_data:
        console.print("[yellow]No head data found.")
        return

    if head_data.get("title"):
        table.add_row("title", head_data["title"])
    if head_data.get("charset"):
        table.add_row("charset", head_data["charset"])
    for k, v in head_data.get("meta", {}).items():
        table.add_row(f"meta:{k}", v)
    for rel, items in head_data.get("link", {}).items():
        for item in items:
            table.add_row(f"link:{rel}", item.get("href", ""))
    console.print(table)


async def section_1_basic_exploration(seed: AsyncUrlSeeder):
    console.rule("[bold cyan]1. Basic Seeding")
    cfg = SeedingConfig(source="cc+sitemap", pattern="*", verbose=True)
    
    start_time = time.time()
    with Progress(SpinnerColumn(), "[progress.description]{task.description}") as p:
        p.add_task(description="Fetching from Common Crawl + Sitemap...", total=None)
        urls = await seed.urls(DOMAIN, cfg)
    elapsed = time.time() - start_time

    console.print(f"[green]✓ Fetched {len(urls)} URLs in {elapsed:.2f} seconds")
    console.print(f"[dim]  Speed: {len(urls)/elapsed:.0f} URLs/second[/dim]\n")
    
    console.print("[bold]Sample URLs:[/bold]")
    for u in urls[:5]:
        console.print(f"  • {u['url']}")


async def section_2_cache_demo(seed: AsyncUrlSeeder):
    console.rule("[bold cyan]2. Caching Demonstration")   
    console.print("[yellow]Using `force=True` to bypass cache and fetch fresh data.[/yellow]")
    cfg = SeedingConfig(source="cc", pattern="*crawl4ai.com/core/*", verbose=False, force = True)
    await seed.urls(DOMAIN, cfg)

async def section_3_live_head(seed: AsyncUrlSeeder):
    console.rule("[bold cyan]3. Live Check + Head Extraction")
    cfg = SeedingConfig(
        extract_head=True,
        concurrency=10,
        hits_per_sec=5,
        pattern="*crawl4ai.com/*",
        max_urls=10,
        verbose=False,
    )
    urls = await seed.urls(DOMAIN, cfg)
    
    valid = [u for u in urls if u["status"] == "valid"]
    console.print(f"[green]Valid: {len(valid)} / {len(urls)}")
    if valid:
        print_head_info(valid[0]["head_data"])


async def section_4_bm25_scoring(seed: AsyncUrlSeeder):
    console.rule("[bold cyan]4. BM25 Relevance Scoring")
    console.print("[yellow]Using AI-powered relevance scoring to find the most relevant content[/yellow]")
    
    query = "markdown generation extraction strategies"
    cfg = SeedingConfig(
        source="sitemap",
        extract_head=True,
        query=query,
        scoring_method="bm25",
        score_threshold=0.3,  # Only URLs with >30% relevance
        max_urls=20,
        verbose=False
    )
    
    with Progress(SpinnerColumn(), "[progress.description]{task.description}") as p:
        p.add_task(description=f"Searching for: '{query}'", total=None)
        urls = await seed.urls(DOMAIN, cfg)
    
    console.print(f"[green]Found {len(urls)} relevant URLs (score > 0.3)")
    
    # Show top results with scores
    table = Table(title="Top 5 Most Relevant Pages", expand=True)
    table.add_column("Score", style="cyan", width=8)
    table.add_column("Title", style="magenta")
    table.add_column("URL", style="blue", overflow="fold")
    
    for url in urls[:5]:
        score = f"{url['relevance_score']:.2f}"
        title = url['head_data'].get('title', 'No title')[:60] + "..."
        table.add_row(score, title, url['url'])
    
    console.print(table)

async def section_5_keyword_filter_to_agent(seed: AsyncUrlSeeder):
    console.rule("[bold cyan]5. Complete Pipeline: Discover → Filter → Crawl")
    cfg = SeedingConfig(
        extract_head=True,
        concurrency=20,
        hits_per_sec=10,
        max_urls=10,
        pattern="*crawl4ai.com/*",
        force=True,
    )
    urls = await seed.urls(DOMAIN, cfg)

    keywords = ["deep crawling", "markdown", "llm"]
    selected = [u for u in urls if any(k in str(u["head_data"]).lower() for k in keywords)]

    console.print(f"[cyan]Selected {len(selected)} URLs with relevant keywords:")
    for u in selected[:10]:
        console.print("•", u["url"])

    console.print("\n[yellow]Passing above URLs to arun_many() LLM agent for crawling...")
    async with AsyncWebCrawler(verbose=True) as crawler:
        crawl_run_config = CrawlerRunConfig(
                # Example crawl settings for these URLs:
                only_text=True, # Just get text content
                screenshot=False,
                pdf=False,
                word_count_threshold=50, # Only process pages with at least 50 words
                stream=True,
                verbose=False # Keep logs clean for arun_many in this demo
            )

        # Extract just the URLs from the selected results
        urls_to_crawl = [u["url"] for u in selected]
        
        # We'll stream results for large lists, but collect them here for demonstration
        crawled_results_stream = await crawler.arun_many(urls_to_crawl, config=crawl_run_config)
        final_crawled_data = []
        async for result in crawled_results_stream:
            final_crawled_data.append(result)
            if len(final_crawled_data) % 5 == 0:
                print(f"   Processed {len(final_crawled_data)}/{len(urls_to_crawl)} URLs...")

        print(f"\n   Successfully crawled {len(final_crawled_data)} URLs.")
        if final_crawled_data:
            print("\n   Example of a crawled result's URL and Markdown (first successful one):")
            for result in final_crawled_data:
                if result.success and result.markdown.raw_markdown:
                    print(f"     URL: {result.url}")
                    print(f"     Markdown snippet: {result.markdown.raw_markdown[:200]}...")
                    break
            else:
                print("   No successful crawls with markdown found.")
        else:
            print("   No successful crawls found.")    


async def section_6_multi_domain(seed: AsyncUrlSeeder):
    console.rule("[bold cyan]6. Multi-Domain Discovery")
    console.print("[yellow]Discovering Python tutorials across multiple educational sites[/yellow]\n")
    
    domains = ["docs.python.org", "realpython.com", "docs.crawl4ai.com"]
    cfg = SeedingConfig(
        source="sitemap",
        extract_head=True,
        query="python tutorial guide",
        scoring_method="bm25",
        score_threshold=0.2,
        max_urls=5  # Per domain
    )
    
    start_time = time.time()
    with Progress(SpinnerColumn(), "[progress.description]{task.description}") as p:
        task = p.add_task(description="Discovering across domains...", total=None)
        results = await seed.many_urls(domains, cfg)
    elapsed = time.time() - start_time
    
    total_urls = sum(len(urls) for urls in results.values())
    console.print(f"[green]✓ Found {total_urls} relevant URLs across {len(domains)} domains in {elapsed:.2f}s\n")
    
    # Show results per domain
    for domain, urls in results.items():
        console.print(f"[bold]{domain}:[/bold] {len(urls)} relevant pages")
        if urls:
            top = urls[0]
            console.print(f"  Top result: [{top['relevance_score']:.2f}] {top['head_data'].get('title', 'No title')}")


async def main():
    async with AsyncUrlSeeder() as seed:
        # Interactive menu
        sections = {
            "1": ("Basic URL Discovery", section_1_basic_exploration),
            "2": ("Cache Management Demo", section_2_cache_demo),
            "3": ("Live Check & Metadata Extraction", section_3_live_head),
            "4": ("BM25 Relevance Scoring", section_4_bm25_scoring),
            "5": ("Complete Pipeline (Discover → Filter → Crawl)", section_5_keyword_filter_to_agent),
            "6": ("Multi-Domain Discovery", section_6_multi_domain),
            "7": ("Run All Demos", None)
        }
        
        console.print("\n[bold]Available Demos:[/bold]")
        for key, (title, _) in sections.items():
            console.print(f"  {key}. {title}")
        
        choice = Prompt.ask("\n[cyan]Which demo would you like to run?[/cyan]", 
                           choices=list(sections.keys()), 
                           default="7")
        
        console.print()
        
        if choice == "7":
            # Run all demos
            for key, (title, func) in sections.items():
                if key != "7" and func:
                    await func(seed)
                    if key != "6":  # Don't pause after the last demo
                        if not Confirm.ask("\n[yellow]Continue to next demo?[/yellow]", default=True):
                            break
                        console.print()
        else:
            # Run selected demo
            _, func = sections[choice]
            await func(seed)
        
        console.rule("[bold green]Demo Complete ✔︎")


if __name__ == "__main__":
    asyncio.run(main())
