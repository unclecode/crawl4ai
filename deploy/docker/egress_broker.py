"""
egress_broker.py - the single rule and primitive for all outbound traffic.

Every SSRF defense before this was enumerate-badness (a hand-maintained list of
blocked CIDRs) and resolve-then-discard: the validator resolved a hostname,
checked the IP against the list, then threw the IP away and let the real
connection re-resolve (DNS rebinding / TOCTOU). It also missed whole families:
the IPv6 unspecified ::, NAT64 64:ff9b::/96, 6to4 2002::/16, and
host.docker.internal as anything but a literal prefix.

This module replaces the blocklist with one rule:

    reject any resolved IP where `not ip.is_global`

evaluated on every transition-embedded IPv4 form as well (v4-mapped, NAT64,
6to4, v4-compatible), and makes the entity that resolves DNS the same entity
that hands back the pinned IP to dial. `resolve_and_pin()` resolves once and
returns the exact IP to connect to; callers must dial that IP (Host/SNI
preserved) so a second, attacker-controlled resolution is never used.

Errors are opaque (`EgressBlocked.reason == "URL blocked"`) so the API never
leaks a resolved internal IP, hostname, or traceback (the old DNS oracle).
"""

from __future__ import annotations

import ipaddress
import os
import socket
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

# Operator escape hatch for trusted internal deployments (off by default).
ALLOW_INTERNAL = os.environ.get("CRAWL4AI_ALLOW_INTERNAL_URLS", "false").lower() == "true"

_NAT64 = ipaddress.ip_network("64:ff9b::/96")
_V4COMPAT = ipaddress.ip_network("::/96")
_6TO4 = ipaddress.ip_network("2002::/16")

# Hostnames we refuse regardless of resolution (belt-and-suspenders; they also
# resolve to non-global addresses and would be caught anyway).
_BLOCKED_HOSTNAMES = {
    "localhost", "metadata.google.internal", "metadata",
    "kubernetes.default", "kubernetes.default.svc",
}


class EgressBlocked(Exception):
    """Outbound target rejected. Carries an OPAQUE reason - never an IP/host."""

    def __init__(self, reason: str = "URL blocked"):
        self.reason = reason
        super().__init__(reason)


@dataclass
class PinnedTarget:
    scheme: str
    host: str          # original hostname (for Host header / SNI)
    port: int
    ip: str            # the exact IP to dial - do NOT re-resolve `host`


def _embedded_v4_forms(ip: ipaddress._BaseAddress) -> List[ipaddress._BaseAddress]:
    """The address plus any IPv4 embedded in a transition IPv6 form.

    Only the well-defined transition ranges are unwrapped, so a normal global
    IPv6 is never mis-derived into a bogus (and possibly non-global) IPv4.
    """
    forms: List[ipaddress._BaseAddress] = [ip]
    if isinstance(ip, ipaddress.IPv6Address):
        mapped = ip.ipv4_mapped
        if mapped is not None:
            forms.append(mapped)
        elif ip in _NAT64 or ip in _V4COMPAT:
            forms.append(ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF))
        elif ip in _6TO4:
            forms.append(ipaddress.IPv4Address((int(ip) >> 80) & 0xFFFFFFFF))
    return forms


