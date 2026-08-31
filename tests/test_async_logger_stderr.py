"""
Tests for issue #1968: AsyncLogger must write to stderr by default so that
stdout-based transports (e.g. MCP stdio) are not corrupted.
"""

import importlib.util
import io
import sys
from pathlib import Path

import pytest
from rich.console import Console

# Load async_logger directly without triggering the full crawl4ai __init__
# (which pulls in many optional deps like aiofiles, OpenSSL, playwright …).
_spec = importlib.util.spec_from_file_location(
    "crawl4ai.async_logger",
    Path(__file__).parent.parent / "crawl4ai" / "async_logger.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

AsyncLogger = _mod.AsyncLogger
LogLevel = _mod.LogLevel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _capture_consoles():
    """Return StringIO objects for stdout and stderr plus a no-color Console
    for each, suitable for injecting into AsyncLogger in tests."""
    out = io.StringIO()
    err = io.StringIO()
    stdout_console = Console(file=out, no_color=True, highlight=False)
    stderr_console = Console(file=err, no_color=True, highlight=False)
    return out, err, stdout_console, stderr_console


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAsyncLoggerDefaultsToStderr:
    """The default AsyncLogger must NOT write to stdout."""

    def test_default_console_writes_to_stderr_not_stdout(self, capsys):
        """Logging to the default AsyncLogger must not pollute stdout."""
        logger = AsyncLogger(verbose=True)

        logger.info("hello from logger", tag="TEST")
        logger.error("error message", tag="TEST")
        logger.warning("warning message", tag="TEST")

        captured = capsys.readouterr()
        # stdout must remain pristine (no log lines mixed in)
        assert captured.out == "", (
            "AsyncLogger wrote to stdout — this breaks MCP stdio transport!\n"
            f"stdout content: {captured.out!r}"
        )
        # stderr should contain the output
        assert "hello from logger" in captured.err, (
            "Expected log output on stderr but found nothing.\n"
            f"stderr content: {captured.err!r}"
        )

    def test_default_console_is_stderr(self):
        """The internal console.file should be sys.stderr (or equivalent)."""
        logger = AsyncLogger(verbose=True)
        # Rich Console with stderr=True writes to sys.stderr
        assert logger.console.file is sys.stderr, (
            f"Expected logger.console.file to be sys.stderr, "
            f"got {logger.console.file!r}"
        )


class TestAsyncLoggerCustomConsole:
    """Callers can inject a custom Console (e.g. stdout for non-MCP use)."""

    def test_custom_console_is_respected(self):
        """When a custom Console is passed, it must be used verbatim."""
        buf = io.StringIO()
        custom = Console(file=buf, no_color=True, highlight=False)
        logger = AsyncLogger(verbose=True, console=custom)

        logger.info("custom target", tag="TEST")

        output = buf.getvalue()
        assert "custom target" in output, (
            f"Expected log output in custom console, got: {output!r}"
        )

    def test_stdout_console_can_be_injected(self, capsys):
        """Passing Console(file=sys.stdout) restores legacy behaviour."""
        stdout_console = Console(file=sys.stdout, no_color=True, highlight=False)
        logger = AsyncLogger(verbose=True, console=stdout_console)

        logger.info("going to stdout", tag="TEST")

        captured = capsys.readouterr()
        assert "going to stdout" in captured.out


class TestAsyncLoggerVerboseFalse:
    """verbose=False must suppress console output regardless of the target stream."""

    def test_no_output_when_verbose_false(self, capsys):
        logger = AsyncLogger(verbose=False)
        logger.info("silent message", tag="TEST")
        logger.error("silent error", tag="TEST")

        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""


class TestAsyncLoggerFileLogging:
    """File logging path should still work after the stderr change."""

    def test_file_logging_still_works(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = AsyncLogger(log_file=str(log_file), verbose=False)
        logger.info("file log entry", tag="FILE")

        content = log_file.read_text(encoding="utf-8")
        assert "file log entry" in content


class TestMCPScenario:
    """Simulates what MCP stdio transport sees on stdout."""

    def test_stdout_clean_across_all_log_levels(self, capsys):
        """Simulate MCP usage: crawl + log, stdout must only have JSON."""
        logger = AsyncLogger(verbose=True)
        fake_json_response = '{"jsonrpc": "2.0", "result": "ok", "id": 1}'

        # Simulate interleaved logging (as would happen during a crawl)
        logger.info("Crawling started", tag="CRAWL")
        logger.warning("Slow response", tag="CRAWL")
        logger.success("Done", tag="CRAWL")

        # MCP server would write JSON to stdout
        print(fake_json_response)

        captured = capsys.readouterr()

        # stdout must contain ONLY the JSON line
        assert captured.out.strip() == fake_json_response, (
            "Stdout was polluted by logger output!\n"
            f"stdout: {captured.out!r}"
        )
        # All log output should be on stderr
        assert "Crawling started" in captured.err
