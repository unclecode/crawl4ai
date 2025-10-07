#!/usr/bin/env python3
"""
Demo: How users will call the Seed endpoint
This shows practical examples of how developers would use the seed endpoint
in their applications to discover URLs for crawling.
"""

import asyncio
from typing import Any, Dict

import aiohttp

# Configuration
API_BASE_URL = "http://localhost:11235"
API_TOKEN = None  # Set if your API requires authentication


class SeedEndpointDemo:
    def __init__(self, base_url: str = API_BASE_URL, token: str = None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def call_seed_endpoint(
        self, url: str, max_urls: int = 20, filter_type: str = "all", **kwargs
    ) -> Dict[str, Any]:
        """Make a call to the seed endpoint"""
        # The seed endpoint expects 'url' and config with other parameters
        config = {
            "max_urls": max_urls,
            "filter_type": filter_type,
            **kwargs,
        }
        payload = {
            "url": url,
            "config": config,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/seed", headers=self.headers, json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # Extract the nested seeded_urls from the response
                    seed_data = result.get('seed_url', {})
                    if isinstance(seed_data, dict):
                        return seed_data
                    else:
                        return {'seeded_urls': seed_data or [], 'count': len(seed_data or [])}
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")

    async def demo_news_site_seeding(self):
        """Demo: Seed URLs from a news website"""
        print("🗞️  Demo: Seeding URLs from a News Website")
        print("=" * 50)

        try:
            result = await self.call_seed_endpoint(
                url="https://techcrunch.com",
                max_urls=15,
                source="sitemap",  # Try sitemap first
                live_check=True,
            )

            urls_found = len(result.get('seeded_urls', []))
            print(f"✅ Found {urls_found} URLs")
            
            if 'message' in result:
                print(f"ℹ️  Server message: {result['message']}")
                
            processing_time = result.get('processing_time', 'N/A')
            print(f"📊 Seed completed in: {processing_time} seconds")

            # Show first 5 URLs as example
            seeded_urls = result.get("seeded_urls", [])
            for i, url in enumerate(seeded_urls[:5]):
                print(f"  {i + 1}. {url}")

            if len(seeded_urls) > 5:
                print(f"  ... and {len(seeded_urls) - 5} more URLs")
            elif len(seeded_urls) == 0:
                print("  💡 Note: No URLs found. This could be because:")
                print("     - The website doesn't have an accessible sitemap")
                print("     - The seeding configuration needs adjustment")
                print("     - Try different source options like 'cc' (Common Crawl)")

        except Exception as e:
            print(f"❌ Error: {e}")
            print("  💡 This might be a connectivity issue or server problem")

    async def demo_ecommerce_seeding(self):
        """Demo: Seed product URLs from an e-commerce site"""
        print("\n🛒 Demo: Seeding Product URLs from E-commerce")
        print("=" * 50)
        print("💡 Note: This demonstrates configuration for e-commerce sites")

        try:
            result = await self.call_seed_endpoint(
                url="https://example-shop.com",
                max_urls=25,
                source="sitemap+cc",
                pattern="*/product/*",  # Focus on product pages
                live_check=False,
            )

            urls_found = len(result.get('seeded_urls', []))
            print(f"✅ Found {urls_found} product URLs")
            
            if 'message' in result:
                print(f"ℹ️  Server message: {result['message']}")

            # Show examples if any found
            seeded_urls = result.get("seeded_urls", [])
            if seeded_urls:
                print("📦 Product URLs discovered:")
                for i, url in enumerate(seeded_urls[:3]):
                    print(f"  {i + 1}. {url}")
            else:
                print("💡 For real e-commerce seeding, you would:")
                print("   • Use actual e-commerce site URLs")
                print("   • Set patterns like '*/product/*' or '*/item/*'")
                print("   • Enable live_check to verify product page availability")
                print("   • Use appropriate max_urls based on catalog size")

        except Exception as e:
            print(f"❌ Error: {e}")
            print("   This is expected for the example URL")

    async def demo_documentation_seeding(self):
        """Demo: Seed documentation pages"""
        print("\n📚 Demo: Seeding Documentation Pages")
        print("=" * 50)

        try:
            result = await self.call_seed_endpoint(
                url="https://docs.python.org",
                max_urls=30,
                source="sitemap",
                pattern="*/library/*",  # Focus on library documentation
                live_check=False,
            )

            urls_found = len(result.get('seeded_urls', []))
            print(f"✅ Found {urls_found} documentation URLs")
            
            if 'message' in result:
                print(f"ℹ️  Server message: {result['message']}")

            # Analyze URL structure if URLs found
            seeded_urls = result.get("seeded_urls", [])
            if seeded_urls:
                sections = {"library": 0, "tutorial": 0, "reference": 0, "other": 0}

                for url in seeded_urls:
                    if "/library/" in url:
                        sections["library"] += 1
                    elif "/tutorial/" in url:
                        sections["tutorial"] += 1
                    elif "/reference/" in url:
                        sections["reference"] += 1
                    else:
                        sections["other"] += 1

                print("📊 URL distribution:")
                for section, count in sections.items():
                    if count > 0:
                        print(f"  {section.title()}: {count} URLs")
                        
                # Show examples
                print("\n📖 Example URLs:")
                for i, url in enumerate(seeded_urls[:3]):
                    print(f"  {i + 1}. {url}")
            else:
                print("💡 For documentation seeding, you would typically:")
                print("   • Use sites with comprehensive sitemaps like docs.python.org")
                print("   • Set patterns to focus on specific sections ('/library/', '/tutorial/')")
                print("   • Consider using 'cc' source for broader coverage")

        except Exception as e:
            print(f"❌ Error: {e}")

    async def demo_seeding_sources(self):
        """Demo: Different seeding sources available"""
        print("\n� Demo: Understanding Seeding Sources")
        print("=" * 50)
        
        print("📖 Available seeding sources:")
        print("  • 'sitemap': Discovers URLs from website's sitemap.xml")
        print("  • 'cc': Uses Common Crawl database for URL discovery")
        print("  • 'sitemap+cc': Combines both sources (default)")
        print()
        
        test_url = "https://docs.python.org"
        sources = ["sitemap", "cc", "sitemap+cc"]
        
        for source in sources:
            print(f"🧪 Testing source: '{source}'")
            try:
                result = await self.call_seed_endpoint(
                    url=test_url,
                    max_urls=5,
                    source=source,
                    live_check=False,  # Faster for demo
                )
                
                urls_found = len(result.get('seeded_urls', []))
                print(f"  ✅ {source}: Found {urls_found} URLs")
                
                if urls_found > 0:
                    # Show first URL as example
                    first_url = result.get('seeded_urls', [])[0]
                    print(f"     Example: {first_url}")
                elif 'message' in result:
                    print(f"     Info: {result['message']}")
                    
            except Exception as e:
                print(f"  ❌ {source}: Error - {e}")
            
            print()  # Space between tests

    async def demo_working_example(self):
        """Demo: A realistic working example"""
        print("\n✨ Demo: Working Example with Live Seeding")
        print("=" * 50)
        
        print("🎯 Testing with a site that likely has good sitemap support...")
        
        try:
            # Use a site that's more likely to have a working sitemap
            result = await self.call_seed_endpoint(
                url="https://github.com",
                max_urls=10,
                source="sitemap",
                pattern="*/blog/*",  # Focus on blog posts
                live_check=False,
            )
            
            urls_found = len(result.get('seeded_urls', []))
            print(f"✅ Found {urls_found} URLs from GitHub")
            
            if urls_found > 0:
                print("🎉 Success! Here are some discovered URLs:")
                for i, url in enumerate(result.get('seeded_urls', [])[:3]):
                    print(f"  {i + 1}. {url}")
                print()
                print("💡 This demonstrates that seeding works when:")
                print("   • The target site has an accessible sitemap")
                print("   • The configuration matches available content")
                print("   • Network connectivity allows sitemap access")
            else:
                print("ℹ️  No URLs found, but this is normal for demo purposes.")
                print("💡 In real usage, you would:")
                print("   • Test with sites you know have sitemaps")
                print("   • Use appropriate URL patterns for your use case")
                print("   • Consider using 'cc' source for broader discovery")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 This might indicate:")
            print("   • Network connectivity issues")
            print("   • Server configuration problems")
            print("   • Need to adjust seeding parameters")


async def main():
    """Run all seed endpoint demos"""
    print("🌱 Crawl4AI Seed Endpoint - User Demo")
    print("=" * 60)
    print("This demo shows how developers use the seed endpoint")
    print("to discover URLs for their crawling workflows.\n")

    demo = SeedEndpointDemo()

    # Run individual demos
    await demo.demo_news_site_seeding()
    await demo.demo_ecommerce_seeding()
    await demo.demo_documentation_seeding()
    await demo.demo_seeding_sources()
    await demo.demo_working_example()

    print("\n🎉 Demo completed!")
    print("\n📚 Key Takeaways:")
    print("1. Seed endpoint discovers URLs from sitemaps and Common Crawl")
    print("2. Different sources ('sitemap', 'cc', 'sitemap+cc') offer different coverage")
    print("3. URL patterns help filter discovered content to your needs")
    print("4. Live checking verifies URL accessibility but slows discovery")
    print("5. Success depends on target site's sitemap availability")
    print("\n💡 Next steps for your application:")
    print("1. Test with your target websites to verify sitemap availability")
    print("2. Choose appropriate seeding sources for your use case")
    print("3. Use discovered URLs as input for your crawling pipeline")
    print("4. Consider fallback strategies if seeding returns few results")


if __name__ == "__main__":
    asyncio.run(main())
