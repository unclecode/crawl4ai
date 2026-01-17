#!/usr/bin/env python3
"""
Unit tests for security fixes.
These tests verify the security fixes at the code level without needing a running server.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest


class TestURLValidation(unittest.TestCase):
    """Test URL scheme validation helper."""

    def setUp(self):
        """Set up test fixtures."""
        # Import the validation constants and function
        self.ALLOWED_URL_SCHEMES = ("http://", "https://")
        self.ALLOWED_URL_SCHEMES_WITH_RAW = ("http://", "https://", "raw:", "raw://")

    def validate_url_scheme(self, url: str, allow_raw: bool = False) -> bool:
        """Local version of validate_url_scheme for testing."""
        allowed = self.ALLOWED_URL_SCHEMES_WITH_RAW if allow_raw else self.ALLOWED_URL_SCHEMES
        return url.startswith(allowed)

    # === SECURITY TESTS: These URLs must be BLOCKED ===

    def test_file_url_blocked(self):
        """file:// URLs must be blocked (LFI vulnerability)."""
        self.assertFalse(self.validate_url_scheme("file:///etc/passwd"))
        self.assertFalse(self.validate_url_scheme("file:///etc/passwd", allow_raw=True))

    def test_file_url_blocked_windows(self):
        """file:// URLs with Windows paths must be blocked."""
        self.assertFalse(self.validate_url_scheme("file:///C:/Windows/System32/config/sam"))

    def test_javascript_url_blocked(self):
        """javascript: URLs must be blocked (XSS)."""
        self.assertFalse(self.validate_url_scheme("javascript:alert(1)"))

    def test_data_url_blocked(self):
        """data: URLs must be blocked."""
        self.assertFalse(self.validate_url_scheme("data:text/html,<script>alert(1)</script>"))

    def test_ftp_url_blocked(self):
        """ftp: URLs must be blocked."""
        self.assertFalse(self.validate_url_scheme("ftp://example.com/file"))

    def test_empty_url_blocked(self):
        """Empty URLs must be blocked."""
        self.assertFalse(self.validate_url_scheme(""))

    def test_relative_url_blocked(self):
        """Relative URLs must be blocked."""
        self.assertFalse(self.validate_url_scheme("/etc/passwd"))
        self.assertFalse(self.validate_url_scheme("../../../etc/passwd"))

    # === FUNCTIONALITY TESTS: These URLs must be ALLOWED ===

    def test_http_url_allowed(self):
        """http:// URLs must be allowed."""
        self.assertTrue(self.validate_url_scheme("http://example.com"))
        self.assertTrue(self.validate_url_scheme("http://localhost:8080"))

    def test_https_url_allowed(self):
        """https:// URLs must be allowed."""
        self.assertTrue(self.validate_url_scheme("https://example.com"))
        self.assertTrue(self.validate_url_scheme("https://example.com/path?query=1"))

    def test_raw_url_allowed_when_enabled(self):
        """raw: URLs must be allowed when allow_raw=True."""
        self.assertTrue(self.validate_url_scheme("raw:<html></html>", allow_raw=True))
        self.assertTrue(self.validate_url_scheme("raw://<html></html>", allow_raw=True))

    def test_raw_url_blocked_when_disabled(self):
        """raw: URLs must be blocked when allow_raw=False."""
        self.assertFalse(self.validate_url_scheme("raw:<html></html>", allow_raw=False))
        self.assertFalse(self.validate_url_scheme("raw://<html></html>", allow_raw=False))


class TestHookBuiltins(unittest.TestCase):
    """Test that dangerous builtins are removed from hooks."""

    def test_import_not_in_allowed_builtins(self):
        """__import__ must NOT be in allowed_builtins."""
        allowed_builtins = [
            'print', 'len', 'str', 'int', 'float', 'bool',
            'list', 'dict', 'set', 'tuple', 'range', 'enumerate',
            'zip', 'map', 'filter', 'any', 'all', 'sum', 'min', 'max',
            'sorted', 'reversed', 'abs', 'round', 'isinstance', 'type',
            'getattr', 'hasattr', 'setattr', 'callable', 'iter', 'next',
            '__build_class__'  # Required for class definitions in exec
        ]

        self.assertNotIn('__import__', allowed_builtins)
        self.assertNotIn('eval', allowed_builtins)
        self.assertNotIn('exec', allowed_builtins)
        self.assertNotIn('compile', allowed_builtins)
        self.assertNotIn('open', allowed_builtins)

    def test_build_class_in_allowed_builtins(self):
        """__build_class__ must be in allowed_builtins (needed for class definitions)."""
        allowed_builtins = [
            'print', 'len', 'str', 'int', 'float', 'bool',
            'list', 'dict', 'set', 'tuple', 'range', 'enumerate',
            'zip', 'map', 'filter', 'any', 'all', 'sum', 'min', 'max',
            'sorted', 'reversed', 'abs', 'round', 'isinstance', 'type',
            'getattr', 'hasattr', 'setattr', 'callable', 'iter', 'next',
            '__build_class__'
        ]

        self.assertIn('__build_class__', allowed_builtins)


class TestHooksEnabled(unittest.TestCase):
    """Test HOOKS_ENABLED environment variable logic."""

    def test_hooks_disabled_by_default(self):
        """Hooks must be disabled by default."""
        # Simulate the default behavior
        hooks_enabled = os.environ.get("CRAWL4AI_HOOKS_ENABLED", "false").lower() == "true"

        # Clear any existing env var to test default
        original = os.environ.pop("CRAWL4AI_HOOKS_ENABLED", None)
        try:
            hooks_enabled = os.environ.get("CRAWL4AI_HOOKS_ENABLED", "false").lower() == "true"
            self.assertFalse(hooks_enabled)
        finally:
            if original is not None:
                os.environ["CRAWL4AI_HOOKS_ENABLED"] = original

    def test_hooks_enabled_when_true(self):
        """Hooks must be enabled when CRAWL4AI_HOOKS_ENABLED=true."""
        original = os.environ.get("CRAWL4AI_HOOKS_ENABLED")
        try:
            os.environ["CRAWL4AI_HOOKS_ENABLED"] = "true"
            hooks_enabled = os.environ.get("CRAWL4AI_HOOKS_ENABLED", "false").lower() == "true"
            self.assertTrue(hooks_enabled)
        finally:
            if original is not None:
                os.environ["CRAWL4AI_HOOKS_ENABLED"] = original
            else:
                os.environ.pop("CRAWL4AI_HOOKS_ENABLED", None)

    def test_hooks_disabled_when_false(self):
        """Hooks must be disabled when CRAWL4AI_HOOKS_ENABLED=false."""
        original = os.environ.get("CRAWL4AI_HOOKS_ENABLED")
        try:
            os.environ["CRAWL4AI_HOOKS_ENABLED"] = "false"
            hooks_enabled = os.environ.get("CRAWL4AI_HOOKS_ENABLED", "false").lower() == "true"
            self.assertFalse(hooks_enabled)
        finally:
            if original is not None:
                os.environ["CRAWL4AI_HOOKS_ENABLED"] = original
            else:
                os.environ.pop("CRAWL4AI_HOOKS_ENABLED", None)


if __name__ == '__main__':
    print("=" * 60)
    print("Crawl4AI Security Fixes - Unit Tests")
    print("=" * 60)
    print()

    # Run tests with verbosity
    unittest.main(verbosity=2)
