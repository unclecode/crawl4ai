import httpx
import asyncio
import json

async def test_regular():
    """Test non-streaming API call"""
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/crawl", json={
            "urls": ["https://example.com"] * 3,  # Test with 3 identical URLs
            "browser_config": {
                "headless": True,
                "verbose": False
            },
            "crawler_config": {
                "cache_mode": "BYPASS",
                "stream": False
            }
        })
        results = response.json()
        print("\nRegular Response:")
        print(f"Got {len(results['results'])} results at once")
        for result in results['results']:
            print(f"URL: {result['url']}, Success: {result['success']}")

async def test_streaming():
    """Test streaming API call"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/crawl",
                json={
                    "urls": ["https://example.com"] * 3,
                    "browser_config": {
                        "headless": True,
                        "verbose": False
                    },
                    "crawler_config": {
                        "cache_mode": "BYPASS",
                        "stream": True
                    }
                },
                timeout=30.0
            )

            print("\nStreaming Response:")
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        result = json.loads(line)
                        print(f"Received result for URL: {result['url']}, Success: {result['success']}")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding response: {e}")
                        continue
        except Exception as e:
            print(f"Error during streaming: {e}")

async def test_complex_config():
    """Test API with complex nested configurations"""
    async with httpx.AsyncClient() as client:
        response = await client.post("http://localhost:8000/crawl",
                timeout=30.0, json={
            "urls": ["https://en.wikipedia.org/wiki/Apple"],
            "browser_config": {
                "headless": True,
                "verbose": False
            },
            "crawler_config": {
                "cache_mode": "BYPASS",
                "excluded_tags": ["nav", "footer", "aside"],
                "remove_overlay_elements": True,
                "markdown_generator": {
                    "type": "DefaultMarkdownGenerator",
                    "params": {
                        "content_filter": {
                            "type": "PruningContentFilter",
                            "params": {
                                "threshold": 0.48,
                                "threshold_type": "fixed",
                                "min_word_threshold": 0
                            }
                        },
                        "options": {"ignore_links": True}
                    }
                }
            }
        })

        result = response.json()
        if result['success']:
            for r in result['results']:
                print(f"Full Markdown Length: {len(r['markdown_v2']['raw_markdown'])}")
                print(f"Fit Markdown Length: {len(r['markdown_v2']['fit_markdown'])}")

async def main():
    """Run both tests"""
    print("Testing Crawl4AI API...")

    # print("\n1. Testing regular (non-streaming) endpoint...")
    # await test_regular()

    # print("\n2. Testing streaming endpoint...")
    # await test_streaming()

    print("\n3. Testing complex configuration...")
    await test_complex_config()

if __name__ == "__main__":
    asyncio.run(main())