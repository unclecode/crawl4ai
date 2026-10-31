import asyncio
import errno
import os

import pytest

from crawl4ai import async_database


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(async_database, "DB_PATH", str(tmp_path / "cache.sqlite"))
    monkeypatch.setattr(async_database, "base_directory", str(tmp_path))
    return async_database.AsyncDatabaseManager()


@pytest.mark.asyncio
async def test_content_read_and_cache_misses(manager):
    content_dir = manager.content_paths["html"]
    with open(os.path.join(content_dir, "unicode"), "w", encoding="utf-8") as file:
        file.write("Cached content 内容")
    with open(os.path.join(content_dir, "invalid"), "wb") as file:
        file.write(b"\xff")
    os.mkdir(os.path.join(content_dir, "directory"))

    assert await manager._load_content("unicode", "html") == "Cached content 内容"
    assert await manager._load_content("", "html") is None
    assert await manager._load_content("missing", "html") is None
    assert await manager._load_content("invalid", "html") is None
    assert await manager._load_content("directory", "html") is None


@pytest.mark.asyncio
@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="Requires POSIX named pipes")
async def test_content_read_propagates_cancellation_and_closes_file(manager):
    import array
    import fcntl
    import termios

    fifo = os.path.join(manager.content_paths["html"], "pending")
    os.mkfifo(fifo)
    writer = None
    task = asyncio.create_task(manager._load_content("pending", "html"))
    cancel_requested = False

    async def wait_for_read():
        nonlocal writer
        while writer is None:
            try:
                writer = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
            except OSError as error:
                if error.errno != errno.ENXIO:
                    raise
                await asyncio.sleep(0.01)
        observer = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
        try:
            os.write(writer, b"x")
            pending = array.array("i", [1])
            while True:
                fcntl.ioctl(observer, termios.FIONREAD, pending, True)
                if not pending[0]:
                    return
                await asyncio.sleep(0.01)
        finally:
            os.close(observer)

    try:
        await asyncio.wait_for(wait_for_read(), timeout=2)
        assert not task.done()
        task.cancel()
        cancel_requested = True
        await asyncio.sleep(0)
    finally:
        if not task.done() and not cancel_requested:
            task.cancel()
        if writer is None:
            writer = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
        os.close(writer)
        await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), timeout=2)

    with pytest.raises(asyncio.CancelledError):
        await task

    assert task.cancelled()
    with pytest.raises(OSError) as error:
        os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
    assert error.value.errno == errno.ENXIO
