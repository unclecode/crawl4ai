"""Regression tests for the PDF fetch path: destination validation and resource caps.

Covers two reported issues:
  - a public URL that redirects to an internal address must fail closed (SSRF)
  - an oversized remote PDF must abort instead of filling the disk (DoS)

The fetch helper takes the `requests` module as an argument, so these drive it
with a stub and need no network or live server.
"""

import os

import pytest

from crawl4ai.processors.pdf import (
    PDFContentScrapingStrategy,
    set_peer_ip_validator,
    set_url_validator,
)
import crawl4ai.processors.pdf as pdf_module


class Blocked(Exception):
    """Stand-in for egress_broker.EgressBlocked."""


class FakeResponse:
    def __init__(self, status_code=200, headers=None, chunks=(), peer_ip="93.184.216.34"):
        self.status_code = status_code
        self.headers = headers or {}
        self._chunks = list(chunks)
        self.closed = False
        self.raw = self._make_raw(peer_ip)

    def _make_raw(self, peer_ip):
        """Mirror urllib3 2.x layout: raw._fp.fp.raw._sock.

        Worth keeping faithful -- an earlier version of this stub exposed the
        socket somewhere urllib3 does not, and hid a real bug.
        """
        if peer_ip is None:
            return object()  # bodyless response: socket already released

        class _Sock:
            def getpeername(self_inner):
                return (peer_ip, 443)

        class _SocketIO:
            _sock = _Sock()

        class _Buffered:
            raw = _SocketIO()

        class _HTTPResponse:
            fp = _Buffered()

        class _Raw:
            _fp = _HTTPResponse()

        return _Raw()

    def iter_content(self, chunk_size=8192):
        for chunk in self._chunks:
            yield chunk

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class FakeRequests:
    """Stub of the `requests` module surface the downloader uses."""

    class exceptions:
        class Timeout(Exception):
            pass

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self._responses.pop(0)

    def Session(self):
        # The downloader opens one Session for the whole redirect chain, so a
        # host that sets a cookie and then redirects gets it back on the next
        # hop. Returning self keeps every call recorded in one place.
        return self


@pytest.fixture(autouse=True)
def _reset_validators():
    """Validators are module-level globals; leaking one breaks later tests."""
    yield
    set_url_validator(None)
    set_peer_ip_validator(None)


def _strategy(**kwargs):
    return PDFContentScrapingStrategy(**kwargs)


# ── destination validation (SSRF) ──────────────────────────────────────


def test_redirect_target_is_validated_and_blocked():
    seen = []

    def validator(url):
        seen.append(url)
        if "169.254.169.254" in url or "127.0.0.1" in url:
            raise Blocked(url)

    set_url_validator(validator)
    strategy = _strategy()
    requests = FakeRequests([
        FakeResponse(302, {"location": "http://169.254.169.254/latest/meta-data/"}),
    ])

    with pytest.raises(Blocked):
        strategy._fetch_with_redirect_checks(requests, "https://public.example/doc.pdf")

    assert seen == [
        "https://public.example/doc.pdf",
        "http://169.254.169.254/latest/meta-data/",
    ], "validator must run on the redirect target, not just the seed"


def test_redirects_are_never_followed_by_requests_itself():
    set_url_validator(lambda url: None)
    strategy = _strategy()
    requests = FakeRequests([
        FakeResponse(302, {"location": "https://public.example/real.pdf"}),
        FakeResponse(200, {"content-length": "4"}, [b"%PDF"]),
    ])

    strategy._fetch_with_redirect_checks(requests, "https://public.example/doc.pdf")

    assert [kw["allow_redirects"] for _, kw in requests.calls] == [False, False]


def test_relative_location_is_resolved_before_validation():
    seen = []
    set_url_validator(seen.append)
    strategy = _strategy()
    requests = FakeRequests([
        FakeResponse(302, {"location": "/elsewhere.pdf"}),
        FakeResponse(200, {}, [b"%PDF"]),
    ])

    strategy._fetch_with_redirect_checks(requests, "https://public.example/a/doc.pdf")

    assert seen[1] == "https://public.example/elsewhere.pdf"


