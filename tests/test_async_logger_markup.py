"""
AsyncLogger must print square brackets in messages and parameters as they are,
instead of letting rich read them as markup.
"""

import importlib.util
import io
from pathlib import Path

from rich.console import Console

# Load async_logger directly without triggering the full crawl4ai __init__
_spec = importlib.util.spec_from_file_location(
    "crawl4ai.async_logger",
    Path(__file__).parent.parent / "crawl4ai" / "async_logger.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

AsyncLogger = _mod.AsyncLogger
LogColor = _mod.LogColor


def _logger(tmp_path):
    out = io.StringIO()
    console = Console(file=out, no_color=True, highlight=False, width=200)
    log_file = tmp_path / "crawl.log"
    return AsyncLogger(log_file=str(log_file), console=console), out, log_file


def test_brackets_in_message_are_printed(tmp_path):
    logger, out, log_file = _logger(tmp_path)

    logger.info("literal [brackets] and [b]bold-looking[/b] text", tag="TEST")

    expected = "literal [brackets] and [b]bold-looking[/b] text"
    assert expected in out.getvalue()
    assert expected in log_file.read_text()


def test_brackets_in_params_are_printed(tmp_path):
    logger, out, log_file = _logger(tmp_path)

    logger.info(
        "value: {value}, colored: {colored}",
        tag="TEST",
        params={"value": "list[int]", "colored": "[1] first"},
        colors={"colored": LogColor.YELLOW},
    )

    expected = "value: list[int], colored: [1] first"
    assert expected in out.getvalue()
    assert expected in log_file.read_text()


def test_error_status_with_closing_tag_does_not_raise(tmp_path):
    logger, out, log_file = _logger(tmp_path)

    logger.error_status(
        url="https://example.com",
        error="waiting for locator('[data-test=price]'), unexpected '[/div]'",
    )

    expected = "waiting for locator('[data-test=price]'), unexpected '[/div]'"
    assert expected in out.getvalue()
    assert expected in log_file.read_text()
