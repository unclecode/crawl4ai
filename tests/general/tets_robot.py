import asyncio
from crawl4ai import *

async def test_real_websites():
    print("\n=== Testing Real Website Robots.txt Compliance ===\n")
    
    browser_config = BrowserConfig(headless=True, verbose=True)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        # Test cases with URLs
        test_cases = [
            # Public sites that should be allowed
            ("https://example.com", True),  # Simple public site
            ("https://httpbin.org/get", True),  # API endpoint
            
            # Sites with known strict robots.txt
            ("https://www.facebook.com/robots.txt", False),  # Social media
            ("https://www.google.com/search", False),  # Search pages
            
            # Edge cases
            ("https://api.github.com", True),  # API service
            ("https://raw.githubusercontent.com", True),  # Content delivery
            
            # Non-existent/error cases
            ("https://thisisnotarealwebsite.com", True),  # Non-existent domain
            ("https://localhost:12345", True),  # Invalid port
        ]

        for url, expected in test_cases:
            print(f"\nTesting: {url}")
            try:
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    check_robots_txt=True,  # Enable robots.txt checking
                    verbose=True
                )
                
                result = await crawler.arun(url=url, config=config)
                allowed = result.success and not result.error_message
                
                print(f"Expected: {'allowed' if expected else 'denied'}")
                print(f"Actual: {'allowed' if allowed else 'denied'}")
                print(f"Status Code: {result.status_code}")
                if result.error_message:
                    print(f"Error: {result.error_message}")
                
                # Optional: Print robots.txt content if available
                if result.metadata and 'robots_txt' in result.metadata:
                    print(f"Robots.txt rules:\n{result.metadata['robots_txt']}")
                
            except Exception as e:
                print(f"Test failed with error: {str(e)}")

async def main():
    try:
        await test_real_websites()
    except Exception as e:
        print(f"Test suite failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())