#!/usr/bin/env python3
"""
Test what's actually happening with the adapters in the API
"""

import asyncio
import os
import sys

import pytest

# Add the project root to Python path
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "deploy", "docker"))


@pytest.mark.asyncio
async def test_adapter_chain():
    """Test the complete adapter chain from API to crawler"""
    print("🔍 Testing Complete Adapter Chain")
    print("=" * 50)

    try:
        # Import the API functions
        from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
        from deploy.docker.api import _apply_headless_setting, _get_browser_adapter
        from deploy.docker.crawler_pool import get_crawler

        print("✅ Successfully imported all functions")

        # Test different strategies
        strategies = ["default", "stealth", "undetected"]

        for strategy in strategies:
            print(f"\n🧪 Testing {strategy} strategy:")
            print("-" * 30)

            try:
                # Step 1: Create browser config
                browser_config = BrowserConfig(headless=True)
                print(
                    f"  1. ✅ Created BrowserConfig: headless={browser_config.headless}"
                )

                # Step 2: Get adapter
                adapter = _get_browser_adapter(strategy, browser_config)
                print(f"  2. ✅ Got adapter: {adapter.__class__.__name__}")

                # Step 3: Test crawler creation
                crawler = await get_crawler(browser_config, adapter)
                print(f"  3. ✅ Created crawler: {crawler.__class__.__name__}")

                # Step 4: Test the strategy inside the crawler
                if hasattr(crawler, "crawler_strategy"):
                    strategy_obj = crawler.crawler_strategy
                    print(
                        f"  4. ✅ Crawler strategy: {strategy_obj.__class__.__name__}"
                    )

                    if hasattr(strategy_obj, "adapter"):
                        adapter_in_strategy = strategy_obj.adapter
                        print(
                            f"  5. ✅ Adapter in strategy: {adapter_in_strategy.__class__.__name__}"
                        )

                        # Check if it's the same adapter we passed
                        if adapter_in_strategy.__class__ == adapter.__class__:
                            print(f"  6. ✅ Adapter correctly passed through!")
                        else:
                            print(
                                f"  6. ❌ Adapter mismatch! Expected {adapter.__class__.__name__}, got {adapter_in_strategy.__class__.__name__}"
                            )
                    else:
                        print(f"  5. ❌ No adapter found in strategy")
                else:
                    print(f"  4. ❌ No crawler_strategy found in crawler")

                # Step 5: Test actual crawling
                test_html = (
                    "<html><body><h1>Test</h1><p>Adapter test page</p></body></html>"
                )
                with open("/tmp/adapter_test.html", "w") as f:
                    f.write(test_html)

                crawler_config = CrawlerRunConfig(cache_mode="bypass")
                result = await crawler.arun(
                    url="file:///tmp/adapter_test.html", config=crawler_config
                )

                if result.success:
                    print(
                        f"  7. ✅ Crawling successful! Content length: {len(result.markdown)}"
                    )
                else:
                    print(f"  7. ❌ Crawling failed: {result.error_message}")

            except Exception as e:
                print(f"  ❌ Error testing {strategy}: {e}")
                import traceback

                traceback.print_exc()

        print(f"\n🎉 Adapter chain testing completed!")

    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_adapter_chain())
