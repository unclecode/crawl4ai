import asyncio
import time

import pytest

from crawl4ai import AsyncUrlSeeder, SeedingConfig


def _stub_seeder(seeder: AsyncUrlSeeder, urls: list[str]) -> None:
    async def from_sitemaps(domain, pattern, force=False):
        for url in urls:
            yield url

    async def validate(url, res_list, *args, **kwargs):
        res_list.append({"url": url, "status": "valid", "head_data": {}})

    seeder._from_sitemaps = from_sitemaps
    seeder._validate = validate


@pytest.mark.asyncio
async def test_urls_returns_promptly_after_last_url():
    urls = [f"https://example.com/page-{i}" for i in range(3)]
    config = SeedingConfig(source="sitemap", extract_head=False, concurrency=4)

    async with AsyncUrlSeeder() as seeder:
        _stub_seeder(seeder, urls)
        started = time.perf_counter()
        results = await asyncio.wait_for(
            seeder.urls("example.com", config), timeout=10
        )
        elapsed = time.perf_counter() - started

    assert sorted(r["url"] for r in results) == urls
    assert elapsed < 1.0


@pytest.mark.asyncio
async def test_urls_with_no_urls_returns_promptly():
    config = SeedingConfig(source="sitemap", extract_head=False, concurrency=4)

    async with AsyncUrlSeeder() as seeder:
        _stub_seeder(seeder, [])
        started = time.perf_counter()
        results = await asyncio.wait_for(
            seeder.urls("example.com", config), timeout=10
        )
        elapsed = time.perf_counter() - started

    assert results == []
    assert elapsed < 1.0


@pytest.mark.asyncio
async def test_urls_max_urls_stops_without_hanging():
    urls = [f"https://example.com/page-{i}" for i in range(50)]
    config = SeedingConfig(
        source="sitemap", extract_head=False, concurrency=4, max_urls=5
    )

    async with AsyncUrlSeeder() as seeder:
        _stub_seeder(seeder, urls)
        started = time.perf_counter()
        results = await asyncio.wait_for(
            seeder.urls("example.com", config), timeout=10
        )
        elapsed = time.perf_counter() - started

    assert len(results) == 5
    assert elapsed < 1.0
