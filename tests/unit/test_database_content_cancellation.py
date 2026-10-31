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
    fifo = os.path.join(manager.content_paths["html"], "pending")
    os.mkfifo(fifo)
    writer = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
    task = asyncio.create_task(manager._load_content("pending", "html"))
    try:
        await asyncio.sleep(0.05)
        assert not task.done()
        task.cancel()
    finally:
        os.close(writer)

    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=1)

    assert task.cancelled()
    with pytest.raises(OSError) as error:
        os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
    assert error.value.errno == errno.ENXIO
