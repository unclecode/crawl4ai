"""Process-wide egress proxy for the library's own HTTP clients.

The library deliberately has no egress policy of its own: as a plain library
the caller already chooses the URL, so there is nothing to defend against.
It matters when the URL comes from an untrusted API client, which is the
Docker server's situation -- deploy/docker/server.py starts a pinning forward
proxy (egress_proxy.PinningProxy) and registers it here at boot, so the
seeder and robots.txt fetches go through the same resolve-and-pin rule the
browser path already gets.

A proxy rather than a validator hook (the shape used by
crawl4ai/processors/pdf) because a validator resolves the name, checks it and
then throws the address away -- the client re-resolves when it dials, which is
the DNS-rebinding window egress_broker.py exists to close. The proxy resolves,
pins and dials the same address, and re-validates every redirect hop because
each hop is a fresh proxied request.

Unset (the plain-library case) means proxy_url() is None, which is the default
value of the `proxy=` kwarg on both httpx and aiohttp: no behaviour change.
"""

from typing import Optional

_proxy_url: Optional[str] = None


def set_egress_proxy(url: Optional[str]) -> None:
    """Route the library's own HTTP clients through `url` (None = direct)."""
    global _proxy_url
    _proxy_url = url


def proxy_url() -> Optional[str]:
    """The installed egress proxy, or None for a direct connection."""
    return _proxy_url
