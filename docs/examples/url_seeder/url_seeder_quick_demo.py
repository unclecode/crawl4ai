"""
🚀 URL Seeder + AsyncWebCrawler = Magic!
Quick demo showing discovery → filter → crawl pipeline

Note: Uses context manager for automatic cleanup of resources.
"""
import asyncio, os
from crawl4ai import AsyncUrlSeeder, AsyncWebCrawler, SeedingConfig, CrawlerRunConfig, AsyncLogger, DefaultMarkdownGenerator 
from crawl4ai.content_filter_strategy import PruningContentFilter

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 🔍 Example 1: Discover ALL → Filter → Crawl
async def discover_and_crawl():
    """Find Python module tutorials & extract them all!"""
    async with AsyncUrlSeeder(logger=AsyncLogger()) as seeder:
        # Step 1: See how many URLs exist (spoiler: A LOT!)
        print("📊 Let's see what RealPython has...")
        all_urls = await seeder.urls("realpython.com", 
                                    SeedingConfig(source="sitemap"))
        print(f"😱 Found {len(all_urls)} total URLs!")
        
        # Step 2: Filter for Python modules (perfect size ~13)
        print("\n🎯 Filtering for 'python-modules' tutorials...")
        module_urls = await seeder.urls("realpython.com", 
                                      SeedingConfig(
                                          source="sitemap",
                                          pattern="*python-modules*",
                                          live_check=True  # Make sure they're alive!
                                      ))
        
        print(f"✨ Found {len(module_urls)} module tutorials")
        for url in module_urls[:3]:  # Show first 3
            status = "✅" if url["status"] == "valid" else "❌"
            print(f"{status} {url['url']}")
    
    # Step 3: Crawl them all with pruning (keep it lean!)
    print("\n🕷️ Crawling all module tutorials...")
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(  # Smart filtering!
                    threshold=0.48,  # Remove fluff
                    threshold_type="fixed",
                ),
            ),
            only_text=True,
            stream=True,  
        )
        
        # Extract just the URLs from the seeder results
        urls_to_crawl = [u["url"] for u in module_urls[:5]]
        results = await crawler.arun_many(urls_to_crawl, config=config)
        
        # Process & save
        saved = 0
        async for result in results:
            if result.success:
                # Save each tutorial (name from URL)
                name = result.url.split("/")[-2] + ".md"
                name = os.path.join(CURRENT_DIR, name)
                with open(name, "w") as f:
                    f.write(result.markdown.fit_markdown)
                saved += 1
                print(f"💾 Saved: {name}")
        
        print(f"\n🎉 Successfully saved {saved} tutorials!")

# 🔍 Example 2: Beautiful Soup articles with metadata peek
async def explore_beautifulsoup():
    """Discover BeautifulSoup content & peek at metadata"""
    async with AsyncUrlSeeder(logger=AsyncLogger()) as seeder:
        print("🍲 Looking for Beautiful Soup articles...")
        soup_urls = await seeder.urls("realpython.com",
                                    SeedingConfig(
                                        source="sitemap",
                                        pattern="*beautiful-soup*",
                                        extract_head=True  # Get the metadata!
                                    ))
        
        print(f"\n📚 Found {len(soup_urls)} Beautiful Soup articles:\n")
        
        # Show what we discovered
        for i, url in enumerate(soup_urls, 1):
            meta = url["head_data"]["meta"]
            
            print(f"{i}. {url['head_data']['title']}")
            print(f"   📝 {meta.get('description', 'No description')[:60]}...")
            print(f"   👤 By: {meta.get('author', 'Unknown')}")
            print(f"   🔗 {url['url']}\n")

# 🔍 Example 3: Smart search with BM25 relevance scoring
async def smart_search_with_bm25():
    """Use AI-powered relevance scoring to find the best content"""
    async with AsyncUrlSeeder(logger=AsyncLogger()) as seeder:
        print("🧠 Smart search: 'web scraping tutorial quiz'")
        
        # Search with BM25 scoring - AI finds the best matches!
        results = await seeder.urls("realpython.com",
                                  SeedingConfig(
                                      source="sitemap",
                                      pattern="*beautiful-soup*",
                                      extract_head=True,
                                      query="web scraping tutorial quiz",  # Our search
                                      scoring_method="bm25",
                                      score_threshold=0.2  # Quality filter
                                  ))
        
        print(f"\n🎯 Top {len(results)} most relevant results:\n")
        
        # Show ranked results with relevance scores
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. [{result['relevance_score']:.2f}] {result['head_data']['title']}")
            print(f"   🔗 {result['url'][:60]}...")
        
        print("\n✨ BM25 automatically ranked by relevance!")

# 🎬 Run the show!
async def main():
    print("=" * 60)
    await discover_and_crawl()
    print("\n" + "=" * 60 + "\n")
    await explore_beautifulsoup()
    print("\n" + "=" * 60 + "\n")
    await smart_search_with_bm25()

if __name__ == "__main__":
    asyncio.run(main())