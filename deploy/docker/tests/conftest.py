"""
Shared fixtures for the Crawl4AI Docker server *behavioral* security tests.

Unlike the legacy `test_security_*.py` suites (which grep the source text and
pass even when the running server is wide open), these fixtures boot the real
FastAPI application via Starlette's TestClient and exercise it as a client
would. That makes the tests behavioral: they assert what the server actually
*does*, not what the source happens to contain.

Design notes
------------
* The app is imported once per session. `deploy/docker` is put on `sys.path`
  first, because `server.py` does `from crawler_pool import ...` at module top,
  before its own `sys.path.append`.
* The TestClient is created *without* the `with` context-manager form on
  purpose: that skips the FastAPI lifespan, so no Chromium is launched and no
  Redis connection is opened at startup. Authentication is decided by a
  dependency/middleware that runs before any route handler, so auth-posture
  assertions resolve before the app ever needs a browser or Redis.
* `offline_dns` / `rebinding_dns` monkeypatch name resolution so the SSRF /
  egress behavioral tests (R3) run fully offline and can model DNS-rebinding
  (resolve-then-reconnect TOCTOU) deterministically.
"""

import importlib
import socket
import sys
from pathlib import Path

import pytest

# deploy/docker (the dir that holds server.py, auth.py, ...) must be importable
# before we import `server`, since server.py imports its siblings by bare name.
DOCKER_DIR = Path(__file__).resolve().parents[1]
if str(DOCKER_DIR) not in sys.path:
    sys.path.insert(0, str(DOCKER_DIR))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "posture: the secure-by-default acceptance gate (expected RED until R1-R7 land)",
    )
    config.addinivalue_line(
        "markers", "cve: regression test for a specific reported vulnerability"
    )


@pytest.fixture(scope="session")
def server_module():
    """Import the Docker server app once for the whole test session.

    Returns the imported `server` module so tests can introspect the loaded
    config, the redis-url builder, feature flags, etc.
    """
    # Import fresh; if a previous test mutated it we still want the real module.
    if "server" in sys.modules:
        return sys.modules["server"]
    return importlib.import_module("server")


@pytest.fixture
def stock_client(server_module):
    """A TestClient bound to the app as shipped (config.yml defaults).

    No lifespan => no real browser, no Redis connect. Auth/headers/routing are
    all exercised normally because they sit in front of the route handlers.
    """
    from starlette.testclient import TestClient

    # raise_server_exceptions=False so an un-gated handler that blows up on a
    # missing pool/redis surfaces as a 500 response (which our posture test
    # treats as "not 401" => still a finding) instead of bubbling out of the
    # test client as an exception.
    return TestClient(server_module.app, raise_server_exceptions=False)


@pytest.fixture
def effective_config(server_module):
    """The configuration dict the running app actually loaded."""
    return server_module.config


@pytest.fixture
def effective_browser_args(effective_config):
    """The Chromium launch flags the app will pass to every browser."""
    return list(effective_config["crawler"]["browser"].get("extra_args", []))


@pytest.fixture
def effective_redis_url(server_module):
    """The Redis URL the app builds from config + environment."""
    return server_module._build_redis_url(server_module.config)


# ─────────────────────── offline DNS control ────────────────────────
# These let SSRF/egress tests run without touching the network and let us
# model DNS rebinding precisely.

class _FakeResolver:
    """Drop-in for socket.getaddrinfo with a controllable host->IP map.

    Unknown hosts resolve to a stable public-ish default so accidental real
    lookups never escape the test process.
    """

    DEFAULT_IP = "93.184.216.34"  # documentation/example address space

    def __init__(self):
        self.map = {}  # host -> ip (single answer)

    def set(self, host, ip):
        self.map[host] = ip

    def getaddrinfo(self, host, port, *args, **kwargs):
        ip = self.map.get(host, self.DEFAULT_IP)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 0))]


@pytest.fixture
def offline_dns(monkeypatch):
    """Patch socket.getaddrinfo with a controllable, offline resolver.

    Usage:
        offline_dns.set("evil.example", "169.254.169.254")
    """
    resolver = _FakeResolver()
    monkeypatch.setattr(socket, "getaddrinfo", resolver.getaddrinfo)
    return resolver


class _RebindingResolver:
    """Returns a *different* answer on the second+ lookup of the same host.

    Models the resolve-then-discard TOCTOU: validation sees a public IP, the
    later real connection re-resolves to an internal IP. A correct egress
    broker resolves once and pins, so the second (internal) answer is never
    dialed.
    """

    def __init__(self, host, first_ip, second_ip):
        self.host = host
        self.first_ip = first_ip
        self.second_ip = second_ip
        self.calls = 0

    def getaddrinfo(self, host, port, *args, **kwargs):
        if host == self.host:
            self.calls += 1
            ip = self.first_ip if self.calls == 1 else self.second_ip
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 0))]
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 0))]


@pytest.fixture
def rebinding_dns(monkeypatch):
    """Factory that installs a DNS-rebinding resolver.

    Usage:
        r = rebinding_dns("rebind.example", "93.184.216.34", "169.254.169.254")
        ... # first lookup public, every later lookup internal
    """
    def _install(host, first_ip, second_ip):
        resolver = _RebindingResolver(host, first_ip, second_ip)
        monkeypatch.setattr(socket, "getaddrinfo", resolver.getaddrinfo)
        return resolver

    return _install
