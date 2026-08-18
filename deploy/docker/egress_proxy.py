"""
egress_proxy.py - localhost pinning forward-proxy for the browser.

context.route() sees URLs, not IPs, so it cannot stop DNS rebinding: Chromium
resolves the target host itself at connect time, and an attacker can answer
"public" to our up-front validation and "169.254.169.254" to the browser.

This proxy is the real control. Chromium is pointed at it (proxy_config), so it
never resolves the target itself - it asks us to CONNECT host:port. We run the
single egress rule (egress_broker.resolve_and_pin: resolve once, reject any
non-global IP, pin one IP), dial the PINNED IP ourselves, and splice raw bytes.
TLS stays end-to-end (we tunnel ciphertext; Chromium verifies the cert/SNI
against the real host - no MITM).

Bound to 127.0.0.1 on an ephemeral port; started at server boot.

If HTTP_PROXY/HTTPS_PROXY (or CRAWL4AI_UPSTREAM_PROXY) is set, we still
resolve-and-pin locally but dial via the upstream proxy, asking it to CONNECT
to the PINNED IP — never the hostname — so the rebinding guarantee holds.
NO_PROXY bypasses it; with no proxy env set, behavior is unchanged.

CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES is the one exception, and it is an
allowlist rather than a switch: names matching a listed suffix are handed to the
upstream unresolved, because some upstreams front a network whose names do not
resolve here at all. For those names the pin is the upstream's responsibility
instead of ours. Everything else — every other name, every IP literal, and every
deployment that leaves the variable unset — keeps resolve-and-pin unchanged.
"""

from __future__ import annotations

import asyncio
import base64
import ipaddress
import logging
import os
import re
from urllib.parse import unquote, urlsplit

from egress_broker import EgressBlocked, resolve_and_pin

logger = logging.getLogger("crawl4ai.egress")

_CONNECT_OK = b"HTTP/1.1 200 Connection established\r\n\r\n"
_BLOCKED = b"HTTP/1.1 403 Forbidden\r\nContent-Length: 11\r\n\r\nURL blocked"
_BAD = b"HTTP/1.1 400 Bad Request\r\nContent-Length: 11\r\n\r\nBad Request"
_MAX_HEADER_BYTES = 64 * 1024


def _env(*names: str) -> str:
    return next((os.environ[n] for n in names if os.environ.get(n)), "")


def upstream_proxy(scheme: str = "https"):
    """(host, port, auth_header_bytes|None) of the upstream proxy, or None.

    Read per-call (not at import) so operators and tests see env changes.
    The target scheme picks HTTP(S)_PROXY per convention, falling back to
    the other pair when only one is set.
    """
    order = ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy") if scheme == "http" \
        else ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy")
    raw = _env("CRAWL4AI_UPSTREAM_PROXY", *order).strip()
    if not raw:
        return None
    sp = urlsplit(raw if "://" in raw else "http://" + raw)
    if not sp.hostname:
        return None
    auth = None
    if sp.username:
        cred = f"{unquote(sp.username)}:{unquote(sp.password or '')}".encode("utf-8")
        auth = b"Proxy-Authorization: Basic " + base64.b64encode(cred) + b"\r\n"
    return sp.hostname, sp.port or 80, auth


def _no_proxy_match(host: str, ip: str) -> bool:
    """True if NO_PROXY says this target must bypass the upstream proxy."""
    entries = [e.strip() for e in _env("NO_PROXY", "no_proxy").split(",") if e.strip()]
    for entry in entries:
        if entry == "*":
            return True
        try:
            if ipaddress.ip_address(ip) in ipaddress.ip_network(entry, strict=False):
                return True
            continue
        except ValueError:
            pass
        suffix = entry.lower().lstrip(".")
        low = host.lower()
        if low == suffix or low.endswith("." + suffix):
            return True
    return False


