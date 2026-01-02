"""
Test and demo script for Adaptive Crawler

This script demonstrates the progressive crawling functionality
with various configurations and use cases.
"""

import asyncio
import json
from pathlib import Path
import time
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich import print as rprint

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from crawl4ai import (
    AsyncWebCrawler,
    AdaptiveCrawler,
    AdaptiveConfig,
    CrawlState
)


console = Console()




def print_relevant_content(crawler: AdaptiveCrawler, top_k: int = 3):
    """Print most relevant content found"""
    relevant = crawler.get_relevant_content(top_k=top_k)
    
    if not relevant:
        console.print("[yellow]No relevant content found yet.[/yellow]")
        return
    
    console.print(f"\n[bold cyan]Top {len(relevant)} Most Relevant Pages:[/bold cyan]")
    for i, doc in enumerate(relevant, 1):
        console.print(f"\n[green]{i}. {doc['url']}[/green]")
        console.print(f"   Score: {doc['score']:.2f}")
        # Show snippet
        content = doc['content'] or ""
        snippet = content[:200].replace('\n', ' ') + "..." if len(content) > 200 else content
        console.print(f"   [dim]{snippet}[/dim]")


async def test_basic_progressive_crawl():
    """Test basic progressive crawling functionality"""
    console.print("\n[bold yellow]Test 1: Basic Progressive Crawl[/bold yellow]")
    console.print("Testing on Python documentation with query about async/await")
    
    config = AdaptiveConfig(
        confidence_threshold=0.7,
        max_pages=10,
        top_k_links=2,
        min_gain_threshold=0.1
    )
    
    # Create crawler
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(
            crawler=crawler,
            config=config
        )
        
        # Start progressive crawl
        start_time = time.time()
        state = await prog_crawler.digest(
            start_url="https://docs.python.org/3/library/asyncio.html",
            query="async await context managers"
        )
        elapsed = time.time() - start_time
        
        # Print results
        prog_crawler.print_stats(detailed=False)
        prog_crawler.print_stats(detailed=True)
        print_relevant_content(prog_crawler)
        
        console.print(f"\n[green]Crawl completed in {elapsed:.2f} seconds[/green]")
        console.print(f"Final confidence: {prog_crawler.confidence:.2%}")
        console.print(f"URLs crawled: {list(state.crawled_urls)[:5]}...")  # Show first 5
        
        # Test export functionality
        export_path = "knowledge_base_export.jsonl"
        prog_crawler.export_knowledge_base(export_path)
        console.print(f"[green]Knowledge base exported to {export_path}[/green]")
        
        # Clean up
        Path(export_path).unlink(missing_ok=True)


async def test_with_persistence():
    """Test state persistence and resumption"""
    console.print("\n[bold yellow]Test 2: Persistence and Resumption[/bold yellow]")
    console.print("Testing state save/load functionality")
    
    state_path = "test_crawl_state.json"
    
    config = AdaptiveConfig(
        confidence_threshold=0.6,
        max_pages=5,
        top_k_links=2,
        save_state=True,
        state_path=state_path
    )
    
    # First crawl - partial
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(
            crawler=crawler,
            config=config
        )
        
        state1 = await prog_crawler.digest(
            start_url="https://httpbin.org",
            query="http headers response"
        )
        
        console.print(f"[cyan]First crawl: {len(state1.crawled_urls)} pages[/cyan]")
        
    # Resume crawl
    config.max_pages = 10  # Increase limit
    
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(
            crawler=crawler,
            config=config
        )
        
        state2 = await prog_crawler.digest(
            start_url="https://httpbin.org",
            query="http headers response",
            resume_from=state_path
        )
        
        console.print(f"[green]Resumed crawl: {len(state2.crawled_urls)} total pages[/green]")
        
    # Clean up
    Path(state_path).unlink(missing_ok=True)


