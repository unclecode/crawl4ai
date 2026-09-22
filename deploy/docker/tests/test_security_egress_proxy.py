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
    "CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES",
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


@pytest.mark.asyncio
class TestHostnamePassthrough:
    """CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES relaxes the pin for listed names only.

    The mode exists for upstreams that front a network whose names do not
    resolve here, so for those names the upstream must receive the hostname.
    Everything the allowlist does not name keeps resolve-and-pin, which is what
    these tests are really guarding.
    """

    async def test_allowlisted_name_reaches_upstream_unresolved(self, monkeypatch):
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".corp.example")

        def must_not_resolve(url):
            raise AssertionError(f"resolve_and_pin must not run for {url}")
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", must_not_resolve)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT wiki.corp.example:443 HTTP/1.1\r\n\r\n")
            await w.drain()
            assert b"200" in await asyncio.wait_for(r.readline(), timeout=5)
            w.close()
        finally:
            await proxy.stop()
            corp.close()
        # The hostname is what the upstream must see; it does the lookup.
        assert seen == [b"CONNECT wiki.corp.example:443 HTTP/1.1\r\n"]

    async def test_name_outside_allowlist_still_pinned(self, monkeypatch):
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".corp.example")

        monkeypatch.setattr(
            egress_proxy, "resolve_and_pin",
            lambda url: PinnedTarget("https", "other.example", 443, "203.0.113.9"),
        )

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT other.example:443 HTTP/1.1\r\n\r\n")
            await w.drain()
            assert b"200" in await asyncio.wait_for(r.readline(), timeout=5)
            w.close()
        finally:
            await proxy.stop()
            corp.close()
        assert seen == [b"CONNECT 203.0.113.9:443 HTTP/1.1\r\n"]

    async def test_ip_literal_never_bypasses_the_pin(self, monkeypatch):
        """An address carries no DNS to defer, so passthrough must not apply —
        otherwise a suffix entry would hand 169.254.169.254 straight through."""
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", "*,.corp.example")

        def fake_pin(url):
            raise EgressBlocked()
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", fake_pin)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT 169.254.169.254:443 HTTP/1.1\r\n\r\n")
            await w.drain()
            assert b"403" in await asyncio.wait_for(r.readline(), timeout=5)
            w.close()
        finally:
            await proxy.stop()
            corp.close()
        assert seen == []

    async def test_unset_variable_changes_nothing(self, monkeypatch):
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")

        monkeypatch.setattr(
            egress_proxy, "resolve_and_pin",
            lambda url: PinnedTarget("https", "wiki.corp.example", 443, "203.0.113.7"),
        )

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT wiki.corp.example:443 HTTP/1.1\r\n\r\n")
            await w.drain()
            assert b"200" in await asyncio.wait_for(r.readline(), timeout=5)
            w.close()
        finally:
            await proxy.stop()
            corp.close()
        assert seen == [b"CONNECT 203.0.113.7:443 HTTP/1.1\r\n"]


class TestUrlValidationDelegation:
    """The entry-point check must honour the same allowlist as the proxy.

    validate_url_destination runs before the browser starts, so a delegated name
    has to be exempt there too — otherwise the request never reaches the proxy
    and the suffix list has no effect. These guard that the exemption stays as
    narrow as the proxy-side one.
    """

    def _validate(self, url):
        import importlib
        import utils
        importlib.reload(utils)
        return utils.validate_url_destination(url)

    def test_delegated_suffix_is_allowed_through(self, monkeypatch):
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".corp.example")
        # Would otherwise be rejected: the name does not resolve here.
        self._validate("https://wiki.corp.example/page")

    def test_host_outside_the_list_still_blocked(self, monkeypatch):
        from fastapi import HTTPException
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".corp.example")
        with pytest.raises(HTTPException):
            self._validate("http://localhost/")

    def test_ip_literal_still_blocked(self, monkeypatch):
        from fastapi import HTTPException
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", "*,.corp.example")
        with pytest.raises(HTTPException):
            self._validate("http://169.254.169.254/latest/meta-data/")

    def test_unset_leaves_validation_untouched(self, monkeypatch):
        from fastapi import HTTPException
        monkeypatch.delenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", raising=False)
        with pytest.raises(HTTPException):
            self._validate("http://127.0.0.1/")


