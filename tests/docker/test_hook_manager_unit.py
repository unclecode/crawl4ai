"""
Unit tests for deploy/docker/hook_manager.py
Covers the __import__ removal fix (#1878) and adversarial edge cases.
"""

import asyncio
import pytest
import sys
import os

# Add deploy/docker to path so we can import hook_manager directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'deploy', 'docker'))
from hook_manager import UserHookManager, process_user_hooks


# ── helpers ──────────────────────────────────────────────────────────────

def compile_ok(mgr, code, hook_point="on_page_context_created"):
    """Compile hook, assert success, return the callable."""
    fn = mgr.compile_hook(code, hook_point)
    assert fn is not None, f"compile_hook returned None; errors: {mgr.errors}"
    return fn


def compile_fail(mgr, code, hook_point="on_page_context_created"):
    """Compile hook, assert failure."""
    fn = mgr.compile_hook(code, hook_point)
    assert fn is None, "Expected compile_hook to fail but it returned a callable"
    return mgr.errors[-1]


async def run_hook(fn, *args, **kwargs):
    """Execute compiled hook, return result."""
    return await fn(*args, **kwargs)


# ── Issue #1878: basic compilation after __import__ removal ──────────────

class TestIssue1878BasicCompilation:
    """The exact scenario from the bug report and close variations."""

    def test_simplest_hook_compiles(self):
        """Exact code from issue #1878."""
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    return page
"""
        fn = compile_ok(mgr, code)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))
        assert result == "PAGE"

    def test_hook_using_asyncio(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    await asyncio.sleep(0)
    return page
"""
        fn = compile_ok(mgr, code)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))
        assert result == "PAGE"

    def test_hook_using_json(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    data = json.dumps({"key": "value"})
    return page
"""
        fn = compile_ok(mgr, code)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))
        assert result == "PAGE"

    def test_hook_using_re(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    m = re.search(r'\\d+', 'abc123')
    return page
"""
        fn = compile_ok(mgr, code)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))
        assert result == "PAGE"

    def test_hook_using_typing(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    x: Dict[str, List[Optional[int]]] = {}
    return page
"""
        fn = compile_ok(mgr, code)

    def test_all_hook_points_compile(self):
        """Every valid hook point should compile a trivial hook."""
        for hook_point, params in UserHookManager.HOOK_SIGNATURES.items():
            mgr = UserHookManager()
            param_str = ", ".join(params) + ", **kwargs"
            code = f"""
async def hook({param_str}):
    return {params[0]}
"""
            fn = compile_ok(mgr, code, hook_point)
            assert asyncio.iscoroutinefunction(fn)


# ── Security: __import__ and import statements blocked at runtime ────────

class TestSecurityImportBlocked:

    def test_import_statement_blocked_at_runtime(self):
        """import os inside hook body must fail at runtime."""
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    import os
    return page
"""
        fn = compile_ok(mgr, code)  # compiles (body not executed yet)
        with pytest.raises(ImportError):
            asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))

    def test_dunder_import_blocked_at_runtime(self):
        """__import__('os') must fail at runtime."""
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    os = __import__('os')
    return page
"""
        fn = compile_ok(mgr, code)
        with pytest.raises(NameError):
            asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))

    def test_builtins_import_via_getattr_blocked(self):
        """Trying to fish __import__ from builtins dict should fail."""
        mgr = UserHookManager()
        # __builtins__ is our restricted dict, no __import__ key
        code = """
async def hook(page, context, **kwargs):
    imp = __builtins__['__import__']
    return page
"""
        fn = compile_ok(mgr, code)
        with pytest.raises(KeyError):
            asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))

    def test_exec_inside_hook_cannot_import(self):
        """exec() is not in safe builtins, so nested exec should fail."""
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    exec('import os')
    return page
"""
        fn = compile_ok(mgr, code)
        with pytest.raises(NameError):
            asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))

    def test_eval_not_available(self):
        """eval() should not be in safe builtins."""
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    eval('1+1')
    return page
"""
        fn = compile_ok(mgr, code)
        with pytest.raises(NameError):
            asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))

    def test_open_not_available(self):
        """open() should not be in safe builtins."""
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    f = open('/etc/passwd')
    return page
"""
        fn = compile_ok(mgr, code)
        with pytest.raises(NameError):
            asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))


# ── Validation edge cases ────────────────────────────────────────────────

