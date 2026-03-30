"""
Tests for _safe_eval_expression sandbox hardening.

Covers:
- The reported gi_frame.f_back RCE exploit (and variants)
- Other sandbox escape vectors (frame walking, builtins access, import tricks)
- Legitimate computed field expressions that must continue to work
- Edge cases (empty strings, nested access, chained methods, unicode, etc.)
"""

import pytest

from crawl4ai.extraction_strategy import _safe_eval_expression


# ---------------------------------------------------------------------------
# 1. SECURITY: Block the reported exploit and variants
# ---------------------------------------------------------------------------

class TestBlockReportedExploit:
    """The exact exploit from the vulnerability report and close variants."""

    def test_full_exploit_expression(self):
        """The exact payload from the security report must be blocked."""
        exploit = (
            "(lambda r: ["
            "dict.update(r, {"
            "'g': ("
            "dict.update(r, {'f': r['g'].gi_frame.f_back}) or 0 "
            "for x in range(1)"
            ")"
            "}),"
            "list(r['g']),"
            "(lambda w, f: w(w, f))("
            "lambda s, f: "
            "f.f_builtins['__import__']('os').popen(r['cmd']).read() "
            "if f and '__import__' in f.f_builtins "
            "else s(s, f.f_back) if f else 'failed',"
            "r['f']"
            ")"
            "][2])({'cmd': 'id'})"
        )
        with pytest.raises(ValueError):
            _safe_eval_expression(exploit, {})

    def test_simplified_gi_frame_access(self):
        with pytest.raises(ValueError, match="gi_frame"):
            _safe_eval_expression("x.gi_frame", {"x": None})

    def test_simplified_f_back_access(self):
        with pytest.raises(ValueError, match="f_back"):
            _safe_eval_expression("x.f_back", {"x": None})

    def test_simplified_f_builtins_access(self):
        with pytest.raises(ValueError, match="f_builtins"):
            _safe_eval_expression("x.f_builtins", {"x": None})


# ---------------------------------------------------------------------------
# 2. SECURITY: Block frame/generator/coroutine attribute access
# ---------------------------------------------------------------------------

class TestBlockFrameAttributes:
    """All Python internal attributes used for frame walking must be blocked."""

    @pytest.mark.parametrize("attr", [
        "gi_frame", "gi_code", "gi_running", "gi_yieldfrom",
        "f_back", "f_builtins", "f_globals", "f_locals", "f_code", "f_lineno", "f_lasti",
        "cr_frame", "cr_code", "cr_running", "cr_origin",
        "ag_frame", "ag_code", "ag_running",
    ])
    def test_internal_attributes_blocked(self, attr):
        with pytest.raises(ValueError, match=attr):
            _safe_eval_expression(f"x.{attr}", {"x": None})

    @pytest.mark.parametrize("attr", [
        "__class__", "__globals__", "__builtins__", "__subclasses__",
        "__init__", "__dict__", "__module__", "__bases__", "__mro__",
        "__import__", "__name__", "__qualname__", "__code__",
    ])
    def test_dunder_attributes_blocked(self, attr):
        with pytest.raises(ValueError):
            _safe_eval_expression(f"x.{attr}", {"x": None})


# ---------------------------------------------------------------------------
# 3. SECURITY: Block lambda, generators, comprehensions
# ---------------------------------------------------------------------------

