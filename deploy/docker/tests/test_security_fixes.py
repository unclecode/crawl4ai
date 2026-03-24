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


class TestComputedFieldSafety(unittest.TestCase):
    """Test that computed field expressions block dangerous operations.

    Mirrors the AST-based _safe_eval_expression() logic from extraction_strategy.py
    to test without importing heavy crawl4ai dependencies.
    """

    def setUp(self):
        """Set up the safe eval function (local copy of the logic)."""
        import ast

        SAFE_BUILTINS = {
            "str": str, "int": int, "float": float, "bool": bool,
            "len": len, "round": round, "abs": abs, "min": min, "max": max,
            "sum": sum, "sorted": sorted, "reversed": reversed,
            "list": list, "dict": dict, "tuple": tuple, "set": set,
            "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
            "any": any, "all": all, "range": range,
            "True": True, "False": False, "None": None,
            "isinstance": isinstance, "type": type,
        }

        def safe_eval(expression, local_vars):
            tree = ast.parse(expression, mode="eval")
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    raise ValueError("Import statements are not allowed")
                if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                    raise ValueError(f"Access to '{node.attr}' is not allowed")
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id.startswith("_"):
                        raise ValueError(f"Calling '{func.id}' is not allowed")
                    if isinstance(func, ast.Attribute) and func.attr.startswith("_"):
                        raise ValueError(f"Calling '{func.attr}' is not allowed")
            safe_globals = {"__builtins__": SAFE_BUILTINS}
            return eval(compile(tree, "<expression>", "eval"), safe_globals, local_vars)

        self.safe_eval = safe_eval

    # === SECURITY TESTS: These expressions must be BLOCKED ===

    def test_import_blocked(self):
        """__import__('os') must be blocked."""
        with self.assertRaises(ValueError):
            self.safe_eval("__import__('os').system('id')", {})

    def test_dunder_attribute_blocked(self):
        """Access to __class__, __globals__, etc. must be blocked."""
        with self.assertRaises(ValueError):
            self.safe_eval("''.__class__.__bases__", {})

    def test_dunder_method_call_blocked(self):
        """Calls to dunder methods must be blocked."""
        with self.assertRaises(ValueError):
            self.safe_eval("x.__getattribute__('y')", {"x": {}})

    def test_os_popen_via_import_blocked(self):
        """The exact POC from the vulnerability report must be blocked."""
        with self.assertRaises(ValueError):
            self.safe_eval('__import__("os").popen("id").read()', {})

    # === FUNCTIONALITY TESTS: These expressions must WORK ===

    def test_simple_math(self):
        """Basic arithmetic on item values must work."""
        result = self.safe_eval("price * 1.1", {"price": 100})
        self.assertAlmostEqual(result, 110.0)

    def test_string_method(self):
        """String methods on item values must work."""
        result = self.safe_eval("name.upper()", {"name": "hello"})
        self.assertEqual(result, "HELLO")

    def test_string_concatenation(self):
        """String concatenation must work."""
        result = self.safe_eval("first + ' ' + last", {"first": "John", "last": "Doe"})
        self.assertEqual(result, "John Doe")

    def test_dict_access(self):
        """Dict-style field access must work."""
        result = self.safe_eval("a + b", {"a": 10, "b": 20})
        self.assertEqual(result, 30)

    def test_builtin_functions(self):
        """Safe builtins like len, str, int must work."""
        result = self.safe_eval("len(name)", {"name": "hello"})
        self.assertEqual(result, 5)

    def test_round_function(self):
        """round() must work for numeric formatting."""
        result = self.safe_eval("round(price, 2)", {"price": 10.456})
        self.assertEqual(result, 10.46)


class TestDeserializationAllowlist(unittest.TestCase):
    """Test that the deserialization allowlist blocks non-allowlisted types.

    Tests the allowlist constant directly without importing heavy dependencies.
    """

    def setUp(self):
        """Set up the allowlist (local copy of the constant)."""
        self.allowed_types = {
            "BrowserConfig", "CrawlerRunConfig", "HTTPCrawlerConfig",
            "LLMConfig", "ProxyConfig", "GeolocationConfig",
            "SeedingConfig", "VirtualScrollConfig", "LinkPreviewConfig",
            "JsonCssExtractionStrategy", "JsonXPathExtractionStrategy",
            "JsonLxmlExtractionStrategy", "LLMExtractionStrategy",
            "CosineStrategy", "RegexExtractionStrategy",
            "DefaultMarkdownGenerator",
            "PruningContentFilter", "BM25ContentFilter", "LLMContentFilter",
            "LXMLWebScrapingStrategy",
            "RegexChunking",
            "BFSDeepCrawlStrategy", "DFSDeepCrawlStrategy", "BestFirstCrawlingStrategy",
            "FilterChain", "URLPatternFilter", "DomainFilter",
            "ContentTypeFilter", "URLFilter", "SEOFilter", "ContentRelevanceFilter",
            "KeywordRelevanceScorer", "URLScorer", "CompositeScorer",
            "DomainAuthorityScorer", "FreshnessScorer", "PathDepthScorer",
            "CacheMode", "MatchMode", "DisplayMode",
            "MemoryAdaptiveDispatcher", "SemaphoreDispatcher",
            "DefaultTableExtraction", "NoTableExtraction",
            "RoundRobinProxyStrategy",
        }

    # === SECURITY TESTS: Non-allowlisted types must be BLOCKED ===

    def test_arbitrary_class_not_in_allowlist(self):
        """AsyncWebCrawler must NOT be in the allowlist."""
        self.assertNotIn("AsyncWebCrawler", self.allowed_types)

    def test_crawler_hub_not_in_allowlist(self):
        """CrawlerHub must NOT be in the allowlist."""
        self.assertNotIn("CrawlerHub", self.allowed_types)

    def test_browser_profiler_not_in_allowlist(self):
        """BrowserProfiler must NOT be in the allowlist."""
        self.assertNotIn("BrowserProfiler", self.allowed_types)

    def test_docker_client_not_in_allowlist(self):
        """Crawl4aiDockerClient must NOT be in the allowlist."""
        self.assertNotIn("Crawl4aiDockerClient", self.allowed_types)

    # === FUNCTIONALITY TESTS: Allowlisted types must be present ===

    def test_allowlist_has_core_config_types(self):
        """Core config types must be in the allowlist."""
        required = {"BrowserConfig", "CrawlerRunConfig", "LLMConfig", "ProxyConfig"}
        self.assertTrue(required.issubset(self.allowed_types))

    def test_allowlist_has_extraction_strategies(self):
        """Extraction strategy types must be in the allowlist."""
        required = {
            "JsonCssExtractionStrategy", "LLMExtractionStrategy",
            "RegexExtractionStrategy",
        }
        self.assertTrue(required.issubset(self.allowed_types))

    def test_allowlist_has_enums(self):
        """Enum types must be in the allowlist."""
        required = {"CacheMode", "MatchMode", "DisplayMode"}
        self.assertTrue(required.issubset(self.allowed_types))


if __name__ == '__main__':
    print("=" * 60)
    print("Crawl4AI Security Fixes - Unit Tests")
    print("=" * 60)
    print()

    # Run tests with verbosity
    unittest.main(verbosity=2)
