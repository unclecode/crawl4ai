#!/usr/bin/env python3
"""
Adversarial security tests for Batch 2 vulns reported 2026-04-14 (by111/August829).
Self-contained tests that verify fixes at the code/source level.

B2-V1: /execute_js disabled by default + SSRF block
B2-V2: Hardcoded JWT secret removed
B2-V3: eval() in /config/dump replaced with JSON
B2-V4: Hook sandbox __builtins__ escape fixed
"""

import os
import sys
import ast
import unittest
import builtins
import types
from unittest import mock

DEPLOY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


# ============================================================================
# B2-V2: Hardcoded JWT Secret
# ============================================================================

class TestJWTSecretHardened(unittest.TestCase):
    """Verify the hardcoded 'mysecret' default is gone from auth.py."""

    def test_no_mysecret_as_default(self):
        """auth.py must not use 'mysecret' as a fallback default for SECRET_KEY."""
        with open(os.path.join(DEPLOY_DIR, "auth.py")) as f:
            source = f.read()
        # The old dangerous pattern: os.environ.get("SECRET_KEY", "mysecret")
        self.assertNotIn('get("SECRET_KEY", "mysecret")', source,
            "auth.py must not use 'mysecret' as env var default")

    def test_weak_secret_validation_exists(self):
        """auth.py must reject weak and too-short SECRET_KEY values (behavioral)."""
        import importlib
        import sys
        sys.path.insert(0, DEPLOY_DIR)
        auth = importlib.import_module("auth")

        # A known-weak secret must be rejected.
        with mock.patch.dict(os.environ, {"SECRET_KEY": "mysecret"}):
            with self.assertRaises(RuntimeError):
                auth.resolve_secret_key(required=True)

        # A too-short secret (< 32 chars) must be rejected.
        with mock.patch.dict(os.environ, {"SECRET_KEY": "short"}):
            with self.assertRaises(RuntimeError):
                auth.resolve_secret_key(required=True)

        # A strong secret must be accepted and returned unchanged.
        strong = "a" * 32
        with mock.patch.dict(os.environ, {"SECRET_KEY": strong}):
            self.assertEqual(auth.resolve_secret_key(required=True), strong)

    def test_mysecret_in_weak_list(self):
        """'mysecret' must be in the weak secrets blocklist."""
        with open(os.path.join(DEPLOY_DIR, "auth.py")) as f:
            source = f.read()
        # Parse the source to find _WEAK_SECRETS set
        self.assertIn("mysecret", source,
            "'mysecret' must be listed in _WEAK_SECRETS blocklist")

    def test_auto_generation_exists(self):
        """auth.py must auto-generate key when none is set."""
        with open(os.path.join(DEPLOY_DIR, "auth.py")) as f:
            source = f.read()
        self.assertIn("token_hex", source,
            "auth.py must use secrets.token_hex for auto-generation")


# ============================================================================
# B2-V3: eval() removed from /config/dump
# ============================================================================

class TestConfigDumpNoEval(unittest.TestCase):
    """Verify eval() is completely removed from the /config/dump path."""

    def test_no_safe_eval_config(self):
        """_safe_eval_config function must be removed from server.py."""
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        self.assertNotIn("def _safe_eval_config", source,
            "_safe_eval_config must be deleted (replaced with JSON input)")

    def test_config_from_json_exists(self):
        """_config_from_json function must exist."""
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        self.assertIn("def _config_from_json", source,
            "_config_from_json must replace _safe_eval_config")

    def test_config_dump_has_auth(self):
        """config_dump endpoint must require authentication."""
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        # Find the config_dump function and check it has token_dep
        idx = source.index("config_dump")
        # Look backwards for the decorator/function definition area
        nearby = source[max(0, idx-200):idx+200]
        self.assertIn("token_dep", nearby,
            "/config/dump must require token_dep authentication")

    def test_no_eval_in_config_path(self):
        """No eval() call should exist in the config dump code path."""
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        # The old allowlist constants should be gone
        self.assertNotIn("_SAFE_CONFIG_ALLOWED_NAMES", source,
            "Old eval allowlist constants should be removed")
        self.assertNotIn("_SAFE_CONFIG_ALLOWED_ATTRS", source,
            "Old eval allowlist constants should be removed")


# ============================================================================
# B2-V1: /execute_js disabled by default
# ============================================================================

