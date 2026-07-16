"""
Advanced Adaptive Crawling Configuration

This example demonstrates all configuration options available for adaptive crawling,
including threshold tuning, persistence, and custom parameters.
"""

import asyncio
from pathlib import Path
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig


async def main():
    """Demonstrate advanced configuration options"""
    
    # Example 1: Custom thresholds for different use cases
    print("="*60)
    print("EXAMPLE 1: Custom Confidence Thresholds")
    print("="*60)
    
    # High-precision configuration (exhaustive crawling)
    high_precision_config = AdaptiveConfig(
        confidence_threshold=0.9,      # Very high confidence required
        max_pages=50,                  # Allow more pages
        top_k_links=5,                 # Follow more links per page
        min_gain_threshold=0.02        # Lower threshold to continue
    )
    
    # Balanced configuration (default use case)
    balanced_config = AdaptiveConfig(
        confidence_threshold=0.7,      # Moderate confidence
        max_pages=20,                  # Reasonable limit
        top_k_links=3,                 # Moderate branching
        min_gain_threshold=0.05        # Standard gain threshold
    )
    
    # Quick exploration configuration
    quick_config = AdaptiveConfig(
        confidence_threshold=0.5,      # Lower confidence acceptable
        max_pages=10,                  # Strict limit
        top_k_links=2,                 # Minimal branching
        min_gain_threshold=0.1         # High gain required
    )
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        # Test different configurations
        for config_name, config in [
            ("High Precision", high_precision_config),
            ("Balanced", balanced_config),
            ("Quick Exploration", quick_config)
        ]:
            print(f"\nTesting {config_name} configuration...")
            adaptive = AdaptiveCrawler(crawler, config=config)
            
            result = await adaptive.digest(
                start_url="https://httpbin.org",
                query="http headers authentication"
            )
            
            print(f"  - Pages crawled: {len(result.crawled_urls)}")
            print(f"  - Confidence achieved: {adaptive.confidence:.2%}")
            print(f"  - Coverage score: {adaptive.coverage_stats['coverage']:.2f}")
    
    # Example 2: Persistence and state management
    print("\n" + "="*60)
    print("EXAMPLE 2: State Persistence")
    print("="*60)
    
    state_file = "crawl_state_demo.json"
    
    # Configuration with persistence
    persistent_config = AdaptiveConfig(
        confidence_threshold=0.8,
        max_pages=30,
        save_state=True,              # Enable auto-save
        state_path=state_file         # Specify save location
    )
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        # First crawl - will be interrupted
        print("\nStarting initial crawl (will interrupt after 5 pages)...")
        
        interrupt_config = AdaptiveConfig(
            confidence_threshold=0.8,
            max_pages=5,              # Artificially low to simulate interruption
            save_state=True,
            state_path=state_file
        )
        
        adaptive = AdaptiveCrawler(crawler, config=interrupt_config)
        result1 = await adaptive.digest(
            start_url="https://docs.python.org/3/",
            query="exception handling try except finally"
        )
        
        print(f"First crawl completed: {len(result1.crawled_urls)} pages")
        print(f"Confidence reached: {adaptive.confidence:.2%}")
        
        # Resume crawl with higher page limit
        print("\nResuming crawl from saved state...")
        
        resume_config = AdaptiveConfig(
            confidence_threshold=0.8,
            max_pages=20,             # Increase limit
            save_state=True,
            state_path=state_file
        )
        
        adaptive2 = AdaptiveCrawler(crawler, config=resume_config)
        result2 = await adaptive2.digest(
            start_url="https://docs.python.org/3/",
            query="exception handling try except finally",
            resume_from=state_file
        )
        
        print(f"Resumed crawl completed: {len(result2.crawled_urls)} total pages")
        print(f"Final confidence: {adaptive2.confidence:.2%}")
        
        # Clean up
        Path(state_file).unlink(missing_ok=True)
    
    # Example 3: Link selection strategies
    print("\n" + "="*60)
    print("EXAMPLE 3: Link Selection Strategies")
    print("="*60)
    
    # Conservative link following
    conservative_config = AdaptiveConfig(
        confidence_threshold=0.7,
        max_pages=15,
        top_k_links=1,                # Only follow best link
        min_gain_threshold=0.15       # High threshold
    )
    
    # Aggressive link following
    aggressive_config = AdaptiveConfig(
        confidence_threshold=0.7,
        max_pages=15,
        top_k_links=10,               # Follow many links
        min_gain_threshold=0.01       # Very low threshold
    )
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        for strategy_name, config in [
            ("Conservative", conservative_config),
            ("Aggressive", aggressive_config)
        ]:
            print(f"\n{strategy_name} link selection:")
            adaptive = AdaptiveCrawler(crawler, config=config)
            
            result = await adaptive.digest(
                start_url="https://httpbin.org",
                query="api endpoints"
            )
            
            # Analyze crawl pattern
            print(f"  - Total pages: {len(result.crawled_urls)}")
            print(f"  - Unique domains: {len(set(url.split('/')[2] for url in result.crawled_urls))}")
            print(f"  - Max depth reached: {max(url.count('/') for url in result.crawled_urls) - 2}")
            
            # Show saturation trend
            if hasattr(result, 'new_terms_history') and result.new_terms_history:
                print(f"  - New terms discovered: {result.new_terms_history[:5]}...")
                print(f"  - Saturation trend: {'decreasing' if result.new_terms_history[-1] < result.new_terms_history[0] else 'increasing'}")
    
    # Example 4: Monitoring crawl progress
    print("\n" + "="*60)
    print("EXAMPLE 4: Progress Monitoring")
    print("="*60)
    
    # Configuration with detailed monitoring
    monitor_config = AdaptiveConfig(
        confidence_threshold=0.75,
        max_pages=10,
        top_k_links=3
    )
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        adaptive = AdaptiveCrawler(crawler, config=monitor_config)
        
        # Start crawl
        print("\nMonitoring crawl progress...")
        result = await adaptive.digest(
            start_url="https://httpbin.org",
            query="http methods headers"
        )
        
        # Detailed statistics
        print("\nDetailed crawl analysis:")
        adaptive.print_stats(detailed=True)
        
        # Export for analysis
        print("\nExporting knowledge base for external analysis...")
        adaptive.export_knowledge_base("knowledge_export_demo.jsonl")
        print("Knowledge base exported to: knowledge_export_demo.jsonl")
        
        # Show sample of exported data
        with open("knowledge_export_demo.jsonl", 'r') as f:
            first_line = f.readline()
            print(f"Sample export: {first_line[:100]}...")
        
        # Clean up
        Path("knowledge_export_demo.jsonl").unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())