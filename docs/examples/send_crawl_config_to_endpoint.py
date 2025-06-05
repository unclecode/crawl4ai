import httpx
import asyncio

# Assuming crawl4ai SDK is installed and accessible
from crawl4ai import BrowserConfig, CrawlerRunConfig, ExtractionConfig, LLMConfig

# Your API endpoint
CRAWL_API_ENDPOINT = "https://crawl.austindurban.com/crawl/"

async def send_crawl_request():
    """
    This example demonstrates how to send a crawl configuration
    to a remote crawl4ai API endpoint.
    """

    # 1. Define your crawl target URL(s)
    target_urls = ["http://example.com"] # Replace with your desired URL

    # 2. Define Browser Configuration (optional, defaults will be used if not provided)
    # These settings would typically be used by the server running the crawl4ai instance.
    # For sending to a remote endpoint, these are more like 'suggestions' or overrides
    # if the endpoint is designed to accept them.
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium",
        # viewport_width=1920,
        # viewport_height=1080,
    )

    # 3. Define Crawler Run Configuration (optional, defaults will be used if not provided)
    # This tells the crawler how to process the page.
    crawler_run_config = CrawlerRunConfig(
        page_timeout=30000,  # 30 seconds
        # extraction_strategy=ExtractionConfig(
        #     llm_config=LLMConfig(provider="openai", api_key="YOUR_OPENAI_API_KEY"), # Replace if needed
        #     instruction="Extract the main title and the first paragraph of the article."
        # ),
        # js_code="document.title = 'Modified by Script!'; return document.title;",
        # screenshot=False,
    )

    # 4. Construct the payload for the API
    # Based on the CrawlRequest schema:
    # urls: List[str]
    # browser_config: Optional[Dict]
    # crawler_config: Optional[Dict]
    payload = {
        "urls": target_urls,
        "browser_config": browser_config.model_dump(exclude_none=True), # Use model_dump() for Pydantic v2+
        "crawler_config": crawler_run_config.model_dump(exclude_none=True) # Use model_dump() for Pydantic v2+
    }

    print(f"Sending payload to {CRAWL_API_ENDPOINT}:")
    import json
    print(json.dumps(payload, indent=2))

    # 5. Send the request to the endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(CRAWL_API_ENDPOINT, json=payload, timeout=60.0) # Adjust timeout as needed

        # 6. Print the response
        print(f"\nResponse Status Code: {response.status_code}")
        try:
            response_json = response.json()
            print("Response JSON:")
            print(json.dumps(response_json, indent=2))
        except ValueError:
            print("Response Content (not JSON):")
            print(response.text)

    except httpx.RequestError as e:
        print(f"\nAn error occurred while requesting {e.request.url!r}: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    # Note: If your endpoint or local setup requires an API token for authentication,
    # you'll need to add an 'Authorization': 'Bearer YOUR_TOKEN' header to the request.
    # For example:
    # headers = {"Authorization": "Bearer YOUR_TOKEN"}
    # response = await client.post(CRAWL_API_ENDPOINT, json=payload, headers=headers, timeout=60.0)
    asyncio.run(send_crawl_request())
