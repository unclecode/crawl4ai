#!/usr/bin/env python3
"""
Link Analysis Example
====================

This example demonstrates how to use the new /links/analyze endpoint
to extract, analyze, and score links from web pages.

Requirements:
- Crawl4AI server running on localhost:11234
- requests library: pip install requests
"""

import requests
import json
import time
from typing import Dict, Any, List


class LinkAnalyzer:
    """Simple client for the link analysis endpoint"""

    def __init__(self, base_url: str = "http://localhost:11234", token: str = None):
        self.base_url = base_url
        self.token = token or self._get_test_token()

    def _get_test_token(self) -> str:
        """Get a test token (for development only)"""
        try:
            response = requests.post(
                f"{self.base_url}/token",
                json={"email": "test@example.com"},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()["access_token"]
        except:
            pass
        return "test-token"  # Fallback for local testing

    def analyze_links(self, url: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze links on a webpage"""
        headers = {"Content-Type": "application/json"}

        if self.token and self.token != "test-token":
            headers["Authorization"] = f"Bearer {self.token}"

        data = {"url": url}
        if config:
            data["config"] = config

        response = requests.post(
            f"{self.base_url}/links/analyze",
            headers=headers,
            json=data,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def print_summary(self, result: Dict[str, Any]):
        """Print a summary of link analysis results"""
        print("\n" + "="*60)
        print("📊 LINK ANALYSIS SUMMARY")
        print("="*60)

        total_links = sum(len(links) for links in result.values())
        print(f"Total links found: {total_links}")

        for category, links in result.items():
            if links:
                print(f"\n📂 {category.upper()}: {len(links)} links")

                # Show top 3 links by score
                top_links = sorted(links, key=lambda x: x.get('total_score', 0), reverse=True)[:3]
                for i, link in enumerate(top_links, 1):
                    score = link.get('total_score', 0)
                    text = link.get('text', 'No text')[:50]
                    url = link.get('href', 'No URL')[:60]
                    print(f"  {i}. [{score:.2f}] {text} → {url}")


def example_1_basic_analysis():
    """Example 1: Basic link analysis"""
    print("\n🔍 Example 1: Basic Link Analysis")
    print("-" * 40)

    analyzer = LinkAnalyzer()

    # Analyze a simple test page
    url = "https://httpbin.org/links/10"
    print(f"Analyzing: {url}")

    try:
        result = analyzer.analyze_links(url)
        analyzer.print_summary(result)
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def example_2_custom_config():
    """Example 2: Analysis with custom configuration"""
    print("\n🔍 Example 2: Custom Configuration")
    print("-" * 40)

    analyzer = LinkAnalyzer()

    # Custom configuration
    config = {
        "include_internal": True,
        "include_external": True,
        "max_links": 50,
        "timeout": 10,
        "verbose": True
    }

    url = "https://httpbin.org/links/10"
    print(f"Analyzing with custom config: {url}")
    print(f"Config: {json.dumps(config, indent=2)}")

    try:
        result = analyzer.analyze_links(url, config)
        analyzer.print_summary(result)
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def example_3_real_world_site():
    """Example 3: Analyzing a real website"""
    print("\n🔍 Example 3: Real Website Analysis")
    print("-" * 40)

    analyzer = LinkAnalyzer()

    # Analyze Python official website
    url = "https://www.python.org"
    print(f"Analyzing real website: {url}")
    print("This may take a moment...")

    try:
        result = analyzer.analyze_links(url)
        analyzer.print_summary(result)

        # Additional analysis
        print("\n📈 DETAILED ANALYSIS")
        print("-" * 20)

        # Find external links with highest scores
        external_links = result.get('external', [])
        if external_links:
            top_external = sorted(external_links, key=lambda x: x.get('total_score', 0), reverse=True)[:5]
            print("\n🌐 Top External Links:")
            for link in top_external:
                print(f"  • {link.get('text', 'N/A')} (score: {link.get('total_score', 0):.2f})")
                print(f"    {link.get('href', 'N/A')}")

        # Find internal links
        internal_links = result.get('internal', [])
        if internal_links:
            top_internal = sorted(internal_links, key=lambda x: x.get('total_score', 0), reverse=True)[:5]
            print("\n🏠 Top Internal Links:")
            for link in top_internal:
                print(f"  • {link.get('text', 'N/A')} (score: {link.get('total_score', 0):.2f})")
                print(f"    {link.get('href', 'N/A')}")

        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️  This example may fail due to network issues")
        return None


def example_4_comparative_analysis():
    """Example 4: Comparing link structures across sites"""
    print("\n🔍 Example 4: Comparative Analysis")
    print("-" * 40)

    analyzer = LinkAnalyzer()

    sites = [
        ("https://httpbin.org/links/10", "Test Page 1"),
        ("https://httpbin.org/links/5", "Test Page 2")
    ]

    results = {}

    for url, name in sites:
        print(f"\nAnalyzing: {name}")
        try:
            result = analyzer.analyze_links(url)
            results[name] = result

            total_links = sum(len(links) for links in result.values())
            categories = len([cat for cat, links in result.items() if links])
            print(f"  Links: {total_links}, Categories: {categories}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Compare results
    if len(results) > 1:
        print("\n📊 COMPARISON")
        print("-" * 15)

        for name, result in results.items():
            total = sum(len(links) for links in result.values())
            print(f"{name}: {total} total links")

            # Calculate average scores
            all_scores = []
            for links in result.values():
                for link in links:
                    all_scores.append(link.get('total_score', 0))

            if all_scores:
                avg_score = sum(all_scores) / len(all_scores)
                print(f"  Average link score: {avg_score:.3f}")


def example_5_advanced_filtering():
    """Example 5: Advanced filtering and analysis"""
    print("\n🔍 Example 5: Advanced Filtering")
    print("-" * 40)

    analyzer = LinkAnalyzer()

    url = "https://httpbin.org/links/10"

    try:
        result = analyzer.analyze_links(url)

        # Filter links by score
        min_score = 0.5
        high_quality_links = {}

        for category, links in result.items():
            if links:
                filtered = [link for link in links if link.get('total_score', 0) >= min_score]
                if filtered:
                    high_quality_links[category] = filtered

        print(f"\n🎯 High-quality links (score >= {min_score}):")
        total_high_quality = sum(len(links) for links in high_quality_links.values())
        print(f"Total: {total_high_quality} links")

        for category, links in high_quality_links.items():
            print(f"\n{category.upper()}:")
            for link in links:
                score = link.get('total_score', 0)
                text = link.get('text', 'No text')
                print(f"  • [{score:.2f}] {text}")

        # Extract unique domains from external links
        external_links = result.get('external', [])
        if external_links:
            domains = set()
            for link in external_links:
                url = link.get('href', '')
                if '://' in url:
                    domain = url.split('://')[1].split('/')[0]
                    domains.add(domain)

            print(f"\n🌐 Unique external domains: {len(domains)}")
            for domain in sorted(domains):
                print(f"  • {domain}")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples"""
    print("🚀 Link Analysis Examples")
    print("=" * 50)
    print("Make sure the Crawl4AI server is running on localhost:11234")
    print()

    examples = [
        example_1_basic_analysis,
        example_2_custom_config,
        example_3_real_world_site,
        example_4_comparative_analysis,
        example_5_advanced_filtering
    ]

    for i, example_func in enumerate(examples, 1):
        print(f"\n{'='*60}")
        print(f"Running Example {i}")
        print('='*60)

        try:
            example_func()
        except KeyboardInterrupt:
            print("\n⏹️  Example interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Example {i} failed: {e}")

        if i < len(examples):
            print("\n⏳ Press Enter to continue to next example...")
            try:
                input()
            except KeyboardInterrupt:
                break

    print("\n🎉 Examples completed!")


if __name__ == "__main__":
    main()