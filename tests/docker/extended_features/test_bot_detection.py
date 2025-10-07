#!/usr/bin/env python3
"""
Test adapters with a site that actually detects bots
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'deploy', 'docker'))

async def test_bot_detection():
    """Test adapters against bot detection"""
    print("🤖 Testing Adapters Against Bot Detection")
    print("=" * 50)
    
    try:
        from api import _get_browser_adapter
        from crawler_pool import get_crawler
        from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
        
        # Test with a site that detects automation
        test_sites = [
            'https://bot.sannysoft.com/',  # Bot detection test site
            'https://httpbin.org/headers',  # Headers inspection
        ]
        
        strategies = [
            ('default', 'PlaywrightAdapter'),
            ('stealth', 'StealthAdapter'), 
            ('undetected', 'UndetectedAdapter')
        ]
        
        for site in test_sites:
            print(f"\n🌐 Testing site: {site}")
            print("=" * 60)
            
            for strategy, expected_adapter in strategies:
                print(f"\n  🧪 {strategy} strategy:")
                print(f"  {'-' * 30}")
                
                try:
                    browser_config = BrowserConfig(headless=True)
                    adapter = _get_browser_adapter(strategy, browser_config)
                    crawler = await get_crawler(browser_config, adapter)
                    
                    print(f"    ✅ Using {adapter.__class__.__name__}")
                    
                    crawler_config = CrawlerRunConfig(cache_mode="bypass")
                    result = await crawler.arun(url=site, config=crawler_config)
                    
                    if result.success:
                        content = result.markdown[:500]
                        print(f"    ✅ Crawl successful ({len(result.markdown)} chars)")
                        
                        # Look for bot detection indicators
                        bot_indicators = [
                            'webdriver', 'automation', 'bot detected', 
                            'chrome-devtools', 'headless', 'selenium'
                        ]
                        
                        detected_indicators = []
                        for indicator in bot_indicators:
                            if indicator.lower() in content.lower():
                                detected_indicators.append(indicator)
                        
                        if detected_indicators:
                            print(f"    ⚠️  Detected indicators: {', '.join(detected_indicators)}")
                        else:
                            print(f"    ✅ No bot detection indicators found")
                            
                        # Show a snippet of content
                        print(f"    📝 Content sample: {content[:200]}...")
                        
                    else:
                        print(f"    ❌ Crawl failed: {result.error_message}")
                        
                except Exception as e:
                    print(f"    ❌ Error: {e}")
        
        print(f"\n🎉 Bot detection testing completed!")
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot_detection())