class TestExecuteJsDisabled(unittest.TestCase):
    """Verify /execute_js is disabled by default with proper guards."""

    def test_execute_js_flag_exists(self):
        """EXECUTE_JS_ENABLED flag must exist in server.py."""
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        self.assertIn("EXECUTE_JS_ENABLED", source)

    def test_execute_js_disabled_by_default(self):
        """EXECUTE_JS_ENABLED must default to false."""
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        # Find the line that sets EXECUTE_JS_ENABLED
        for line in source.splitlines():
            if "EXECUTE_JS_ENABLED" in line and "os.environ" in line:
                self.assertIn('"false"', line,
                    "EXECUTE_JS_ENABLED must default to 'false'")
                return
        self.fail("Could not find EXECUTE_JS_ENABLED env var line")

    def test_execute_js_checks_flag(self):
        """execute_js endpoint must check EXECUTE_JS_ENABLED."""
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        idx = source.index("async def execute_js")
        func_body = source[idx:idx+3000]
        self.assertIn("EXECUTE_JS_ENABLED", func_body,
            "execute_js must check EXECUTE_JS_ENABLED flag")

    def test_execute_js_has_ssrf_check(self):
        """execute_js must validate URL against SSRF blocklist."""
        with open(os.path.join(DEPLOY_DIR, "server.py")) as f:
            source = f.read()
        idx = source.index("async def execute_js")
        func_body = source[idx:idx+3000]
        self.assertIn("validate_webhook_url", func_body,
            "execute_js must validate URL against SSRF blocklist")

    def test_disable_web_security_removed_from_defaults(self):
        """--disable-web-security must not be in default browser args."""
        with open(os.path.join(DEPLOY_DIR, "utils.py")) as f:
            source = f.read()
        # Find the DEFAULT_CONFIG extra_args
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "--disable-web-security":
                self.fail("--disable-web-security must not be in DEFAULT_CONFIG extra_args")

    def test_disable_web_security_removed_from_config_yml(self):
        """--disable-web-security must not be active in config.yml."""
        with open(os.path.join(DEPLOY_DIR, "config.yml")) as f:
            for line in f:
                stripped = line.strip()
                if stripped == '- "--disable-web-security"':
                    self.fail("--disable-web-security must not be an active entry in config.yml")


# ============================================================================
# B2-V4: exec-based hook system removed (replaced by declarative registry)
# ============================================================================

class TestHookExecPathRemoved(unittest.TestCase):
    """The exec()/compile() hook system is gone; hooks are now declarative.

    No sandbox survives attacker Python in-process, so hook_manager.py was
    deleted and replaced by hook_registry.py (a fixed set of server-authored
    actions selected by name with schema-validated scalar params).
    """

    def test_hook_manager_module_deleted(self):
        self.assertFalse(
            os.path.exists(os.path.join(DEPLOY_DIR, "hook_manager.py")),
            "hook_manager.py (the exec-based hook system) must be deleted",
        )

    def test_no_exec_compile_eval_in_docker_layer(self):
        """The RCE primitives must be absent from the docker server code.

        Uses AST so it flags only bare-builtin calls (exec/eval/compile), not
        attribute calls like re.compile(...) or the words in comments/docstrings.
        """
        import ast
        import glob
        offenders = []
        for path in glob.glob(os.path.join(DEPLOY_DIR, "*.py")):
            with open(path) as f:
                tree = ast.parse(f.read(), filename=path)
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in {"exec", "eval", "compile"}
                ):
                    offenders.append((os.path.basename(path), node.func.id, node.lineno))
        self.assertEqual(offenders, [], f"bare exec/eval/compile call found: {offenders}")

    def test_registry_rejects_unknown_action(self):
        sys.path.insert(0, DEPLOY_DIR)
        from hook_registry import build_declarative_hooks, HookValidationError
        with self.assertRaises(HookValidationError):
            build_declarative_hooks([{"action": "run_python", "params": {"code": "x"}}])

    def test_registry_rejects_bad_params(self):
        sys.path.insert(0, DEPLOY_DIR)
        from hook_registry import build_declarative_hooks, HookValidationError
        with self.assertRaises(HookValidationError):
            build_declarative_hooks([{"action": "block_resources", "params": {"resource_types": ["script"]}}])

    def test_registry_builds_valid_hooks(self):
        sys.path.insert(0, DEPLOY_DIR)
        from hook_registry import build_declarative_hooks
        hooks = build_declarative_hooks([
            {"action": "block_resources", "params": {"resource_types": ["image"]}},
            {"action": "scroll_to_bottom", "params": {"max_steps": 5}},
        ])
        # block_resources -> on_page_context_created, scroll -> before_retrieve_html
        self.assertIn("on_page_context_created", hooks)
        self.assertIn("before_retrieve_html", hooks)
        for fn in hooks.values():
            self.assertTrue(callable(fn))


if __name__ == "__main__":
    unittest.main()