def is_forbidden_ip(ip_str: str) -> bool:
    """True if the IP (or any embedded transition form) is not globally routable."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return any(not form.is_global for form in _embedded_v4_forms(ip))


def _resolve(host: str, port: int):
    try:
        return socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise EgressBlocked()


def assert_host_allowed(host: str, port: int = 0) -> None:
    """Resolve `host` and reject if ANY answer is non-global. Opaque on failure."""
    if ALLOW_INTERNAL:
        return
    if not host:
        raise EgressBlocked()
    low = host.lower()
    if low in _BLOCKED_HOSTNAMES or low.startswith("host.docker.internal"):
        raise EgressBlocked()
    for *_, sockaddr in _resolve(host, port):
        if is_forbidden_ip(sockaddr[0]):
            raise EgressBlocked()


def resolve_and_pin(url: str) -> PinnedTarget:
    """Resolve `url` once, reject if any answer is non-global, and pin one IP.

    The returned PinnedTarget.ip is the address the caller must dial; resolving
    `host` again at connect time would reopen the rebinding hole.
    """
    parsed = urlparse(str(url))
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise EgressBlocked()
    host = parsed.hostname
    if not host:
        raise EgressBlocked()
    port = parsed.port or (443 if scheme == "https" else 80)

    if ALLOW_INTERNAL:
        # Still resolve so we can pin, but skip the global check.
        answers = _resolve(host, port)
        return PinnedTarget(scheme, host, port, answers[0][4][0])

    low = host.lower()
    if low in _BLOCKED_HOSTNAMES or low.startswith("host.docker.internal"):
        raise EgressBlocked()

    answers = _resolve(host, port)
    pinned = None
    for *_, sockaddr in answers:
        if is_forbidden_ip(sockaddr[0]):
            # Reject the host outright if ANY of its records is internal.
            raise EgressBlocked()
        if pinned is None:
            pinned = sockaddr[0]
    if pinned is None:
        raise EgressBlocked()
    return PinnedTarget(scheme, host, port, pinned)


def check_redirect(location: str) -> PinnedTarget:
    """Re-validate (and pin) a redirect Location. Same rule as the initial hop."""
    return resolve_and_pin(location)


ALLOW_INSECURE_TLS = os.environ.get("CRAWL4AI_ALLOW_INSECURE_TLS", "false").lower() == "true"

# URL of the localhost pinning forward-proxy (egress_proxy.py), set at boot.
# When present, enforce_egress routes the browser through it so Chromium never
# resolves the target itself (closes DNS rebinding on the browser path).
_EGRESS_PROXY_URL: Optional[str] = None


def set_egress_proxy(url: Optional[str]) -> None:
    global _EGRESS_PROXY_URL
    _EGRESS_PROXY_URL = url


def get_egress_proxy() -> Optional[str]:
    return _EGRESS_PROXY_URL

# Chromium flags that would re-route or weaken egress; scrubbed server-side.
_DANGEROUS_BROWSER_ARGS = (
    "--proxy-server", "--proxy-pac-url", "--proxy-bypass-list",
    "--host-resolver-rules", "--ignore-certificate-errors",
    "--allow-insecure-localhost",
)


def enforce_egress(browser_config) -> None:
    """Server-side egress hardening applied to the effective browser config.

    R2 already forbids untrusted bodies from setting proxy/extra_args, so this
    is defense in depth that also covers server/SDK-built configs:
      - TLS verification ON (ignore_https_errors=False) unless the operator
        opts into CRAWL4AI_ALLOW_INSECURE_TLS;
      - no caller proxy (the key/SSRF redirect vector);
      - strip any proxy/TLS-weakening Chromium launch flags.
    """
    if browser_config is None:
        return
    if not ALLOW_INSECURE_TLS and hasattr(browser_config, "ignore_https_errors"):
        browser_config.ignore_https_errors = False
    # Drop any caller proxy, then route the browser through the pinning proxy so
    # Chromium never resolves the target host itself (DNS-rebinding control).
    for attr in ("proxy", "proxy_config"):
        if getattr(browser_config, attr, None) is not None:
            setattr(browser_config, attr, None)
    if _EGRESS_PROXY_URL and hasattr(browser_config, "proxy_config"):
        try:
            from crawl4ai import ProxyConfig
            browser_config.proxy_config = ProxyConfig(server=_EGRESS_PROXY_URL)
        except Exception:
            pass
    args = getattr(browser_config, "extra_args", None)
    if args:
        browser_config.extra_args = [
            a for a in args
            if not any(str(a).startswith(bad) for bad in _DANGEROUS_BROWSER_ARGS)
        ]
