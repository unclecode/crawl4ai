"""Offline regression for URL seeding with an invalid worker count."""

import asyncio

import httpx
import pytest

from crawl4ai import AsyncUrlSeeder, SeedingConfig


@pytest.mark.parametrize("concurrency", [0, -1])
@pytest.mark.parametrize("entry", ["urls", "extract_head_for_urls"])
def test_nonpositive_worker_count_fails_before_io(tmp_path, concurrency, entry):
    requests = []

    def reply(request):
        requests.append(request)
        if request.url.path == "/sitemap.xml":
            return httpx.Response(
                200,
                text="<urlset><url><loc>https://example.org/page</loc></url></urlset>",
            )
        return httpx.Response(200, text="<html><head><title>Page</title></head></html>")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(reply)) as client:
            async with AsyncUrlSeeder(
                client=client, base_directory=tmp_path, cache_root=tmp_path / "cache"
            ) as seeder:
                config = SeedingConfig(source="sitemap", force=True)
                if entry == "urls":
                    config.concurrency = concurrency
                    request = seeder.urls("https://example.org", config)
                else:
                    request = seeder.extract_head_for_urls(
                        ["https://example.org/page"], config, concurrency=concurrency
                    )
                await asyncio.wait_for(request, timeout=0.5)

    with pytest.raises(ValueError, match="concurrency must be positive"):
        asyncio.run(run())
    assert requests == []
