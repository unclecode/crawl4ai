import asyncio
from crawl4ai.docker_client import Crawl4aiDockerClient
from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig
)

async def main():
    async with Crawl4aiDockerClient(base_url="http://localhost:8000", verbose=True) as client:
        await client.authenticate("test@example.com")
        
        # Non-streaming crawl
        results = await client.crawl(
            ["https://example.com", "https://python.org"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=CrawlerRunConfig()
        )
        print(f"Non-streaming results: {results}")
        
        # Streaming crawl
        crawler_config = CrawlerRunConfig(stream=True)
        async for result in await client.crawl(
            ["https://example.com", "https://python.org"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=crawler_config
        ):
            print(f"Streamed result: {result}")
        
        # Get schema
        schema = await client.get_schema()
        print(f"Schema: {schema}")

if __name__ == "__main__":
    asyncio.run(main())