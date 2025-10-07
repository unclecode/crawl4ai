#!/usr/bin/env python3
"""
Test what's actually happening with the adapters - check the correct attribute
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'deploy', 'docker'))

async def test_adapter_verification():
    """Test that adapters are actually being used correctly"""
    print("🔍 Testing Adapter Usage Verification")
    print("=" * 50)
    
    try:
        # Import the API functions
        from api import _get_browser_adapter, _apply_headless_setting
        from crawler_pool import get_crawler
        from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
        
        print("✅ Successfully imported all functions")
        
        # Test different strategies
        strategies = [
            ('default', 'PlaywrightAdapter'),
            ('stealth', 'StealthAdapter'), 
            ('undetected', 'UndetectedAdapter')
        ]
        
        for strategy, expected_adapter in strategies:
            print(f"\n🧪 Testing {strategy} strategy (expecting {expected_adapter}):")
            print("-" * 50)
            
            try:
                # Step 1: Create browser config
                browser_config = BrowserConfig(headless=True)
                print(f"  1. ✅ Created BrowserConfig")
                
                # Step 2: Get adapter
                adapter = _get_browser_adapter(strategy, browser_config)
                adapter_name = adapter.__class__.__name__
                print(f"  2. ✅ Got adapter: {adapter_name}")
                
                if adapter_name == expected_adapter:
                    print(f"  3. ✅ Correct adapter type selected!")
                else:
                    print(f"  3. ❌ Wrong adapter! Expected {expected_adapter}, got {adapter_name}")
                
                # Step 4: Test crawler creation and adapter usage
                crawler = await get_crawler(browser_config, adapter)
                print(f"  4. ✅ Created crawler")
                
                # Check if the strategy has the correct adapter
                if hasattr(crawler, 'crawler_strategy'):
                    strategy_obj = crawler.crawler_strategy
                    
                    if hasattr(strategy_obj, 'adapter'):
                        adapter_in_strategy = strategy_obj.adapter
                        strategy_adapter_name = adapter_in_strategy.__class__.__name__
                        print(f"  5. ✅ Strategy adapter: {strategy_adapter_name}")
                        
                        # Check if it matches what we expected
                        if strategy_adapter_name == expected_adapter:
                            print(f"  6. ✅ ADAPTER CORRECTLY APPLIED!")
                        else:
                            print(f"  6. ❌ Adapter mismatch! Expected {expected_adapter}, strategy has {strategy_adapter_name}")
                    else:
                        print(f"  5. ❌ No adapter attribute found in strategy")
                else:
                    print(f"  4. ❌ No crawler_strategy found in crawler")
                    
                # Test with a real website to see user-agent differences
                print(f"  7. 🌐 Testing with httpbin.org...")
                
                crawler_config = CrawlerRunConfig(cache_mode="bypass")
                result = await crawler.arun(url='https://httpbin.org/user-agent', config=crawler_config)
                
                if result.success:
                    print(f"  8. ✅ Crawling successful!")
                    if 'user-agent' in result.markdown.lower():
                        # Extract user agent info
                        lines = result.markdown.split('\\n')
                        ua_line = [line for line in lines if 'user-agent' in line.lower()]
                        if ua_line:
                            print(f"  9. 🔍 User-Agent detected: {ua_line[0][:100]}...")
                        else:
                            print(f"  9. 📝 Content: {result.markdown[:200]}...")
                    else:
                        print(f"  9. 📝 No user-agent in content, got: {result.markdown[:100]}...")
                else:
                    print(f"  8. ❌ Crawling failed: {result.error_message}")
                    
            except Exception as e:
                print(f"  ❌ Error testing {strategy}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n🎉 Adapter verification completed!")
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_adapter_verification())