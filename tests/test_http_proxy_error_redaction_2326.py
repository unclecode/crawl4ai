"""
Tests for #2326: errors raised by AsyncHTTPCrawlerStrategy._handle_http must not
carry the proxy password, in the message or in the traceback.

Offline: the proxy is 127.0.0.1 on a port nothing listens on.
"""
import socket
import traceback

import pytest

from crawl4ai.async_configs import CrawlerRunConfig, ProxyConfig
from crawl4ai.async_crawler_strategy import (
    AsyncHTTPCrawlerStrategy,
    ConnectionTimeoutError,
    HTTPCrawlerError,
)

redact = AsyncHTTPCrawlerStrategy._redact_proxy_credentials
wrap = AsyncHTTPCrawlerStrategy._wrap_error


def closed_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestRedactProxyCredentials:
    @pytest.mark.parametrize("password", ["s3cret", "s3cret#pw", "pa/ss", "a?b", "50%off", "p@ss"])
    def test_the_password_does_not_survive(self, password):
        proxy_url = f"http://user:{password}@127.0.0.1:9"
        message = f"Cannot connect via {proxy_url}: refused"
        out = redact(message, proxy_url)
        assert password not in out
        assert "127.0.0.1:9" in out

    def test_a_percent_encoded_proxy_url_is_matched_in_its_decoded_form(self):
        proxy_url = "http://user:s3cret%23pw@127.0.0.1:9"
        out = redact("http://user:s3cret#pw@127.0.0.1:9", proxy_url)
        assert "s3cret" not in out

    def test_credentials_in_any_url_are_masked_without_a_proxy_url(self):
        out = redact("Proxy http://user:secret@host:8080 failed", None)
        assert out == "Proxy http://***@host:8080 failed"

    def test_a_message_without_credentials_is_unchanged(self):
        message = "Cannot connect to host 127.0.0.1:9 ssl:default"
        assert redact(message, "http://127.0.0.1:9") == message
        assert redact(message, "http://user:secret@127.0.0.1:9") == message


class TestWrapError:
    def test_the_original_is_kept_out_of_the_traceback_when_it_held_credentials(self):
        proxy_url = "http://user:s3cret#pw@127.0.0.1:9"
        try:
            try:
                raise ValueError(proxy_url)
            except ValueError as e:
                raise wrap(HTTPCrawlerError, "HTTP client error", e, proxy_url)
        except HTTPCrawlerError as err:
            printed = "".join(traceback.format_exception(err))
        assert "s3cret" not in printed
        assert "HTTP client error: http://***@127.0.0.1:9" in printed

    def test_the_original_stays_in_the_traceback_when_it_held_none(self):
        try:
            try:
                raise TimeoutError("read timed out")
            except TimeoutError as e:
                raise wrap(ConnectionTimeoutError, "Request timed out", e, None)
        except ConnectionTimeoutError as err:
            printed = "".join(traceback.format_exception(err))
            message = str(err)
        assert "During handling of the above exception" in printed
        assert message == "Request timed out: read timed out"


@pytest.mark.asyncio
@pytest.mark.parametrize("password", ["s3cret", "s3cret#pw", "pa/ss"])
async def test_handle_http_raises_without_the_password(password):
    port = closed_port()
    config = CrawlerRunConfig(
        proxy_config=ProxyConfig(
            server=f"http://127.0.0.1:{port}", username="user", password=password
        )
    )
    strategy = AsyncHTTPCrawlerStrategy()
    with pytest.raises(Exception) as caught:
        await strategy._handle_http(f"http://127.0.0.1:{port}/", config)
    await strategy.close()
    printed = "".join(traceback.format_exception(caught.value))
    assert password not in printed
