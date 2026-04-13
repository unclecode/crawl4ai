#!/usr/bin/env python3
"""
Adversarial security tests for the 4 vulns reported 2026-04-13.
Self-contained: copies validation logic to avoid import issues with dns.resolver etc.

Vuln 1: Arbitrary File Write via /screenshot + /pdf output_path
Vuln 2: Monitor Auth Bypass (structural source check)
Vuln 3: Stored XSS in Monitor Dashboard (server-side + client-side)
Vuln 4: SSRF via Webhook URL
"""

import os
import sys
import unittest
import ipaddress
import socket
from urllib.parse import urlparse


# ============================================================================
# Local copies of security utilities (to avoid dns.resolver import in utils.py)
# ============================================================================

ALLOWED_OUTPUT_DIR = os.environ.get("CRAWL4AI_OUTPUT_DIR", "/tmp/crawl4ai-outputs")


def validate_output_path(user_path):
    safe_path = os.path.normpath(user_path).lstrip(os.sep)
    abs_path = os.path.abspath(os.path.join(ALLOWED_OUTPUT_DIR, safe_path))
    abs_allowed = os.path.abspath(ALLOWED_OUTPUT_DIR) + os.sep
    if not abs_path.startswith(abs_allowed):
        raise ValueError(f"output_path must resolve within {ALLOWED_OUTPUT_DIR}")
    return abs_path


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


def validate_webhook_url(url):
    parsed = urlparse(str(url))
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Webhook URL must have a valid hostname")
    hostname_lower = hostname.lower()
    if hostname_lower in _BLOCKED_HOSTNAMES:
        raise ValueError(f"Webhook URL hostname '{hostname}' is blocked")
    if hostname_lower.startswith("host.docker.internal"):
        raise ValueError(f"Webhook URL hostname '{hostname}' is blocked")
    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError(f"Cannot resolve webhook hostname '{hostname}'")
    for _, _, _, _, sockaddr in resolved:
        ip = ipaddress.ip_address(sockaddr[0])
        for network in _BLOCKED_NETWORKS:
            if ip in network:
                raise ValueError(f"Webhook URL resolves to blocked address: {ip}")


DEPLOY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


# ============================================================================
# VULN 1: Arbitrary File Write - Path Traversal
# ============================================================================

class TestPathTraversalBlocked(unittest.TestCase):
    """Test validate_output_path blocks all traversal attempts."""

    def test_absolute_path_gets_jailed(self):
        """Absolute paths get stripped and jailed inside allowed dir."""
        result = validate_output_path("/app/server.py")
        self.assertTrue(result.startswith(ALLOWED_OUTPUT_DIR))
        self.assertNotEqual(result, "/app/server.py")

    def test_absolute_etc_passwd_gets_jailed(self):
        result = validate_output_path("/etc/passwd")
        self.assertTrue(result.startswith(ALLOWED_OUTPUT_DIR))
        self.assertNotEqual(result, "/etc/passwd")

    def test_relative_traversal_simple(self):
        with self.assertRaises(ValueError):
            validate_output_path("../../etc/passwd")

    def test_relative_traversal_deep(self):
        with self.assertRaises(ValueError):
            validate_output_path("foo/../../bar/../../../app/evil.py")

    def test_absolute_path_home_gets_jailed(self):
        result = validate_output_path("/home/appuser/.bashrc")
        self.assertTrue(result.startswith(ALLOWED_OUTPUT_DIR))

    def test_absolute_path_tmp_outside_gets_jailed(self):
        result = validate_output_path("/tmp/other-dir/evil.py")
        self.assertTrue(result.startswith(ALLOWED_OUTPUT_DIR))

    def test_simple_filename(self):
        result = validate_output_path("test.png")
        self.assertTrue(result.startswith(ALLOWED_OUTPUT_DIR))
        self.assertTrue(result.endswith("test.png"))

    def test_subdirectory(self):
        result = validate_output_path("subdir/deep/test.png")
        self.assertTrue(result.startswith(ALLOWED_OUTPUT_DIR))

    def test_filename_with_dots(self):
        result = validate_output_path("my.screenshot.2024.png")
        self.assertTrue(result.endswith("my.screenshot.2024.png"))


class TestPydanticPathValidator(unittest.TestCase):
    """Verify schemas.py has traversal rejection on output_path."""

    def test_schemas_has_validator(self):
        with open(os.path.join(DEPLOY_DIR, "schemas.py")) as f:
            source = f.read()
        self.assertIn("reject_traversal", source,
            "schemas.py must have reject_traversal validator on output_path")
        self.assertIn('".."', source,
            "Validator must check for '..' traversal")


# ============================================================================
# VULN 2: Monitor Auth Bypass (structural check)
# ============================================================================

