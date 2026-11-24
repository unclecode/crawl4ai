"""Pooled browsers must recycle their context by pages served (#2231).

The pool's janitor only closes *idle* browsers, so a server under sustained
load never recycles one. Recycling by page count is what bounds the context
state (cookies/localStorage/service workers) that slows navigation down.

The policy has to be applied by the pool, not by config.yml's browser kwargs:
/crawl and /crawl/stream build their BrowserConfig from the request body
(api.py handle_crawl_request), so those kwargs never reach them.
"""
import sys
from pathlib import Path

import pytest
import yaml

from crawl4ai import BrowserConfig

ROOT = Path(__file__).resolve().parents[2]
DOCKER_DIR = ROOT / "deploy" / "docker"
sys.path.insert(0, str(DOCKER_DIR))

pool = pytest.importorskip("crawler_pool", reason="docker server deps not installed")


def test_config_enables_recycling():
    cfg = yaml.safe_load((DOCKER_DIR / "config.yml").read_text())
    assert cfg["crawler"]["pool"].get("max_pages_before_recycle", 0) > 0, (
        "config.yml must set crawler.pool.max_pages_before_recycle > 0, else "
        "pooled contexts are never recycled under sustained load (#2231)."
    )


def test_pool_applies_recycling_to_a_request_supplied_config():
    """A config off the wire carries no recycle setting; the pool must add it."""
    from_request = BrowserConfig()
    assert from_request.max_pages_before_recycle == 0  # guard the premise

    pool._apply_pool_defaults(from_request)
    assert from_request.max_pages_before_recycle == pool.RECYCLE_PAGES > 0


def test_explicit_caller_value_wins():
    cfg = BrowserConfig(max_pages_before_recycle=7)
    pool._apply_pool_defaults(cfg)
    assert cfg.max_pages_before_recycle == 7


@pytest.mark.asyncio
async def test_get_crawler_applies_it(monkeypatch):
    """The call site matters, not just the helper: a config handed to
    get_crawler() must come back carrying the pool's recycle policy."""
    class _FakeCrawler:
        def __init__(self, config, **kw):
            self.config = config

        async def start(self):
            return self

    monkeypatch.setattr(pool, "AsyncWebCrawler", _FakeCrawler)
    monkeypatch.setattr(pool, "COLD_POOL", {})
    monkeypatch.setattr(pool, "HOT_POOL", {})
    monkeypatch.setattr(pool, "PERMANENT", None)
    monkeypatch.setattr(pool, "get_container_memory_percent", lambda: 10.0)

    cfg = BrowserConfig()
    await pool.get_crawler(cfg)
    assert cfg.max_pages_before_recycle == pool.RECYCLE_PAGES > 0


def test_signature_is_stable_across_requests():
    """Applying the default must not split the pool into two signatures."""
    a, b = BrowserConfig(), BrowserConfig()
    assert pool._sig(pool._apply_pool_defaults(a)) == pool._sig(pool._apply_pool_defaults(b))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
