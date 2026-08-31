import asyncio
import pytest
from crawl4ai import AsyncLogger, AsyncUrlSeeder, SeedingConfig
from pathlib import Path
import httpx


@pytest.mark.asyncio
async def test_sitemap_source_does_not_hit_commoncrawl():
    config = SeedingConfig(
        source="sitemap",
        live_check=False,
        extract_head=False,
        max_urls=50,
        verbose=True,
        force=False
    )

    async with AsyncUrlSeeder(logger=AsyncLogger(verbose=True)) as seeder:
        async def boom(*args, **kwargs):
            print("DEBUG: _latest_index called")
            raise httpx.ConnectTimeout("Simulated CommonCrawl outage")

        seeder._latest_index = boom
        try:
            await seeder.urls("https://docs.crawl4ai.com/", config)
            print("PASS: _latest_index was NOT called (expected after fix).")
        except httpx.ConnectTimeout:
            print("FAIL: _latest_index WAS called even though source='sitemap'.")

if __name__ == "__main__":
    asyncio.run(test_sitemap_source_does_not_hit_commoncrawl())
