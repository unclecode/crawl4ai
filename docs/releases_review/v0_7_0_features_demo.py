"""
🚀 Crawl4AI v0.7.0 Feature Demo
================================
This file demonstrates the major features introduced in v0.7.0 with practical examples.
"""

import asyncio
import json
from pathlib import Path
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BrowserConfig,
    CacheMode,
    # New imports for v0.7.0
    VirtualScrollConfig,
    LinkPreviewConfig,
    AdaptiveCrawler,
    AdaptiveConfig,
    AsyncUrlSeeder,
    SeedingConfig,
    c4a_compile,
)


async def demo_link_preview():
    """
    Demo 1: Link Preview with 3-Layer Scoring
    
    Shows how to analyze links with intrinsic quality scores,
    contextual relevance, and combined total scores.
    """
    print("\n" + "="*60)
    print("🔗 DEMO 1: Link Preview & Intelligent Scoring")
    print("="*60)
    
    # Configure link preview with contextual scoring
    config = CrawlerRunConfig(
        link_preview_config=LinkPreviewConfig(
            include_internal=True,
            include_external=False,
            max_links=10,
            concurrency=5,
            query="machine learning tutorials",  # For contextual scoring
            score_threshold=0.3,  # Minimum relevance
            verbose=True
        ),
        score_links=True,  # Enable intrinsic scoring
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://scikit-learn.org/stable/", config=config)
        
        if result.success:
            # Get scored links
            internal_links = result.links.get("internal", [])
            scored_links = [l for l in internal_links if l.get("total_score")]
            scored_links.sort(key=lambda x: x.get("total_score", 0), reverse=True)
            
            print(f"\nTop 5 Most Relevant Links:")
            for i, link in enumerate(scored_links[:5], 1):
                print(f"\n{i}. {link.get('text', 'No text')[:50]}...")
                print(f"   URL: {link['href']}")
                print(f"   Intrinsic Score: {link.get('intrinsic_score', 0):.2f}/10")
                print(f"   Contextual Score: {link.get('contextual_score', 0):.3f}")
                print(f"   Total Score: {link.get('total_score', 0):.3f}")
                
                # Show metadata if available
                if link.get('head_data'):
                    title = link['head_data'].get('title', 'No title')
                    print(f"   Title: {title[:60]}...")


async def demo_adaptive_crawling():
    """
    Demo 2: Adaptive Crawling
    
    Shows intelligent crawling that stops when enough information
    is gathered, with confidence tracking.
    """
    print("\n" + "="*60)
    print("🎯 DEMO 2: Adaptive Crawling with Confidence Tracking")
    print("="*60)
    
    # Configure adaptive crawler
    config = AdaptiveConfig(
        strategy="statistical",  # or "embedding" for semantic understanding
        max_pages=10,
        confidence_threshold=0.7,  # Stop at 70% confidence
        top_k_links=3,  # Follow top 3 links per page
        min_gain_threshold=0.05  # Need 5% information gain to continue
    )
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        adaptive = AdaptiveCrawler(crawler, config)
        
        print("Starting adaptive crawl about Python decorators...")
        result = await adaptive.digest(
            start_url="https://docs.python.org/3/glossary.html",
            query="python decorators functions wrapping"
        )
        
        print(f"\n✅ Crawling Complete!")
        print(f"• Confidence Level: {adaptive.confidence:.0%}")
        print(f"• Pages Crawled: {len(result.crawled_urls)}")
        print(f"• Knowledge Base: {len(adaptive.state.knowledge_base)} documents")
        
        # Get most relevant content
        relevant = adaptive.get_relevant_content(top_k=3)
        print(f"\nMost Relevant Pages:")
        for i, page in enumerate(relevant, 1):
            print(f"{i}. {page['url']} (relevance: {page['score']:.2%})")


async def demo_virtual_scroll():
    """
    Demo 3: Virtual Scroll for Modern Web Pages
    
    Shows how to capture content from pages with DOM recycling
    (Twitter, Instagram, infinite scroll).
    """
    print("\n" + "="*60)
    print("📜 DEMO 3: Virtual Scroll Support")
    print("="*60)
    
    # Configure virtual scroll for a news site
    virtual_config = VirtualScrollConfig(
        container_selector="main, article, .content",  # Common containers
        scroll_count=20,  # Scroll up to 20 times
        scroll_by="container_height",  # Scroll by container height
        wait_after_scroll=0.5  # Wait 500ms after each scroll
    )
    
    config = CrawlerRunConfig(
        virtual_scroll_config=virtual_config,
        cache_mode=CacheMode.BYPASS,
        wait_for="css:article"  # Wait for articles to load
    )
    
    # Example with a real news site
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            "https://news.ycombinator.com/",
            config=config
        )
        
        if result.success:
            # Count items captured
            import re
            items = len(re.findall(r'class="athing"', result.html))
            print(f"\n✅ Captured {items} news items")
            print(f"• HTML size: {len(result.html):,} bytes")
            print(f"• Without virtual scroll, would only capture ~30 items")


