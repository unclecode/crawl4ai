"""Opt-in SSRF protection for the library layer.

This module provides ``block_internal_urls`` enforcement for the core
``crawl4ai`` library. It is intentionally dependency-free (no FastAPI, no
egress proxy) so it can be imported from the library without pulling in the
Docker server stack.

Design notes
------------
* The trust boundary for *untrusted* URL sources remains the Docker API server
  (``deploy/docker/egress_broker.py``), which pins DNS and revalidates every
  redirect hop through a dedicated egress proxy. That server-side enforcement
  is authoritative for multi-tenant deployments.
* This library-side helper is the same *destination-classification* logic,
  exposed as an opt-in flag for callers who embed Crawl4AI in an agent where an
  LLM / prompt-injection can steer the crawl target at internal hosts *before*
  the embedding app validates the URL.
* Because the library connects directly (it does not proxy through a pinning
  egress broker), the check is a pre-connection, single-resolution check. It
  therefore defends against the obvious cases (literal internal IPs, localhost,
  link-local/cloud-metadata, private ranges) but does **not** guarantee
  protection against DNS-rebinding / TOCTOU attacks. Deployments that need that
  guarantee must still terminate egress through the Docker server.
"""

import ipaddress
import os
import socket
from urllib.parse import urlparse

# Same address ranges the Docker server blocks (deploy/docker/utils.py).
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

# Hostnames that should never be crawled regardless of resolution.
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
    "kubernetes.default",
    "kubernetes.default.svc",
}

# Escape hatch mirroring the Docker server (deploy/docker/utils.py).
ALLOW_INTERNAL_URLS = (
    os.environ.get("CRAWL4AI_ALLOW_INTERNAL_URLS", "false").lower() == "true"
)


class BlockedURLError(ValueError):
    """Raised when a crawl URL targets an internal/private address and
    ``block_internal_urls`` is enabled.

    The message is intentionally opaque: it never echoes the resolved IP or
    hostname, so the error is not a DNS-oracle leak.
    """


def _expand_ip_candidates(ip: "ipaddress.IPv4Address | ipaddress.IPv6Address"):
    """Return ``[ip]`` plus any IPv4 form embedded inside an IPv6 address.

    SSRF guards must check the unwrapped form because ``::ffff:127.0.0.1`` and
    ``::127.0.0.1`` route to ``127.0.0.1`` but would not match IPv4 blocklists
    directly.
    """
    candidates = [ip]
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            candidates.append(ip.ipv4_mapped)
        else:
            as_int = int(ip)
            if 0 < as_int < 2**32:
                candidates.append(ipaddress.IPv4Address(as_int))
    return candidates


def _is_internal_ip(addr: "ipaddress.IPv4Address | ipaddress.IPv6Address") -> bool:
    for candidate in _expand_ip_candidates(addr):
        if any(candidate in net for net in _BLOCKED_NETWORKS):
            return True
        # is_global is False for loopback / private / link-local / ULA / reserved.
        if not candidate.is_global:
            return True
    return False


def is_internal_url(url: str) -> bool:
    """Return ``True`` if ``url`` resolves to an internal/private address.

    ``raw:``/``raw://`` URLs are inline HTML (no network fetch) and are never
    considered internal. Resolution failures are treated as internal
    (fail-closed) so an attacker cannot abuse a DNS error to bypass the check.
    """
    if str(url).startswith(("raw:", "raw://")):
        return False
    parsed = urlparse(str(url))
    if not parsed.hostname:
        # No host to validate (e.g. a bare path) -> nothing to block.
        return False
    hostname = parsed.hostname
    if hostname in _BLOCKED_HOSTNAMES:
        return True

    # Fast path: a literal IP address.
    try:
        addr = ipaddress.ip_address(hostname)
        return _is_internal_ip(addr)
    except ValueError:
        pass

    # Hostname: resolve and inspect every A/AAAA record.
    try:
        infos = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, UnicodeError, OSError):
        # Fail closed: cannot prove the target is safe.
        return True

    for family, _type, _proto, _canon, sockaddr in infos:
        ip_text = sockaddr[0].split("%")[0]  # strip IPv6 scope id
        try:
            addr = ipaddress.ip_address(ip_text)
        except ValueError:
            # Unparseable resolved address -> fail closed.
            return True
        if _is_internal_ip(addr):
            return True
    return False


def check_url_destination(url: str) -> None:
    """Raise :class:`BlockedURLError` if ``url`` targets an internal address.

    No-op when ``CRAWL4AI_ALLOW_INTERNAL_URLS`` is set, and for ``raw:`` URLs.
    """
    if ALLOW_INTERNAL_URLS:
        return
    if is_internal_url(url):
        raise BlockedURLError(
            "URL blocked by block_internal_urls: destination is internal/private"
        )
