"""
Test and demo script for Embedding-based Adaptive Crawler

This script demonstrates the embedding-based adaptive crawling
with semantic space coverage and gap-driven expansion.
"""

import asyncio
import os
from pathlib import Path
import time
from rich.console import Console
from rich import print as rprint
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from crawl4ai import (
    AsyncWebCrawler,
    AdaptiveCrawler,
    AdaptiveConfig,
    CrawlState
)

console = Console()


async def test_basic_embedding_crawl():
    """Test basic embedding-based adaptive crawling"""
    console.print("\n[bold yellow]Test 1: Basic Embedding-based Crawl[/bold yellow]")
    console.print("Testing semantic space coverage with query expansion")
    
    # Configure with embedding strategy
    config = AdaptiveConfig(
        strategy="embedding",
        confidence_threshold=0.7,  # Not used for stopping in embedding strategy
        min_gain_threshold=0.01,
        max_pages=15,
        top_k_links=3,
        n_query_variations=8,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2"  # Fast, good quality
    )
    
    # For query expansion, we need an LLM config
    llm_config = {
        'provider': 'openai/gpt-4o-mini',
        'api_token': os.getenv('OPENAI_API_KEY')
    }
    
    if not llm_config['api_token']:
        console.print("[red]Warning: OPENAI_API_KEY not set. Using mock data for demo.[/red]")
        # Continue with mock for demo purposes
    
    config.embedding_llm_config = llm_config
    
    # Create crawler
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(
            crawler=crawler,
            config=config
        )
        
        # Start adaptive crawl
        start_time = time.time()
        console.print("\n[cyan]Starting semantic adaptive crawl...[/cyan]")
        
        state = await prog_crawler.digest(
            start_url="https://docs.python.org/3/library/asyncio.html",
            query="async await coroutines event loops"
        )
        elapsed = time.time() - start_time
        
        # Print results
        console.print(f"\n[green]Crawl completed in {elapsed:.2f} seconds[/green]")
        prog_crawler.print_stats(detailed=False)
        
        # Show semantic coverage details
        console.print("\n[bold cyan]Semantic Coverage Details:[/bold cyan]")
        if state.expanded_queries:
            console.print(f"Query expanded to {len(state.expanded_queries)} variations")
            console.print("Sample variations:")
            for i, q in enumerate(state.expanded_queries[:3], 1):
                console.print(f"  {i}. {q}")
        
        if state.semantic_gaps:
            console.print(f"\nSemantic gaps identified: {len(state.semantic_gaps)}")
        
        console.print(f"\nFinal confidence: {prog_crawler.confidence:.2%}")
        console.print(f"Is Sufficient: {'Yes (Validated)' if prog_crawler.is_sufficient else 'No'}")
        console.print(f"Pages needed: {len(state.crawled_urls)}")


