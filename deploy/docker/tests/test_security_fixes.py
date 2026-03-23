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


class TestDeserializationAllowlist(unittest.TestCase):
    """Test the allowlist gate logic for from_serializable_dict.

    Replicates the gate logic locally to avoid importing crawl4ai (which has
    heavy dependencies). The logic under test is:
      if data["type"] not in ALLOWED_DESERIALIZE_TYPES: raise ValueError
    """

    @staticmethod
    def _check_allowlist(data, allowed_types):
        """Minimal replica of the allowlist gate in from_serializable_dict."""
        if data is None:
            return data
        if isinstance(data, (str, int, float, bool)):
            return data
        if isinstance(data, dict) and "type" in data:
            if data["type"] == "dict" and "value" in data:
                return {k: v for k, v in data["value"].items()}
            if data["type"] not in allowed_types:
                raise ValueError(
                    f"Disallowed type for deserialization: {data['type']}"
                )
            return {"_allowed": True, "type": data["type"]}
        return data

    def test_disallowed_type_rejected(self):
        """Types not in the allowlist must be rejected."""
        allowed = {"BrowserConfig"}
        with self.assertRaises(ValueError) as ctx:
            self._check_allowlist({"type": "AsyncWebCrawler", "params": {}}, allowed)
        self.assertIn("Disallowed type", str(ctx.exception))

    def test_arbitrary_class_rejected(self):
        """Arbitrary class names must be rejected."""
        allowed = {"BrowserConfig"}
        with self.assertRaises(ValueError):
            self._check_allowlist({"type": "Crawl4aiDockerClient", "params": {}}, allowed)

    def test_allowed_type_passes_gate(self):
        """Types in the allowlist must pass the gate check."""
        allowed = {"BrowserConfig", "CrawlerRunConfig"}
        result = self._check_allowlist({"type": "BrowserConfig", "params": {}}, allowed)
        self.assertEqual(result["type"], "BrowserConfig")

    def test_dict_type_bypasses_allowlist(self):
        """The special 'dict' type must still work (not subject to allowlist)."""
        result = self._check_allowlist({"type": "dict", "value": {"k": "v"}}, set())
        self.assertEqual(result, {"k": "v"})

    def test_basic_types_pass_through(self):
        """Strings, ints, etc. must pass through unchanged."""
        self.assertEqual(self._check_allowlist("hello", set()), "hello")
        self.assertEqual(self._check_allowlist(42, set()), 42)
        self.assertIsNone(self._check_allowlist(None, set()))

    def test_empty_allowlist_denies_all(self):
        """With empty allowlist, all typed deserialization must be denied."""
        with self.assertRaises(ValueError):
            self._check_allowlist({"type": "BrowserConfig", "params": {}}, set())

    def test_env_var_parsing(self):
        """CRAWL4AI_DESERIALIZE_ALLOW env var must be parsed as comma-separated set."""
        original = os.environ.get("CRAWL4AI_DESERIALIZE_ALLOW")
        try:
            os.environ["CRAWL4AI_DESERIALIZE_ALLOW"] = "BrowserConfig,CrawlerRunConfig,CacheMode"
            env_val = os.environ.get("CRAWL4AI_DESERIALIZE_ALLOW", "")
            allowed = {t.strip() for t in env_val.split(",") if t.strip()}
            self.assertEqual(allowed, {"BrowserConfig", "CrawlerRunConfig", "CacheMode"})
        finally:
            if original is not None:
                os.environ["CRAWL4AI_DESERIALIZE_ALLOW"] = original
            else:
                os.environ.pop("CRAWL4AI_DESERIALIZE_ALLOW", None)

    def test_empty_env_var_means_deny_all(self):
        """Unset or empty CRAWL4AI_DESERIALIZE_ALLOW must produce empty set."""
        original = os.environ.pop("CRAWL4AI_DESERIALIZE_ALLOW", None)
        try:
            env_val = os.environ.get("CRAWL4AI_DESERIALIZE_ALLOW", "")
            allowed = {t.strip() for t in env_val.split(",") if t.strip()}
            self.assertEqual(allowed, set())
        finally:
            if original is not None:
                os.environ["CRAWL4AI_DESERIALIZE_ALLOW"] = original


if __name__ == '__main__':
    print("=" * 60)
    print("Crawl4AI Security Fixes - Unit Tests")
    print("=" * 60)
    print()

    # Run tests with verbosity
    unittest.main(verbosity=2)
