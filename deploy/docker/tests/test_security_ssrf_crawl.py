#!/usr/bin/env python3
"""
Adversarial tests for SSRF protection on crawl/md/llm URL entry points.
Reported by secsys_codex (2026-04-18).

Tests that validate_url_destination() blocks internal IPs on all crawl paths,
and that CRAWL4AI_ALLOW_INTERNAL_URLS=true bypasses the check.
"""

import os
import sys
import unittest
import ipaddress
import socket
from urllib.parse import urlparse

DEPLOY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Local copy of validation logic for self-contained testing
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
_BLOCKED_HOSTNAMES = {
    "localhost", "metadata.google.internal", "metadata",
    "kubernetes.default", "kubernetes.default.svc",
}


def _expand_ip_candidates(ip):
    """Mirror of utils.py: unwrap IPv4 from IPv4-mapped/compat IPv6."""
    candidates = [ip]
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            candidates.append(ip.ipv4_mapped)
        else:
            as_int = int(ip)
            if 0 < as_int < 2**32:
                candidates.append(ipaddress.IPv4Address(as_int))
    return candidates


def _validate_webhook_url(url):
    parsed = urlparse(str(url))
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a valid hostname")
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise ValueError(f"Hostname '{hostname}' is blocked")
    if hostname.lower().startswith("host.docker.internal"):
        raise ValueError(f"Hostname '{hostname}' is blocked")
    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError(f"Cannot resolve hostname '{hostname}'")
    for _, _, _, _, sockaddr in resolved:
        ip = ipaddress.ip_address(sockaddr[0])
        for candidate in _expand_ip_candidates(ip):
            for network in _BLOCKED_NETWORKS:
                if candidate in network:
                    raise ValueError(f"URL resolves to blocked address: {ip}")


def validate_url_destination(url, allow_internal=False):
    """Simulates the actual validate_url_destination from utils.py."""
    if allow_internal:
        return
    if str(url).startswith(("raw:", "raw://")):
        return
    _validate_webhook_url(url)


# ============================================================================
# SSRF attacks on crawl URLs
# ============================================================================

class TestCrawlURLSSRF(unittest.TestCase):
    """Test SSRF protection on URLs that go to crawler.arun()."""

    def test_localhost_blocked(self):
        with self.assertRaises(ValueError):
            validate_url_destination("http://127.0.0.1:8080/admin")

    def test_localhost_name_blocked(self):
        with self.assertRaises(ValueError):
            validate_url_destination("http://localhost:8080/secret")

    def test_10_network_blocked(self):
        with self.assertRaises(ValueError):
            validate_url_destination("http://10.0.0.1/internal")

    def test_172_16_blocked(self):
        with self.assertRaises(ValueError):
            validate_url_destination("http://172.16.0.1/dashboard")

    def test_192_168_blocked(self):
        with self.assertRaises(ValueError):
            validate_url_destination("http://192.168.1.1/router")

    def test_aws_metadata(self):
        with self.assertRaises(ValueError):
            validate_url_destination("http://169.254.169.254/latest/meta-data/")

    def test_gcp_metadata(self):
        with self.assertRaises(ValueError):
            validate_url_destination("http://metadata.google.internal/computeMetadata/v1/")

    def test_docker_internal(self):
        with self.assertRaises(ValueError):
            validate_url_destination("http://host.docker.internal:3000/api")

    def test_kubernetes(self):
        with self.assertRaises(ValueError):
            validate_url_destination("http://kubernetes.default/api/v1/secrets")

    # -- Must allow: external URLs --

    def test_external_url_allowed(self):
        validate_url_destination("https://example.com")
        validate_url_destination("https://www.google.com")

    # -- raw: URLs bypass (no network fetch) --

    def test_raw_url_bypasses(self):
        validate_url_destination("raw:<html><body>hello</body></html>")
        validate_url_destination("raw://<html>test</html>")

    # -- ALLOW_INTERNAL_URLS opt-out --

    def test_allow_internal_bypasses(self):
        """When opted in, internal URLs should pass."""
        validate_url_destination("http://127.0.0.1:8080", allow_internal=True)
        validate_url_destination("http://10.0.0.1/internal", allow_internal=True)
        validate_url_destination("http://169.254.169.254/meta", allow_internal=True)