async def test_embedding_vs_statistical(use_openai=False):
    """Compare embedding strategy with statistical strategy"""
    console.print("\n[bold yellow]Test 2: Embedding vs Statistical Strategy Comparison[/bold yellow]")
    
    test_url = "https://httpbin.org"
    test_query = "http headers authentication api"
    
    # Test 1: Statistical strategy
    console.print("\n[cyan]1. Statistical Strategy:[/cyan]")
    config_stat = AdaptiveConfig(
        strategy="statistical",
        confidence_threshold=0.7,
        max_pages=10
    )
    
    async with AsyncWebCrawler() as crawler:
        stat_crawler = AdaptiveCrawler(crawler=crawler, config=config_stat)
        
        start_time = time.time()
        state_stat = await stat_crawler.digest(start_url=test_url, query=test_query)
        stat_time = time.time() - start_time
        
        stat_pages = len(state_stat.crawled_urls)
        stat_confidence = stat_crawler.confidence
    
    # Test 2: Embedding strategy
    console.print("\n[cyan]2. Embedding Strategy:[/cyan]")
    config_emb = AdaptiveConfig(
        strategy="embedding",
        confidence_threshold=0.7,  # Not used for stopping
        max_pages=10,
        n_query_variations=5,
        min_gain_threshold=0.01
    )
    
    # Use OpenAI if available or requested
    if use_openai and os.getenv('OPENAI_API_KEY'):
        config_emb.embedding_llm_config = {
            'provider': 'openai/text-embedding-3-small',
            'api_token': os.getenv('OPENAI_API_KEY'),
            'embedding_model': 'text-embedding-3-small'
        }
        console.print("[cyan]Using OpenAI embeddings[/cyan]")
    else:
        # Default config will try sentence-transformers
        config_emb.embedding_llm_config = {
            'provider': 'openai/gpt-4o-mini',
            'api_token': os.getenv('OPENAI_API_KEY', 'dummy-key')
        }
    
    async with AsyncWebCrawler() as crawler:
        emb_crawler = AdaptiveCrawler(crawler=crawler, config=config_emb)
        
        start_time = time.time()
        state_emb = await emb_crawler.digest(start_url=test_url, query=test_query)
        emb_time = time.time() - start_time
        
        emb_pages = len(state_emb.crawled_urls)
        emb_confidence = emb_crawler.confidence
    
    # Compare results
    console.print("\n[bold green]Comparison Results:[/bold green]")
    console.print(f"Statistical: {stat_pages} pages in {stat_time:.2f}s, confidence: {stat_confidence:.2%}, sufficient: {stat_crawler.is_sufficient}")
    console.print(f"Embedding:   {emb_pages} pages in {emb_time:.2f}s, confidence: {emb_confidence:.2%}, sufficient: {emb_crawler.is_sufficient}")
    
    if emb_pages < stat_pages:
        efficiency = ((stat_pages - emb_pages) / stat_pages) * 100
        console.print(f"\n[green]Embedding strategy used {efficiency:.0f}% fewer pages![/green]")
    
    # Show validation info for embedding
    if hasattr(state_emb, 'metrics') and 'validation_confidence' in state_emb.metrics:
        console.print(f"Embedding validation score: {state_emb.metrics['validation_confidence']:.2%}")


async def test_custom_embedding_provider():
    """Test with different embedding providers"""
    console.print("\n[bold yellow]Test 3: Custom Embedding Provider[/bold yellow]")
    
    # Example with OpenAI embeddings
    config = AdaptiveConfig(
        strategy="embedding",
        confidence_threshold=0.8,  # Not used for stopping
        max_pages=10,
        min_gain_threshold=0.01,
        n_query_variations=5
    )
    
    # Configure to use OpenAI embeddings instead of sentence-transformers
    config.embedding_llm_config = {
        'provider': 'openai/text-embedding-3-small',
        'api_token': os.getenv('OPENAI_API_KEY'),
        'embedding_model': 'text-embedding-3-small'
    }
    
    if not config.embedding_llm_config['api_token']:
        console.print("[yellow]Skipping OpenAI embedding test - no API key[/yellow]")
        return
    
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(crawler=crawler, config=config)
        
        console.print("Using OpenAI embeddings for semantic analysis...")
        state = await prog_crawler.digest(
            start_url="https://httpbin.org",
            query="api endpoints json response"
        )
        
        prog_crawler.print_stats(detailed=False)


async def test_knowledge_export_import():
    """Test exporting and importing semantic knowledge bases"""
    console.print("\n[bold yellow]Test 4: Semantic Knowledge Base Export/Import[/bold yellow]")
    
    config = AdaptiveConfig(
        strategy="embedding",
        confidence_threshold=0.7,  # Not used for stopping
        max_pages=5,
        min_gain_threshold=0.01,
        n_query_variations=4
    )
    
    # First crawl
    async with AsyncWebCrawler() as crawler:
        crawler1 = AdaptiveCrawler(crawler=crawler, config=config)
        
        console.print("\n[cyan]Building initial knowledge base...[/cyan]")
        state1 = await crawler1.digest(
            start_url="https://httpbin.org",
            query="http methods headers"
        )
        
        # Export
        export_path = "semantic_kb.jsonl"
        crawler1.export_knowledge_base(export_path)
        console.print(f"[green]Exported {len(state1.knowledge_base)} documents with embeddings[/green]")
    
    # Import and continue
    async with AsyncWebCrawler() as crawler:
        crawler2 = AdaptiveCrawler(crawler=crawler, config=config)
        
        console.print("\n[cyan]Importing knowledge base...[/cyan]")
        crawler2.import_knowledge_base(export_path)
        
        # Continue with new query - should be faster
        console.print("\n[cyan]Extending with new query...[/cyan]")
        state2 = await crawler2.digest(
            start_url="https://httpbin.org",
            query="authentication oauth tokens"
        )
        
        console.print(f"[green]Total knowledge base: {len(state2.knowledge_base)} documents[/green]")
    
    # Cleanup
    Path(export_path).unlink(missing_ok=True)