class TestMonitorAuthStructural(unittest.TestCase):

    def test_monitor_router_has_auth(self):
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        # Find the line with monitor_router
        for line in source.splitlines():
            if "monitor_router" in line and "include_router" in line:
                self.assertIn("dependencies=", line,
                    "Monitor router must have dependencies=[Depends(token_dep)]")
                return
        self.fail("Could not find monitor_router include_router line")

    def test_websocket_has_token_check(self):
        with open(os.path.join(DEPLOY_DIR, "monitor_routes.py")) as f:
            source = f.read()
        self.assertIn("CRAWL4AI_API_TOKEN", source,
            "WebSocket endpoint must check CRAWL4AI_API_TOKEN")
        self.assertIn("websocket.close", source,
            "WebSocket must close connection on auth failure")


# ============================================================================
# VULN 3: Stored XSS (server-side + client-side)
# ============================================================================

class TestXSSPrevention(unittest.TestCase):

    def test_html_escape_blocks_script_tags(self):
        import html
        payload = '<script>alert(document.cookie)</script>'
        escaped = html.escape(payload)
        self.assertNotIn("<script>", escaped)
        self.assertIn("&lt;script&gt;", escaped)

    def test_html_escape_blocks_img_tag(self):
        import html
        payload = '"><img src=x onerror=alert(1)>'
        escaped = html.escape(payload)
        self.assertNotIn("<img", escaped)
        self.assertIn("&lt;img", escaped)

    def test_monitor_py_uses_html_escape(self):
        with open(os.path.join(DEPLOY_DIR, "monitor.py")) as f:
            source = f.read()
        self.assertIn("import html", source)
        self.assertIn("html.escape(url", source)
        self.assertIn("html.escape(str(error)", source)

    def test_index_html_has_escape_function(self):
        html_path = os.path.join(DEPLOY_DIR, "static", "monitor", "index.html")
        with open(html_path) as f:
            source = f.read()
        self.assertIn("function escapeHtml(", source)

    def test_index_html_no_raw_url_injection(self):
        html_path = os.path.join(DEPLOY_DIR, "static", "monitor", "index.html")
        with open(html_path) as f:
            source = f.read()
        self.assertNotIn("${req.url}", source, "Raw ${req.url} found")
        self.assertNotIn("${err.url}", source, "Raw ${err.url} found")
        self.assertNotIn("${err.error}", source, "Raw ${err.error} found")


# ============================================================================
# VULN 4: SSRF via Webhook URL
# ============================================================================

class TestSSRFBlocked(unittest.TestCase):

    def test_localhost_ip(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://127.0.0.1:9999/steal")

    def test_localhost_hostname(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://localhost:9999/steal")

    def test_loopback_127_x(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://127.0.0.2:9999/steal")

    def test_10_network(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://10.0.0.1:8080/admin")

    def test_172_16_network(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://172.16.0.1:8080/admin")

    def test_192_168_network(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://192.168.1.1:8080/admin")

    def test_aws_metadata_ip(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://169.254.169.254/latest/meta-data/")

    def test_gcp_metadata_hostname(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://metadata.google.internal/computeMetadata/v1/")

    def test_docker_internal(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://host.docker.internal:9998/steal")

    def test_kubernetes_default(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http://kubernetes.default/api/v1/secrets")

    def test_empty_hostname(self):
        with self.assertRaises(ValueError):
            validate_webhook_url("http:///steal")

    def test_valid_external_url(self):
        validate_webhook_url("https://webhook.site/test-uuid")
        validate_webhook_url("https://hooks.slack.com/services/T00/B00/xxx")

    def test_valid_external_with_port(self):
        """External URL with port -- may fail DNS in CI, that's expected."""
        try:
            validate_webhook_url("https://google.com:443/webhook")
        except ValueError as e:
            if "Cannot resolve" in str(e):
                self.skipTest("DNS resolution unavailable in this environment")
            raise


class TestWebhookSourceChecks(unittest.TestCase):

    def test_follow_redirects_disabled(self):
        with open(os.path.join(DEPLOY_DIR, "webhook.py")) as f:
            source = f.read()
        self.assertIn("follow_redirects=False", source)

    def test_webhook_validates_at_send_time(self):
        with open(os.path.join(DEPLOY_DIR, "webhook.py")) as f:
            source = f.read()
        self.assertIn("validate_webhook_url", source)

    def test_job_validates_webhook(self):
        with open(os.path.join(DEPLOY_DIR, "job.py")) as f:
            source = f.read()
        self.assertIn("validate_webhook_url", source)


if __name__ == "__main__":
    print("=" * 70)
    print("Crawl4AI Security Tests - 2026-04-13 Vulnerabilities")
    print("=" * 70)
    print()
    unittest.main(verbosity=2)
