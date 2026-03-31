#!/usr/bin/env python3
"""
Adversarial security tests for all eval/exec paths in crawl4ai.

Tests three attack surfaces:
1. _compute_field expression path (extraction_strategy.py) - MUST be fully disabled
2. _safe_eval_config (deploy/docker/server.py) - MUST block all escapes
3. hook_manager exec (deploy/docker/hook_manager.py) - MUST restrict builtins

Each section tries progressively creative bypass techniques.
"""

import ast
import sys
import os
import unittest
import logging

# Ensure crawl4ai is importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deploy", "docker"))


# ============================================================================
# PART 1: _compute_field expression path - MUST BE COMPLETELY DEAD
# ============================================================================

class TestComputeFieldExpressionKilled(unittest.TestCase):
    """The expression key in computed fields must NEVER evaluate anything.
    It should log a warning and return default. Period."""

    @classmethod
    def setUpClass(cls):
        from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
        schema = {"baseSelector": "div", "fields": [
            {"name": "x", "selector": "span", "type": "text"}
        ]}
        cls.strategy = JsonCssExtractionStrategy(schema)

    def _try_expression(self, expr, item=None, default="BLOCKED"):
        """Helper: run expression through _compute_field, expect default back."""
        field = {"name": "test", "type": "computed", "expression": expr, "default": default}
        return self.strategy._compute_field(item or {}, field)

    # -- Basic RCE attempts --

    def test_import_os_system(self):
        self.assertEqual(self._try_expression("__import__('os').system('id')"), "BLOCKED")

    def test_import_subprocess(self):
        self.assertEqual(self._try_expression("__import__('subprocess').check_output('id', shell=True)"), "BLOCKED")

    def test_open_etc_passwd(self):
        self.assertEqual(self._try_expression("open('/etc/passwd').read()"), "BLOCKED")

    def test_eval_inside_eval(self):
        self.assertEqual(self._try_expression("eval('__import__(\"os\").system(\"id\")')"), "BLOCKED")

    def test_exec_code(self):
        self.assertEqual(self._try_expression("exec('import os; os.system(\"id\")')"), "BLOCKED")

    # -- The original vuln report exploit --

    def test_original_exploit_payload(self):
        """Exact payload from the vulnerability report."""
        payload = (
            "(lambda: (g := (f := type(type).mro).__func__.__globals__), "
            "g['__builtins__']['__import__']('os').popen('id').read()))()"
        )
        self.assertEqual(self._try_expression(payload), "BLOCKED")

    # -- Frame/generator traversal --

    def test_gi_frame(self):
        self.assertEqual(self._try_expression("(x for x in [1]).gi_frame.f_builtins['__import__']('os')"), "BLOCKED")

    def test_f_back(self):
        self.assertEqual(self._try_expression("(x for x in [1]).gi_frame.f_back.f_builtins"), "BLOCKED")

    def test_cr_frame(self):
        self.assertEqual(self._try_expression("x.cr_frame.f_globals"), "BLOCKED")

    # -- Dunder traversal --

    def test_class_bases_subclasses(self):
        self.assertEqual(self._try_expression("().__class__.__bases__[0].__subclasses__()"), "BLOCKED")

    def test_class_mro(self):
        self.assertEqual(self._try_expression("''.__class__.__mro__[1].__subclasses__()"), "BLOCKED")

    def test_globals_access(self):
        self.assertEqual(self._try_expression("(lambda: 0).__globals__"), "BLOCKED")

    def test_init_globals(self):
        self.assertEqual(self._try_expression("''.__class__.__init__.__globals__"), "BLOCKED")

    # -- Format string bypass (the one I flagged) --

    def test_format_string_dunder_access(self):
        """Format strings bypass AST attribute checks - dunder access happens at runtime."""
        self.assertEqual(
            self._try_expression("'{0.__class__.__init__.__globals__}'.format('')"),
            "BLOCKED"
        )

    def test_fstring_dunder_access(self):
        self.assertEqual(
            self._try_expression("f'{\"\".__class__.__init__.__globals__}'"),
            "BLOCKED"
        )

    # -- Lambda/generator tricks --

    def test_lambda_exec(self):
        self.assertEqual(self._try_expression("(lambda: exec('import os'))()"), "BLOCKED")

    def test_generator_with_side_effects(self):
        self.assertEqual(self._try_expression("list(x for x in __import__('os').listdir('/'))"), "BLOCKED")

    def test_nested_lambda(self):
        self.assertEqual(self._try_expression("(lambda f: f(f))(lambda f: 'pwned')"), "BLOCKED")

    # -- Comprehension tricks --

    def test_listcomp_with_import(self):
        self.assertEqual(self._try_expression("[__import__('os') for _ in [1]]"), "BLOCKED")

    def test_dictcomp_with_import(self):
        self.assertEqual(self._try_expression("{k: __import__('os') for k in [1]}"), "BLOCKED")

    def test_setcomp_with_import(self):
        self.assertEqual(self._try_expression("{__import__('os') for _ in [1]}"), "BLOCKED")

    # -- Indirect access --

    def test_getattr_bypass(self):
        self.assertEqual(self._try_expression("getattr(getattr('', '__class__'), '__bases__')"), "BLOCKED")

    def test_vars_bypass(self):
        self.assertEqual(self._try_expression("vars()"), "BLOCKED")

    def test_dir_probe(self):
        self.assertEqual(self._try_expression("dir(__builtins__)"), "BLOCKED")

    def test_type_call(self):
        self.assertEqual(self._try_expression("type.__bases__[0].__subclasses__()"), "BLOCKED")

    # -- Benign expressions also return default (expression is fully disabled) --

    def test_simple_math_also_disabled(self):
        """Even harmless math must return default - no eval at all."""
        self.assertEqual(self._try_expression("price * 2", {"price": 100}), "BLOCKED")

    def test_string_method_also_disabled(self):
        self.assertEqual(self._try_expression("name.upper()", {"name": "test"}), "BLOCKED")

    def test_string_concat_also_disabled(self):
        self.assertEqual(self._try_expression("a + b", {"a": "hello", "b": "world"}), "BLOCKED")

    # -- Verify function key still works --

    def test_function_key_works(self):
        field = {"name": "test", "type": "computed", "function": lambda item: item["x"] * 3}
        result = self.strategy._compute_field({"x": 10}, field)
        self.assertEqual(result, 30)

    def test_function_key_with_complex_logic(self):
        def compute(item):
            return f"{item['first']} {item['last']}".upper()
        field = {"name": "test", "type": "computed", "function": compute}
        result = self.strategy._compute_field({"first": "John", "last": "Doe"}, field)
        self.assertEqual(result, "JOHN DOE")


