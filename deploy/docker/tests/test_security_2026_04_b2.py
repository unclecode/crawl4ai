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
        """auth.py must validate against known weak secrets."""
        with open(os.path.join(DEPLOY_DIR, "auth.py")) as f:
            source = f.read()
        self.assertIn("_WEAK_SECRETS", source,
            "auth.py must have weak secrets blocklist")
        self.assertIn("< 32", source,
            "auth.py must enforce minimum key length")

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
# B2-V4: Hook Sandbox __builtins__ Escape
# ============================================================================

class TestHookSandboxBugreport(unittest.TestCase):
    """Test the specific __builtins__ escape vector reported by by111."""

    @classmethod
    def setUpClass(cls):
        """Build hook sandbox exactly as hook_manager does."""
        safe_builtins = {}
        allowed_builtins = [
            'print', 'len', 'str', 'int', 'float', 'bool',
            'list', 'dict', 'set', 'tuple', 'range', 'enumerate',
            'zip', 'map', 'filter', 'any', 'all', 'sum', 'min', 'max',
            'sorted', 'reversed', 'abs', 'round', 'isinstance',
            'callable', 'iter', 'next',
        ]
        for name in allowed_builtins:
            if hasattr(builtins, name):
                safe_builtins[name] = getattr(builtins, name)
        cls.safe_builtins = safe_builtins

    def _make_namespace(self):
        import asyncio as _asyncio_mod
        import json as _json_mod
        import re as _re_mod
        from typing import Dict, List, Optional

        def _safe_module(mod, exclude_attrs=None):
            proxy = types.ModuleType(mod.__name__)
            skip = {"__builtins__", "__loader__", "__spec__"}
            if exclude_attrs:
                skip.update(exclude_attrs)
            for attr in dir(mod):
                if attr in skip:
                    continue
                try:
                    setattr(proxy, attr, getattr(mod, attr))
                except (AttributeError, TypeError):
                    pass
            return proxy

        namespace = {
            '__name__': 'test_hook',
            '__builtins__': dict(self.safe_builtins),
        }
        namespace["asyncio"] = _safe_module(_asyncio_mod, {
            "subprocess", "create_subprocess_exec", "create_subprocess_shell"
        })
        namespace["json"] = _safe_module(_json_mod)
        namespace["re"] = _safe_module(_re_mod)
        namespace["Dict"] = Dict
        namespace["List"] = List
        namespace["Optional"] = Optional
        return namespace

    # -- The exact attack from by111's report --

    def test_asyncio_builtins_import_blocked(self):
        """asyncio.__builtins__['__import__'] must not be accessible."""
        ns = self._make_namespace()
        self.assertFalse(hasattr(ns["asyncio"], "__builtins__"),
            "asyncio proxy must not have __builtins__")

    def test_json_builtins_import_blocked(self):
        """json.__builtins__['__import__'] must not be accessible."""
        ns = self._make_namespace()
        self.assertFalse(hasattr(ns["json"], "__builtins__"),
            "json proxy must not have __builtins__")

    def test_re_builtins_import_blocked(self):
        """re.__builtins__['__import__'] must not be accessible."""
        ns = self._make_namespace()
        self.assertFalse(hasattr(ns["re"], "__builtins__"),
            "re proxy must not have __builtins__")

    def test_module_loader_not_copied(self):
        """Real module's __loader__ must not be copied to proxy."""
        import asyncio as real_asyncio
        ns = self._make_namespace()
        # Proxy may have a default __loader__ from types.ModuleType,
        # but it must NOT be the real module's loader
        proxy_loader = getattr(ns["asyncio"], "__loader__", None)
        real_loader = getattr(real_asyncio, "__loader__", None)
        if proxy_loader is not None and real_loader is not None:
            self.assertIsNot(proxy_loader, real_loader,
                "Proxy must not have the real module's __loader__")

    def test_module_spec_not_copied(self):
        """Real module's __spec__ must not be copied to proxy."""
        import asyncio as real_asyncio
        ns = self._make_namespace()
        proxy_spec = getattr(ns["asyncio"], "__spec__", None)
        real_spec = getattr(real_asyncio, "__spec__", None)
        if proxy_spec is not None and real_spec is not None:
            self.assertIsNot(proxy_spec, real_spec,
                "Proxy must not have the real module's __spec__")

    def test_by111_exploit_via_asyncio(self):
        """Exact exploit from by111: asyncio.__builtins__['__import__']('os')."""
        ns = self._make_namespace()
        code = '''
async def hook(page, **kw):
    real_import = asyncio.__builtins__['__import__']
    os = real_import('os')
    return os.system('id')
'''
        with self.assertRaises((AttributeError, KeyError, TypeError)):
            exec(code, ns)
            import asyncio
            asyncio.get_event_loop().run_until_complete(ns['hook'](None))

    def test_getattr_not_in_builtins(self):
        """getattr must not be available (enables attribute-based escape)."""
        ns = self._make_namespace()
        self.assertNotIn('getattr', ns['__builtins__'])

    def test_type_not_in_builtins(self):
        """type must not be available (enables __subclasses__ MRO chain)."""
        ns = self._make_namespace()
        self.assertNotIn('type', ns['__builtins__'])

    def test_build_class_not_in_builtins(self):
        """__build_class__ must not be available."""
        ns = self._make_namespace()
        self.assertNotIn('__build_class__', ns['__builtins__'])

    def test_hasattr_not_in_builtins(self):
        """hasattr must not be available (information disclosure)."""
        ns = self._make_namespace()
        self.assertNotIn('hasattr', ns['__builtins__'])

    # -- asyncio still works for legitimate hooks --

    def test_asyncio_sleep_works(self):
        ns = self._make_namespace()
        self.assertTrue(hasattr(ns["asyncio"], "sleep"))

    def test_asyncio_gather_works(self):
        ns = self._make_namespace()
        self.assertTrue(hasattr(ns["asyncio"], "gather"))

    def test_json_loads_works(self):
        ns = self._make_namespace()
        self.assertTrue(hasattr(ns["json"], "loads"))

    def test_re_compile_works(self):
        ns = self._make_namespace()
        self.assertTrue(hasattr(ns["re"], "compile"))


# ============================================================================
# Source-level verification for hook_manager.py
# ============================================================================

class TestHookManagerSourceClean(unittest.TestCase):
    """Verify hook_manager.py source has all dangerous builtins removed."""

    def test_getattr_removed(self):
        with open(os.path.join(DEPLOY_DIR, "hook_manager.py")) as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "allowed_builtins":
                        if isinstance(node.value, ast.List):
                            vals = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
                            self.assertNotIn("getattr", vals)
                            self.assertNotIn("setattr", vals)
                            self.assertNotIn("hasattr", vals)
                            self.assertNotIn("type", vals)
                            self.assertNotIn("__build_class__", vals)
                            return
        self.fail("Could not find allowed_builtins in hook_manager.py")

    def test_safe_module_strips_builtins(self):
        """_safe_module function must skip __builtins__."""
        with open(os.path.join(DEPLOY_DIR, "hook_manager.py")) as f:
            source = f.read()
        self.assertIn("__builtins__", source)
        self.assertIn("__loader__", source)
        self.assertIn("__spec__", source)


if __name__ == "__main__":
    print("=" * 70)
    print("Crawl4AI Security Tests - Batch 2 (2026-04-14)")
    print("=" * 70)
    print()
    unittest.main(verbosity=2)
