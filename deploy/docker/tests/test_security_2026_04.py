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

class TestOutputPathRemoved(unittest.TestCase):
    """output_path is gone; the server owns paths via the artifact store.

    The old string-only validate_output_path was bypassable (symlink/TOCTOU,
    sibling-prefix '...-evil') -> arbitrary write -> RCE. The fix is to never
    accept a caller path at all. Behavioral artifact-store coverage (O_NOFOLLOW,
    O_EXCL, hex id, TTL, quota) lives in test_security_artifact_store.py.
    """

    def test_screenshot_request_has_no_output_path(self):
        sys.path.insert(0, DEPLOY_DIR)
        from schemas import ScreenshotRequest
        self.assertNotIn("output_path", ScreenshotRequest.model_fields)

    def test_pdf_request_has_no_output_path(self):
        sys.path.insert(0, DEPLOY_DIR)
        from schemas import PDFRequest
        self.assertNotIn("output_path", PDFRequest.model_fields)

    def test_validate_output_path_deleted(self):
        sys.path.insert(0, DEPLOY_DIR)
        import utils
        self.assertFalse(
            hasattr(utils, "validate_output_path"),
            "validate_output_path must be deleted (caller paths no longer accepted)",
        )


class TestPydanticPathValidator(unittest.TestCase):
    """output_path (and its traversal validator) are gone entirely.

    Traversal rejection used to be the mitigation; the real fix is that no
    caller path is accepted at all, so there is nothing to traverse. The
    sandboxed artifact store owns all paths now.
    """

    def test_no_output_path_field_on_request_models(self):
        sys.path.insert(0, DEPLOY_DIR)
        from schemas import ScreenshotRequest, PDFRequest
        self.assertNotIn("output_path", ScreenshotRequest.model_fields)
        self.assertNotIn("output_path", PDFRequest.model_fields)

    def test_traversal_validator_removed(self):
        # No reject_traversal validator should remain registered on the models.
        sys.path.insert(0, DEPLOY_DIR)
        from schemas import ScreenshotRequest, PDFRequest
        for model in (ScreenshotRequest, PDFRequest):
            names = set(getattr(model, "__pydantic_decorators__").field_validators)
            self.assertNotIn("reject_traversal", names)


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

    def test_websocket_auth_enforced_by_gate(self):
        """The monitor WS is gated by the AuthGateMiddleware (behavioral).

        Auth moved out of the route's bespoke, timing-unsafe env-token check
        and into the outermost ASGI gate, which closes an unauthenticated
        WebSocket before it is accepted.
        """
        import sys
        sys.path.insert(0, DEPLOY_DIR)
        import server
        from starlette.testclient import TestClient

        client = TestClient(server.app)
        # Unauthenticated connect must be rejected by the gate.
        with self.assertRaises(Exception):
            with client.websocket_connect("/monitor/ws") as ws:
                ws.receive_text()

        # The old in-route check must be gone (it read a different secret than
        # the REST path and compared with a timing-unsafe `!=`).
        with open(os.path.join(DEPLOY_DIR, "monitor_routes.py")) as f:
            source = f.read()
        self.assertNotIn('os.environ.get("CRAWL4AI_API_TOKEN"', source,
            "bespoke WS token check must be removed; the gate owns WS auth")


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

    def test_redirects_not_auto_followed(self):
        # Redirects are followed manually and re-validated per hop, never
        # auto-followed (which would skip the SSRF re-check).
        with open(os.path.join(DEPLOY_DIR, "webhook.py")) as f:
            source = f.read()
        self.assertIn("allow_redirects=False", source)
        self.assertIn("check_redirect", source)  # each hop re-validated

    def test_webhook_validates_at_send_time(self):
        # Validation happens at send time via the egress broker (resolve_and_pin
        # rejects non-global targets); the connection is also pinned to that IP.
        with open(os.path.join(DEPLOY_DIR, "webhook.py")) as f:
            source = f.read()
        self.assertIn("resolve_and_pin", source)

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