def test_redirect_chain_is_bounded():
    set_url_validator(lambda url: None)
    strategy = _strategy(max_redirects=2)
    requests = FakeRequests([
        FakeResponse(302, {"location": f"https://public.example/{i}.pdf"})
        for i in range(5)
    ])

    with pytest.raises(RuntimeError, match="Too many redirects"):
        strategy._fetch_with_redirect_checks(requests, "https://public.example/doc.pdf")


def test_redirect_without_location_is_rejected():
    set_url_validator(lambda url: None)
    strategy = _strategy()
    requests = FakeRequests([FakeResponse(302, {})])

    with pytest.raises(RuntimeError, match="Redirect without Location"):
        strategy._fetch_with_redirect_checks(requests, "https://public.example/doc.pdf")


def test_peer_ip_is_checked_closing_dns_rebinding():
    """The name may pass validation and still resolve inward when requests dials."""
    set_url_validator(lambda url: None)

    def peer_validator(ip):
        if ip.startswith("127.") or ip.startswith("169.254."):
            raise Blocked(ip)

    set_peer_ip_validator(peer_validator)
    strategy = _strategy()
    response = FakeResponse(200, {}, [b"%PDF"], peer_ip="169.254.169.254")
    requests = FakeRequests([response])

    with pytest.raises(Blocked):
        strategy._fetch_with_redirect_checks(requests, "https://public.example/doc.pdf")
    assert response.closed, "blocked response must be closed, not leaked"


def test_unverifiable_peer_fails_closed_on_the_body_response():
    set_url_validator(lambda url: None)
    set_peer_ip_validator(lambda ip: None)
    strategy = _strategy()
    response = FakeResponse(200, {}, [b"%PDF"], peer_ip=None)  # no reachable socket
    requests = FakeRequests([response])

    with pytest.raises(RuntimeError, match="Could not determine peer address"):
        strategy._fetch_with_redirect_checks(requests, "https://public.example/doc.pdf")


def test_redirect_hop_without_observable_socket_is_not_fatal():
    """urllib3 releases the socket on a bodyless 302; that must not break redirects."""
    set_url_validator(lambda url: None)
    set_peer_ip_validator(lambda ip: None)
    strategy = _strategy()
    requests = FakeRequests([
        FakeResponse(302, {"location": "https://public.example/real.pdf"}, peer_ip=None),
        FakeResponse(200, {}, [b"%PDF"]),
    ])

    response = strategy._fetch_with_redirect_checks(requests, "https://public.example/doc.pdf")

    assert response.status_code == 200


def test_no_validator_installed_leaves_plain_library_use_working():
    strategy = _strategy()
    requests = FakeRequests([FakeResponse(200, {}, [b"%PDF"])])

    response = strategy._fetch_with_redirect_checks(requests, "https://public.example/doc.pdf")

    assert response.status_code == 200


# ── resource caps (DoS) ────────────────────────────────────────────────


def test_download_aborts_past_max_bytes_and_cleans_up(monkeypatch):
    strategy = _strategy(max_pdf_bytes=1024)
    # Understated content-length must not be trusted: the running total decides.
    requests = FakeRequests([
        FakeResponse(200, {"content-length": "10"}, [b"A" * 512] * 8),
    ])
    monkeypatch.setattr(pdf_module, "requests", requests, raising=False)

    import sys
    monkeypatch.setitem(sys.modules, "requests", requests)

    with pytest.raises(RuntimeError, match="exceeds max_pdf_bytes"):
        strategy._get_pdf_path("https://public.example/huge.pdf")

    assert strategy._temp_files == [], "temp file must be dropped from tracking"


def test_download_under_cap_succeeds(monkeypatch):
    import sys

    strategy = _strategy(max_pdf_bytes=1024)
    requests = FakeRequests([FakeResponse(200, {"content-length": "4"}, [b"%PDF"])])
    monkeypatch.setitem(sys.modules, "requests", requests)

    path = strategy._get_pdf_path("https://public.example/small.pdf")

    try:
        assert os.path.getsize(path) == 4
    finally:
        strategy._discard_temp_file(path)