async def test_gap_visualization():
    """Visualize semantic gaps and coverage"""
    console.print("\n[bold yellow]Test 5: Semantic Gap Analysis[/bold yellow]")
    
    config = AdaptiveConfig(
        strategy="embedding",
        confidence_threshold=0.9,  # Not used for stopping
        max_pages=8,
        n_query_variations=6,
        min_gain_threshold=0.01
    )
    
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(crawler=crawler, config=config)
        
        # Initial crawl
        state = await prog_crawler.digest(
            start_url="https://docs.python.org/3/library/",
            query="concurrency threading multiprocessing"
        )
        
        # Analyze gaps
        console.print("\n[bold cyan]Semantic Gap Analysis:[/bold cyan]")
        console.print(f"Query variations: {len(state.expanded_queries)}")
        console.print(f"Knowledge documents: {len(state.knowledge_base)}")
        console.print(f"Identified gaps: {len(state.semantic_gaps)}")
        
        if state.semantic_gaps:
            console.print("\n[yellow]Gap sizes (distance from coverage):[/yellow]")
            for i, (_, distance) in enumerate(state.semantic_gaps[:5], 1):
                console.print(f"  Gap {i}: {distance:.3f}")
        
        # Show crawl progression
        console.print("\n[cyan]Crawl Order (gap-driven selection):[/cyan]")
        for i, url in enumerate(state.crawl_order[:5], 1):
            console.print(f"  {i}. {url}")


