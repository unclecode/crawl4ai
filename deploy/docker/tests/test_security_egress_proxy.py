"""
R3 browser egress-proxy tests (real loopback sockets, fully offline).

The pinning proxy is what actually stops DNS rebinding on the browser path:
Chromium is pointed at it, so it asks the proxy to CONNECT host:port; the proxy
resolves-and-pins (egress_broker.resolve_and_pin) and dials only the pinned,
global IP. We drive it with a raw asyncio client + a fake upstream, and stub
resolve_and_pin so a "public" host pins to the loopback upstream while an
"internal" host is refused. (The not-is_global rule itself is covered in
test_security_ssrf_egress.py.)
"""

import asyncio

import pytest

import egress_proxy
from egress_broker import EgressBlocked, PinnedTarget
from egress_proxy import PinningProxy

pytestmark = pytest.mark.posture

_PROXY_ENV = (
    "CRAWL4AI_UPSTREAM_PROXY", "HTTP_PROXY", "http_proxy",
    "HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy",
)


@pytest.fixture(autouse=True)
def _clear_proxy_env(monkeypatch):
    # Keep the suite deterministic on dev machines that sit behind a proxy.
    for name in _PROXY_ENV:
        monkeypatch.delenv(name, raising=False)


async def _fake_upstream():
    async def handle(reader, writer):
        await reader.read(65536)
        writer.write(b"UPSTREAM-OK")
        await writer.drain()
        writer.close()
    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


@pytest.mark.asyncio
class TestPinningProxy:
    async def test_connect_to_global_host_tunnels(self, monkeypatch):
        up, up_port = await _fake_upstream()

        # Pin "good.example" to the loopback upstream (stand-in for a global IP).
        def fake_pin(url):
            return PinnedTarget("https", "good.example", up_port, "127.0.0.1")
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", fake_pin)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(f"CONNECT good.example:{up_port} HTTP/1.1\r\n\r\n".encode())
            await w.drain()
            status = await asyncio.wait_for(r.readline(), timeout=5)
            assert b"200" in status
            await r.readline()  # blank line after the 200
            w.write(b"hello")
            await w.drain()
            body = await asyncio.wait_for(r.read(100), timeout=5)
            assert b"UPSTREAM-OK" in body
            w.close()
        finally:
            await proxy.stop()
            up.close()

    async def test_connect_to_internal_host_blocked(self, monkeypatch):
        def fake_pin(url):
            raise EgressBlocked()
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", fake_pin)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT evil.example:443 HTTP/1.1\r\n\r\n")
            await w.drain()
            status = await asyncio.wait_for(r.readline(), timeout=5)
            assert b"403" in status
            w.close()
        finally:
            await proxy.stop()

    async def test_proxy_dials_pinned_ip_not_requested_host(self, monkeypatch):
        # resolve_and_pin returns a pinned ip distinct from the CONNECT host;
        # assert the proxy dials the pinned ip.
        dialed = {}
        up, up_port = await _fake_upstream()

        def fake_pin(url):
            return PinnedTarget("https", "rebind.example", up_port, "127.0.0.1")
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", fake_pin)

        real_open = asyncio.open_connection

        async def spy_open(host, port, *a, **k):
            dialed["host"], dialed["port"] = host, port
            return await real_open(host, port, *a, **k)
        # patch only the name the proxy module uses
        monkeypatch.setattr(egress_proxy.asyncio, "open_connection", spy_open)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await real_open(proxy.bound_host, proxy.bound_port)
            w.write(f"CONNECT rebind.example:{up_port} HTTP/1.1\r\n\r\n".encode())
            await w.drain()
            await asyncio.wait_for(r.readline(), timeout=5)
            assert dialed.get("host") == "127.0.0.1"  # the pinned ip
            w.close()
        finally:
            await proxy.stop()
            up.close()

    async def test_malformed_connect_400(self):
        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT not-a-host-port HTTP/1.1\r\n\r\n")
            await w.drain()
            status = await asyncio.wait_for(r.readline(), timeout=5)
            assert b"400" in status
            w.close()
        finally:
            await proxy.stop()


async def _fake_corporate_proxy(seen):
    """Minimal HTTP proxy: records the CONNECT request line, replies 200, then
    answers any tunneled bytes with TUNNEL-OK."""
    async def handle(reader, writer):
        line = await reader.readline()
        seen.append(line)
        while True:  # drain CONNECT headers
            h = await reader.readline()
            if h in (b"\r\n", b"\n", b""):
                break
        writer.write(b"HTTP/1.1 200 Connection established\r\nVia: fake\r\n\r\n")
        await writer.drain()
        await reader.read(65536)
        writer.write(b"TUNNEL-OK")
        await writer.drain()
        writer.close()
    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