def test_page_limit_caps_page_count():
    from crawl4ai.processors.pdf.processor import NaivePDFProcessorStrategy

    processor = NaivePDFProcessorStrategy(max_pages=10)
    assert processor._page_limit(5000) == 10
    assert processor._page_limit(3) == 3


def test_page_limit_unbounded_by_default():
    from crawl4ai.processors.pdf.processor import NaivePDFProcessorStrategy

    processor = NaivePDFProcessorStrategy()
    assert processor._page_limit(5000) == 5000


# ── untrusted-body clamping ────────────────────────────────────────────


@pytest.mark.parametrize(
    "sent, expected_bytes, expected_pages",
    [
        ({"max_pdf_bytes": 10**12, "max_pdf_pages": 10**6}, 100 * 1024 * 1024, 2000),
        ({"max_pdf_bytes": 0, "max_pdf_pages": 0}, 100 * 1024 * 1024, 2000),
        ({"max_pdf_bytes": -1, "max_pdf_pages": -1}, 100 * 1024 * 1024, 2000),
        ({"max_pdf_bytes": "huge", "max_pdf_pages": None}, 100 * 1024 * 1024, 2000),
        ({"max_pdf_bytes": 1024, "max_pdf_pages": 5}, 1024, 5),
    ],
)
def test_untrusted_body_cannot_raise_its_own_caps(sent, expected_bytes, expected_pages):
    """An untrusted client must not be able to restore unbounded behavior."""
    from crawl4ai.async_configs import _clamp_untrusted

    out = _clamp_untrusted("PDFContentScrapingStrategy", dict(sent))

    assert out["max_pdf_bytes"] == expected_bytes
    assert out["max_pdf_pages"] == expected_pages


# ── against real requests/urllib3 ───────────────────────────────────────


@pytest.fixture
def live_server():
    """Loopback HTTP server serving a redirect and a small PDF body."""
    import http.server
    import socketserver
    import threading

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/doc.pdf")
                self.end_headers()
                return
            body = b"%PDF-1.4 " + b"x" * 4096
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def test_real_redirect_chain_validates_every_hop_and_reads_peer(live_server):
    """Exercises the actual urllib3 object graph, not a stub of it."""
    import requests as real_requests

    seen_urls, seen_ips = [], []
    set_url_validator(seen_urls.append)
    set_peer_ip_validator(seen_ips.append)
    strategy = _strategy()

    response = strategy._fetch_with_redirect_checks(real_requests, f"{live_server}/redirect")
    response.close()

    assert seen_urls == [f"{live_server}/redirect", f"{live_server}/doc.pdf"]
    assert seen_ips == ["127.0.0.1"], "peer must be read from the body response"


def test_real_internal_redirect_is_blocked(live_server):
    """The reported attack shape: public seed -> 302 -> internal address."""
    import requests as real_requests

    def validator(url):
        if "169.254.169.254" in url:
            raise Blocked(url)

    set_url_validator(validator)
    strategy = _strategy()

    # Point the seed at a redirect whose target is the metadata service.
    requests = FakeRequests([
        FakeResponse(302, {"location": "http://169.254.169.254/latest/meta-data/"}),
    ])
    with pytest.raises(Blocked):
        strategy._fetch_with_redirect_checks(requests, f"{live_server}/redirect")

    # And the real client never followed anything on its own.
    response = real_requests.get(f"{live_server}/redirect", allow_redirects=False)
    assert response.status_code == 302
    response.close()


def test_real_oversize_body_aborts(live_server, monkeypatch):
    import sys

    import requests as real_requests

    monkeypatch.setitem(sys.modules, "requests", real_requests)
    strategy = _strategy(max_pdf_bytes=1024)  # server sends ~4 KiB

    with pytest.raises(RuntimeError, match="exceeds max_pdf_bytes"):
        strategy._get_pdf_path(f"{live_server}/doc.pdf")

    assert strategy._temp_files == []


def test_untrusted_body_cannot_enable_image_extraction():
    from crawl4ai.async_configs import _clamp_untrusted

    out = _clamp_untrusted("PDFContentScrapingStrategy", {"extract_images": True})

    assert out["extract_images"] is False
