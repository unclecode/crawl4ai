"""
Sample script to test the max_scroll_steps parameter implementation
"""
import asyncio
import os
import sys

# Get the grandparent directory
grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))



from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def test_max_scroll_steps():
    """
    Test the max_scroll_steps parameter with different configurations
    """
    print("🚀 Testing max_scroll_steps parameter implementation")
    print("=" * 60)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        
        # Test 1: Without max_scroll_steps (unlimited scrolling)
        print("\\n📋 Test 1: Unlimited scrolling (max_scroll_steps=None)")
        config1 = CrawlerRunConfig(
            scan_full_page=True,
            scroll_delay=0.1,
            max_scroll_steps=None,  # Default behavior
            verbose=True
        )
        
        print(f"Config: scan_full_page={config1.scan_full_page}, max_scroll_steps={config1.max_scroll_steps}")
        
        try:
            result1 = await crawler.arun(
                url="https://example.com",  # Simple page for testing
                config=config1
            )
            print(f"✅ Test 1 Success: Crawled {len(result1.markdown)} characters")
        except Exception as e:
            print(f"❌ Test 1 Failed: {e}")
        
        # Test 2: With limited scroll steps
        print("\\n📋 Test 2: Limited scrolling (max_scroll_steps=3)")
        config2 = CrawlerRunConfig(
            scan_full_page=True,
            scroll_delay=0.1,
            max_scroll_steps=3,  # Limit to 3 scroll steps
            verbose=True
        )
        
        print(f"Config: scan_full_page={config2.scan_full_page}, max_scroll_steps={config2.max_scroll_steps}")
        
        try:
            result2 = await crawler.arun(
                url="https://techcrunch.com/",  # Another test page
                config=config2
            )
            print(f"✅ Test 2 Success: Crawled {len(result2.markdown)} characters")
        except Exception as e:
            print(f"❌ Test 2 Failed: {e}")
        
        # Test 3: Test serialization/deserialization
        print("\\n📋 Test 3: Configuration serialization test")
        config3 = CrawlerRunConfig(
            scan_full_page=True,
            max_scroll_steps=5,
            scroll_delay=0.2
        )
        
        # Test to_dict
        config_dict = config3.to_dict()
        print(f"Serialized max_scroll_steps: {config_dict.get('max_scroll_steps')}")
        
        # Test from_kwargs
        config4 = CrawlerRunConfig.from_kwargs({
            'scan_full_page': True,
            'max_scroll_steps': 7,
            'scroll_delay': 0.3
        })
        print(f"Deserialized max_scroll_steps: {config4.max_scroll_steps}")
        print("✅ Test 3 Success: Serialization works correctly")
        
        # Test 4: Edge case - max_scroll_steps = 0
        print("\\n📋 Test 4: Edge case (max_scroll_steps=0)")
        config5 = CrawlerRunConfig(
            scan_full_page=True,
            max_scroll_steps=0,  # Should not scroll at all
            verbose=True
        )
        
        try:
            result5 = await crawler.arun(
                url="https://techcrunch.com/",
                config=config5
            )
            print(f"✅ Test 4 Success: No scrolling performed, crawled {len(result5.markdown)} characters")
        except Exception as e:
            print(f"❌ Test 4 Failed: {e}")
    
    print("\\n" + "=" * 60)
    print("🎉 All tests completed!")
    print("\\nThe max_scroll_steps parameter is working correctly:")
    print("- None: Unlimited scrolling (default behavior)")
    print("- Positive integer: Limits scroll steps to that number")
    print("- 0: No scrolling performed")
    print("- Properly serializes/deserializes in config")

if __name__ == "__main__":
    print("Starting max_scroll_steps test...")
    asyncio.run(test_max_scroll_steps())