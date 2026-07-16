"""
R5 resource-governance tests: request body-size limit (413) and the
defense-in-depth deep-crawl clamp. (The client-driven unbounded-crawl critical
is closed upstream by R2 forbidding deep_crawl_strategy on untrusted bodies.)
"""

import pytest

pytestmark = pytest.mark.posture


class TestBodySizeLimit:
    def test_oversize_content_length_413(self, stock_client, server_module):
        from auth import create_access_token
        h = {
            "Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'})}",
            "Content-Length": str(50 * 1024 * 1024),  # 50 MiB, over the 10 MiB cap
            "Content-Type": "application/json",
        }
        # TestClient won't actually send 50MiB; the declared Content-Length is
        # what the middleware checks.
        r = stock_client.post("/crawl", data=b"{}", headers=h)
        assert r.status_code == 413, r.status_code

    def test_normal_body_not_blocked_by_size(self, stock_client, server_module):
        from auth import create_access_token
        h = {"Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'})}"}
        # Small body: must pass the size gate (then rejected for missing urls, etc).
        r = stock_client.post("/crawl", json={}, headers=h)
        assert r.status_code != 413


class TestDeepCrawlClamp:
    def test_infinite_max_pages_clamped(self):
        from governor import clamp_deep_crawl, DEFAULT_MAX_PAGES
        from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
        from crawl4ai import CrawlerRunConfig

        strat = BFSDeepCrawlStrategy(max_depth=99)  # max_pages defaults to infinity
        cfg = CrawlerRunConfig(deep_crawl_strategy=strat)
        clamp_deep_crawl(cfg)
        assert cfg.deep_crawl_strategy.max_pages <= DEFAULT_MAX_PAGES
        assert cfg.deep_crawl_strategy.max_depth <= 5

    def test_no_deep_crawl_is_noop(self):
        from governor import clamp_deep_crawl
        from crawl4ai import CrawlerRunConfig
        cfg = CrawlerRunConfig()
        clamp_deep_crawl(cfg)  # must not raise
        assert cfg.deep_crawl_strategy is None


class TestUntrustedDeepCrawlStillForbidden:
    def test_request_cannot_set_deep_crawl(self):
        # The clamp is defense in depth; the primary control is R2 rejecting it.
        from crawl4ai.async_configs import CrawlerRunConfig, Provenance, UntrustedConfigError
        with pytest.raises(UntrustedConfigError):
            CrawlerRunConfig.load(
                {"deep_crawl_strategy": {"type": "BFSDeepCrawlStrategy", "params": {"max_depth": 9}}},
                provenance=Provenance.UNTRUSTED,
            )


class TestConfigCaps:
    def test_job_queue_caps_defaults(self):
        from governor import job_queue_caps
        caps = job_queue_caps({})
        assert caps == {"maxsize": 1000, "workers": 4, "per_principal": 0}

    def test_zero_means_unbounded(self):
        from governor import job_queue_caps, wall_clock_seconds
        caps = job_queue_caps({"limits": {"queue": {"maxsize": 0, "per_principal": 0}}})
        assert caps["maxsize"] == 0 and caps["per_principal"] == 0
        assert wall_clock_seconds({}) == 0  # no deadline by default

    def test_wall_clock_configurable(self):
        from governor import wall_clock_seconds
        assert wall_clock_seconds({"limits": {"wall_clock_s": 30}}) == 30


@pytest.mark.asyncio
class TestWorkQueue:
    async def test_queue_full_without_drain(self):
        import asyncio
        from work_queue import WorkQueue, QueueFull
        q = WorkQueue(maxsize=1, workers=1)
        q._q = asyncio.Queue(maxsize=1)  # bypass workers so nothing drains

        async def noop():
            pass
        q.submit(noop)
        with pytest.raises(QueueFull):
            q.submit(noop)

    async def test_unbounded_never_full(self):
        import asyncio
        from work_queue import WorkQueue
        q = WorkQueue(maxsize=0, workers=1)
        q._q = asyncio.Queue(maxsize=0)

        async def noop():
            pass
        for _ in range(200):
            q.submit(noop)  # maxsize 0 => unbounded, never raises

    async def test_per_principal_quota(self):
        import asyncio
        from work_queue import WorkQueue, QuotaExceeded
        q = WorkQueue(maxsize=0, workers=1, per_principal=1)
        q._q = asyncio.Queue(maxsize=0)

        async def noop():
            pass
        q.submit(noop, principal="alice")
        with pytest.raises(QuotaExceeded):
            q.submit(noop, principal="alice")
        q.submit(noop, principal="bob")  # different caller is fine

    async def test_runs_job_and_releases_counter(self):
        import asyncio
        from work_queue import WorkQueue
        q = WorkQueue(maxsize=10, workers=1, per_principal=5)
        await q.start()
        try:
            done = asyncio.Event()

            async def job():
                done.set()
            q.submit(job, principal="p")
            await asyncio.wait_for(done.wait(), timeout=2)
            await asyncio.sleep(0.05)  # allow the finally/release to run
            assert q._counts.get("p", 0) == 0
        finally:
            await q.stop()


class TestEnqueueMapping:
    def test_enqueue_maps_queue_full_to_503(self):
        import asyncio
        import api
        import work_queue
        from fastapi import HTTPException
        q = work_queue.WorkQueue(maxsize=1, workers=1)
        q._q = asyncio.Queue(maxsize=1)
        work_queue.set_job_queue(q)

        async def noop():
            pass
        try:
            api._enqueue_job(None, noop)  # fills the queue
            with pytest.raises(HTTPException) as exc:
                api._enqueue_job(None, noop)
            assert exc.value.status_code == 503
            assert exc.value.headers.get("Retry-After")
        finally:
            work_queue.set_job_queue(None)

    def test_enqueue_maps_quota_to_429(self):
        import asyncio
        import api
        import work_queue
        from fastapi import HTTPException
        q = work_queue.WorkQueue(maxsize=0, workers=1, per_principal=1)
        q._q = asyncio.Queue(maxsize=0)
        work_queue.set_job_queue(q)

        async def noop():
            pass
        try:
            api._enqueue_job(None, noop, principal="a")
            with pytest.raises(HTTPException) as exc:
                api._enqueue_job(None, noop, principal="a")
            assert exc.value.status_code == 429
        finally:
            work_queue.set_job_queue(None)
