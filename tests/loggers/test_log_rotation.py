import os

from crawl4ai.async_logger import AsyncLogger


def test_loggers_on_same_path_share_one_rotating_file(tmp_path):
    log_file = str(tmp_path / "crawler.log")
    first = AsyncLogger(log_file=log_file, verbose=False)
    second = AsyncLogger(log_file=log_file, verbose=False)

    assert first._file_handler is second._file_handler
    first._file_handler.maxBytes = 2_000

    for i in range(300):
        first.info(f"a {i} " + "x" * 80, tag="TEST")
        second.info(f"b {i} " + "x" * 80, tag="TEST")

    files = sorted(os.listdir(tmp_path))
    assert files == ["crawler.log", "crawler.log.1", "crawler.log.2", "crawler.log.3"]
    assert all((tmp_path / name).stat().st_size <= 2_000 for name in files)