# ============================================================================
# PART 2: _safe_eval_config - server.py config deserializer
# ============================================================================

class TestSafeEvalConfigAdversarial(unittest.TestCase):
    """Attack the server.py _safe_eval_config AST validation logic.
    Self-contained: copies the validation logic to avoid needing FastAPI/Redis.
    Must allow CrawlerRunConfig(...) / BrowserConfig(...) but block everything else."""

    @classmethod
    def setUpClass(cls):
        import crawl4ai as _c4
        from crawl4ai import CrawlerRunConfig, BrowserConfig

        _SAFE_CONFIG_ALLOWED_NAMES = {
            "CrawlerRunConfig", "BrowserConfig", "HTTPCrawlerConfig",
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

        _SAFE_CONFIG_ALLOWED_ATTRS = frozenset({
            "BYPASS", "READ_ONLY", "WRITE_ONLY", "ENABLED", "DISABLED",
            "READ_WRITE", "BYPASS_CACHE", "STANDARD", "COMPACT", "DETAILED",
            "value", "name",
        })

        def safe_eval_config(expr):
            tree = ast.parse(expr, mode="eval")
            if not isinstance(tree.body, ast.Call):
                raise ValueError("Expression must be a single constructor call")
            call = tree.body
            if not (isinstance(call.func, ast.Name) and call.func.id in {"CrawlerRunConfig", "BrowserConfig"}):
                raise ValueError("Only CrawlerRunConfig(...) or BrowserConfig(...) are allowed")
            for node in ast.walk(call):
                if isinstance(node, ast.Call) and node is not call:
                    raise ValueError("Nested function calls are not permitted")
                if isinstance(node, ast.Lambda):
                    raise ValueError("Lambda expressions are not permitted")
                if isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)):
                    raise ValueError("Comprehensions and generators are not permitted")
                if isinstance(node, ast.Attribute):
                    if node.attr not in _SAFE_CONFIG_ALLOWED_ATTRS:
                        raise ValueError(f"Attribute access '{node.attr}' is not permitted")
                if isinstance(node, ast.Name) and node.id not in _SAFE_CONFIG_ALLOWED_NAMES:
                    if node.id not in {"True", "False", "None"}:
                        raise ValueError(f"Name '{node.id}' is not permitted")
            safe_env = {}
            for name in _SAFE_CONFIG_ALLOWED_NAMES:
                obj = getattr(_c4, name, None)
                if obj is not None:
                    safe_env[name] = obj
            safe_env.update({"True": True, "False": False, "None": None})
            obj = eval(compile(tree, "<config>", "eval"), {"__builtins__": {}}, safe_env)
            return obj.dump()

        cls.safe_eval_config = staticmethod(safe_eval_config)

    # -- Must work: legitimate config --

    def test_basic_crawler_run_config(self):
        result = self.safe_eval_config("CrawlerRunConfig()")
        self.assertIsInstance(result, dict)

    def test_basic_browser_config(self):
        result = self.safe_eval_config("BrowserConfig()")
        self.assertIsInstance(result, dict)

    def test_config_with_simple_args(self):
        result = self.safe_eval_config("BrowserConfig(headless=True)")
        self.assertIsInstance(result, dict)

    def test_config_with_string_args(self):
        result = self.safe_eval_config('CrawlerRunConfig(wait_until="load")')
        self.assertIsInstance(result, dict)

    # -- Must block: not a config constructor --

    def test_arbitrary_function_call(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("print('hello')")

    def test_import_call(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("__import__('os')")

    def test_bare_expression(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("1 + 1")

    def test_eval_call(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("eval('1+1')")

    # -- Must block: nested function calls --

    def test_nested_import_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=__import__('os').popen('id').read())")

    def test_nested_eval_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=eval('bad'))")

    def test_nested_open_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=open('/etc/passwd').read())")

    # -- Must block: lambda/generator in args --

    def test_lambda_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=lambda: __import__('os'))")

    def test_generator_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=(x for x in [1]))")

    def test_listcomp_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=[x for x in [1]])")

    def test_dictcomp_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code={x: 1 for x in [1]})")

    def test_setcomp_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code={x for x in [1]})")

    # -- Must block: attribute traversal attacks --

    def test_dunder_class_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=''.__class__)")

    def test_dunder_globals_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=''.__class__.__init__.__globals__)")

    def test_dunder_bases_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=().__class__.__bases__)")

    def test_gi_frame_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=x.gi_frame)")

    def test_f_builtins_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=x.f_builtins)")

    def test_f_back_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=x.f_back)")

    def test_f_globals_in_args(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=x.f_globals)")

    # -- Must block: name references to non-allowlisted objects --

    def test_os_name_ref(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=os)")

    def test_sys_name_ref(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=sys)")

    def test_builtins_name_ref(self):
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code=__builtins__)")

    # -- Must block: string-based escapes --

    def test_format_string_dunder(self):
        """Format strings evaluated at runtime - blocked because format() is a nested call."""
        with self.assertRaises(ValueError):
            self.safe_eval_config("CrawlerRunConfig(js_code='{0.__class__}'.format(''))")

    # -- Must block: walrus operator / assignment --

    def test_walrus_operator(self):
        with self.assertRaises((ValueError, SyntaxError)):
            self.safe_eval_config("CrawlerRunConfig(js_code=(x := __import__('os')))")


