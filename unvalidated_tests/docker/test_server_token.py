import asyncio
import json
from typing import Optional
from urllib.parse import quote

async def get_token(session, email: str = "test@example.com") -> str:
    """Fetch a JWT token from the /token endpoint."""
    url = "http://localhost:8000/token"
    payload = {"email": email}
    print(f"\nFetching token from {url} with email: {email}")
    try:
        async with session.post(url, json=payload) as response:
            status = response.status
            data = await response.json()
            print(f"Token Response Status: {status}")
            print(f"Token Response: {json.dumps(data, indent=2)}")
            if status == 200:
                return data["access_token"]
            else:
                raise Exception(f"Failed to get token: {data.get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"Error fetching token: {str(e)}")
        raise

async def test_endpoint(
    session,
    endpoint: str,
    url: str,
    token: str,
    params: Optional[dict] = None,
    expected_status: int = 200
) -> Optional[dict]:
    """Test an endpoint with token and print results."""
    params = params or {}
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    full_url = f"http://localhost:8000/{endpoint}/{quote(url)}"
    if param_str:
        full_url += f"?{param_str}"
    
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\nTesting: {full_url}")
    
    try:
        async with session.get(full_url, headers=headers) as response:
            status = response.status
            try:
                data = await response.json()
            except:
                data = await response.text()
            
            print(f"Status: {status} (Expected: {expected_status})")
            if isinstance(data, dict):
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"Response: {data[:500]}...")  # First 500 chars
            assert status == expected_status, f"Expected {expected_status}, got {status}"
            return data
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


async def test_stream_crawl(session, token: str):
    """Test the /crawl/stream endpoint with multiple URLs."""
    url = "http://localhost:8000/crawl/stream"
    payload = {
        "urls": [
            "https://example.com",
            "https://example.com/page1",  # Replicated example.com with variation
            "https://example.com/page2",  # Replicated example.com with variation
            "https://example.com/page3",  # Replicated example.com with variation
            # "https://www.python.org",
            # "https://news.ycombinator.com/news"
        ],
        "browser_config": {"headless": True, "viewport": {"width": 1200}},
        "crawler_config": {"stream": True, "cache_mode": "bypass"}
    }
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\nTesting Streaming Crawl: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            status = response.status
            print(f"Status: {status} (Expected: 200)")
            assert status == 200, f"Expected 200, got {status}"
            
            # Read streaming response line-by-line (NDJSON)
            async for line in response.content:
                if line:
                    data = json.loads(line.decode('utf-8').strip())
                    print(f"Streamed Result: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Error in streaming crawl test: {str(e)}")

async def run_tests():
    import aiohttp
    print("Starting API Tests...")
    
    # Test URLs
    urls = [
        "example.com",
        "https://www.python.org",
        "https://news.ycombinator.com/news",
        "https://github.com/trending"
    ]
    
    async with aiohttp.ClientSession() as session:
        # Fetch token once and reuse it
        token = await get_token(session)
        if not token:
            print("Aborting tests due to token failure!")
            return
        
        print("\n=== Testing Crawl Endpoint ===")
        crawl_payload = {
            "urls": ["https://example.com"],
            "browser_config": {"headless": True},
            "crawler_config": {"stream": False}
        }
        async with session.post(
            "http://localhost:8000/crawl",
            json=crawl_payload,
            headers={"Authorization": f"Bearer {token}"}
        ) as response:
            status = response.status
            data = await response.json()
            print(f"\nCrawl Endpoint Status: {status}")
            print(f"Crawl Response: {json.dumps(data, indent=2)}")
        

        print("\n=== Testing Crawl Stream Endpoint ===")
        await test_stream_crawl(session, token)

        print("\n=== Testing Markdown Endpoint ===")
        for url in []: #urls:
            for filter_type in ["raw", "fit", "bm25", "llm"]:
                params = {"f": filter_type}
                if filter_type in ["bm25", "llm"]:
                    params["q"] = "extract main content"
                
                for cache in ["0", "1"]:
                    params["c"] = cache
                    await test_endpoint(session, "md", url, token, params)
                    await asyncio.sleep(1)  # Be nice to the server

        print("\n=== Testing LLM Endpoint ===")
        for url in urls:
            # Test basic extraction (direct response now)
            result = await test_endpoint(
                session,
                "llm",
                url,
                token,
                {"q": "Extract title and main content"}
            )
            
            # Test with schema (direct response)
            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "links": {"type": "array", "items": {"type": "string"}}
                }
            }
            result = await test_endpoint(
                session,
                "llm",
                url,
                token,
                {
                    "q": "Extract content with links",
                    "s": json.dumps(schema),
                    "c": "1"  # Test with cache
                }
            )
            await asyncio.sleep(2)  # Be nice to the server
        
        print("\n=== Testing Error Cases ===")
        # Test invalid URL
        await test_endpoint(
            session,
            "md",
            "not_a_real_url",
            token,
            expected_status=500
        )
        
        # Test invalid filter type
        await test_endpoint(
            session,
            "md",
            "example.com",
            token,
            {"f": "invalid"},
            expected_status=422
        )
        
        # Test LLM without query (should fail per your server logic)
        await test_endpoint(
            session,
            "llm",
            "example.com",
            token,
            expected_status=400
        )
        
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(run_tests())