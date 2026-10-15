"""SSLCertificate.from_url dials the URL's real host, through the egress proxy.

Report 2026-10 (ssl-cert-userinfo-ssrf): from_url took the host from netloc, so
for https://127.0.0.1:443@example.com/ the Docker SSRF check saw example.com
while the certificate fetch dialled 127.0.0.1. It also dialled directly, outside
the pinning egress proxy, which left DNS rebinding open with a plain hostname.

No network: socket.create_connection is replaced with a recorder.
"""

import socket

import pytest

from crawl4ai import egress_policy
from crawl4ai.ssl_certificate import SSLCertificate


class _FakeSock:
    def __init__(self, reply):
        self.sent = b""
        self._reply = reply

    def sendall(self, data):
        self.sent += data

    def recv(self, n):
        out, self._reply = self._reply[:n], self._reply[n:]
        return out

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


@pytest.fixture
def dials(monkeypatch):
    calls = []

    def fake_create_connection(addr, *a, **kw):
        sock = _FakeSock(b"HTTP/1.1 403 Forbidden\r\n\r\n")
        calls.append((addr, sock))
        if not egress_policy.proxy_url():
            raise ConnectionRefusedError("test: no real dial")
        return sock

    monkeypatch.setattr(socket, "create_connection", fake_create_connection)
    yield calls
    egress_policy.set_egress_proxy(None)


def test_userinfo_is_not_taken_as_the_host(dials):
    assert SSLCertificate.from_url("https://127.0.0.1:443@example.com/") is None
    assert [addr for addr, _ in dials] == [("example.com", 443)]


def test_url_port_is_used(dials):
    SSLCertificate.from_url("https://example.com:8443/")
    assert [addr for addr, _ in dials] == [("example.com", 8443)]


def test_installed_egress_proxy_gets_a_connect_for_the_real_host(dials):
    egress_policy.set_egress_proxy("http://127.0.0.1:3128")
    assert SSLCertificate.from_url("https://127.0.0.1:443@example.com/") is None
    (addr, sock), = dials
    assert addr == ("127.0.0.1", 3128)
    assert sock.sent.startswith(b"CONNECT example.com:443 HTTP/1.1\r\n")


def test_ipv6_host_is_bracketed_in_connect(dials):
    egress_policy.set_egress_proxy("http://127.0.0.1:3128")
    SSLCertificate.from_url("https://[2001:db8::1]/")
    (_, sock), = dials
    assert sock.sent.startswith(b"CONNECT [2001:db8::1]:443 HTTP/1.1\r\n")
