"""Regression tests: text IO must not depend on the system locale.

Two failure shapes are covered:

* Subprocess output decoded with the strict default codec. tasklist and
  Chromium emit ANSI/OEM-encoded text on Windows, while Python 3.15 enables
  UTF-8 mode by default (PEP 686), so a strict decode raises
  UnicodeDecodeError exactly when diagnosing a failing browser launch.
* Cache files written and read back with the locale codec. Common Crawl URL
  caches contain non-ASCII URLs, which cannot be encoded under cp1252/cp936
  locales and mojibake on read-back.
"""

import json
import subprocess
import sys

import aiofiles
import pytest

import crawl4ai.async_url_seeder as seeder_module
import crawl4ai.browser_profiler as profiler_module
from crawl4ai.async_url_seeder import AsyncUrlSeeder
from crawl4ai.browser_profiler import BrowserProfiler

# ── Windows process probe (browser_profiler) ─────────────────────────────


def test_tasklist_probe_pins_tolerant_decoding(monkeypatch):
    recorded = {}

    def fake_run(args, **kwargs):
        recorded.update(kwargs)
        return subprocess.CompletedProcess(args, 0, stdout="foo.exe  1234 Console")

    monkeypatch.setattr(profiler_module.subprocess, "run", fake_run)
    profiler = BrowserProfiler.__new__(BrowserProfiler)
    assert profiler._is_browser_running(1234) is True
    assert recorded.get("encoding") == "utf-8"
    assert recorded.get("errors") == "replace"


@pytest.mark.skipif(sys.platform != "win32", reason="tasklist is Windows-only")
def test_tasklist_probe_never_raises_on_localized_output():
    profiler = BrowserProfiler.__new__(BrowserProfiler)
    # PID 4 (System) always answers; the probe must survive any console
    # codepage, including under UTF-8 mode.
    assert profiler._is_browser_running(4) is True


# ── Browser startup diagnostics (browser_manager) ────────────────────────


@pytest.mark.asyncio
async def test_startup_check_tolerates_non_utf8_browser_output():
    from crawl4ai.browser_manager import BrowserManager

    class FakeProcess:
        returncode = 1

        def poll(self):
            return 1  # terminated during startup

        def communicate(self, timeout=None):
            # ANSI/OEM-encoded diagnostics: invalid as UTF-8.
            return b"", b"\xd3\xef\xd1\xd4"

    class FakeLogger:
        def __init__(self):
            self.params = None

        def error(self, message="", tag="", params=None, **kwargs):
            self.params = params

    manager = BrowserManager.__new__(BrowserManager)
    manager.browser_process = FakeProcess()
    manager.logger = FakeLogger()
    await manager._initial_startup_check()
    assert manager.logger.params is not None


# ── Common Crawl cache (async_url_seeder) ────────────────────────────────


class _FakeResponse:
    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        pass

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class _FakeClient:
    def __init__(self, lines):
        self._lines = lines
        self.requests = []

    def stream(self, method, url):
        self.requests.append(url)
        return _FakeStreamContext(self._lines)


class _FakeStreamContext:
    def __init__(self, lines):
        self._lines = lines

    async def __aenter__(self):
        return _FakeResponse(self._lines)

    async def __aexit__(self, *exc):
        return False


def _make_seeder(tmp_path, lines):
    seeder = AsyncUrlSeeder.__new__(AsyncUrlSeeder)
    seeder.cache_dir = tmp_path / "seeder_cache"
    seeder.cache_dir.mkdir(parents=True, exist_ok=True)
    seeder.index_id = "CC-MAIN-2026-01"
    seeder.client = _FakeClient(lines)
    seeder.logger = None
    return seeder


@pytest.mark.asyncio
async def test_cc_cache_roundtrip_preserves_non_ascii_urls(tmp_path):
    urls = ["https://例え.jp/パス/一覧", "https://example.com/plain"]
    seeder = _make_seeder(tmp_path, [json.dumps({"url": u}) for u in urls])
    got = [u async for u in seeder._from_cc("example.jp", "*", False)]
    assert got == urls
    cache_file = next(seeder.cache_dir.glob("*.jsonl"))
    assert "例え".encode("utf-8") in cache_file.read_bytes()

    # Second run must serve the same URLs from the cache, with no network.
    seeder.client.requests.clear()
    got2 = [u async for u in seeder._from_cc("example.jp", "*", False)]
    assert got2 == urls
    assert seeder.client.requests == []


@pytest.mark.asyncio
async def test_cc_cache_survives_non_utf8_system_locale(tmp_path, monkeypatch):
    """Simulate a latin-1 system locale: any implicit-encoding file IO fails."""
    real_open = aiofiles.open

    def locale_open(file, mode="r", *args, **kwargs):
        if "b" not in mode and "encoding" not in kwargs:
            kwargs["encoding"] = "latin-1"
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(seeder_module.aiofiles, "open", locale_open)
    url = "https://例え.jp/一覧"
    seeder = _make_seeder(tmp_path, [json.dumps({"url": url})])
    got = [u async for u in seeder._from_cc("例え.jp", "*", False)]
    assert got == [url]
    # Read-back must also stay UTF-8, not the simulated locale codec.
    got2 = [u async for u in seeder._from_cc("例え.jp", "*", False)]
    assert got2 == [url]
