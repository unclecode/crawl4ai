import sys

from httpx import codes
import pytest

from crawl4ai import (
    BrowserConfig, CrawlerRunConfig, DefaultMarkdownGenerator,
    PruningContentFilter, JsonCssExtractionStrategy, LLMContentFilter, CacheMode
)
from crawl4ai.async_configs import LLMConfig

from .common import async_client, docker_client


@pytest.fixture
def browser_config() -> BrowserConfig:
    return BrowserConfig(headless=True, viewport_width=1200, viewport_height=800)


@pytest.mark.asyncio
async def test_direct_filtering(browser_config: BrowserConfig):
    """Direct request with content filtering."""
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=0
            ),
            options={"ignore_links": True}
        )
    )

    request_data = {
        "urls": ["https://example.com"],
        "browser_config": browser_config.dump(),
        "crawler_config": crawler_config.dump()
    }

    # Make direct API call
    async with async_client() as client:
        response = await client.post(
            "/crawl",
            json=request_data,
            timeout=300
        )
        assert response.status_code == codes.OK
        result = response.json()
        assert result["success"]


@pytest.mark.asyncio
async def test_direct_structured_extraction(browser_config: BrowserConfig):
    """Direct request using structured extraction with JSON CSS."""
    schema = {
        "baseSelector": "body > div",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": "p", "type": "html"}
        ]
    }

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema=schema)
    )

    request_data = {
        "urls": ["https://example.com"],
        "browser_config": browser_config.dump(),
        "crawler_config": crawler_config.dump()
    }

    async with async_client() as client:
        response = await client.post(
            "/crawl",
            json=request_data
        )
        assert response.status_code == codes.OK
        result = response.json()
        assert result["success"]
        assert result["results"]
        assert len(result["results"]) == 1
        assert "extracted_content" in result["results"][0]
        assert (
            result["results"][0]["extracted_content"]
            == """[
    {
        "title": "Example Domain",
        "content": "<p>This domain is for use in illustrative examples in documents. You may use this\\n    domain in literature without prior coordination or asking for permission.</p>"
    }
]"""
        )


@pytest.mark.asyncio
async def test_direct_schema(browser_config: BrowserConfig):
    """Get the schema."""
    async with async_client() as client:
        response = await client.get("/schema")
        assert response.status_code == codes.OK
        schemas = response.json()
        assert schemas
        assert len(schemas.keys()) == 2
        print("Retrieved schemas for:", list(schemas.keys()))


@pytest.mark.asyncio
async def test_with_client_basic():
    """Test using the Crawl4AI Docker client SDK"""
    async with docker_client() as client:
        browser_config = BrowserConfig(headless=True)
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.48,
                    threshold_type="fixed"
                )
            ),
            stream=False,
        )

        await client.authenticate("test@example.com")
        result = await client.crawl(
            urls=["https://example.com"],
            browser_config=browser_config,
            crawler_config=crawler_config
        )
        assert result.success


@pytest.mark.asyncio
async def test_with_client_llm_streaming():
    async with docker_client() as client:
        browser_config = BrowserConfig(headless=True)
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=LLMContentFilter(
                    llm_config=LLMConfig(provider="openai/gpt-40"),
                    instruction="Extract key technical concepts"
                )
            ),
            stream=True
        )

        await client.authenticate("test@example.com")
        async for result in await client.crawl(
            urls=["https://example.com"],
            browser_config=browser_config,
            crawler_config=crawler_config
        ):
            assert result.success, f"Stream failed with: {result.error_message}"


@pytest.mark.asyncio
async def test_with_client_get_schema():
    async with docker_client() as client:
        await client.authenticate("test@example.com")
        schemas = await client.get_schema()
        print("Retrieved client schemas for:", list(schemas.keys()))


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