class TestValidation:

    def test_empty_code(self):
        mgr = UserHookManager()
        ok, msg = mgr.validate_hook_structure("", "on_page_context_created")
        assert not ok

    def test_sync_function_rejected(self):
        mgr = UserHookManager()
        code = """
def hook(page, context, **kwargs):
    return page
"""
        ok, msg = mgr.validate_hook_structure(code, "on_page_context_created")
        assert not ok
        assert "async" in msg.lower()

    def test_missing_params_rejected(self):
        mgr = UserHookManager()
        code = """
async def hook():
    return None
"""
        ok, msg = mgr.validate_hook_structure(code, "on_page_context_created")
        assert not ok
        assert "missing" in msg.lower() or "parameter" in msg.lower()

    def test_syntax_error_rejected(self):
        mgr = UserHookManager()
        code = "async def hook(page, context, **kwargs):\n    return page @@@ bad"
        ok, msg = mgr.validate_hook_structure(code, "on_page_context_created")
        assert not ok

    def test_unknown_hook_point_rejected(self):
        mgr = UserHookManager()
        code = """
async def hook(page, **kwargs):
    return page
"""
        ok, msg = mgr.validate_hook_structure(code, "nonexistent_hook_point")
        assert not ok

    def test_no_function_def(self):
        mgr = UserHookManager()
        code = "x = 42"
        ok, msg = mgr.validate_hook_structure(code, "on_page_context_created")
        assert not ok


# ── Adversarial: things that should not crash the manager ────────────────

class TestAdversarial:

    def test_infinite_loop_times_out(self):
        """Hook with infinite loop should time out, not hang."""
        mgr = UserHookManager(timeout=1)
        code = """
async def hook(page, context, **kwargs):
    while True:
        await asyncio.sleep(0.01)
    return page
"""
        fn = compile_ok(mgr, code)
        result, error = asyncio.get_event_loop().run_until_complete(
            mgr.execute_hook_safely(fn, "on_page_context_created", "PAGE", "CTX")
        )
        assert error is not None
        assert error['type'] == 'timeout'

    def test_exception_in_hook_captured(self):
        """Exceptions in user code should be captured, not propagated."""
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    raise ValueError("user bug")
"""
        fn = compile_ok(mgr, code)
        result, error = asyncio.get_event_loop().run_until_complete(
            mgr.execute_hook_safely(fn, "on_page_context_created", "PAGE", "CTX")
        )
        assert error is not None
        assert "user bug" in error['error']
        # Should return the first arg (page) as fallback
        assert result == "PAGE"

    def test_very_large_code_string(self):
        """Large but valid code should compile without crashing."""
        mgr = UserHookManager()
        # 10k lines of assignments
        lines = [f"    x{i} = {i}" for i in range(10_000)]
        code = "async def hook(page, context, **kwargs):\n" + "\n".join(lines) + "\n    return page\n"
        fn = compile_ok(mgr, code)

    def test_unicode_in_hook(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    msg = "日本語テスト 🚀"
    return page
"""
        fn = compile_ok(mgr, code)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn, "PAGE", "CTX"))
        assert result == "PAGE"

    def test_none_return_handled(self):
        """Hook returning None should not crash execute_hook_safely."""
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    pass
"""
        fn = compile_ok(mgr, code)
        result, error = asyncio.get_event_loop().run_until_complete(
            mgr.execute_hook_safely(fn, "on_page_context_created", "PAGE", "CTX")
        )
        assert error is None
        # None is a valid return
        assert result is None

    def test_hook_modifying_namespace_modules(self):
        """Hook reassigning json/re in its scope should not affect other hooks."""
        mgr = UserHookManager()
        code1 = """
async def hook(page, context, **kwargs):
    json = "overwritten"
    return page
"""
        code2 = """
async def hook(page, context, **kwargs):
    data = json.dumps({"still": "works"})
    return page
"""
        compile_ok(mgr, code1)
        fn2 = compile_ok(mgr, code2)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn2, "PAGE", "CTX"))
        assert result == "PAGE"

    def test_multiple_functions_picks_async(self):
        """When code defines multiple functions, should pick the async one."""
        mgr = UserHookManager()
        code = """
def helper():
    return 42

async def hook(page, context, **kwargs):
    return page
"""
        fn = compile_ok(mgr, code)
        assert asyncio.iscoroutinefunction(fn)


# ── process_user_hooks integration ───────────────────────────────────────

class TestProcessUserHooks:

    def test_valid_hooks_processed(self):
        hooks_input = {
            "on_page_context_created": """
async def hook(page, context, **kwargs):
    return page
