import sys

import pytest

from crawl4ai import BrowserConfig, CrawlerRunConfig

from .common import docker_client


@pytest.mark.asyncio
async def test_non_streaming():
    async with docker_client() as client:
        await client.authenticate("test@example.com")

        # Non-streaming crawl
        results = await client.crawl(
            ["https://example.com", "https://python.org"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=CrawlerRunConfig()
        )
        assert results
        for result in results:
            assert result.success
            print(f"Non-streamed result: {result}")


@pytest.mark.asyncio
async def test_streaming():
    async with docker_client() as client:
        # Streaming crawl
        crawler_config = CrawlerRunConfig(stream=True)
        await client.authenticate("user@example.com")
        async for result in await client.crawl(
            ["https://example.com", "https://python.org"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=crawler_config
        ):
            assert result.success
            print(f"Streamed result: {result}")

        # Get schema
        schema = await client.get_schema()
        assert schema
        print(f"Schema: {schema}")


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
