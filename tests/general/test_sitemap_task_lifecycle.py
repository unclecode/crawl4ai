import asyncio

import httpx
import pytest

from crawl4ai import AsyncUrlSeeder, SeedingConfig


@pytest.mark.parametrize("discovery", ["prefetched", "refetched", "robots"])
def test_cancelling_seeding_joins_nested_sitemap_tasks(tmp_path, discovery):
    async def run():
        nested_request_started = asyncio.Event()
        cleanup_started = asyncio.Event()
        finish_request = asyncio.Event()
        request_task = None
        root_fetches = 0

        async def handle(request):
            nonlocal request_task, root_fetches
            path = request.url.path
            if request.method == "HEAD":
                return httpx.Response(
                    200 if discovery != "robots" and path == "/sitemap.xml" else 404
                )
            if path == "/robots.txt":
                return httpx.Response(
                    200, text="Sitemap: https://example.test/sitemap.xml\n"
                )
            if path == "/sitemap.xml":
                root_fetches += 1
                if discovery == "refetched" and root_fetches == 1:
                    return httpx.Response(503)
                return httpx.Response(
                    200,
                    text="<sitemapindex><sitemap><loc>/nested.xml</loc></sitemap></sitemapindex>",
                )
            if path == "/nested.xml":
                return httpx.Response(
                    200,
                    text="<sitemapindex><sitemap><loc>/leaf.xml</loc></sitemap></sitemapindex>",
                )
            assert path == "/leaf.xml"
            request_task = asyncio.current_task()
            nested_request_started.set()
            try:
                await finish_request.wait()
            except asyncio.CancelledError:
                cleanup_started.set()
                await finish_request.wait()
                raise
            return httpx.Response(200, text="<urlset/>")

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            async with AsyncUrlSeeder(client=client, cache_root=tmp_path) as seeder:
                config = SeedingConfig(source="sitemap", concurrency=1, force=True)
                seeding = asyncio.create_task(seeder.urls("example.test", config))
                cancellation_sent = False
                try:
                    await asyncio.wait_for(nested_request_started.wait(), timeout=2)
                    seeding.cancel()
                    cancellation_sent = True
                    await asyncio.wait_for(cleanup_started.wait(), timeout=2)
                    completed, _ = await asyncio.wait({seeding}, timeout=0.05)
                    assert (
                        not completed
                    ), "seeding returned before nested cleanup finished"
                    finish_request.set()
                    with pytest.raises(asyncio.CancelledError):
                        await asyncio.wait_for(seeding, timeout=2)
                    assert request_task.done(), "nested sitemap task outlived seeding"
                finally:
                    finish_request.set()
                    if not cancellation_sent and not seeding.done():
                        seeding.cancel()
                    await asyncio.wait_for(
                        asyncio.gather(seeding, return_exceptions=True), timeout=2
                    )
                    if request_task is not None:
                        await asyncio.wait_for(
                            asyncio.gather(request_task, return_exceptions=True),
                            timeout=2,
                        )

    asyncio.run(run())


def test_closing_sitemap_iterator_joins_full_queue_producer(tmp_path):
    async def run():
        request_task = None

        async def handle(request):
            nonlocal request_task
            if request.url.path == "/index.xml":
                return httpx.Response(
                    200,
                    text="<sitemapindex><sitemap><loc>/leaf.xml</loc></sitemap></sitemapindex>",
                )
            assert request.url.path == "/leaf.xml"
            request_task = asyncio.current_task()
            urls = "".join(f"<url><loc>/page-{i}</loc></url>" for i in range(1100))
            return httpx.Response(200, text=f"<urlset>{urls}</urlset>")

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            async with AsyncUrlSeeder(client=client, cache_root=tmp_path) as seeder:
                stream = seeder._iter_sitemap("https://example.test/index.xml")
                try:
                    assert await asyncio.wait_for(anext(stream), 2) == (
                        "https://example.test/page-0"
                    )
                    await asyncio.sleep(0)
                    assert not request_task.done()
                    await asyncio.wait_for(stream.aclose(), 2)
                    assert request_task.done(), "child blocked on an abandoned queue"
                finally:
                    await stream.aclose()
                    if request_task is not None and not request_task.done():
                        request_task.cancel()
                        await asyncio.sleep(0)
                        request_task.cancel()
                        await asyncio.gather(request_task, return_exceptions=True)

    asyncio.run(run())


def test_sitemap_child_error_or_cancellation_does_not_lose_healthy_urls(tmp_path):
    async def run():
        async def handle(request):
            path = request.url.path
            if request.method == "HEAD":
                return httpx.Response(200)
            if path == "/sitemap.xml":
                children = "".join(
                    f"<sitemap><loc>/{name}.xml</loc></sitemap>"
                    for name in ("healthy", "failed", "cancelled")
                )
                return httpx.Response(
                    200, text=f"<sitemapindex>{children}</sitemapindex>"
                )
            if path == "/healthy.xml":
                return httpx.Response(
                    200, text="<urlset><url><loc>/page</loc></url></urlset>"
                )
            if path == "/failed.xml":
                return httpx.Response(503)
            assert path == "/cancelled.xml"
            raise asyncio.CancelledError

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            async with AsyncUrlSeeder(client=client, cache_root=tmp_path) as seeder:
                config = SeedingConfig(
                    source="sitemap",
                    concurrency=1,
                    force=True,
                    filter_nonsense_urls=False,
                )
                urls = await asyncio.wait_for(seeder.urls("example.test", config), 8)
                assert [row["url"] for row in urls] == ["https://example.test/page"]

    asyncio.run(run())
