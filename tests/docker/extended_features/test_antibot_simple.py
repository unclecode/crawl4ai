#!/usr/bin/env python3
"""
Simple test of anti-bot strategy functionality
"""

import asyncio
import os
import sys

import pytest

# Add the project root to Python path
sys.path.insert(0, os.getcwd())


@pytest.mark.asyncio
async def test_antibot_strategies():
    """Test different anti-bot strategies"""
    print("🧪 Testing Anti-Bot Strategies with AsyncWebCrawler")
    print("=" * 60)

    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        from crawl4ai.browser_adapter import PlaywrightAdapter

        # Test HTML content
        test_html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Anti-Bot Strategy Test</h1>
            <p>This page tests different browser adapters.</p>
            <div id="content">
                <p>User-Agent detection test</p>
                <script>
                    document.getElementById('content').innerHTML += 
                        '<p>Browser: ' + navigator.userAgent + '</p>';
                </script>
            </div>
        </body>
        </html>
        """

        # Save test HTML
        with open("/tmp/antibot_test.html", "w") as f:
            f.write(test_html)

        test_url = "file:///tmp/antibot_test.html"

        strategies = [
            ("default", "Default Playwright"),
            ("stealth", "Stealth Mode"),
        ]

        for strategy, description in strategies:
            print(f"\n🔍 Testing: {description} (strategy: {strategy})")
            print("-" * 40)

            try:
                # Import adapter based on strategy
                if strategy == "stealth":
                    try:
                        from crawl4ai import StealthAdapter

                        adapter = StealthAdapter()
                        print(f"✅ Using StealthAdapter")
                    except ImportError:
                        print(
                            f"⚠️  StealthAdapter not available, using PlaywrightAdapter"
                        )
                        adapter = PlaywrightAdapter()
                else:
                    adapter = PlaywrightAdapter()
                    print(f"✅ Using PlaywrightAdapter")

                # Configure browser
                browser_config = BrowserConfig(headless=True, browser_type="chromium")

                # Configure crawler
                crawler_config = CrawlerRunConfig(cache_mode="bypass")

                # Run crawler
                async with AsyncWebCrawler(
                    config=browser_config, browser_adapter=adapter
                ) as crawler:
                    result = await crawler.arun(url=test_url, config=crawler_config)

                    if result.success:
                        print(f"✅ Crawl successful")
                        print(f"   📄 Title: {result.metadata.get('title', 'N/A')}")
                        print(f"   📏 Content length: {len(result.markdown)} chars")

                        # Check if user agent info is in content
                        if (
                            "User-Agent" in result.markdown
                            or "Browser:" in result.markdown
                        ):
                            print(f"   🔍 User-agent info detected in content")
                        else:
                            print(f"   ℹ️  No user-agent info in content")
                    else:
                        print(f"❌ Crawl failed: {result.error_message}")

            except Exception as e:
                print(f"❌ Error testing {strategy}: {e}")
                import traceback

                traceback.print_exc()

        print(f"\n🎉 Anti-bot strategy testing completed!")

    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_antibot_strategies())
