"""
DomainMapper Demo — Comprehensive domain URL discovery

Discovers all URLs under a domain using 8 sources:
sitemap, Common Crawl, Wayback Machine, Certificate Transparency,
path probing, robots.txt mining, RSS/Atom feeds, homepage link extraction.

Usage:
    python domain_mapper_demo.py [domain] [--source SOURCE] [--query QUERY]

Examples:
    python domain_mapper_demo.py superdesign.dev
    python domain_mapper_demo.py example.com --source sitemap+crt+probe
    python domain_mapper_demo.py docs.crawl4ai.com --query "extraction tutorial"
"""

import asyncio
import argparse
from collections import defaultdict
from crawl4ai import DomainMapper, DomainMapperConfig


async def main():
    parser = argparse.ArgumentParser(description="DomainMapper Demo")
    parser.add_argument("domain", help="Domain to scan (e.g., example.com)")
    parser.add_argument("--source", default="sitemap+cc+crt+probe+robots+homepage",
                        help="Discovery sources (default: sitemap+cc+crt+probe+robots+homepage)")
    parser.add_argument("--query", default=None, help="BM25 relevance query")
    parser.add_argument("--max-urls", type=int, default=-1, help="Max URLs to return")
    parser.add_argument("--no-head", action="store_true", help="Skip head extraction")
    args = parser.parse_args()

    config = DomainMapperConfig(
        source=args.source,
        extract_head=not args.no_head,
        query=args.query,
        max_urls=args.max_urls,
        verbose=True,
        force=True,
    )

    async with DomainMapper() as mapper:
        results = await mapper.scan(args.domain, config)

    # Group by host
    by_host = defaultdict(list)
    for r in results:
        by_host[r["host"]].append(r)

    # Print results
    print("\n" + "=" * 70)
    print(f"RESULTS: {len(results)} URLs across {len(by_host)} hosts")
    print("=" * 70)

    for host in sorted(by_host.keys()):
        urls = by_host[host]
        print(f"\n  {host} ({len(urls)} URLs):")
        for r in urls[:10]:
            title = r.get("head_data", {}).get("title", "")
            score = r.get("relevance_score")
            line = f"    [{r['source']}] {r['url']}"
            if title:
                line += f"\n      Title: {title}"
            if score is not None:
                line += f"\n      Score: {score:.3f}"
            print(line)
        if len(urls) > 10:
            print(f"    ... and {len(urls) - 10} more")

    # Source breakdown
    source_counts = defaultdict(int)
    for r in results:
        for s in r["source"].split("+"):
            source_counts[s] += 1

    print(f"\nSource breakdown:")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"  {source}: {count} URLs")


if __name__ == "__main__":
    asyncio.run(main())
