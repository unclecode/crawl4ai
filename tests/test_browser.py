import asyncio
import os
import psutil
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def test_persistent_context_page_creation():
    # Log memory usage for debugging
    process = psutil.Process(os.getpid())
    print(f"Initial Memory Usage: {process.memory_info().rss // (1024 * 1024)} MB")

    # Browser configuration for persistent context
    browser_config = BrowserConfig(
        headless=True,
        java_script_enabled=True,
        user_agent_mode="random",
        light_mode=True,
        viewport_width=1280,
        viewport_height=720,
        use_persistent_context=True,
        verbose=True  # Enable verbose logging for debugging
    )

    # JSON extraction schema for testing
    schema = {
        "name": "Test Items",
        "baseSelector": "div",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }

    # Crawler configuration
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        session_id="test_persistent_session",
        wait_for="css:body",
        simulate_user=True,
        page_timeout=120000
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            # Test 1: Initial crawl with persistent context
            print("\nTest 1: Initial crawl with persistent context")
            result = await crawler.arun(
                url="https://example.com",
                config=crawler_config
            )
            print("Initial Crawl Success!")
            print(f"Extracted JSON: {result.extracted_content[:300]}")
            print(f"Links: {len(result.links)}")

            # Test 2: Multiple crawls to test session reuse
            print("\nTest 2: Multiple crawls to test persistent context")
            result = await crawler.arun(
                url="https://example.com",
                config=crawler_config
            )
            print("Second Crawl Success!")
            print(f"Extracted JSON: {result.extracted_content[:300]}")
            print(f"Links: {len(result.links)}")

            # Test 3: Crawl a dynamic site with JavaScript
            print("\nTest 3: Crawl dynamic site with persistent context")
            result = await crawler.arun(
                url="https://www.kidocode.com/degrees/technology",
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    session_id="test_persistent_session",
                    js_code="""document.querySelectorAll('a').forEach(a => a.click());""",
                    wait_for="css:body",
                    page_timeout=120000
                )
            )
            print("Dynamic Crawl Success!")
            print(f"Extracted JSON: {result.extracted_content[:300]}")
            print(f"Links: {len(result.links)}")

            # Test 4: Additional crawl to verify session persistence
            print("\nTest 4: Additional crawl to verify session persistence")
            result = await crawler.arun(
                url="https://example.com",
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    session_id="test_persistent_session",
                    wait_for="css:body",
                    simulate_user=True,
                    page_timeout=120000
                )
            )
            print("Additional Crawl Success!")
            print(f"Extracted JSON: {result.extracted_content[:300]}")
            print(f"Links: {len(result.links)}")

            # Test 5: Crawl with new session
            print("\nTest 5: Crawl with new session")
            result = await crawler.arun(
                url="https://example.com",
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    session_id="new_session",
                    wait_for="css:body",
                    simulate_user=True,
                    page_timeout=120000
                )
            )
            print("Crawl with new session Success!")
            print(f"Extracted JSON: {result.extracted_content[:300]}")
            print(f"Links: {len(result.links)}")

            print(f"Final Memory Usage: {process.memory_info().rss // (1024 * 1024)} MB")
        except Exception as e:
            print(f"Error during test: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(test_persistent_context_page_creation())