"""Pooled browser contexts never cross a context partition.

Report 2026-10 (docker-shared-browser-context): the Docker server reused one
BrowserContext per config, so one API caller's cookies, localStorage and
service workers were present in the next caller's crawl. The server now sets
crawl4ai.browser_manager.browser_context_partition per request, and the
context cache is keyed by it.

Real Chromium, local HTTP server only. Every "isolated" assertion is paired
with a same-partition run that shows the probe would have seen the state.
"""

import asyncio
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.browser_manager import BrowserManager, browser_context_partition

RUN = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

# /set?v=X  -> Set-Cookie secret=X, localStorage secret=X, registers /sw.js
# /echo     -> shows the Cookie header and localStorage in the DOM
# /sw.js    -> a service worker that answers /echo with HIJACKED
# Pages carry filler text so the crawler's anti-bot check does not flag them.
_FILL = "<p>" + "This page exists to test browser context isolation. " * 20 + "</p>"
_SET = """<html><body><p>set</p>""" + _FILL + """<script>
localStorage.setItem('secret', new URL(location).searchParams.get('v'));
window.__swReady = false;
if (new URL(location).searchParams.get('sw')) {
  navigator.serviceWorker.register('/sw.js').then(() => navigator.serviceWorker.ready)
    .then(() => { window.__swReady = true; });
} else { window.__swReady = true; }
</script></body></html>"""
_ECHO = """<html><body><p id=c>COOKIE[%s]</p><p id=l></p>""" + _FILL + """<script>
document.getElementById('l').textContent = 'LS[' + (localStorage.getItem('secret') || '') + ']';
</script></body></html>"""
_SW = """self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (new URL(e.request.url).pathname === '/echo')
    e.respondWith(new Response('<html><body><p>HIJACKED</p>' + '<p>filler text for the anti-bot check.</p>'.repeat(20) + '</body></html>',
                               {headers: {'Content-Type': 'text/html'}}));
});"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path, _, query = self.path.partition("?")
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
        self.send_response(200)
        if path == "/sw.js":
            self.send_header("Content-Type", "application/javascript")
            body = _SW
        elif path == "/set":
            self.send_header("Content-Type", "text/html")
            self.send_header("Set-Cookie", f"secret={params.get('v', '')}; Path=/")
            body = _SET
        else:
            self.send_header("Content-Type", "text/html")
            body = _ECHO % (self.headers.get("Cookie") or "")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def site():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


async def _in(partition, coro_fn):
    """Run coro_fn() with the partition set, as the server does per request."""
    token = browser_context_partition.set(partition)
    try:
        return await coro_fn()
    finally:
        browser_context_partition.reset(token)


async def _set(crawler, site, partition, value, sw=False):
    url = f"{site}/set?v={value}" + ("&sw=1" if sw else "")
    cfg = RUN.clone(wait_for="js:() => window.__swReady === true") if sw else RUN
    r = await _in(partition, lambda: crawler.arun(url, config=cfg))
    assert r.success, r.error_message


async def _echo(crawler, site, partition):
    r = await _in(partition, lambda: crawler.arun(f"{site}/echo", config=RUN))
    assert r.success, r.error_message
    return r.html


@pytest.mark.asyncio
async def test_cookie_and_storage_stay_in_their_partition(site):
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as c:
        await _set(c, site, "alice", "ALICE-SECRET")
        own = await _echo(c, site, "alice")
        other = await _echo(c, site, "mallory")
    # Probe sensitivity: the owner sees both.
    assert "secret=ALICE-SECRET" in own and "LS[ALICE-SECRET]" in own
    assert "ALICE-SECRET" not in other
    assert "LS[]" in other


@pytest.mark.asyncio
async def test_attacker_state_does_not_reach_the_victim(site):
    """Write direction: mallory plants a cookie, alice must not send it."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as c:
        await _set(c, site, "mallory", "PLANTED")
        victim = await _echo(c, site, "alice")
        attacker = await _echo(c, site, "mallory")
    assert "PLANTED" in attacker
    assert "PLANTED" not in victim


@pytest.mark.asyncio
async def test_service_worker_does_not_cross_partitions(site):
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as c:
        await _set(c, site, "mallory", "SW", sw=True)
        attacker = await _echo(c, site, "mallory")
        victim = await _echo(c, site, "alice")
    assert "HIJACKED" in attacker  # the worker is live in mallory's context
    assert "HIJACKED" not in victim and "COOKIE[" in victim


@pytest.mark.asyncio
async def test_unset_partition_is_its_own_bucket(site):
    """Plain-library use (no partition) keeps one shared context per config,
    and that bucket is still separate from every named partition."""
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as c:
        await _set(c, site, None, "LIB")
        lib_again = await _echo(c, site, None)
        named = await _echo(c, site, "alice")
        await _set(c, site, "alice", "ALICE")
        lib_after = await _echo(c, site, None)
    assert "secret=LIB" in lib_again  # unchanged library behaviour
    assert "LIB" not in named
    assert "ALICE" not in lib_after