""",
            "before_goto": """
async def hook(page, context, url, **kwargs):
    return page
""",
        }
        compiled, errors, mgr = asyncio.get_event_loop().run_until_complete(
            process_user_hooks(hooks_input)
        )
        assert len(errors) == 0
        assert len(compiled) == 2
        assert "on_page_context_created" in compiled
        assert "before_goto" in compiled

    def test_mix_valid_and_invalid(self):
        hooks_input = {
            "on_page_context_created": """
async def hook(page, context, **kwargs):
    return page
""",
            "fake_hook_point": """
async def hook(**kwargs):
    pass
""",
        }
        compiled, errors, mgr = asyncio.get_event_loop().run_until_complete(
            process_user_hooks(hooks_input)
        )
        assert len(compiled) == 1
        assert len(errors) == 1
        assert errors[0]['hook_point'] == 'fake_hook_point'

    def test_empty_code_skipped(self):
        hooks_input = {
            "on_page_context_created": "",
            "before_goto": "   ",
        }
        compiled, errors, mgr = asyncio.get_event_loop().run_until_complete(
            process_user_hooks(hooks_input)
        )
        assert len(compiled) == 0
        assert len(errors) == 0


# ── Builtins availability ────────────────────────────────────────────────

class TestBuiltinsAvailable:
    """Verify allowed builtins actually work inside hooks."""

    def test_len_str_int(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    assert len("abc") == 3
    assert str(42) == "42"
    assert int("7") == 7
    return page
"""
        fn = compile_ok(mgr, code)
        asyncio.get_event_loop().run_until_complete(run_hook(fn, "P", "C"))

    def test_list_dict_operations(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    items = list(range(5))
    d = dict(a=1, b=2)
    assert len(items) == 5
    assert d['a'] == 1
    return page
"""
        fn = compile_ok(mgr, code)
        asyncio.get_event_loop().run_until_complete(run_hook(fn, "P", "C"))

    def test_isinstance_type(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    assert isinstance("hello", str)
    assert type(42) == int
    return page
"""
        fn = compile_ok(mgr, code)
        asyncio.get_event_loop().run_until_complete(run_hook(fn, "P", "C"))


# ── Exception classes available in hooks ─────────────────────────────────

class TestExceptionClassesAvailable:
    """Exception classes should be usable inside hooks for proper error handling."""

    def test_raise_and_catch_value_error(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    try:
        raise ValueError("bad value")
    except ValueError:
        pass
    return page
"""
        fn = compile_ok(mgr, code)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn, "P", "C"))
        assert result == "P"

    def test_raise_and_catch_key_error(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    try:
        raise KeyError("missing")
    except KeyError:
        pass
    return page
"""
        fn = compile_ok(mgr, code)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn, "P", "C"))
        assert result == "P"

    def test_catch_broad_exception(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    try:
        x = 1 / 0
    except Exception as e:
        pass
    return page
"""
        fn = compile_ok(mgr, code)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn, "P", "C"))
        assert result == "P"

    def test_isinstance_check_on_exceptions(self):
        mgr = UserHookManager()
        code = """
async def hook(page, context, **kwargs):
    try:
        raise TypeError("wrong type")
    except Exception as e:
        assert isinstance(e, TypeError)
    return page
"""
        fn = compile_ok(mgr, code)
        result = asyncio.get_event_loop().run_until_complete(run_hook(fn, "P", "C"))
        assert result == "P"

    def test_all_exception_classes_accessible(self):
        """Every exception class in allowed_builtins should be reachable."""
        # BaseException excluded: it bypasses except Exception (by design)
        exception_names = [
            'Exception', 'ValueError', 'TypeError',
            'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
            'StopIteration', 'NotImplementedError', 'ZeroDivisionError',
            'OSError', 'IOError', 'TimeoutError', 'ConnectionError',
        ]
        for exc_name in exception_names:
            mgr = UserHookManager()
            code = f"""
async def hook(page, context, **kwargs):
    raise {exc_name}("test")
"""
            fn = compile_ok(mgr, code)
            result, error = asyncio.get_event_loop().run_until_complete(
                mgr.execute_hook_safely(fn, "on_page_context_created", "P", "C")
            )
            assert error is not None, f"{exc_name} did not raise"
            # StopIteration gets wrapped by asyncio into RuntimeError
            if exc_name == 'StopIteration':
                assert "StopIteration" in error['error']
            else:
                assert "test" in error['error'], f"{exc_name} message lost"
