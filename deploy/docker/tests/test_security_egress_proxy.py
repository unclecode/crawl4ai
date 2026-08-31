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


class TestEnforceEgressWiring:
    def test_enforce_egress_sets_proxy(self, monkeypatch):
        import egress_broker
        from crawl4ai import BrowserConfig
        monkeypatch.setattr(egress_broker, "_EGRESS_PROXY_URL", "http://127.0.0.1:9999")
        b = BrowserConfig()
        egress_broker.enforce_egress(b)
        assert b.proxy_config is not None
        assert b.proxy_config.server == "http://127.0.0.1:9999"