class TestSuffixMatching:
    """Equivalent spellings of one name must not disagree with the allowlist.

    A suffix list is only as good as the comparison behind it: if "app.internal."
    and "app.internal" are treated as different names, an operator's list silently
    misses one of them. These pin the normalisation so a match means the same
    thing on both sides, and so the near-misses stay misses.
    """

    def _matches(self, suffixes, host, monkeypatch):
        import egress_proxy
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", suffixes)
        allowed = egress_proxy.passthrough_suffixes()
        normalized = egress_proxy.normalize_host(host)
        return bool(normalized) and any(
            normalized == s or normalized.endswith("." + s) for s in allowed
        )

    @pytest.mark.parametrize("host", [
        "app.internal",
        "sub.app.internal",
        "APP.INTERNAL",
        "app.internal.",       # root dot: the same name, written absolutely
        "APP.INTERNAL.",
    ])
    def test_equivalent_spellings_all_match(self, host, monkeypatch):
        assert self._matches(".internal", host, monkeypatch)

    @pytest.mark.parametrize("host", [
        "app.internal.attacker.com",   # suffix in the middle, not at the end
        "fakeinternal",                # no dot boundary
        "notapp.internal.evil.net",
        "",
    ])
    def test_near_misses_stay_pinned(self, host, monkeypatch):
        assert not self._matches(".internal", host, monkeypatch)

    @pytest.mark.parametrize("host", ["wiki.corp.example", "wiki.corp.example."])
    def test_both_layers_read_one_name_identically(self, host, monkeypatch):
        """A name delegated by the proxy must also be exempt at the entry point.

        The two layers run in different processes and were written apart; if they
        disagreed, a name would pass one and be rejected by the other and the
        setting would look broken rather than unsafe. Assert them together.
        """
        import importlib
        import egress_proxy
        import utils
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".corp.example")
        monkeypatch.setenv("HTTPS_PROXY", "http://upstream:3128")
        monkeypatch.delenv("NO_PROXY", raising=False)
        importlib.reload(utils)
        assert egress_proxy._passthrough_upstream("https", host, 443) == (
            ("upstream", 3128, None), "wiki.corp.example")
        assert utils._delegated_to_upstream(f"https://{host}/page")

    @pytest.mark.parametrize("entry", ["*", "*.internal", "a*b"])
    def test_wildcards_are_dropped_not_honoured(self, entry, monkeypatch):
        """A wildcard would delegate every name; that is the one shape to refuse."""
        import egress_proxy
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", entry)
        assert egress_proxy.passthrough_suffixes() == []

    def test_wildcard_does_not_poison_the_rest_of_the_list(self, monkeypatch):
        import egress_proxy
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", "*,.corp.example")
        assert egress_proxy.passthrough_suffixes() == ["corp.example"]

    @pytest.mark.parametrize("host", ["169.254.169.254", "127.0.0.1", "::1"])
    def test_listing_an_ip_literal_does_not_bypass_the_pin(self, host, monkeypatch):
        """Even an operator who lists an address gets resolve-and-pin for it.

        An IP literal carries no DNS to defer, so there is nothing passthrough
        could be for; honouring one would hand 169.254.169.254 to the upstream
        verbatim and give up the non-global rule for nothing in return. Both
        layers reject the literal before the suffix list is ever consulted.
        """
        import importlib
        import egress_proxy
        import utils
        from fastapi import HTTPException
        monkeypatch.setenv(
            "CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", f".internal,{host}")
        monkeypatch.setenv("HTTPS_PROXY", "http://upstream:3128")
        importlib.reload(utils)
        assert egress_proxy._passthrough_upstream("https", host, 443) is None
        with pytest.raises(HTTPException):
            utils.validate_url_destination(f"http://{host}/")