# ============================================================================
# IPv6-mapped IPv4 bypass (caught in internal security review)
# Prior code only checked blocked networks directly; ::ffff:127.0.0.1
# parses as ::ffff:7f00:1 which is not in 127.0.0.0/8, bypassing the guard.
# ============================================================================

class TestIPv6MappedBypass(unittest.TestCase):
    """Test the IPv4-mapped IPv6 SSRF bypass class."""

    def test_mapped_loopback_blocked(self):
        """http://[::ffff:127.0.0.1]/ must be blocked (maps to 127.0.0.1)."""
        with self.assertRaises(ValueError):
            validate_url_destination("http://[::ffff:127.0.0.1]/admin")

    def test_mapped_private_10_blocked(self):
        """::ffff:10.0.0.1 must be blocked (maps to RFC 1918)."""
        with self.assertRaises(ValueError):
            validate_url_destination("http://[::ffff:10.0.0.1]/")

    def test_mapped_aws_metadata_blocked(self):
        """::ffff:169.254.169.254 must be blocked (maps to cloud metadata)."""
        with self.assertRaises(ValueError):
            validate_url_destination("http://[::ffff:169.254.169.254]/latest/meta-data/")

    def test_mapped_192_168_blocked(self):
        """::ffff:192.168.1.1 must be blocked."""
        with self.assertRaises(ValueError):
            validate_url_destination("http://[::ffff:192.168.1.1]/")

    def test_ipv4_compatible_loopback_blocked(self):
        """IPv4-compatible IPv6 (deprecated but still exists): ::127.0.0.1."""
        with self.assertRaises(ValueError):
            validate_url_destination("http://[::127.0.0.1]/")

    def test_regular_ipv6_loopback_still_blocked(self):
        """::1 must remain blocked (IPv6 loopback)."""
        with self.assertRaises(ValueError):
            validate_url_destination("http://[::1]:8080/")


# ============================================================================
# Source-level verification
# ============================================================================

class TestSSRFSourceCoverage(unittest.TestCase):
    """Verify all URL entry points have SSRF validation."""

    def test_server_validate_url_scheme_calls_destination(self):
        """validate_url_scheme must also call validate_url_destination."""
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        # Find validate_url_scheme function body
        idx = source.index("def validate_url_scheme")
        func_end = source.index("\ndef ", idx + 1) if "\ndef " in source[idx+1:] else idx + 500
        func_body = source[idx:func_end]
        self.assertIn("validate_url_destination", func_body,
            "validate_url_scheme must call validate_url_destination")

    def test_api_py_has_destination_validation(self):
        """api.py must call validate_url_destination for all URL entry points."""
        with open(os.path.join(DEPLOY_DIR, "api.py")) as f:
            source = f.read()
        self.assertIn("validate_url_destination", source,
            "api.py must import and use validate_url_destination")
        # Count occurrences -- should have at least 4 (one per entry point)
        count = source.count("validate_url_destination")
        self.assertGreaterEqual(count, 5,  # 1 import + 4 call sites
            f"api.py should call validate_url_destination at all URL entry points (found {count})")

    def test_utils_has_allow_internal_flag(self):
        """utils.py must have CRAWL4AI_ALLOW_INTERNAL_URLS env var."""
        with open(os.path.join(DEPLOY_DIR, "utils.py")) as f:
            source = f.read()
        self.assertIn("CRAWL4AI_ALLOW_INTERNAL_URLS", source)
        self.assertIn("ALLOW_INTERNAL_URLS", source)

    def test_validate_url_destination_skips_raw(self):
        """validate_url_destination must skip raw: URLs."""
        with open(os.path.join(DEPLOY_DIR, "utils.py")) as f:
            source = f.read()
        idx = source.index("def validate_url_destination")
        func_body = source[idx:idx+500]
        self.assertIn("raw:", func_body,
            "validate_url_destination must skip raw: URLs")


if __name__ == "__main__":
    print("=" * 70)
    print("Crawl4AI SSRF Tests - Crawl/MD/LLM Endpoints (secsys_codex)")
    print("=" * 70)
    print()
    unittest.main(verbosity=2)
