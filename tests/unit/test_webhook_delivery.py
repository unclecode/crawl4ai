import asyncio
import logging
import socket
import sys
from pathlib import Path

import pytest

DOCKER_DIR = Path(__file__).resolve().parents[2] / "deploy" / "docker"
if str(DOCKER_DIR) not in sys.path:
    sys.path.insert(0, str(DOCKER_DIR))

import egress_broker  # noqa: E402
from egress_broker import PinnedTarget  # noqa: E402
from webhook import WebhookDeliveryService  # noqa: E402


async def _step_server(steps):
    received = []
    idx = [0]

    async def handle(reader, writer):
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = await reader.read(4096)
            if not chunk:
                break
            data += chunk
        head, rest = data.split(b"\r\n\r\n", 1)
        content_len = 0
        for line in head.split(b"\r\n")[1:]:
            if line.lower().startswith(b"content-length:"):
                content_len = int(line.split(b":", 1)[1].strip())
        while len(rest) < content_len:
            chunk = await reader.read(4096)
            if not chunk:
                break
            rest += chunk
        received.append(
            (head.decode("latin-1"), rest.decode("utf-8", errors="replace"))
        )

        step_i = min(idx[0], len(steps) - 1)
        idx[0] += 1
        writer.write(steps[step_i])
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1], received


def _service(**extra_webhooks):
    cfg = {
        "retry": {"max_attempts": 2, "initial_delay_ms": 1, "timeout_ms": 5000},
        **extra_webhooks,
    }
    return WebhookDeliveryService({"webhooks": cfg})


@pytest.mark.asyncio
async def test_relative_redirect_succeeds_under_real_egress_validation(monkeypatch):
    server, port, received = await _step_server(
        [
            b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /v2/ingest?ok=1\r\nContent-Length: 0\r\n\r\n",
            b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok",
        ]
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda host, p, *a, **kw: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", p or 0))
        ],
    )
    monkeypatch.setattr(
        "webhook._PinnedResolver.resolve",
        lambda self, host, p=0, family=socket.AF_INET: asyncio.sleep(
            0,
            result=[
                {
                    "hostname": host,
                    "host": "127.0.0.1",
                    "port": port,
                    "family": family,
                    "proto": 0,
                    "flags": 0,
                }
            ],
        ),
    )
    try:
        ok = await _service().send_webhook(
            f"http://hooks.example:{port}/v1/ingest", {"job": "1"}
        )
        assert ok is True
        assert len(received) == 2
        assert received[1][0].startswith("POST /v2/ingest?ok=1 HTTP/1.1")
        assert '"job": "1"' in received[1][1]
    finally:
        server.close()


@pytest.mark.asyncio
async def test_redirect_hop_resolves_and_pins_each_url_once(monkeypatch):
    server, port, _ = await _step_server(
        [
            b"HTTP/1.1 308 Permanent Redirect\r\nLocation: /v2/cb\r\nContent-Length: 0\r\n\r\n",
            b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok",
        ]
    )
    resolved_urls = []

    def fake_resolve(url):
        resolved_urls.append(url)
        return PinnedTarget("http", "hooks.example", port, "127.0.0.1")

    monkeypatch.setattr(egress_broker, "resolve_and_pin", fake_resolve)
    try:
        ok = await _service().send_webhook(
            f"http://hooks.example:{port}/v1/cb", {"x": 1}
        )
        assert ok is True
        assert resolved_urls == [
            f"http://hooks.example:{port}/v1/cb",
            f"http://hooks.example:{port}/v2/cb",
        ]
    finally:
        server.close()


@pytest.mark.asyncio
async def test_303_see_other_switches_followup_request_to_get_without_body(monkeypatch):
    steps = []
    server, port, received = await _step_server(steps)
    steps.extend(
        [
            f"HTTP/1.1 303 See Other\r\nLocation: http://hooks.example:{port}/hooks/ack\r\nContent-Length: 0\r\n\r\n".encode(),
            b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok",
        ]
    )
    monkeypatch.setattr(
        egress_broker,
        "resolve_and_pin",
        lambda url: PinnedTarget("http", "hooks.example", port, "127.0.0.1"),
    )
    try:
        ok = await _service().send_webhook(
            f"http://hooks.example:{port}/hooks/submit", {"done": True}
        )
        assert ok is True
        assert len(received) == 2
        assert received[0][0].startswith("POST /hooks/submit HTTP/1.1")
        assert received[1][0].startswith("GET /hooks/ack HTTP/1.1")
        assert received[1][1] == ""
    finally:
        server.close()


@pytest.mark.asyncio
async def test_exhausted_retries_log_final_error(monkeypatch, caplog):
    server, port, _ = await _step_server(
        [b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\n\r\n"]
    )
    monkeypatch.setattr(
        egress_broker,
        "resolve_and_pin",
        lambda url: PinnedTarget("http", "hooks.example", port, "127.0.0.1"),
    )
    target = f"http://hooks.example:{port}/cb"
    try:
        with caplog.at_level(logging.ERROR):
            ok = await _service().send_webhook(target, {"x": 1})
        assert ok is False
        assert any(
            "Webhook delivery failed after 2 attempts" in rec.message
            and target in rec.message
            for rec in caplog.records
        )
    finally:
        server.close()