class TestPassthroughPorts:
    """Passthrough gives up the address check, so the port is what still narrows it.

    On the pinned path any port is reachable but only at a global address. A
    delegated name has no such floor, so without a port policy a listed suffix
    would expose whatever the upstream can reach on 9200, 5432 or 2375 — not
    just its web servers. Default to the web ports and let operators widen it.
    """

    EXPECTED = (("upstream", 3128, None), "wiki.corp.example")

    def _upstream(self, port, monkeypatch, ports_env=None):
        import egress_proxy
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".corp.example")
        monkeypatch.setenv("HTTPS_PROXY", "http://upstream:3128")
        monkeypatch.delenv("NO_PROXY", raising=False)
        if ports_env is None:
            monkeypatch.delenv("CRAWL4AI_UPSTREAM_PROXY_DNS_PORTS", raising=False)
        else:
            monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_PORTS", ports_env)
        return egress_proxy._passthrough_upstream("https", "wiki.corp.example", port)

    @pytest.mark.parametrize("port", [80, 443])
    def test_web_ports_are_delegated_by_default(self, port, monkeypatch):
        assert self._upstream(port, monkeypatch) == self.EXPECTED

    @pytest.mark.parametrize("port", [22, 2375, 5432, 6379, 9200, 8080])
    def test_other_ports_fall_back_to_the_pin(self, port, monkeypatch):
        """Not delegated, so the caller resolves and pins it like any other target."""
        assert self._upstream(port, monkeypatch) is None

    def test_operator_can_widen_the_list(self, monkeypatch):
        assert self._upstream(8443, monkeypatch, "80,443,8443") == self.EXPECTED

    def test_widening_replaces_rather_than_extends(self, monkeypatch):
        """An explicit list is the whole policy, so 443 is gone unless named."""
        assert self._upstream(443, monkeypatch, "8443") is None

    @pytest.mark.parametrize("value", ["nope", "0", "70000", "-1", "80x,443x"])
    def test_a_set_but_unusable_list_closes_rather_than_opens(self, value, monkeypatch):
        """The operator asked for a policy we could not honour; do not fall back."""
        assert self._upstream(443, monkeypatch, value) is None

    @pytest.mark.parametrize("value", ["", "   "])
    def test_blank_means_unset_not_empty(self, value, monkeypatch):
        """Blank is how an unset variable arrives; it must not disable the mode."""
        assert self._upstream(443, monkeypatch, value) == self.EXPECTED

    def test_one_bad_entry_does_not_drop_the_good_ones(self, monkeypatch):
        assert self._upstream(443, monkeypatch, "nope,443") == self.EXPECTED

    def test_entry_point_applies_the_same_port_policy(self, monkeypatch):
        """Otherwise a URL would pass validation and then be refused by the proxy."""
        import importlib
        import utils
        from fastapi import HTTPException
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".corp.example")
        monkeypatch.delenv("CRAWL4AI_UPSTREAM_PROXY_DNS_PORTS", raising=False)
        importlib.reload(utils)
        assert utils._delegated_to_upstream("https://wiki.corp.example/page")
        assert not utils._delegated_to_upstream("https://wiki.corp.example:9200/")
        with pytest.raises(HTTPException):
            utils.validate_url_destination("https://wiki.corp.example:9200/")