def upstream_only_suffixes() -> list:
    """Suffixes that are the ONLY targets routed through the upstream proxy.

    Empty (the default) keeps the existing rule: with an upstream set every
    target is chained through it and NO_PROXY carves out exceptions. That fits a
    site whose whole egress leaves via one corporate proxy, but it makes a single
    deployment unable to serve two egress routes at once — a public crawl is
    tunnelled through the proxy as well, where it may be refused outright or
    attributed to the wrong network.

    Naming suffixes here inverts the rule for those names only: they are chained,
    everything else dials direct. It is an allowlist for the same reason
    CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES is one, and the two compose: a name may
    be delegated unresolved only if it is also allowed to use the upstream, so
    neither list can widen what the other permits.
    """
    raw = _env("CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES")
    out = []
    for entry in raw.split(","):
        entry = entry.strip().lstrip(".")
        if not entry:
            continue
        if "*" in entry:
            logger.warning(
                "ignoring wildcard entry %r in CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES; "
                "list explicit suffixes instead", entry,
            )
            continue
        normalized = normalize_host(entry)
        if not normalized:
            logger.warning(
                "ignoring invalid suffix %r in CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES", entry,
            )
            continue
        out.append(normalized)
    return out


def _upstream_allows(host: str) -> bool:
    """True if `host` may use the upstream proxy at all.

    With no allowlist configured every host may, which is the existing rule. The
    comparison is on the DNS label boundary, so "corp.example" matches
    "wiki.corp.example" but never "corp.example.attacker.com".
    """
    only = upstream_only_suffixes()
    if not only:
        return True
    low = normalize_host(host)
    if not low:
        return False
    return any(low == s or low.endswith("." + s) for s in only)


def _use_upstream(pin):
    """The upstream (host, port, auth) to route `pin` through, or None for direct."""
    up = upstream_proxy(pin.scheme)
    if up is None or _no_proxy_match(pin.host, pin.ip):
        return None
    if not _upstream_allows(pin.host):
        return None
    return up


_MAX_HOSTNAME = 253
_LABEL = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_host(host: str) -> str:
    """Lowercase, strip the root dot, and IDNA-encode; "" if not a valid name.

    Comparing raw input against the allowlist would let equivalent spellings of
    the same name disagree — a trailing root dot, uppercase, or a unicode form
    of an ASCII label. Anything that is not a syntactically valid hostname
    returns "" so it can never match and simply keeps the pinned path.
    """
    host = (host or "").strip().rstrip(".")
    if not host or len(host) > _MAX_HOSTNAME:
        return ""
    try:
        host = host.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError):
        # Already ASCII, or not encodable; fall back and let the label check rule.
        try:
            host.encode("ascii")
        except UnicodeEncodeError:
            return ""
    # Re-check: the A-label form of a unicode name is usually longer than the
    # name we measured above, so the first check does not bound this one.
    if len(host) > _MAX_HOSTNAME:
        return ""
    host = host.lower()
    labels = host.split(".")
    if not all(_LABEL.match(label) for label in labels):
        return ""
    return host


def passthrough_suffixes() -> list:
    """Hostname suffixes the operator allows the upstream to resolve.

    Empty (the default) disables passthrough entirely. This is deliberately an
    allowlist rather than a boolean: the pin is what stops a caller-supplied URL
    from reaching link-local or private space, so it is only given up for the
    exact names an operator names, never wholesale.

    A bare "*" is rejected rather than honoured. Delegating every name would
    turn any attacker-supplied URL into a lookup performed by the upstream, which
    is the one shape this must not allow; an operator who genuinely wants that
    already has CRAWL4AI_ALLOW_INTERNAL_URLS.
    """
    raw = _env("CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES")
    out = []
    for entry in raw.split(","):
        entry = entry.strip().lstrip(".")
        if not entry:
            continue
        if entry == "*" or "*" in entry:
            logger.warning(
                "ignoring wildcard entry %r in CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES; "
                "list explicit suffixes instead", entry,
            )
            continue
        normalized = normalize_host(entry)
        if not normalized:
            logger.warning(
                "ignoring invalid suffix %r in CRAWL4AI_UPSTREAM_PROXY_DNS_SUFFIXES", entry,
            )
            continue
        out.append(normalized)
    return out


_DEFAULT_PASSTHROUGH_PORTS = (80, 443)