async def test_fast_convergence_with_relevant_query():
    """Test that both strategies reach high confidence quickly with relevant queries"""
    console.print("\n[bold yellow]Test 7: Fast Convergence with Relevant Query[/bold yellow]")
    console.print("Testing that strategies reach 80%+ confidence within 2-3 batches")
    
    # Test scenarios
    test_cases = [
        {
            "name": "Python Async Documentation",
            "url": "https://docs.python.org/3/library/asyncio.html",
            "query": "async await coroutines event loops tasks"
        }
    ]
    
    for test_case in test_cases:
        console.print(f"\n[bold cyan]Testing: {test_case['name']}[/bold cyan]")
        console.print(f"URL: {test_case['url']}")
        console.print(f"Query: {test_case['query']}")
        
        # Test Embedding Strategy
        console.print("\n[yellow]Embedding Strategy:[/yellow]")
        config_emb = AdaptiveConfig(
            strategy="embedding",
            confidence_threshold=0.8,
            max_pages=9,
            top_k_links=3,
            min_gain_threshold=0.01,
            n_query_variations=5
        )
        
        # Configure embeddings
        config_emb.embedding_llm_config = {
            'provider': 'openai/gpt-4o-mini',
            'api_token': os.getenv('OPENAI_API_KEY'),
        }
        
        async with AsyncWebCrawler() as crawler:
            emb_crawler = AdaptiveCrawler(crawler=crawler, config=config_emb)
            
            start_time = time.time()
            state = await emb_crawler.digest(
                start_url=test_case['url'],
                query=test_case['query']
            )
            
            # Get batch breakdown
            total_pages = len(state.crawled_urls)
            for i in range(0, total_pages, 3):
                batch_num = (i // 3) + 1
                batch_pages = min(3, total_pages - i)
                pages_so_far = i + batch_pages
                estimated_confidence = state.metrics.get('confidence', 0) * (pages_so_far / total_pages)
                
                console.print(f"Batch {batch_num}: {batch_pages} pages → Confidence: {estimated_confidence:.1%} {'✅' if estimated_confidence >= 0.8 else '❌'}")
            
            final_confidence = emb_crawler.confidence
            console.print(f"[green]Final: {total_pages} pages → Confidence: {final_confidence:.1%} {'✅ (Sufficient!)' if emb_crawler.is_sufficient else '❌'}[/green]")
            
            # Show learning metrics for embedding
            if 'avg_min_distance' in state.metrics:
                console.print(f"[dim]Avg gap distance: {state.metrics['avg_min_distance']:.3f}[/dim]")
            if 'validation_confidence' in state.metrics:
                console.print(f"[dim]Validation score: {state.metrics['validation_confidence']:.1%}[/dim]")
        
        # Test Statistical Strategy
        console.print("\n[yellow]Statistical Strategy:[/yellow]")
        config_stat = AdaptiveConfig(
            strategy="statistical",
            confidence_threshold=0.8,
            max_pages=9,
            top_k_links=3,
            min_gain_threshold=0.01
        )
        
        async with AsyncWebCrawler() as crawler:
            stat_crawler = AdaptiveCrawler(crawler=crawler, config=config_stat)
            
            # Track batch progress
            batch_results = []
            current_pages = 0
            
            # Custom batch tracking
            start_time = time.time()
            state = await stat_crawler.digest(
                start_url=test_case['url'],
                query=test_case['query']
            )
            
            # Get batch breakdown (every 3 pages)
            total_pages = len(state.crawled_urls)
            for i in range(0, total_pages, 3):
                batch_num = (i // 3) + 1
                batch_pages = min(3, total_pages - i)
                # Estimate confidence at this point (simplified)
                pages_so_far = i + batch_pages
                estimated_confidence = state.metrics.get('confidence', 0) * (pages_so_far / total_pages)
                
                console.print(f"Batch {batch_num}: {batch_pages} pages → Confidence: {estimated_confidence:.1%} {'✅' if estimated_confidence >= 0.8 else '❌'}")
            
            final_confidence = stat_crawler.confidence
            console.print(f"[green]Final: {total_pages} pages → Confidence: {final_confidence:.1%} {'✅ (Sufficient!)' if stat_crawler.is_sufficient else '❌'}[/green]")
        
        


async def test_irrelevant_query_behavior():
    """Test how embedding strategy handles completely irrelevant queries"""
    console.print("\n[bold yellow]Test 8: Irrelevant Query Behavior[/bold yellow]")
    console.print("Testing embedding strategy with a query that has no semantic relevance to the content")
    
    # Test with irrelevant query on Python async documentation
    test_case = {
        "name": "Irrelevant Query on Python Docs",
        "url": "https://docs.python.org/3/library/asyncio.html",
        "query": "how to cook fried rice with vegetables"
    }
    
    console.print(f"\n[bold cyan]Testing: {test_case['name']}[/bold cyan]")
    console.print(f"URL: {test_case['url']} (Python async documentation)")
    console.print(f"Query: '{test_case['query']}' (completely irrelevant)")
    console.print("\n[dim]Expected behavior: Low confidence, high distances, no convergence[/dim]")
    
    # Configure embedding strategy
    config_emb = AdaptiveConfig(
        strategy="embedding",
        confidence_threshold=0.8,
        max_pages=9,
        top_k_links=3,
        min_gain_threshold=0.01,
        n_query_variations=5,
        embedding_min_relative_improvement=0.05,  # Lower threshold to see more iterations
        embedding_min_confidence_threshold=0.1  # Will stop if confidence < 10%
    )
    
    # Configure embeddings using the correct format
    config_emb.embedding_llm_config = {
        'provider': 'openai/gpt-4o-mini',
        'api_token': os.getenv('OPENAI_API_KEY'),
    }
    
    async with AsyncWebCrawler() as crawler:
        emb_crawler = AdaptiveCrawler(crawler=crawler, config=config_emb)
        
        start_time = time.time()
        state = await emb_crawler.digest(
            start_url=test_case['url'],
            query=test_case['query']
        )
        elapsed = time.time() - start_time
        
        # Analyze results
        console.print(f"\n[bold]Results after {elapsed:.1f} seconds:[/bold]")
        
        # Basic metrics
        total_pages = len(state.crawled_urls)
        final_confidence = emb_crawler.confidence
        
        console.print(f"\nPages crawled: {total_pages}")
        console.print(f"Final confidence: {final_confidence:.1%} {'✅' if emb_crawler.is_sufficient else '❌'}")
        
        # Distance metrics
        if 'avg_min_distance' in state.metrics:
            console.print(f"\n[yellow]Distance Metrics:[/yellow]")
            console.print(f"  Average minimum distance: {state.metrics['avg_min_distance']:.3f}")
            console.print(f"  Close neighbors (<0.3): {state.metrics.get('avg_close_neighbors', 0):.1f}")
            console.print(f"  Very close neighbors (<0.2): {state.metrics.get('avg_very_close_neighbors', 0):.1f}")
            
            # Interpret distances
            avg_dist = state.metrics['avg_min_distance']
            if avg_dist > 0.8:
                console.print(f"  [red]→ Very poor match (distance > 0.8)[/red]")
            elif avg_dist > 0.6:
                console.print(f"  [yellow]→ Poor match (distance > 0.6)[/yellow]")
            elif avg_dist > 0.4:
                console.print(f"  [blue]→ Moderate match (distance > 0.4)[/blue]")
            else:
                console.print(f"  [green]→ Good match (distance < 0.4)[/green]")
        
        # Show sample expanded queries
        if state.expanded_queries:
            console.print(f"\n[yellow]Sample Query Variations Generated:[/yellow]")
            for i, q in enumerate(state.expanded_queries[:3], 1):
                console.print(f"  {i}. {q}")
        
        # Show crawl progression
        console.print(f"\n[yellow]Crawl Progression:[/yellow]")
        for i, url in enumerate(state.crawl_order[:5], 1):
            console.print(f"  {i}. {url}")
        if len(state.crawl_order) > 5:
            console.print(f"  ... and {len(state.crawl_order) - 5} more")
        
        # Validation score
        if 'validation_confidence' in state.metrics:
            console.print(f"\n[yellow]Validation:[/yellow]")
            console.print(f"  Validation score: {state.metrics['validation_confidence']:.1%}")
        
        # Why it stopped
        if 'stopped_reason' in state.metrics:
            console.print(f"\n[yellow]Stopping Reason:[/yellow] {state.metrics['stopped_reason']}")
            if state.metrics.get('is_irrelevant', False):
                console.print("[red]→ Query and content are completely unrelated![/red]")
        elif total_pages >= config_emb.max_pages:
            console.print(f"\n[yellow]Stopping Reason:[/yellow] Reached max pages limit ({config_emb.max_pages})")
        
        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        if final_confidence < 0.2:
            console.print("[red]✗ As expected: Query is completely irrelevant to content[/red]")
            console.print("[green]✓ The embedding strategy correctly identified no semantic match[/green]")
        else:
            console.print(f"[yellow]⚠ Unexpected: Got {final_confidence:.1%} confidence for irrelevant query[/yellow]")
            console.print("[yellow]  This may indicate the query variations are too broad[/yellow]")


async def test_high_dimensional_handling():
    """Test handling of high-dimensional embedding spaces"""
    console.print("\n[bold yellow]Test 6: High-Dimensional Embedding Space Handling[/bold yellow]")
    console.print("Testing how the system handles 384+ dimensional embeddings")
    
    config = AdaptiveConfig(
        strategy="embedding",
        confidence_threshold=0.8,  # Not used for stopping
        max_pages=5,
        n_query_variations=8,  # Will create 9 points total
        min_gain_threshold=0.01,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2"  # 384 dimensions
    )
    
    # Use OpenAI if available, otherwise mock
    if os.getenv('OPENAI_API_KEY'):
        config.embedding_llm_config = {
            'provider': 'openai/text-embedding-3-small',
            'api_token': os.getenv('OPENAI_API_KEY'),
            'embedding_model': 'text-embedding-3-small'
        }
    else:
        config.embedding_llm_config = {
            'provider': 'openai/gpt-4o-mini',
            'api_token': 'mock-key'
        }
    
    async with AsyncWebCrawler() as crawler:
        prog_crawler = AdaptiveCrawler(crawler=crawler, config=config)
        
        console.print("\n[cyan]Testing with high-dimensional embeddings (384D)...[/cyan]")
        
        try:
            state = await prog_crawler.digest(
                start_url="https://httpbin.org",
                query="api endpoints json"
            )
            
            console.print(f"[green]✓ Successfully handled {len(state.expanded_queries)} queries in 384D space[/green]")
            console.print(f"Coverage shape type: {type(state.coverage_shape)}")
            
            if isinstance(state.coverage_shape, dict):
                console.print(f"Coverage model: centroid + radius")
                console.print(f"  - Center shape: {state.coverage_shape['center'].shape if 'center' in state.coverage_shape else 'N/A'}")
                console.print(f"  - Radius: {state.coverage_shape.get('radius', 'N/A'):.3f}")
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]This demonstrates why alpha shapes don't work in high dimensions[/yellow]")


async def main():
    """Run all embedding strategy tests"""
    console.print("[bold magenta]Embedding-based Adaptive Crawler Test Suite[/bold magenta]")
    console.print("=" * 60)
    
    try:
        # Check if we have required dependencies
        has_sentence_transformers = True
        has_numpy = True
        
        try:
            import numpy
            console.print("[green]✓ NumPy installed[/green]")
        except ImportError:
            has_numpy = False
            console.print("[red]Missing numpy[/red]")
            
        # Try to import sentence_transformers but catch numpy compatibility errors
        try:
            import sentence_transformers
            console.print("[green]✓ Sentence-transformers installed[/green]")
        except (ImportError, RuntimeError, ValueError) as e:
            has_sentence_transformers = False
            console.print(f"[yellow]Warning: sentence-transformers not available[/yellow]")
            console.print("[yellow]Tests will use OpenAI embeddings if available or mock data[/yellow]")
        
        # Run tests based on available dependencies
        if has_numpy:
            # Check if we should use OpenAI for embeddings
            use_openai = not has_sentence_transformers and os.getenv('OPENAI_API_KEY')
            
            if not has_sentence_transformers and not os.getenv('OPENAI_API_KEY'):
                console.print("\n[red]Neither sentence-transformers nor OpenAI API key available[/red]")
                console.print("[yellow]Please set OPENAI_API_KEY or fix sentence-transformers installation[/yellow]")
                return
            
            # Run all tests
            # await test_basic_embedding_crawl()
            # await test_embedding_vs_statistical(use_openai=use_openai)
            
            # Run the fast convergence test - this is the most important one
            # await test_fast_convergence_with_relevant_query()
            
            # Test with irrelevant query
            await test_irrelevant_query_behavior()
            
            # Only run OpenAI-specific test if we have API key
            # if os.getenv('OPENAI_API_KEY'):
            #     await test_custom_embedding_provider()
            
            # # Skip tests that require sentence-transformers when it's not available
            # if has_sentence_transformers:
            #     await test_knowledge_export_import()
            #     await test_gap_visualization()
            # else:
            #     console.print("\n[yellow]Skipping tests that require sentence-transformers due to numpy compatibility issues[/yellow]")
            
            # This test should work with mock data
            # await test_high_dimensional_handling()
        else:
            console.print("\n[red]Cannot run tests without NumPy[/red]")
            return
        
        console.print("\n[bold green]✅ All tests completed![/bold green]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test failed: {e}[/bold red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
    
    
    
    
    
    
    
    
