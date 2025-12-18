"""
Knowledge Base Export and Import

This example demonstrates how to export crawled knowledge bases and
import them for reuse, sharing, or analysis.
"""

import asyncio
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig


async def build_knowledge_base():
    """Build a knowledge base about web technologies"""
    print("="*60)
    print("PHASE 1: Building Knowledge Base")
    print("="*60)
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        adaptive = AdaptiveCrawler(crawler)
        
        # Crawl information about HTTP
        print("\n1. Gathering HTTP protocol information...")
        await adaptive.digest(
            start_url="https://httpbin.org",
            query="http methods headers status codes"
        )
        print(f"   - Pages crawled: {len(adaptive.state.crawled_urls)}")
        print(f"   - Confidence: {adaptive.confidence:.2%}")
        
        # Add more information about APIs
        print("\n2. Adding API documentation knowledge...")
        await adaptive.digest(
            start_url="https://httpbin.org/anything",
            query="rest api json response request"
        )
        print(f"   - Total pages: {len(adaptive.state.crawled_urls)}")
        print(f"   - Confidence: {adaptive.confidence:.2%}")
        
        # Export the knowledge base
        export_path = "web_tech_knowledge.jsonl"
        print(f"\n3. Exporting knowledge base to {export_path}")
        adaptive.export_knowledge_base(export_path)
        
        # Show export statistics
        export_size = Path(export_path).stat().st_size / 1024
        with open(export_path, 'r') as f:
            line_count = sum(1 for _ in f)
        
        print(f"   - Exported {line_count} documents")
        print(f"   - File size: {export_size:.1f} KB")
        
        return export_path


async def analyze_knowledge_base(kb_path):
    """Analyze the exported knowledge base"""
    print("\n" + "="*60)
    print("PHASE 2: Analyzing Exported Knowledge Base")
    print("="*60)
    
    # Read and analyze JSONL
    documents = []
    with open(kb_path, 'r') as f:
        for line in f:
            documents.append(json.loads(line))
    
    print(f"\nKnowledge base contains {len(documents)} documents:")
    
    # Analyze document properties
    total_content_length = 0
    urls_by_domain = {}
    
    for doc in documents:
        # Content analysis
        content_length = len(doc.get('content', ''))
        total_content_length += content_length
        
        # URL analysis
        url = doc.get('url', '')
        domain = url.split('/')[2] if url.startswith('http') else 'unknown'
        urls_by_domain[domain] = urls_by_domain.get(domain, 0) + 1
        
        # Show sample document
        if documents.index(doc) == 0:
            print(f"\nSample document structure:")
            print(f"  - URL: {url}")
            print(f"  - Content length: {content_length} chars")
            print(f"  - Has metadata: {'metadata' in doc}")
            print(f"  - Has links: {len(doc.get('links', []))} links")
            print(f"  - Query: {doc.get('query', 'N/A')}")
    
    print(f"\nContent statistics:")
    print(f"  - Total content: {total_content_length:,} characters")
    print(f"  - Average per document: {total_content_length/len(documents):,.0f} chars")
    
    print(f"\nDomain distribution:")
    for domain, count in urls_by_domain.items():
        print(f"  - {domain}: {count} pages")


async def import_and_continue():
    """Import a knowledge base and continue crawling"""
    print("\n" + "="*60)
    print("PHASE 3: Importing and Extending Knowledge Base")
    print("="*60)
    
    kb_path = "web_tech_knowledge.jsonl"
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        # Create new adaptive crawler
        adaptive = AdaptiveCrawler(crawler)
        
        # Import existing knowledge base
        print(f"\n1. Importing knowledge base from {kb_path}")
        adaptive.import_knowledge_base(kb_path)
        
        print(f"   - Imported {len(adaptive.state.knowledge_base)} documents")
        print(f"   - Existing URLs: {len(adaptive.state.crawled_urls)}")
        
        # Check current state
        print("\n2. Checking imported knowledge state:")
        adaptive.print_stats(detailed=False)
        
        # Continue crawling with new query
        print("\n3. Extending knowledge with new query...")
        await adaptive.digest(
            start_url="https://httpbin.org/status/200",
            query="error handling retry timeout"
        )
        
        print("\n4. Final knowledge base state:")
        adaptive.print_stats(detailed=False)
        
        # Export extended knowledge base
        extended_path = "web_tech_knowledge_extended.jsonl"
        adaptive.export_knowledge_base(extended_path)
        print(f"\n5. Extended knowledge base exported to {extended_path}")


async def share_knowledge_bases():
    """Demonstrate sharing knowledge bases between projects"""
    print("\n" + "="*60)
    print("PHASE 4: Sharing Knowledge Between Projects")
    print("="*60)
    
    # Simulate two different projects
    project_a_kb = "project_a_knowledge.jsonl"
    project_b_kb = "project_b_knowledge.jsonl"
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        # Project A: Security documentation
        print("\n1. Project A: Building security knowledge...")
        crawler_a = AdaptiveCrawler(crawler)
        await crawler_a.digest(
            start_url="https://httpbin.org/basic-auth/user/pass",
            query="authentication security headers"
        )
        crawler_a.export_knowledge_base(project_a_kb)
        print(f"   - Exported {len(crawler_a.state.knowledge_base)} documents")
        
        # Project B: API testing
        print("\n2. Project B: Building testing knowledge...")
        crawler_b = AdaptiveCrawler(crawler)
        await crawler_b.digest(
            start_url="https://httpbin.org/anything",
            query="testing endpoints mocking"
        )
        crawler_b.export_knowledge_base(project_b_kb)
        print(f"   - Exported {len(crawler_b.state.knowledge_base)} documents")
        
        # Merge knowledge bases
        print("\n3. Merging knowledge bases...")
        merged_crawler = AdaptiveCrawler(crawler)
        
        # Import both knowledge bases
        merged_crawler.import_knowledge_base(project_a_kb)
        initial_size = len(merged_crawler.state.knowledge_base)
        
        merged_crawler.import_knowledge_base(project_b_kb)
        final_size = len(merged_crawler.state.knowledge_base)
        
        print(f"   - Project A documents: {initial_size}")
        print(f"   - Additional from Project B: {final_size - initial_size}")
        print(f"   - Total merged documents: {final_size}")
        
        # Export merged knowledge
        merged_kb = "merged_knowledge.jsonl"
        merged_crawler.export_knowledge_base(merged_kb)
        print(f"\n4. Merged knowledge base exported to {merged_kb}")
        
        # Show combined coverage
        print("\n5. Combined knowledge coverage:")
        merged_crawler.print_stats(detailed=False)


async def main():
    """Run all examples"""
    try:
        # Build initial knowledge base
        kb_path = await build_knowledge_base()
        
        # Analyze the export
        await analyze_knowledge_base(kb_path)
        
        # Import and extend
        await import_and_continue()
        
        # Demonstrate sharing
        await share_knowledge_bases()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)
        
    finally:
        # Clean up generated files
        print("\nCleaning up generated files...")
        for file in [
            "web_tech_knowledge.jsonl",
            "web_tech_knowledge_extended.jsonl", 
            "project_a_knowledge.jsonl",
            "project_b_knowledge.jsonl",
            "merged_knowledge.jsonl"
        ]:
            Path(file).unlink(missing_ok=True)
        print("Cleanup complete.")


if __name__ == "__main__":
    asyncio.run(main())