def passthrough_ports() -> frozenset:
    """Ports a delegated name may be reached on; defaults to the web ports.

    On the pinned path the port is unconstrained but the address must be global,
    so a non-web port can still only reach the public internet. Passthrough
    gives up exactly that address check, which leaves the port as the only thing
    still narrowing where a delegated name can land — unconstrained, a crawl of
    a listed suffix could reach an internal database or admin port rather than a
    web server. Defaulting to 80 and 443 keeps the mode doing what it exists
    for: crawling.

    An operator fronting an internal site on another port can list it, and an
    explicit list replaces the default rather than extending it. Unset (or
    blank) means the default; a list that is set but yields no usable port
    disables passthrough rather than opening it up.
    """
    raw = _env("CRAWL4AI_UPSTREAM_PROXY_DNS_PORTS").strip()
    if not raw:
        return frozenset(_DEFAULT_PASSTHROUGH_PORTS)
    out = set()
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        try:
            port = int(entry)
        except ValueError:
            logger.warning(
                "ignoring non-numeric port %r in CRAWL4AI_UPSTREAM_PROXY_DNS_PORTS", entry,
            )
            continue
        if not 0 < port < 65536:
            logger.warning(
                "ignoring out-of-range port %d in CRAWL4AI_UPSTREAM_PROXY_DNS_PORTS", port,
            )
            continue
        out.add(port)
    return frozenset(out)


def _no_proxy_host_match(host: str) -> bool:
    """NO_PROXY check by hostname alone, for targets we deliberately do not resolve.

    The CIDR entries in _no_proxy_match cannot apply here: opting into
    passthrough means we never learn an IP for this target.
    """
    for entry in [e.strip() for e in _env("NO_PROXY", "no_proxy").split(",") if e.strip()]:
        if entry == "*":
            return True
        suffix = entry.lower().lstrip(".")
        low = host.lower()
        if low == suffix or low.endswith("." + suffix):
            return True
    return False


def _passthrough_upstream(scheme: str, host: str, port: int):
    """(upstream, authorised name) to hand `host` to unresolved, or None.

    The normalised name is returned rather than recomputed by each caller so the
    name that goes on the wire is necessarily the one the allowlist approved.
    Deriving it twice would let the check and the connection disagree, which is
    the shape of bug this whole path has to avoid.

    Returning None keeps the caller on resolve-and-pin, so a deployment that has
    not configured any suffix behaves byte-identically to today. It is also how
    a rejected target fails closed: the caller then resolves and pins it like
    any other, which is what blocks it — nothing skips both checks.

    Five conditions, all required:
      - the operator listed a matching suffix (an allowlist, not a switch);
      - CRAWL4AI_UPSTREAM_PROXY_ONLY_SUFFIXES, if set, also allows the name —
        a name may not be delegated to an upstream it is not allowed to use;
      - the target is a name, not an IP literal — an address carries no DNS to
        defer, so letting one through would hand the upstream 169.254.169.254
        verbatim and give up the non-global rule for nothing;
      - the port is one passthrough is allowed to reach;
      - an upstream exists and NO_PROXY does not exempt the host.
    """
    suffixes = passthrough_suffixes()
    if not suffixes:
        return None
    try:
        ipaddress.ip_address(host.strip().rstrip("."))
        return None
    except ValueError:
        pass
    low = normalize_host(host)
    if not low:
        return None
    # Compare on the DNS label boundary, so "corp.example" matches
    # "wiki.corp.example" but never "corp.example.attacker.com" or "notcorp.example".
    if not any(low == s or low.endswith("." + s) for s in suffixes):
        return None
    if port not in passthrough_ports():
        return None
    up = upstream_proxy(scheme)
    if up is None or _no_proxy_host_match(low):
        return None
    if not _upstream_allows(low):
        return None
    return up, low


def _bracket(ip: str) -> str:
    return f"[{ip}]" if ":" in ip else ip


