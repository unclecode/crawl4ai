"""screenshot_wait_for is capped for untrusted callers.

Report 2026-11 (docker-screenshot-wait-unbounded): the GHSA-rhjm fix capped
delay_before_return_html, mean_delay and max_range, but not
screenshot_wait_for. /screenshot built its CrawlerRunConfig directly (so no
untrusted clamp ran) and has no deadline; the crawler sleeps that long with a
page and a GLOBAL_SEM permit held. 40 requests stopped every crawl for days.

TestClient, crawler stubbed: no browser or Redis needed.
"""

import base64
import math
from types import SimpleNamespace

import pytest

from auth import create_access_token  # noqa: E402
from crawl4ai import CrawlerRunConfig
from crawl4ai.async_configs import Provenance, _MAX_DELAY_SECONDS


def _bearer() -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': 'user@x.com'}, scope='data')}"}


@pytest.fixture
def seen_configs(server_module, monkeypatch):
    seen = []
    fake_result = SimpleNamespace(success=True, screenshot=base64.b64encode(b"png").decode())

    class _FakeCrawler:
        async def arun(self, url, config):
            seen.append(config)
            return [fake_result]

    async def fake_get_crawler(cfg):
        return _FakeCrawler()

    async def fake_release_crawler(crawler):
        pass

    monkeypatch.setattr(server_module, "get_crawler", fake_get_crawler)
    monkeypatch.setattr(server_module, "release_crawler", fake_release_crawler)
    monkeypatch.setattr(server_module, "_store_artifact",
                        lambda kind, data: {"artifact_id": "a1", "url": "/artifacts/a1"})
    return seen


@pytest.mark.parametrize("sent,expected", [
    (1_000_000, _MAX_DELAY_SECONDS),
    (_MAX_DELAY_SECONDS + 0.5, _MAX_DELAY_SECONDS),
    (5, 5),
    (0, 0),
])
def test_screenshot_endpoint_caps_the_wait(stock_client, seen_configs, sent, expected):
    r = stock_client.post("/screenshot", headers=_bearer(),
                          json={"url": "https://example.com", "screenshot_wait_for": sent})
    assert r.status_code == 200, r.text
    cfg = seen_configs[-1]
    assert cfg.screenshot is True
    assert cfg.screenshot_wait_for == expected


def test_screenshot_endpoint_default_wait_unchanged(stock_client, seen_configs):
    r = stock_client.post("/screenshot", headers=_bearer(), json={"url": "https://example.com"})
    assert r.status_code == 200, r.text
    assert seen_configs[-1].screenshot_wait_for == 2


def test_screenshot_endpoint_keeps_wait_for_images(stock_client, seen_configs):
    r = stock_client.post("/screenshot", headers=_bearer(),
                          json={"url": "https://example.com", "wait_for_images": True})
    assert r.status_code == 200, r.text
    assert seen_configs[-1].wait_for_images is True


@pytest.mark.parametrize("sent,expected", [
    (1_000_000, _MAX_DELAY_SECONDS),
    (7, 7),
    (-1, None),
    (math.nan, None),
    ("100", None),
    (True, None),
])
def test_untrusted_crawler_config_caps_screenshot_wait_for(sent, expected):
    cfg = CrawlerRunConfig.load(
        {"type": "CrawlerRunConfig", "params": {"screenshot": True, "screenshot_wait_for": sent}},
        provenance=Provenance.UNTRUSTED,
    )
    assert cfg.screenshot_wait_for == expected


def test_trusted_crawler_config_is_not_capped():
    cfg = CrawlerRunConfig.load(
        {"type": "CrawlerRunConfig", "params": {"screenshot_wait_for": 1_000}},
        provenance=Provenance.TRUSTED,
    )
    assert cfg.screenshot_wait_for == 1_000
