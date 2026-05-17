from io import StringIO

from rich.console import Console

from crawl4ai.async_logger import AsyncLogger


def test_async_logger_writes_to_stderr_by_default(capsys):
    logger = AsyncLogger(verbose=True)

    logger.info("structured stdout should stay clean")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "structured stdout should stay clean" in captured.err


def test_async_logger_accepts_custom_console():
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)
    logger = AsyncLogger(verbose=True, console=console)

    logger.info("custom stream")

    assert "custom stream" in stream.getvalue()
