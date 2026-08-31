"""
R3 webhook connection-pinning tests (real loopback server, offline).

The webhook sender pins the connection to the validated IP (aiohttp resolver),
follows redirects manually, and re-validates every hop. We stub the egress
broker so a "good" host pins to the loopback test server and "internal" hosts /
redirects are refused.
"""

import asyncio

import pytest

import egress_broker
from egress_broker import EgressBlocked, PinnedTarget
from webhook import WebhookDeliveryService

pytestmark = pytest.mark.posture


async def _raw_server(response: bytes):
    async def handle(reader, writer):
        await reader.read(65536)
        writer.write(response)
        await writer.drain()
        writer.close()
    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


def _svc():
    return WebhookDeliveryService({"webhooks": {"retry": {"max_attempts": 2,
                                   "initial_delay_ms": 1, "timeout_ms": 5000}}})


@pytest.mark.asyncio
class TestWebhookPinning:
    async def test_delivered_to_pinned_host(self, monkeypatch):
        server, port = await _raw_server(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
        monkeypatch.setattr(
            egress_broker, "resolve_and_pin",
            lambda url: PinnedTarget("http", "good.example", port, "127.0.0.1"),
        )
        try:
            ok = await _svc().send_webhook(f"http://good.example:{port}/cb", {"x": 1})
            assert ok is True
        finally:
            server.close()

    async def test_internal_target_blocked_no_retry(self, monkeypatch):
        def boom(url):
            raise EgressBlocked()
        monkeypatch.setattr(egress_broker, "resolve_and_pin", boom)
        ok = await _svc().send_webhook("http://169.254.169.254/cb", {"x": 1})
        assert ok is False

    async def test_redirect_to_internal_blocked(self, monkeypatch):
        server, port = await _raw_server(
            b"HTTP/1.1 302 Found\r\nLocation: http://evil.internal/\r\nContent-Length: 0\r\n\r\n"
        )
        monkeypatch.setattr(
            egress_broker, "resolve_and_pin",
            lambda url: PinnedTarget("http", "good.example", port, "127.0.0.1"),
        )

        def check(loc):
            raise EgressBlocked()  # the redirect target is internal
        monkeypatch.setattr(egress_broker, "check_redirect", check)
        try:
            ok = await _svc().send_webhook(f"http://good.example:{port}/cb", {"x": 1})
            assert ok is False  # redirect re-validation refused it
        finally:
            server.close()

    async def test_uses_pinned_resolver(self):
        # The resolver returns the pinned IP for any host (TLS still verifies the
        # hostname); confirm the wiring.
        from webhook import _PinnedResolver
        r = _PinnedResolver("good.example", "203.0.113.7")
        out = await r.resolve("good.example", 443)
        assert out[0]["host"] == "203.0.113.7"
        assert out[0]["hostname"] == "good.example"