async def test_different_domains():
    """Test on different types of websites"""
    console.print("\n[bold yellow]Test 3: Different Domain Types[/bold yellow]")
    
    test_cases = [
        {
            "name": "Documentation Site",
            "url": "https://docs.python.org/3/",
            "query": "decorators and context managers"
        },
        {
            "name": "API Documentation",  
            "url": "https://httpbin.org",
            "query": "http authentication headers"
        }
    ]
    
    for test in test_cases:
        console.print(f"\n[cyan]Testing: {test['name']}[/cyan]")
        console.print(f"URL: {test['url']}")
        console.print(f"Query: {test['query']}")
        
        config = AdaptiveConfig(
            confidence_threshold=0.6,
            max_pages=5,
            top_k_links=2
        )
        
        async with AsyncWebCrawler() as crawler:
            prog_crawler = AdaptiveCrawler(
                crawler=crawler,
                config=config
            )
            
            start_time = time.time()
            state = await prog_crawler.digest(
                start_url=test['url'],
                query=test['query']
            )
            elapsed = time.time() - start_time
            
            # Summary using print_stats
            prog_crawler.print_stats(detailed=False)


async def test_stopping_criteria():
    """Test different stopping criteria"""
    console.print("\n[bold yellow]Test 4: Stopping Criteria[/bold yellow]")
    
    # Test 1: High confidence threshold
    console.print("\n[cyan]4.1 High confidence threshold (0.9)[/cyan]")
    config = AdaptiveConfig(
        confidence_threshold=0.9,  # Very high
        max_pages=20,
        top_k_links=3
    )
    
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(crawler=crawler, config=config)
        state = await prog_crawler.digest(
            start_url="https://docs.python.org/3/library/",
            query="python standard library"
        )
        
        console.print(f"Pages needed for 90% confidence: {len(state.crawled_urls)}")
        prog_crawler.print_stats(detailed=False)
    
    # Test 2: Page limit
    console.print("\n[cyan]4.2 Page limit (3 pages max)[/cyan]")
    config = AdaptiveConfig(
        confidence_threshold=0.9,
        max_pages=3,  # Very low limit
        top_k_links=2
    )
    
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(crawler=crawler, config=config)
        state = await prog_crawler.digest(
            start_url="https://docs.python.org/3/library/",
            query="python standard library modules"
        )
        
        console.print(f"Stopped by: {'Page limit' if len(state.crawled_urls) >= 3 else 'Other'}")
        prog_crawler.print_stats(detailed=False)


async def test_crawl_patterns():
    """Analyze crawl patterns and link selection"""
    console.print("\n[bold yellow]Test 5: Crawl Pattern Analysis[/bold yellow]")
    
    config = AdaptiveConfig(
        confidence_threshold=0.7,
        max_pages=8,
        top_k_links=2,
        min_gain_threshold=0.05
    )
    
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(crawler=crawler, config=config)
        
        # Track crawl progress
        console.print("\n[cyan]Crawl Progress:[/cyan]")
        
        state = await prog_crawler.digest(
            start_url="https://httpbin.org",
            query="http methods post get"
        )
        
        # Show crawl order
        console.print("\n[green]Crawl Order:[/green]")
        for i, url in enumerate(state.crawl_order, 1):
            console.print(f"{i}. {url}")
        
        # Show new terms discovered per page
        console.print("\n[green]New Terms Discovered:[/green]")
        for i, new_terms in enumerate(state.new_terms_history, 1):
            console.print(f"Page {i}: {new_terms} new terms")
        
        # Final metrics
        console.print(f"\n[yellow]Saturation reached: {state.metrics.get('saturation', 0):.2%}[/yellow]")


async def main():
    """Run all tests"""
    console.print("[bold magenta]Adaptive Crawler Test Suite[/bold magenta]")
    console.print("=" * 50)
    
    try:
        # Run tests
        await test_basic_progressive_crawl()
        # await test_with_persistence()
        # await test_different_domains()
        # await test_stopping_criteria()
        # await test_crawl_patterns()
        
        console.print("\n[bold green]✅ All tests completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test failed with error: {e}[/bold red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())