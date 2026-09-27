from unittest.mock import MagicMock

import pytest

from crawl4ai.ssl_certificate import SSLCertificate


@pytest.mark.parametrize(
    "url, hostname, port",
    [
        ("https://example.com:8443/page", "example.com", 8443),
        ("https://[2001:db8::1]:9443/page", "2001:db8::1", 9443),
        ("https://[2001:db8::1]/page", "2001:db8::1", 443),
        ("https://user:password@example.com:8443", "example.com", 8443),
        ("https://example.com/page", "example.com", 443),
    ],
)
def test_certificate_connects_to_url_endpoint(monkeypatch, url, hostname, port):
    connect = MagicMock()
    context = MagicMock()
    # Stop after the TLS handshake: certificate parsing is independent of routing.
    context.wrap_socket.return_value.__enter__.return_value.getpeercert.return_value = None
    monkeypatch.setattr("crawl4ai.ssl_certificate.socket.create_connection", connect)
    monkeypatch.setattr(
        "crawl4ai.ssl_certificate.ssl.create_default_context", lambda: context
    )

    assert SSLCertificate.from_url(url, timeout=3) is None

    connect.assert_called_once_with((hostname, port), timeout=3)
    context.wrap_socket.assert_called_once_with(
        connect.return_value.__enter__.return_value, server_hostname=hostname
    )


@pytest.mark.parametrize("url", ["https:///missing-host", "https://example.com:bad/"])
def test_invalid_certificate_endpoint_does_not_connect(monkeypatch, url):
    connect = MagicMock()
    monkeypatch.setattr("crawl4ai.ssl_certificate.socket.create_connection", connect)
    assert SSLCertificate.from_url(url) is None
    connect.assert_not_called()
