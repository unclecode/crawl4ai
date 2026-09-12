"""Offline regression tests for robots.txt TLS verification (issue #2252).

No network access: aiohttp.ClientSession is replaced by a recorder that exposes the
kwargs the parser passes to ``session.get``.
"""

import asyncio

from crawl4ai import utils
from crawl4ai.utils import RobotsParser


class _FakeResponse:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self._body = body

    async def text(self) -> str:
        return self._body

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *exc) -> bool:
        return False


class _FakeSession:
    """Records every session.get(...) call; returns a canned 200 + robots body."""

    calls: list[tuple[str, dict]] = []
    body: str = "User-agent: *\nDisallow: /private\n"

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    def get(self, url: str, **kwargs):
        type(self).calls.append((url, kwargs))
        return _FakeResponse(200, type(self).body)


def _parse(url: str, verify_ssl: bool, tmp_path):
    _FakeSession.calls = []
    parser = RobotsParser(cache_dir=str(tmp_path), verify_ssl=verify_ssl)
    allowed = asyncio.new_event_loop().run_until_complete(parser.can_fetch(url))
    return allowed, _FakeSession.calls


def test_https_robots_keeps_tls_verification_by_default(monkeypatch, tmp_path):
    """Default: https robots.txt must NOT disable certificate validation."""
    monkeypatch.setattr(utils.aiohttp, "ClientSession", _FakeSession)
    _, calls = _parse("https://example.com/page", verify_ssl=True, tmp_path=tmp_path)
    assert len(calls) == 1, calls
    url, kwargs = calls[0]
    assert url == "https://example.com/robots.txt"
    # aiohttp: ssl=None -> default context (verification ON). ssl=False would disable it.
    assert kwargs.get("ssl", "<missing>") is None, kwargs
    assert kwargs.get("ssl") is not False, kwargs


def test_explicit_opt_out_still_disables_verification(monkeypatch, tmp_path):
    """Escape hatch: verify_ssl=False keeps the old behaviour, explicitly."""
    monkeypatch.setattr(utils.aiohttp, "ClientSession", _FakeSession)
    _, calls = _parse("https://example.com/page", verify_ssl=False, tmp_path=tmp_path)
    assert len(calls) == 1, calls
    assert calls[0][1].get("ssl") is False, calls[0][1]


def test_rules_are_still_enforced_after_fetch(monkeypatch, tmp_path):
    """Behaviour regression: a fetched Disallow rule still blocks the URL."""
    monkeypatch.setattr(utils.aiohttp, "ClientSession", _FakeSession)
    _FakeSession.body = "User-agent: *\nDisallow: /private\n"
    allowed, _ = _parse("https://example.com/private/page", verify_ssl=True, tmp_path=tmp_path)
    assert allowed is False
    _FakeSession.body = "User-agent: *\nDisallow: /private\n"
    allowed_ok, _ = _parse("https://example.com/public/page", verify_ssl=True, tmp_path=tmp_path)
    assert allowed_ok is True


def test_non_200_or_error_still_allows(monkeypatch, tmp_path):
    """Behaviour regression: 404 / connection error => allow (unchanged)."""
    monkeypatch.setattr(utils.aiohttp, "ClientSession", _FakeSession)
    _FakeSession.body = ""
    original_status = _FakeResponse.__init__

    def _status404(self, status, body):  # noqa: ANN001
        original_status(self, 404, body)

    monkeypatch.setattr(_FakeResponse, "__init__", _status404)
    allowed, calls = _parse("https://example.com/anything", verify_ssl=True, tmp_path=tmp_path)
    assert allowed is True and len(calls) == 1
    monkeypatch.setattr(_FakeResponse, "__init__", original_status)

    class _Boom(_FakeSession):
        def get(self, url, **kwargs):  # noqa: ANN001
            raise ConnectionError("no network in tests")

    monkeypatch.setattr(utils.aiohttp, "ClientSession", _Boom)
    allowed_err, _ = _parse("https://example.com/anything", verify_ssl=True, tmp_path=tmp_path)
    assert allowed_err is True
