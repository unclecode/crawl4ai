"""Text files that crawl4ai reads must be decoded as UTF-8, whatever the platform default is.

On Windows ``open()`` and ``Path.read_text()`` use the ANSI code page (cp1252, cp1254, cp936, ...). A UTF-8 file
with non-ASCII text then fails to decode on some code pages and is silently turned into different text on others.
Each test runs the real function in a child interpreter with a non-UTF-8 default encoding (``-X utf8=0``, plus
``LC_ALL=C`` and ``PYTHONCOERCECLOCALE=0`` on POSIX), so it fails without the fix on every platform and not only
on a machine that happens to use a legacy code page.

Non-ASCII text is written as ``\\u`` escapes because a non-ASCII command line argument cannot be decoded
reliably under the C locale.
"""
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

import crawl4ai.js_snippet as js_snippet
from crawl4ai.script.c4ai_script import compile_string

NI_HAO = "你好"
KONNICHIWA = "こんにちは"


def _run_with_legacy_locale(code: str, *args: str) -> str:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "LC_ALL": "C", "PYTHONCOERCECLOCALE": "0"}
    env.pop("PYTHONUTF8", None)
    result = subprocess.run(
        [sys.executable, "-X", "utf8=0", "-c", textwrap.dedent(code), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_bundled_js_snippets_load_as_utf8():
    snippet_dir = Path(js_snippet.__file__).parent
    names = sorted(path.stem for path in snippet_dir.glob("*.js"))
    assert names, "no bundled JS snippets found"
    expected = {name: (snippet_dir / f"{name}.js").read_text(encoding="utf-8") for name in names}
    code = """
        import json, sys
        from crawl4ai.js_snippet import load_js_script

        print(json.dumps({name: load_js_script(name) for name in sys.argv[1:]}))
    """
    assert json.loads(_run_with_legacy_locale(code, *names)) == expected


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
def test_cli_config_file_is_read_as_utf8(tmp_path, suffix):
    data = {"instruction": NI_HAO, "selector": "div.title"}
    path = tmp_path / f"config{suffix}"
    if suffix == ".json":
        text = json.dumps(data, ensure_ascii=False)
    else:
        text = yaml.safe_dump(data, allow_unicode=True)
    path.write_text(text, encoding="utf-8")
    code = """
        import json, sys
        from crawl4ai.cli import load_config_file

        print(json.dumps(load_config_file(sys.argv[1])))
    """
    assert json.loads(_run_with_legacy_locale(code, str(path))) == data


def test_c4a_script_files_are_read_as_utf8(tmp_path):
    (tmp_path / "part.c4a").write_text(f'TYPE "{NI_HAO}"\n', encoding="utf-8")
    main = tmp_path / "main.c4a"
    main.write_text(f'USE "part.c4a"\nTYPE "{KONNICHIWA}"\n', encoding="utf-8")
    # the reference is built from the already inlined text, so it never reads a file with the default encoding
    expected = compile_string(f'TYPE "{NI_HAO}"\nTYPE "{KONNICHIWA}"\n')
    assert any(NI_HAO in line for line in expected) and any(KONNICHIWA in line for line in expected)
    code = """
        import json, pathlib, sys
        from crawl4ai.script.c4a_compile import C4ACompiler
        from crawl4ai.script.c4ai_script import compile_file

        path = pathlib.Path(sys.argv[1])
        result = C4ACompiler.compile_file(path)
        print(json.dumps({"function": compile_file(path), "method": result.js_code, "ok": result.success}))
    """
    out = json.loads(_run_with_legacy_locale(code, str(main)))
    assert out["ok"] is True
    assert out["function"] == expected
    assert out["method"] == expected