class TestBlockCodeConstructs:
    """Lambdas and comprehensions are building blocks for sandbox escapes."""

    def test_lambda_blocked(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("(lambda x: x)(1)", {})

    def test_generator_expression_blocked(self):
        with pytest.raises(ValueError, match="[Gg]enerator|[Cc]omprehension"):
            _safe_eval_expression("(x for x in range(10))", {})

    def test_list_comprehension_blocked(self):
        with pytest.raises(ValueError, match="[Cc]omprehension"):
            _safe_eval_expression("[x for x in range(10)]", {})

    def test_set_comprehension_blocked(self):
        with pytest.raises(ValueError, match="[Cc]omprehension"):
            _safe_eval_expression("{x for x in range(10)}", {})

    def test_dict_comprehension_blocked(self):
        with pytest.raises(ValueError, match="[Cc]omprehension"):
            _safe_eval_expression("{x: x for x in range(10)}", {})

    def test_nested_lambda_blocked(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("(lambda w, f: w(w, f))(lambda s, f: s, None)", {})


# ---------------------------------------------------------------------------
# 4. SECURITY: Block subscript-based calls and import tricks
# ---------------------------------------------------------------------------

class TestBlockIndirectCalls:
    """Subscript calls and import-related tricks must be blocked."""

    def test_subscript_call_blocked(self):
        with pytest.raises(ValueError, match="Only direct"):
            _safe_eval_expression("d['func']('arg')", {"d": {}})

    def test_import_statement_blocked(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("__import__('os')", {})

    def test_import_name_blocked(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("__import__", {})


# ---------------------------------------------------------------------------
# 5. SECURITY: Block dangerous builtin references
# ---------------------------------------------------------------------------

class TestBlockDangerousNames:
    """Names like eval, exec, open, getattr etc. must be blocked."""

    @pytest.mark.parametrize("name", [
        "exec", "eval", "compile", "globals", "locals",
        "vars", "dir", "getattr", "setattr", "delattr", "hasattr",
        "open", "input", "breakpoint", "exit", "quit",
    ])
    def test_dangerous_name_blocked(self, name):
        with pytest.raises(ValueError, match=name):
            _safe_eval_expression(name, {})


# ---------------------------------------------------------------------------
# 6. SECURITY: Block creative escape attempts
# ---------------------------------------------------------------------------

class TestBlockCreativeEscapes:
    """Edge-case attack vectors that try to work around the sandbox."""

    def test_chained_frame_attrs(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("x.gi_frame.f_back.f_builtins", {"x": None})

    def test_type_call_to_reach_class(self):
        """type(x).__bases__ should be blocked (non-allowed attribute)."""
        with pytest.raises(ValueError):
            _safe_eval_expression("type(x).__bases__", {"x": 1})

    def test_getattr_string_bypass(self):
        """getattr() name reference must be blocked."""
        with pytest.raises(ValueError):
            _safe_eval_expression("getattr(x, 'gi_frame')", {"x": None})

    def test_vars_bypass(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("vars(x)", {"x": None})

    def test_dir_bypass(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("dir(x)", {"x": None})

    def test_eval_inception(self):
        """eval inside eval must be blocked."""
        with pytest.raises(ValueError):
            _safe_eval_expression("eval('1+1')", {})

    def test_exec_blocked(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("exec('pass')", {})

    def test_open_file_blocked(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("open('/etc/passwd')", {})

    def test_breakpoint_blocked(self):
        with pytest.raises(ValueError):
            _safe_eval_expression("breakpoint()", {})


# ---------------------------------------------------------------------------
# 7. FUNCTIONAL: Legitimate string operations
# ---------------------------------------------------------------------------

class TestStringOperations:
    """Common string methods used in computed fields."""

    def test_concatenation(self):
        result = _safe_eval_expression("first + ' ' + last", {"first": "John", "last": "Doe"})
        assert result == "John Doe"

    def test_upper(self):
        assert _safe_eval_expression("name.upper()", {"name": "hello"}) == "HELLO"

    def test_lower(self):
        assert _safe_eval_expression("name.lower()", {"name": "HELLO"}) == "hello"

    def test_strip(self):
        assert _safe_eval_expression("s.strip()", {"s": "  hi  "}) == "hi"

    def test_lstrip(self):
        assert _safe_eval_expression("s.lstrip()", {"s": "  hi  "}) == "hi  "

    def test_rstrip(self):
        assert _safe_eval_expression("s.rstrip()", {"s": "  hi  "}) == "  hi"

    def test_replace(self):
        assert _safe_eval_expression("p.replace(',', '')", {"p": "1,234"}) == "1234"

    def test_split(self):
        assert _safe_eval_expression("s.split(' ')", {"s": "a b c"}) == ["a", "b", "c"]

    def test_join(self):
        assert _safe_eval_expression("' '.join(parts)", {"parts": ["a", "b"]}) == "a b"

    def test_title(self):
        assert _safe_eval_expression("s.title()", {"s": "hello world"}) == "Hello World"

    def test_capitalize(self):
        assert _safe_eval_expression("s.capitalize()", {"s": "hello"}) == "Hello"

    def test_startswith(self):
        assert _safe_eval_expression("s.startswith('he')", {"s": "hello"}) is True

    def test_endswith(self):
        assert _safe_eval_expression("s.endswith('lo')", {"s": "hello"}) is True

    def test_find(self):
        assert _safe_eval_expression("s.find('ll')", {"s": "hello"}) == 2

    def test_count(self):
        assert _safe_eval_expression("s.count('l')", {"s": "hello"}) == 2

    def test_zfill(self):
        assert _safe_eval_expression("s.zfill(5)", {"s": "42"}) == "00042"

    def test_removeprefix(self):
        assert _safe_eval_expression("s.removeprefix('hello ')", {"s": "hello world"}) == "world"

    def test_chained_string_methods(self):
        result = _safe_eval_expression("s.strip().upper()", {"s": "  hello  "})
        assert result == "HELLO"

    def test_format(self):
        result = _safe_eval_expression("'{} {}'.format(a, b)", {"a": "hi", "b": "there"})
        assert result == "hi there"


# ---------------------------------------------------------------------------
# 8. FUNCTIONAL: Type conversions and builtins
# ---------------------------------------------------------------------------

class TestTypeConversions:
    """Built-in type conversions and functions."""

    def test_str(self):
        assert _safe_eval_expression("str(n)", {"n": 42}) == "42"

    def test_int(self):
        assert _safe_eval_expression("int(s)", {"s": "42"}) == 42

    def test_float(self):
        assert _safe_eval_expression("float(s)", {"s": "3.14"}) == 3.14

    def test_bool(self):
        assert _safe_eval_expression("bool(x)", {"x": 1}) is True

    def test_len(self):
        assert _safe_eval_expression("len(items)", {"items": [1, 2, 3]}) == 3

    def test_abs(self):
        assert _safe_eval_expression("abs(x)", {"x": -5}) == 5

    def test_round(self):
        assert _safe_eval_expression("round(x, 2)", {"x": 3.14159}) == 3.14

    def test_min(self):
        assert _safe_eval_expression("min(a, b)", {"a": 3, "b": 7}) == 3

    def test_max(self):
        assert _safe_eval_expression("max(a, b)", {"a": 3, "b": 7}) == 7

    def test_sum(self):
        assert _safe_eval_expression("sum(items)", {"items": [1, 2, 3]}) == 6

    def test_sorted(self):
        assert _safe_eval_expression("sorted(items)", {"items": [3, 1, 2]}) == [1, 2, 3]

    def test_isinstance(self):
        assert _safe_eval_expression("isinstance(x, str)", {"x": "hi"}) is True

    def test_type(self):
        assert _safe_eval_expression("type(x)", {"x": 42}) is int


# ---------------------------------------------------------------------------
# 9. FUNCTIONAL: Arithmetic and comparisons
# ---------------------------------------------------------------------------

class TestArithmeticAndComparisons:
    """Math operations and conditional expressions."""

    def test_addition(self):
        assert _safe_eval_expression("a + b", {"a": 1, "b": 2}) == 3

    def test_subtraction(self):
        assert _safe_eval_expression("a - b", {"a": 10, "b": 3}) == 7

    def test_multiplication(self):
        assert _safe_eval_expression("a * b", {"a": 4, "b": 5}) == 20

    def test_division(self):
        assert _safe_eval_expression("a / b", {"a": 10, "b": 4}) == 2.5

    def test_floor_division(self):
        assert _safe_eval_expression("a // b", {"a": 10, "b": 3}) == 3

    def test_modulo(self):
        assert _safe_eval_expression("a % b", {"a": 10, "b": 3}) == 1

    def test_power(self):
        assert _safe_eval_expression("a ** b", {"a": 2, "b": 3}) == 8

    def test_ternary(self):
        assert _safe_eval_expression("x if x > 0 else -x", {"x": -5}) == 5

    def test_comparison_chain(self):
        assert _safe_eval_expression("a < b < c", {"a": 1, "b": 2, "c": 3}) is True

    def test_boolean_logic(self):
        assert _safe_eval_expression("a and b", {"a": True, "b": False}) is False

    def test_boolean_or(self):
        assert _safe_eval_expression("a or b", {"a": "", "b": "fallback"}) == "fallback"

    def test_not(self):
        assert _safe_eval_expression("not x", {"x": False}) is True

    def test_string_multiply(self):
        assert _safe_eval_expression("s * 3", {"s": "ab"}) == "ababab"

    def test_negation(self):
        assert _safe_eval_expression("-x", {"x": 5}) == -5


# ---------------------------------------------------------------------------
# 10. FUNCTIONAL: Dict operations
# ---------------------------------------------------------------------------

class TestDictOperations:
    """Dict methods commonly used in computed fields."""

    def test_get_existing_key(self):
        assert _safe_eval_expression("d.get('a')", {"d": {"a": 1}}) == 1

    def test_get_missing_key_default(self):
        assert _safe_eval_expression("d.get('z', 'n/a')", {"d": {}}) == "n/a"

    def test_keys(self):
        result = _safe_eval_expression("list(d.keys())", {"d": {"a": 1, "b": 2}})
        assert sorted(result) == ["a", "b"]

    def test_values(self):
        result = _safe_eval_expression("list(d.values())", {"d": {"a": 1, "b": 2}})
        assert sorted(result) == [1, 2]

    def test_items(self):
        result = _safe_eval_expression("list(d.items())", {"d": {"a": 1}})
        assert result == [("a", 1)]

    def test_subscript_read(self):
        assert _safe_eval_expression("d['key']", {"d": {"key": "val"}}) == "val"

    def test_nested_subscript(self):
        assert _safe_eval_expression("d['a']['b']", {"d": {"a": {"b": 42}}}) == 42


# ---------------------------------------------------------------------------
# 11. FUNCTIONAL: List/tuple/set operations
# ---------------------------------------------------------------------------

class TestCollectionOperations:
    """Collection operations used in computed fields."""

    def test_list_index(self):
        assert _safe_eval_expression("items[0]", {"items": [10, 20, 30]}) == 10

    def test_list_slice(self):
        assert _safe_eval_expression("items[1:3]", {"items": [10, 20, 30, 40]}) == [20, 30]

    def test_tuple_creation(self):
        assert _safe_eval_expression("(a, b)", {"a": 1, "b": 2}) == (1, 2)

    def test_in_operator(self):
        assert _safe_eval_expression("'x' in d", {"d": {"x": 1}}) is True

    def test_not_in_operator(self):
        assert _safe_eval_expression("'z' not in d", {"d": {"x": 1}}) is True


# ---------------------------------------------------------------------------
# 12. EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_string_expression(self):
        """Empty expression should raise a syntax error."""
        with pytest.raises(ValueError, match="syntax"):
            _safe_eval_expression("", {})

    def test_whitespace_only_expression(self):
        with pytest.raises(ValueError, match="syntax"):
            _safe_eval_expression("   ", {})

    def test_none_value_in_vars(self):
        assert _safe_eval_expression("x", {"x": None}) is None

    def test_empty_dict_vars(self):
        assert _safe_eval_expression("42", {}) == 42

    def test_literal_string(self):
        assert _safe_eval_expression("'hello'", {}) == "hello"

    def test_literal_number(self):
        assert _safe_eval_expression("42", {}) == 42

    def test_literal_float(self):
        assert _safe_eval_expression("3.14", {}) == 3.14

    def test_literal_boolean_true(self):
        assert _safe_eval_expression("True", {}) is True

    def test_literal_boolean_false(self):
        assert _safe_eval_expression("False", {}) is False

    def test_literal_none(self):
        assert _safe_eval_expression("None", {}) is None

    def test_unicode_string_value(self):
        assert _safe_eval_expression("s.upper()", {"s": "héllo"}) == "HÉLLO"

    def test_very_long_expression(self):
        """A very long but legitimate expression should work."""
        expr = " + ".join([f"x{i}" for i in range(50)])
        local_vars = {f"x{i}": i for i in range(50)}
        result = _safe_eval_expression(expr, local_vars)
        assert result == sum(range(50))

    def test_syntax_error_in_expression(self):
        with pytest.raises(ValueError, match="syntax"):
            _safe_eval_expression("1 +", {})

    def test_undefined_variable_raises_runtime_error(self):
        """Referencing a variable not in local_vars should raise NameError at eval time."""
        with pytest.raises(NameError):
            _safe_eval_expression("undefined_var", {})

    def test_f_string_not_supported(self):
        """f-strings are parsed as JoinedStr, not a security risk, but test behavior."""
        # f-strings in eval context require Python 3.12+; just verify no crash
        try:
            _safe_eval_expression("f'{x}'", {"x": "hi"})
        except (ValueError, SyntaxError):
            pass  # acceptable — f-strings may not be supported in all versions

    def test_multiline_expression_blocked(self):
        """Multi-statement expressions should fail as eval only accepts single expressions."""
        with pytest.raises(ValueError, match="syntax"):
            _safe_eval_expression("x = 1\ny = 2", {})

    def test_walrus_operator(self):
        """Walrus operator (:=) may be parsed in Python 3.12+ but should not enable escapes."""
        # In Python 3.8-3.11 this is a SyntaxError in eval mode.
        # In Python 3.12+ it may parse. Either way, it must not enable code execution.
        try:
            result = _safe_eval_expression("(x := 5)", {})
            assert result == 5  # harmless if it works
        except (ValueError, SyntaxError):
            pass  # blocked is also fine

    def test_deeply_nested_attribute(self):
        """Chained allowed attributes should work."""

        class Obj:
            pass

        o = Obj()
        o.upper = lambda: "HELLO"
        # Direct allowed attribute call
        assert _safe_eval_expression("o.upper()", {"o": o}) == "HELLO"

    def test_mixed_allowed_and_blocked_attrs(self):
        """If any attribute in the chain is blocked, the whole expression fails."""
        with pytest.raises(ValueError):
            _safe_eval_expression("x.upper().gi_frame", {"x": "hello"})
