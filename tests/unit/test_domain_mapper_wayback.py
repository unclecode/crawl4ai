import asyncio

import httpx
import pytest

from crawl4ai import DomainMapper, DomainMapperConfig


@pytest.mark.asyncio
@pytest.mark.parametrize("second_domain", ["alpha.test", "beta.test"])
@pytest.mark.parametrize("second_status", [200, 503])
async def test_wayback_results_stay_with_the_scan(
    tmp_path, second_domain, second_status
):
    first_url = "https://alpha.test/first"
    second_url = f"https://{second_domain}/second"
    cdx_queries = []
    validations = []
    first_validating = asyncio.Event()
    release_first = asyncio.Event()

    async def respond(request):
        if request.url.host == "web.archive.org":
            cdx_queries.append(request.url.params["url"])
            if len(cdx_queries) == 1:
                return httpx.Response(200, text=first_url + "\n")
            return httpx.Response(second_status, text=second_url + "\n")
        validations.append((request.method, request.url.host, request.url.path))
        if len(validations) == 1:
            first_validating.set()
            await release_first.wait()
        return httpx.Response(200)

    config = DomainMapperConfig(
        source="wayback", extract_head=False, soft_404_detection=False
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        async with DomainMapper(client=client, base_directory=tmp_path) as mapper:
            first_scan = asyncio.create_task(mapper.scan("alpha.test", config))
            try:
                await asyncio.wait_for(first_validating.wait(), timeout=5)
                second = await asyncio.wait_for(
                    mapper.scan(second_domain, config), timeout=5
                )
            finally:
                release_first.set()
                first = await asyncio.wait_for(first_scan, timeout=5)

    assert cdx_queries == ["*.alpha.test/*", f"*.{second_domain}/*"]
    assert validations == [("HEAD", "alpha.test", "/"), ("HEAD", second_domain, "/")]
    assert [(result["url"], result["source"]) for result in first] == [
        (first_url, "wayback")
    ]
    assert [(result["url"], result["source"]) for result in second] == (
        [(second_url, "wayback")] if second_status == 200 else []
    )


@pytest.mark.asyncio
async def test_cancelled_wayback_scan_can_be_retried_on_the_same_mapper(tmp_path):
    validation_started = asyncio.Event()
    release_validation = asyncio.Event()
    cdx_requests = 0

    async def respond(request):
        nonlocal cdx_requests
        if request.url.host == "web.archive.org":
            cdx_requests += 1
            return httpx.Response(200, text=f"https://alpha.test/scan-{cdx_requests}\n")
        if cdx_requests == 1:
            validation_started.set()
            await release_validation.wait()
        return httpx.Response(200)

    config = DomainMapperConfig(
        source="wayback", extract_head=False, soft_404_detection=False
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        async with DomainMapper(client=client, base_directory=tmp_path) as mapper:
            cancelled_scan = asyncio.create_task(mapper.scan("alpha.test", config))
            try:
                await asyncio.wait_for(validation_started.wait(), timeout=5)
                cancelled_scan.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await asyncio.wait_for(cancelled_scan, timeout=5)
                results = await asyncio.wait_for(
                    mapper.scan("alpha.test", config), timeout=5
                )
            finally:
                release_validation.set()
                await asyncio.gather(cancelled_scan, return_exceptions=True)
        assert not client.is_closed

    assert client.is_closed
    assert cdx_requests == 2
    assert [(result["url"], result["source"]) for result in results] == [
        ("https://alpha.test/scan-2", "wayback")
    ]