@pytest.mark.asyncio
@pytest.mark.asyncio
class TestUpstreamOnlySuffixes:
    """CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES narrows chaining to listed names.

    Chaining is otherwise all-or-nothing: with an upstream set every target goes
    through it and NO_PROXY subtracts exceptions. One deployment therefore cannot
    serve an internal-only proxy and direct public egress at the same time. This
    allowlist inverts the rule for the names it holds; everything else dials
    direct and keeps resolve-and-pin, which is what these tests guard.
    """

    async def test_unset_variable_changes_nothing(self, monkeypatch):
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")
        monkeypatch.setattr(
            egress_proxy, "resolve_and_pin",
            lambda url: PinnedTarget("https", "any.example", 443, "203.0.113.7"),
        )

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT any.example:443 HTTP/1.1\r\n\r\n")
            await w.drain()
            assert b"200" in await asyncio.wait_for(r.readline(), timeout=5)
            w.close()
        finally:
            await proxy.stop()
            corp.close()
        # No allowlist: the upstream is still used for everything, as before.
        assert seen == [b"CONNECT 203.0.113.7:443 HTTP/1.1\r\n"]

    async def test_listed_suffix_still_reaches_the_upstream(self, monkeypatch):
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES", ".corp.example")
        monkeypatch.setattr(
            egress_proxy, "resolve_and_pin",
            lambda url: PinnedTarget("https", "wiki.corp.example", 443, "203.0.113.8"),
        )

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(b"CONNECT wiki.corp.example:443 HTTP/1.1\r\n\r\n")
            await w.drain()
            assert b"200" in await asyncio.wait_for(r.readline(), timeout=5)
            w.close()
        finally:
            await proxy.stop()
            corp.close()
        # Listed, so chained — and still as the pinned IP, since only the DNS
        # suffix list may hand a name over unresolved.
        assert seen == [b"CONNECT 203.0.113.8:443 HTTP/1.1\r\n"]

    async def test_unlisted_host_never_touches_the_upstream(self, monkeypatch):
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES", ".corp.example")

        upstream, upstream_port = await _fake_upstream()
        monkeypatch.setattr(
            egress_proxy, "resolve_and_pin",
            lambda url: PinnedTarget("https", "public.example", 443, "127.0.0.1"),
        )
        monkeypatch.setattr(egress_proxy, "_bracket", lambda ip: ip)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(f"CONNECT public.example:{upstream_port} HTTP/1.1\r\n\r\n".encode())
            await w.drain()
            assert b"200" in await asyncio.wait_for(r.readline(), timeout=5)
            w.close()
        finally:
            await proxy.stop()
            upstream.close()
            corp.close()
        # Not listed: dialled direct, so the corporate proxy saw nothing at all.
        assert seen == []

    async def test_match_is_on_the_label_boundary(self, monkeypatch):
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES", ".corp.example")

        upstream, upstream_port = await _fake_upstream()
        monkeypatch.setattr(
            egress_proxy, "resolve_and_pin",
            lambda url: PinnedTarget("https", "notcorp.example", 443, "127.0.0.1"),
        )
        monkeypatch.setattr(egress_proxy, "_bracket", lambda ip: ip)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(f"CONNECT notcorp.example:{upstream_port} HTTP/1.1\r\n\r\n".encode())
            await w.drain()
            assert b"200" in await asyncio.wait_for(r.readline(), timeout=5)
            w.close()
        finally:
            await proxy.stop()
            upstream.close()
            corp.close()
        # "notcorp.example" is not under "corp.example"; a substring must not match.
        assert seen == []

    async def test_delegation_requires_both_allowlists(self, monkeypatch):
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")
        # Delegation is permitted for the name, but the upstream is not.
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".corp.example")
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES", ".other.example")

        upstream, upstream_port = await _fake_upstream()
        resolved = []

        def pin(url):
            resolved.append(url)
            return PinnedTarget("https", "wiki.corp.example", upstream_port, "127.0.0.1")
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", pin)
        monkeypatch.setattr(egress_proxy, "_bracket", lambda ip: ip)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write(f"CONNECT wiki.corp.example:{upstream_port} HTTP/1.1\r\n\r\n".encode())
            await w.drain()
            assert b"200" in await asyncio.wait_for(r.readline(), timeout=5)
            w.close()
        finally:
            await proxy.stop()
            upstream.close()
            corp.close()
        # The name was pinned rather than handed over: one list cannot widen the
        # other, so an upstream the name may not use never receives it unresolved.
        assert resolved, "resolve_and_pin must run when the upstream is not allowed"
        assert seen == []