async def demo_url_seeder():
    """
    Demo 4: URL Seeder for Intelligent Discovery
    
    Shows how to discover and filter URLs before crawling,
    with relevance scoring.
    """
    print("\n" + "="*60)
    print("🌱 DEMO 4: URL Seeder - Smart URL Discovery")
    print("="*60)
    
    async with AsyncUrlSeeder() as seeder:
        # Discover Python tutorial URLs
        config = SeedingConfig(
            source="sitemap",  # Use sitemap
            pattern="*python*",  # URL pattern filter
            extract_head=True,  # Get metadata
            query="python tutorial",  # For relevance scoring
            scoring_method="bm25",
            score_threshold=0.2,
            max_urls=10
        )
        
        print("Discovering Python async tutorial URLs...")
        urls = await seeder.urls("https://www.geeksforgeeks.org/", config)
        
        print(f"\n✅ Found {len(urls)} relevant URLs:")
        for i, url_info in enumerate(urls[:5], 1):
            print(f"\n{i}. {url_info['url']}")
            if url_info.get('relevance_score'):
                print(f"   Relevance: {url_info['relevance_score']:.3f}")
            if url_info.get('head_data', {}).get('title'):
                print(f"   Title: {url_info['head_data']['title'][:60]}...")


async def demo_c4a_script():
    """
    Demo 5: C4A Script Language
    
    Shows the domain-specific language for web automation
    with JavaScript transpilation.
    """
    print("\n" + "="*60)
    print("🎭 DEMO 5: C4A Script - Web Automation Language")
    print("="*60)
    
    # Example C4A script
    c4a_script = """
# E-commerce automation script
WAIT `body` 3

# Handle cookie banner
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-cookies`

# Search for product
CLICK `.search-box`
TYPE "wireless headphones"
PRESS Enter

# Wait for results
WAIT `.product-grid` 10

# Load more products
REPEAT (SCROLL DOWN 500, `document.querySelectorAll('.product').length < 50`)

# Apply filter
IF (EXISTS `.price-filter`) THEN CLICK `input[data-max-price="100"]`
"""
    
    # Compile the script
    print("Compiling C4A script...")
    result = c4a_compile(c4a_script)
    
    if result.success:
        print(f"✅ Successfully compiled to {len(result.js_code)} JavaScript statements!")
        print("\nFirst 3 JS statements:")
        for stmt in result.js_code[:3]:
            print(f"  • {stmt}")
        
        # Use with crawler
        config = CrawlerRunConfig(
            c4a_script=c4a_script,  # Pass C4A script directly
            cache_mode=CacheMode.BYPASS
        )
        
        print("\n✅ Script ready for use with AsyncWebCrawler!")
    else:
        print(f"❌ Compilation error: {result.first_error.message}")


async def main():
    """Run all demos"""
    print("\n🚀 Crawl4AI v0.7.0 Feature Demonstrations")
    print("=" * 60)
    
    demos = [
        ("Link Preview & Scoring", demo_link_preview),
        ("Adaptive Crawling", demo_adaptive_crawling),
        ("Virtual Scroll", demo_virtual_scroll),
        ("URL Seeder", demo_url_seeder),
        ("C4A Script", demo_c4a_script),
    ]
    
    for name, demo_func in demos:
        try:
            await demo_func()
        except Exception as e:
            print(f"\n❌ Error in {name} demo: {str(e)}")
        
        # Pause between demos
        await asyncio.sleep(1)
    
    print("\n" + "="*60)
    print("✅ All demos completed!")
    print("\nKey Takeaways:")
    print("• Link Preview: 3-layer scoring for intelligent link analysis")
    print("• Adaptive Crawling: Stop when you have enough information")
    print("• Virtual Scroll: Capture all content from modern web pages")
    print("• URL Seeder: Pre-discover and filter URLs efficiently")
    print("• C4A Script: Simple language for complex automations")


if __name__ == "__main__":
    asyncio.run(main())