class PinningProxy:
    """Async HTTP forward-proxy that connects only to pinned, global IPs."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self._host = host
        self._port = port
        self._server: asyncio.AbstractServer | None = None
        self.bound_host: str | None = None
        self.bound_port: int | None = None

    @property
    def url(self) -> str | None:
        if self.bound_port is None:
            return None
        return f"http://{self.bound_host}:{self.bound_port}"

    async def start(self) -> str:
        self._server = await asyncio.start_server(self._handle, self._host, self._port)
        sock = self._server.sockets[0]
        self.bound_host, self.bound_port = sock.getsockname()[:2]
        logger.info("egress pinning proxy listening on %s", self.url)
        up = upstream_proxy()
        if up is not None:
            logger.info(
                "egress pinning proxy chaining through upstream proxy %s:%s",
                up[0], up[1],
            )
        return self.url

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            try:
                await self._server.wait_closed()
            except Exception:
                pass

    # ─────────────────────────── connection handling ───────────────────────────
    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            request_line = await asyncio.wait_for(reader.readline(), timeout=30)
            if not request_line:
                return
            parts = request_line.split()
            if len(parts) < 3:
                await self._reply(writer, _BAD)
                return
            method = parts[0].decode("latin-1", "replace").upper()
            target = parts[1].decode("latin-1", "replace")

            if method == "CONNECT":
                await self._handle_connect(target, reader, writer)
            else:
                await self._handle_absolute(method, target, request_line, reader, writer)
        except asyncio.TimeoutError:
            await self._reply(writer, _BAD)
        except Exception as e:
            logger.debug("proxy connection error: %s", e)
            await self._safe_close(writer)

    async def _handle_connect(self, target, client_reader, client_writer):
        # target is "host:port"
        host, _, port_s = target.rpartition(":")
        if not host or not port_s.isdigit():
            await self._reply(client_writer, _BAD)
            return
        # Opt-in: hand the hostname to the upstream and let it resolve. Decided
        # before resolve_and_pin, because the point of the mode is that this name
        # may not resolve here at all, or may resolve to an address the pin
        # refuses. Without the opt-in this is None and nothing below changes.
        passthrough = _passthrough_upstream("https", host, int(port_s))

        if passthrough is None:
            try:
                pin = resolve_and_pin(f"https://{host}:{port_s}")
            except EgressBlocked:
                await self._reply(client_writer, _BLOCKED)
                return

        # Drain the rest of the client's CONNECT headers.
        await self._drain_headers(client_reader)

        try:
            if passthrough is not None:
                up, delegated_host = passthrough
                up_reader, up_writer = await self._dial_hostname(
                    up, delegated_host, int(port_s)
                )
            else:
                up_reader, up_writer = await self._dial(pin, int(port_s))
        except Exception:
            await self._reply(client_writer, _BLOCKED)
            return

        client_writer.write(_CONNECT_OK)
        await client_writer.drain()
        await self._splice(client_reader, client_writer, up_reader, up_writer)

    async def _handle_absolute(self, method, target, request_line, client_reader, client_writer):
        # Plain HTTP proxying: target is an absolute URI "http://host/path".
        sp = urlsplit(target)
        if sp.scheme != "http" or not sp.hostname:
            await self._reply(client_writer, _BAD)
            return
        port = sp.port or 80
        # Same opt-in as the CONNECT path, decided before we try to resolve.
        passthrough = _passthrough_upstream("http", sp.hostname, port)
        pin = None
        if passthrough is None:
            try:
                pin = resolve_and_pin(f"http://{sp.hostname}:{port}")
            except EgressBlocked:
                await self._reply(client_writer, _BLOCKED)
                return

        headers = await self._read_headers(client_reader)
        path = sp.path or "/"
        if sp.query:
            path += "?" + sp.query
        delegated_host = passthrough[1] if passthrough is not None else None
        upstream = passthrough[0] if passthrough is not None else _use_upstream(pin)
        dst = (upstream[0], upstream[1]) if upstream else (pin.ip, port)
        try:
            up_reader, up_writer = await asyncio.wait_for(
                asyncio.open_connection(*dst), timeout=30
            )
        except Exception:
            await self._reply(client_writer, _BLOCKED)
            return
        # Re-issue with Host preserved: origin form when dialing the pinned IP
        # directly, absolute form against the pinned IP when going through the
        # upstream proxy (which then needs no DNS lookup of its own).
        if upstream is None:
            out = f"{method} {path} HTTP/1.1\r\n".encode("latin-1")
        else:
            # Absolute form to the upstream. Against a delegated name send the
            # name the allowlist approved and let the upstream resolve it;
            # otherwise send the pinned IP, so the upstream needs no lookup.
            origin = (
                f"{delegated_host}:{port}" if passthrough is not None
                else f"{_bracket(pin.ip)}:{port}"
            )
            out = f"{method} http://{origin}{path} HTTP/1.1\r\n".encode("latin-1")
            if upstream[2]:
                out += upstream[2]
            # One validated request per upstream connection: only this first
            # request is pinned/rewritten, so force close to keep a reused
            # client connection from smuggling unvalidated requests upstream.
            # A delegated name needs this just as much: the suffix and port were
            # checked for this request only.
            headers = b"".join(
                ln + b"\r\n" for ln in headers.split(b"\r\n")
                if ln and not ln.lower().startswith(b"connection:")
            ) + b"Connection: close\r\n"
        host_header = delegated_host if passthrough is not None else sp.hostname
        out += b"Host: " + host_header.encode("latin-1")
        if sp.port:
            out += f":{sp.port}".encode("latin-1")
        out += b"\r\n" + headers + b"\r\n"
        up_writer.write(out)
        await up_writer.drain()
        await self._splice(client_reader, client_writer, up_reader, up_writer)

    # ─────────────────────────── helpers ───────────────────────────
    async def _dial_hostname(self, upstream, host: str, port: int):
        """CONNECT to the upstream by hostname, letting it resolve.

        Only reachable once the operator opted in. `host` is the name the
        allowlist approved, already normalised to its A-label form, so it goes
        out as-is for a proxy that fronts a private network, or enforces
        hostname ACLs, to route; we perform no lookup of our own, which is the
        point — the name may not resolve on this side at all. ASCII is the wire
        form of a hostname and normalisation is what guarantees it here.
        """
        p_host, p_port, auth = upstream
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(p_host, p_port), timeout=30
        )
        try:
            dst = f"{host}:{port}"
            req = f"CONNECT {dst} HTTP/1.1\r\nHost: {dst}\r\n".encode("ascii")
            if auth:
                req += auth
            req += b"\r\n"
            writer.write(req)
            await writer.drain()
            status = await asyncio.wait_for(reader.readline(), timeout=30)
            parts = status.split()
            if len(parts) < 2 or parts[1] != b"200":
                logger.warning(
                    "upstream proxy refused CONNECT %s: %s", dst, status.strip()
                )
                raise EgressBlocked("upstream proxy refused CONNECT")
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=30)
                if line in (b"\r\n", b"\n", b""):
                    break
            return reader, writer
        except Exception:
            writer.close()
            raise

    async def _dial(self, pin, port: int):
        """Open a byte pipe to the pinned IP: direct, or tunneled through the
        upstream proxy via CONNECT-to-the-pinned-IP (no upstream DNS lookup)."""
        upstream = _use_upstream(pin)
        if upstream is None:
            return await asyncio.wait_for(
                asyncio.open_connection(pin.ip, port), timeout=30
            )
        p_host, p_port, auth = upstream
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(p_host, p_port), timeout=30
        )
        try:
            dst = f"{_bracket(pin.ip)}:{port}"
            req = f"CONNECT {dst} HTTP/1.1\r\nHost: {dst}\r\n".encode("latin-1")
            if auth:
                req += auth
            req += b"\r\n"
            writer.write(req)
            await writer.drain()
            status = await asyncio.wait_for(reader.readline(), timeout=30)
            parts = status.split()
            if len(parts) < 2 or parts[1] != b"200":
                logger.warning("upstream proxy refused CONNECT: %r", status[:64])
                raise ConnectionError("upstream proxy refused CONNECT")
            # Drain the upstream's response headers so none of them leak into
            # the tunneled byte stream.
            await self._drain_headers(reader)
        except Exception:
            await self._safe_close(writer)
            raise
        return reader, writer

    async def _drain_headers(self, reader):
        read = 0
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=30)
            read += len(line)
            if line in (b"\r\n", b"\n", b""):
                return
            if read > _MAX_HEADER_BYTES:
                return

    async def _read_headers(self, reader) -> bytes:
        buf = b""
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=30)
            if line in (b"\r\n", b"\n", b""):
                break
            buf += line
            if len(buf) > _MAX_HEADER_BYTES:
                break
        # strip any proxy-only / connection headers
        kept = []
        for ln in buf.split(b"\r\n"):
            name = ln.split(b":", 1)[0].strip().lower()
            if name in (b"proxy-connection", b"proxy-authorization", b"host"):
                continue
            if ln:
                kept.append(ln)
        return (b"\r\n".join(kept) + b"\r\n") if kept else b""

    async def _splice(self, c_reader, c_writer, u_reader, u_writer):
        async def pipe(src, dst):
            try:
                while True:
                    data = await src.read(65536)
                    if not data:
                        break
                    dst.write(data)
                    await dst.drain()
            except Exception:
                pass
            finally:
                await self._safe_close(dst)

        await asyncio.gather(
            pipe(c_reader, u_writer),
            pipe(u_reader, c_writer),
        )

    async def _reply(self, writer, payload: bytes):
        try:
            writer.write(payload)
            await writer.drain()
        except Exception:
            pass
        await self._safe_close(writer)

    @staticmethod
    async def _safe_close(writer):
        try:
            if not writer.is_closing():
                writer.close()
        except Exception:
            pass