def test_upstream_only_suffixes_parsing(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES", "*")
    assert egress_proxy.upstream_only_suffixes() == []
    # An ignored list is an absent list: the pre-existing rule applies, which
    # chains everything. It never becomes a way to skip the pin.
    assert egress_proxy._upstream_allows("anything.example") is True

    monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES", ".corp.example,not_a_host!,*.x")
    assert egress_proxy.upstream_only_suffixes() == ["corp.example"]
    assert egress_proxy._upstream_allows("wiki.corp.example") is True
    assert egress_proxy._upstream_allows("elsewhere.example") is False
    # An IP literal carries no suffix to match, so it is never chained here.
    assert egress_proxy._upstream_allows("203.0.113.9") is False


class TestDelegatedNameOnTheWire:
    """What the upstream receives must be the name the allowlist authorised.

    Matching on a normalised name while sending the caller's original spelling
    would mean the allowlist and the connection are about two different strings.
    These assert the bytes the upstream actually sees, not just the decision.
    """

    async def test_connect_sends_the_authorised_name(self, monkeypatch):
        seen = []
        corp, corp_port = await _fake_corporate_proxy(seen)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{corp_port}")
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".internal")
        monkeypatch.delenv("NO_PROXY", raising=False)

        def fake_pin(url):
            raise AssertionError("delegated name must not be resolved locally")
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", fake_pin)

        proxy = PinningProxy()
        await proxy.start()
        try:
            # Uppercase, a trailing root dot, and a unicode label: three
            # spellings the allowlist accepts, one name it authorised.
            for raw in ("WIKI.INTERNAL", "wiki.internal.", "café.internal"):
                r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
                w.write(f"CONNECT {raw}:443 HTTP/1.1\r\n\r\n".encode("latin-1"))
                await w.drain()
                assert b"200" in await asyncio.wait_for(r.readline(), timeout=5)
                w.close()
        finally:
            await proxy.stop()
            corp.close()

        assert seen == [
            b"CONNECT wiki.internal:443 HTTP/1.1\r\n",
            b"CONNECT wiki.internal:443 HTTP/1.1\r\n",
            b"CONNECT xn--caf-dma.internal:443 HTTP/1.1\r\n",
        ]

    async def test_plain_http_sends_the_authorised_name_and_closes(self, monkeypatch):
        """Absolute form, Host header, upstream auth and Connection: close.

        A delegated request needs the close as much as a pinned one: the suffix
        and port were checked for this request only, so a reused connection must
        not carry a second, unchecked one upstream.
        """
        lines = []

        async def handle(reader, writer):
            req = b""
            while b"\r\n\r\n" not in req:
                chunk = await reader.read(4096)
                if not chunk:
                    break
                req += chunk
            lines.append(req)
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nhi")
            await writer.drain()
            writer.close()
        corp = await asyncio.start_server(handle, "127.0.0.1", 0)
        corp_port = corp.sockets[0].getsockname()[1]
        monkeypatch.setenv("HTTP_PROXY", f"http://user:pw@127.0.0.1:{corp_port}")
        monkeypatch.setenv("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", ".internal")
        monkeypatch.delenv("NO_PROXY", raising=False)

        def fake_pin(url):
            raise AssertionError("delegated name must not be resolved locally")
        monkeypatch.setattr(egress_proxy, "resolve_and_pin", fake_pin)

        proxy = PinningProxy()
        await proxy.start()
        try:
            r, w = await asyncio.open_connection(proxy.bound_host, proxy.bound_port)
            w.write("GET http://WIKI.INTERNAL./p HTTP/1.1\r\n"
                    "Host: WIKI.INTERNAL.\r\nConnection: keep-alive\r\n\r\n".encode("latin-1"))
            await w.drain()
            assert b"200" in await asyncio.wait_for(r.read(200), timeout=5)
            # Try to smuggle an unchecked request onto the same connection.
            w.write(b"GET http://evil.example/ HTTP/1.1\r\nHost: evil.example\r\n\r\n")
            await w.drain()
            assert await asyncio.wait_for(r.read(200), timeout=5) == b""
            w.close()
        finally:
            await proxy.stop()
            corp.close()

        sent = b"".join(lines)
        assert sent.startswith(b"GET http://wiki.internal:80/p HTTP/1.1\r\n")
        assert b"Host: wiki.internal\r\n" in sent
        assert b"Proxy-Authorization: Basic " in sent
        assert b"Connection: close" in sent
        assert b"keep-alive" not in sent
        assert b"evil.example" not in sent