# ============================================================================
# PART 3: _safe_eval_expression function (still exists but unused from compute_field)
# Verify it still has blocklist protections in case anyone calls it directly
# ============================================================================

class TestSafeEvalExpressionFunction(unittest.TestCase):
    """Test the _safe_eval_expression function directly.
    Even though _compute_field no longer calls it, the function still exists
    and should still block dangerous patterns if called."""

    @classmethod
    def setUpClass(cls):
        from crawl4ai.extraction_strategy import _safe_eval_expression
        cls.safe_eval = staticmethod(_safe_eval_expression)

    # -- Must block --

    def test_import_blocked(self):
        with self.assertRaises(ValueError):
            self.safe_eval("__import__('os').system('id')", {})

    def test_dunder_attribute_blocked(self):
        with self.assertRaises(ValueError):
            self.safe_eval("''.__class__.__bases__", {})

    def test_dunder_method_call_blocked(self):
        with self.assertRaises(ValueError):
            self.safe_eval("x.__getattribute__('y')", {"x": {}})

    def test_private_attribute_blocked(self):
        with self.assertRaises(ValueError):
            self.safe_eval("x._private_method()", {"x": {}})

    # -- Must work --

    def test_simple_math(self):
        self.assertAlmostEqual(self.safe_eval("price * 1.1", {"price": 100}), 110.0)

    def test_string_method(self):
        self.assertEqual(self.safe_eval("name.upper()", {"name": "hello"}), "HELLO")

    def test_builtin_len(self):
        self.assertEqual(self.safe_eval("len(name)", {"name": "hello"}), 5)


