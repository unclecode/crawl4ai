"""
Advanced Embedding Configuration Example

This example demonstrates all configuration options available for the
embedding strategy, including fine-tuning parameters for different use cases.
"""

import asyncio
import os
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig


async def test_configuration(name: str, config: AdaptiveConfig, url: str, query: str):
    """Test a specific configuration"""
    print(f"\n{'='*60}")
    print(f"Configuration: {name}")
    print(f"{'='*60}")
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        adaptive = AdaptiveCrawler(crawler, config)
        result = await adaptive.digest(start_url=url, query=query)
        
        print(f"Pages crawled: {len(result.crawled_urls)}")
        print(f"Final confidence: {adaptive.confidence:.1%}")
        print(f"Stopped reason: {result.metrics.get('stopped_reason', 'max_pages')}")
        
        if result.metrics.get('is_irrelevant', False):
            print("⚠️  Query detected as irrelevant!")
        
        return result


async def main():
    """Demonstrate various embedding configurations"""
    
    print("EMBEDDING STRATEGY CONFIGURATION EXAMPLES")
    print("=" * 60)
    
    # Base URL and query for testing
    test_url = "https://docs.python.org/3/library/asyncio.html"
    
    # 1. Default Configuration
    config_default = AdaptiveConfig(
        strategy="embedding",
        max_pages=10
    )
    
    await test_configuration(
        "Default Settings",
        config_default,
        test_url,
        "async programming patterns"
    )
    
    # 2. Strict Coverage Requirements
    config_strict = AdaptiveConfig(
        strategy="embedding",
        max_pages=20,
        
        # Stricter similarity requirements
        embedding_k_exp=5.0,  # Default is 3.0, higher = stricter
        embedding_coverage_radius=0.15,  # Default is 0.2, lower = stricter
        
        # Higher validation threshold
        embedding_validation_min_score=0.6,  # Default is 0.3
        
        # More query variations for better coverage
        n_query_variations=15  # Default is 10
    )
    
    await test_configuration(
        "Strict Coverage (Research/Academic)",
        config_strict,
        test_url,
        "comprehensive guide async await"
    )
    
    # 3. Fast Exploration
    config_fast = AdaptiveConfig(
        strategy="embedding",
        max_pages=10,
        top_k_links=5,  # Follow more links per page
        
        # Relaxed requirements for faster convergence
        embedding_k_exp=1.0,  # Lower = more lenient
        embedding_min_relative_improvement=0.05,  # Stop earlier
        
        # Lower quality thresholds
        embedding_quality_min_confidence=0.5,  # Display lower confidence
        embedding_quality_max_confidence=0.85,
        
        # Fewer query variations for speed
        n_query_variations=5
    )
    
    await test_configuration(
        "Fast Exploration (Quick Overview)",
        config_fast,
        test_url,
        "async basics"
    )
    
    # 4. Irrelevance Detection Focus
    config_irrelevance = AdaptiveConfig(
        strategy="embedding",
        max_pages=5,
        
        # Aggressive irrelevance detection
        embedding_min_confidence_threshold=0.2,  # Higher threshold (default 0.1)
        embedding_k_exp=5.0,  # Strict similarity
        
        # Quick stopping for irrelevant content
        embedding_min_relative_improvement=0.15
    )
    
    await test_configuration(
        "Irrelevance Detection",
        config_irrelevance,
        test_url,
        "recipe for chocolate cake"  # Irrelevant query
    )
    
    # 5. High-Quality Knowledge Base
    config_quality = AdaptiveConfig(
        strategy="embedding",
        max_pages=30,
        
        # Deduplication settings
        embedding_overlap_threshold=0.75,  # More aggressive deduplication
        
        # Quality focus
        embedding_validation_min_score=0.5,
        embedding_quality_scale_factor=1.0,  # Linear quality mapping
        
        # Balanced parameters
        embedding_k_exp=3.0,
        embedding_nearest_weight=0.8,  # Focus on best matches
        embedding_top_k_weight=0.2
    )
    
    await test_configuration(
        "High-Quality Knowledge Base",
        config_quality,
        test_url,
        "asyncio advanced patterns best practices"
    )
    
    # 6. Custom Embedding Provider
    if os.getenv('OPENAI_API_KEY'):
        config_openai = AdaptiveConfig(
            strategy="embedding",
            max_pages=10,
            
            # Use OpenAI embeddings
            embedding_llm_config={
                'provider': 'openai/text-embedding-3-small',
                'api_token': os.getenv('OPENAI_API_KEY')
            },
            
            # OpenAI embeddings are high quality, can be stricter
            embedding_k_exp=4.0,
            n_query_variations=12
        )
        
        await test_configuration(
            "OpenAI Embeddings",
            config_openai,
            test_url,
            "event-driven architecture patterns"
        )
    
    # Parameter Guide
    print("\n" + "="*60)
    print("PARAMETER TUNING GUIDE")
    print("="*60)
    
    print("\n📊 Key Parameters and Their Effects:")
    print("\n1. embedding_k_exp (default: 3.0)")
    print("   - Lower (1-2): More lenient, faster convergence")
    print("   - Higher (4-5): Stricter, better precision")
    
    print("\n2. embedding_coverage_radius (default: 0.2)")
    print("   - Lower (0.1-0.15): Requires closer matches")
    print("   - Higher (0.25-0.3): Accepts broader matches")
    
    print("\n3. n_query_variations (default: 10)")
    print("   - Lower (5-7): Faster, less comprehensive")
    print("   - Higher (15-20): Better coverage, slower")
    
    print("\n4. embedding_min_confidence_threshold (default: 0.1)")
    print("   - Set to 0.15-0.2 for aggressive irrelevance detection")
    print("   - Set to 0.05 to crawl even barely relevant content")
    
    print("\n5. embedding_validation_min_score (default: 0.3)")
    print("   - Higher (0.5-0.6): Requires strong validation")
    print("   - Lower (0.2): More permissive stopping")
    
    print("\n💡 Tips:")
    print("- For research: High k_exp, more variations, strict validation")
    print("- For exploration: Low k_exp, fewer variations, relaxed thresholds")
    print("- For quality: Focus on overlap_threshold and validation scores")
    print("- For speed: Reduce variations, increase min_relative_improvement")


if __name__ == "__main__":
    asyncio.run(main())