@pytest.mark.asyncio
class TestUpstreamChaining:
    async def test_chained_connect_pins_ip_and_blocks_before_upstream(self, monkeypatch):
        """The chained-CONNECT security contract: the upstream receives the
        PINNED IP (never a hostname to resolve), its response headers do not
        leak into the tunnel, and a blocked target produces an opaque 403
        with zero upstream traffic."""
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")

        def fake_pin(url):
            if "internal.example" in url:
                raise EgressBlocked()
            return PinnedTarget("https", "good.example", 443, "203.0.113.7")
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", fake_pin)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT good.example:443 HTTP/1.1\r\n\r\n")
            await w.drain()
            status = await asyncio.wait_for(r.readline(), timeout=5)
            assert b"200" in status
            await r.readline()  # blank line after the 200
            w.write(b"hello")
            await w.drain()
            body = await asyncio.wait_for(r.read(100), timeout=5)
            # Upstream's Via header must NOT leak into the tunnel.
            assert body == b"TUNNEL-OK"
            w.close()

            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT internal.example:443 HTTP/1.1\r\n\r\n")
            await w.drain()
            status = await asyncio.wait_for(r.readline(), timeout=5)
            assert b"403" in status
            w.close()
        finally:
            await proxy.stop()
            corp.close()
        # The upstream saw ONLY the pinned IP of the allowed target.
        assert seen == [b"CONNECT 203.0.113.7:443 HTTP/1.1\r\n"]

    async def test_chained_plain_http_pinned_absolute_form_no_smuggling(self, monkeypatch):
        """Plain HTTP via upstream: the request is re-issued in absolute form
        against the PINNED IP (no name for the upstream to resolve), carries
        Connection: close, and a reused client connection cannot smuggle a
        second, unvalidated request upstream."""
        lines = []

        async def handle(reader, writer):
            req = b""
            while b"\r\n\r\n" not in req:
                req += await reader.read(4096)
            lines.append(req)
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nhi")
            await writer.drain()
            writer.close()
        corp = await asyncio.start_server(handle, "127.0.0.1", 0)
        corp_port = corp.sockets[0].getsockname()[1]
        monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{corp_port}")

        def fake_pin(url):
            return PinnedTarget("http", "plain.example", 80, "203.0.113.7")
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", fake_pin)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"GET http://plain.example/ HTTP/1.1\r\n"
                    b"Host: plain.example\r\nConnection: keep-alive\r\n\r\n")
            await w.drain()
            first = await asyncio.wait_for(r.read(200), timeout=5)
            assert b"200" in first
            # Attempt to smuggle an unvalidated request on the same connection.
            w.write(b"GET http://rebind.evil/ HTTP/1.1\r\nHost: rebind.evil\r\n\r\n")
            await w.drain()
            leftover = await asyncio.wait_for(r.read(200), timeout=5)
            assert leftover == b""  # upstream closed; nothing came back
            w.close()
        finally:
            await proxy.stop()
            corp.close()
        sent = b"".join(lines)
        assert sent.startswith(b"GET http://203.0.113.7:80/ HTTP/1.1\r\n")
        assert b"Connection: close" in sent
        assert b"keep-alive" not in sent
        assert b"rebind.evil" not in sent  # the smuggled request never got upstream


def test_upstream_proxy_env_parsing(monkeypatch):
    assert egress_proxy.upstream_proxy() is None
    monkeypatch.setenv("HTTP_PROXY", "http://192.168.180.254:56560")
    assert egress_proxy.upstream_proxy() == ("192.168.180.254", 56560, None)
    monkeypatch.setenv("HTTPS_PROXY", "http://user:p%40ss@10.0.0.1:8080")
    host, port, auth = egress_proxy.upstream_proxy()
    assert (host, port) == ("10.0.0.1", 8080)
    import base64
    assert base64.b64decode(auth.split(b" ")[-1].strip()) == b"user:p@ss"
    # scheme-aware selection: http targets prefer HTTP_PROXY
    assert egress_proxy.upstream_proxy("http") == ("192.168.180.254", 56560, None)
    monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY", "proxy.corp:3128")
    assert egress_proxy.upstream_proxy() == ("proxy.corp", 3128, None)
    # whitespace-only env var means unset, not a proxy named "   "
    monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY", "   ")
    monkeypatch.delenv("HTTP_PROXY")
    monkeypatch.delenv("HTTPS_PROXY")
    assert egress_proxy.upstream_proxy() is None
    # a junk/unsupported candidate falls through to a valid fallback
    monkeypatch.setenv("HTTP_PROXY", "http://good:3128")
    monkeypatch.setenv("HTTPS_PROXY", "http://")
    assert egress_proxy.upstream_proxy() == ("good", 3128, None)
    monkeypatch.setenv("HTTPS_PROXY", "https://tls-proxy.corp")  # unsupported scheme
    assert egress_proxy.upstream_proxy() == ("good", 3128, None)
    monkeypatch.delenv("CRAWL4AI_UPSTREAM_PROXY")
    monkeypatch.delenv("HTTP_PROXY")
    assert egress_proxy.upstream_proxy() is None  # https:// alone -> refused, not mis-dialed
    # non-latin-1 credentials must not raise (encoded as UTF-8)
    monkeypatch.setenv("HTTPS_PROXY", "http://u:%E5%AF%86%E7%A0%81@10.0.0.1:8080")
    assert egress_proxy.upstream_proxy()[2] is not None
    # NO_PROXY routing: suffix and CIDR entries force a direct dial
    pin = PinnedTarget("https", "site.corp.example", 443, "203.0.113.7")
    assert egress_proxy._use_upstream(pin) is not None
    monkeypatch.setenv("NO_PROXY", ".corp.example")
    assert egress_proxy._use_upstream(pin) is None
    monkeypatch.setenv("NO_PROXY", "203.0.113.0/24")
    assert egress_proxy._use_upstream(pin) is None
    monkeypatch.setenv("NO_PROXY", "site.corp.example:443")  # host:port form
    assert egress_proxy._use_upstream(pin) is None


class TestEnforceEgressWiring:
    def test_enforce_egress_sets_proxy(self, monkeypatch):
        import egress_broker
        from crawl4ai import BrowserConfig
        monkeypatch.setattr(egress_broker, "_EGRESS_PROXY_URL", "http://127.0.0.1:9999")
        b = BrowserConfig()
        egress_broker.enforce_egress(b)
        assert b.proxy_config is not None
        assert b.proxy_config.server == "http://127.0.0.1:9999"