# ============================================================================
# PART 4: hook_manager builtins - verify getattr/setattr are gone
# ============================================================================

class TestHookManagerBuiltins(unittest.TestCase):
    """Verify hook_manager no longer provides getattr/setattr."""

    def test_getattr_removed_from_source(self):
        """Read hook_manager.py and verify getattr not in allowed_builtins."""
        hook_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..",
            "deploy", "docker", "hook_manager.py"
        )
        with open(hook_path, "r") as f:
            source = f.read()

        # Parse the source and find the allowed_builtins list
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "allowed_builtins":
                        if isinstance(node.value, ast.List):
                            values = [
                                elt.value for elt in node.value.elts
                                if isinstance(elt, ast.Constant)
                            ]
                            self.assertNotIn("getattr", values,
                                "getattr must not be in hook allowed_builtins (sandbox escape)")
                            self.assertNotIn("setattr", values,
                                "setattr must not be in hook allowed_builtins (sandbox escape)")
                            self.assertIn("hasattr", values,
                                "hasattr should remain (read-only, safe)")
                            return

        self.fail("Could not find allowed_builtins in hook_manager.py")


# ============================================================================
# PART 5: Meta-checks - verify no unprotected eval/exec paths exist
# ============================================================================

class TestNoUnprotectedEval(unittest.TestCase):
    """Scan the codebase for eval/exec calls to catch regressions."""

    def _scan_python_files(self, directory, exclude_dirs=None):
        """Find all eval()/exec() calls in Python files."""
        exclude_dirs = exclude_dirs or {"__pycache__", ".git", "node_modules", "venv", ".venv"}
        hits = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath) as f:
                        source = f.read()
                    tree = ast.parse(source, filename=fpath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            func = node.func
                            if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
                                hits.append((fpath, node.lineno, func.id))
                except (SyntaxError, UnicodeDecodeError):
                    continue
        return hits

    def test_all_eval_exec_are_known(self):
        """Every eval/exec in the repo must be in the known-safe list."""
        repo_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

        # Known, audited locations (file suffix, line range, call type)
        known_safe = {
            # extraction_strategy.py _safe_eval_expression - blocklisted, no longer called from untrusted path
            ("crawl4ai/extraction_strategy.py", "eval"),
            # server.py _safe_eval_config - hardened with allowlist
            ("deploy/docker/server.py", "eval"),
            # hook_manager.py - restricted namespace, hooks gated behind env var
            ("deploy/docker/hook_manager.py", "exec"),
            # test files are fine
        }

        hits = self._scan_python_files(repo_root)
        unknown = []
        for fpath, lineno, call_type in hits:
            rel = os.path.relpath(fpath, repo_root)
            # Skip test files
            if "test" in rel.lower():
                continue
            # Check if known
            is_known = any(
                rel.replace("\\", "/").endswith(known_file) and call_type == known_call
                for known_file, known_call in known_safe
            )
            if not is_known:
                unknown.append(f"  {rel}:{lineno} - {call_type}()")

        if unknown:
            self.fail(
                f"Found {len(unknown)} unknown eval/exec call(s):\n"
                + "\n".join(unknown)
                + "\n\nAudit these and add to known_safe if they are properly protected."
            )


if __name__ == "__main__":
    print("=" * 70)
    print("Crawl4AI Adversarial Security Tests")
    print("=" * 70)
    print()
    unittest.main(verbosity=2)