@pytest.mark.asyncio
async def test_similar_partition_names_do_not_collide(site):
    names = ["alice", "Alice", "alice ", "alice\x00", "", "None", "null"]
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as c:
        for i, n in enumerate(names):
            await _set(c, site, n, f"V{i}X")
        seen = [await _echo(c, site, n) for n in names]
        unset = await _echo(c, site, None)
    for i, html in enumerate(seen):
        others = [f"V{j}X" for j in range(len(names)) if j != i]
        assert f"secret=V{i}X" in html, names[i]
        assert not any(o in html for o in others), names[i]
    assert not any(f"V{i}X" in unset for i in range(len(names)))


@pytest.mark.asyncio
async def test_concurrent_partitions_never_mix(site):
    n = 8
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as c:
        await asyncio.gather(*(_set(c, site, f"user{i}", f"S{i}X") for i in range(n)))
        # Interleave the reads with fresh writes so contexts are busy at once.
        reads = await asyncio.gather(
            *(_echo(c, site, f"user{i}") for i in range(n)),
            *(_set(c, site, f"late{i}", f"L{i}X") for i in range(n)),
        )
    for i, html in enumerate(reads[:n]):
        assert f"secret=S{i}X" in html
        leaked = [f"S{j}X" for j in range(n) if j != i] + [f"L{j}X" for j in range(n)]
        assert not any(x in html for x in leaked), (i, html)


@pytest.mark.asyncio
async def test_arun_many_runs_in_the_callers_partition(site):
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as c:
        await _set(c, site, "alice", "MANY")
        urls = [f"{site}/echo?i={i}" for i in range(4)]
        own = await _in("alice", lambda: c.arun_many(urls, config=RUN))
        other = await _in("mallory", lambda: c.arun_many(urls, config=RUN))
    assert all("secret=MANY" in r.html for r in own)
    assert not any("MANY" in r.html for r in other)


@pytest.mark.asyncio
async def test_isolation_holds_across_browser_recycle(site):
    cfg = BrowserConfig(headless=True, verbose=False, max_pages_before_recycle=3)
    async with AsyncWebCrawler(config=cfg) as c:
        for i in range(7):  # crosses the recycle threshold twice
            await _set(c, site, "alice", f"R{i}X")
            other = await _echo(c, site, "mallory")
            assert not any(f"R{j}X" in other for j in range(i + 1)), i


# ── managed browser: the shared default_context must not be used ──────────


class _FakePage:
    def __init__(self, context):
        self.context = context


class _FakeContext:
    def __init__(self, name):
        self.name = name
        self.pages = []

    async def new_page(self):
        page = _FakePage(self)
        self.pages.append(page)
        return page


@pytest.mark.asyncio
async def test_managed_browser_gives_each_partition_its_own_context(monkeypatch):
    bm = BrowserManager(BrowserConfig(use_managed_browser=True, verbose=False))
    shared = _FakeContext("default")
    bm.default_context = shared
    made = []

    async def create_browser_context(cfg=None):
        ctx = _FakeContext(f"ctx{len(made)}")
        made.append(ctx)
        return ctx

    async def noop(*a, **k):
        return None

    monkeypatch.setattr(bm, "create_browser_context", create_browser_context)
    monkeypatch.setattr(bm, "setup_context", noop)
    monkeypatch.setattr(bm, "_apply_stealth_to_page", noop)
    monkeypatch.setattr(bm, "_maybe_bump_browser_version", noop)
    monkeypatch.setattr(bm, "_cleanup_expired_sessions", lambda: None)

    cfg = CrawlerRunConfig()
    _, a1 = await _in("alice", lambda: bm.get_page(cfg))
    _, a2 = await _in("alice", lambda: bm.get_page(cfg))
    _, m1 = await _in("mallory", lambda: bm.get_page(cfg))

    assert a1 is a2 and a1 is not m1
    assert shared not in (a1, m1)
    # Unpartitioned library use keeps the managed default_context.
    monkeypatch.setattr(BrowserManager, "_get_global_lock", staticmethod(lambda: asyncio.Lock()))
    _, lib = await bm.get_page(cfg)
    assert lib is shared


def test_signature_depends_on_partition_only_when_set():
    bm = BrowserManager(BrowserConfig(verbose=False))
    cfg = CrawlerRunConfig()

    def sig(p):
        token = browser_context_partition.set(p)
        try:
            return bm._make_config_signature(cfg)
        finally:
            browser_context_partition.reset(token)

    assert sig("alice") == sig("alice")
    assert len({sig(None), sig("alice"), sig("Alice"), sig(""), sig("None")}) == 5
