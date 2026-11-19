import asyncio
import sqlite3
import threading
from contextlib import closing

import pytest
import pytest_asyncio

from crawl4ai import async_database


@pytest_asyncio.fixture
async def database(tmp_path, monkeypatch):
    monkeypatch.setattr(async_database, "DB_PATH", str(tmp_path / "cache.sqlite"))
    monkeypatch.setattr(async_database, "base_directory", str(tmp_path))
    monkeypatch.setenv("CRAWL4_AI_BASE_DIRECTORY", str(tmp_path))
    manager = async_database.AsyncDatabaseManager(pool_size=1)
    await manager.ainit_db()
    manager._initialized = True

    connections = []
    real_connect = async_database.aiosqlite.connect

    def connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(async_database.aiosqlite, "connect", connect)
    try:
        yield manager, connections
    finally:
        await manager.cleanup()
        # Also close any connection leaked by the unfixed code so failing
        # regressions do not leave SQLite worker threads running.
        for connection in connections:
            await connection.close()


async def assert_closed(connection):
    with pytest.raises(ValueError, match="(no active connection|Connection closed)"):
        await connection.execute("SELECT 1")
    worker = (
        connection if isinstance(connection, threading.Thread) else connection._thread
    )
    await asyncio.to_thread(worker.join, timeout=1)
    assert not worker.is_alive()


async def assert_slot_reusable(manager):
    await asyncio.wait_for(manager.connection_semaphore.acquire(), timeout=1)
    manager.connection_semaphore.release()
    assert not manager.connection_pool


@pytest.mark.asyncio
async def test_schema_validation_failure_closes_connection(database):
    manager, connections = database
    with closing(sqlite3.connect(manager.db_path)) as db:
        db.execute("DROP TABLE crawled_data")

    with pytest.raises(ValueError, match="Database missing columns"):
        async with manager.get_connection():
            pytest.fail("An invalid database must not be yielded")

    assert len(connections) == 1
    await assert_closed(connections[0])
    await assert_slot_reusable(manager)


@pytest.mark.asyncio
async def test_pragma_failure_closes_connection(database, monkeypatch):
    manager, connections = database
    connect = async_database.aiosqlite.connect

    def short_timeout_connect(*args, **kwargs):
        return connect(*args, **{**kwargs, "timeout": 0.01})

    monkeypatch.setattr(async_database.aiosqlite, "connect", short_timeout_connect)
    blocker = sqlite3.connect(manager.db_path)
    try:
        blocker.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            async with manager.get_connection():
                pytest.fail("WAL setup must fail while the database is locked")
    finally:
        blocker.close()

    assert len(connections) == 1
    await assert_closed(connections[0])
    await assert_slot_reusable(manager)

    async with manager.get_connection() as connection:
        async with connection.execute("SELECT 1") as cursor:
            assert await cursor.fetchone() == (1,)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "statement",
    [
        "PRAGMA journal_mode = WAL",
        "PRAGMA busy_timeout = 5000",
        "PRAGMA table_info(crawled_data)",
    ],
)
async def test_setup_cancellation_closes_connection(database, monkeypatch, statement):
    manager, connections = database
    started = asyncio.Event()
    release = threading.Event()
    loop = asyncio.get_running_loop()
    connect = async_database.aiosqlite.connect

    def trace(sql):
        if sql == statement:
            loop.call_soon_threadsafe(started.set)
            release.wait(timeout=5)

    async def traced_connect(*args, **kwargs):
        connection = await connect(*args, **kwargs)
        await connection.set_trace_callback(trace)
        return connection

    monkeypatch.setattr(async_database.aiosqlite, "connect", traced_connect)

    async def use_connection():
        async with manager.get_connection():
            pytest.fail("Cancelled setup must not yield a connection")

    task = asyncio.create_task(use_connection())
    try:
        await asyncio.wait_for(started.wait(), timeout=2)
        task.cancel()
        # Deliver cancellation while real SQLite work is still pending.
        await asyncio.sleep(0)
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)
    finally:
        release.set()
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    assert len(connections) == 1
    await assert_closed(connections[0])
    await assert_slot_reusable(manager)


@pytest.mark.asyncio
async def test_connect_failure_releases_pool_slot(database, tmp_path):
    manager, connections = database
    manager.db_path = str(tmp_path)
    with pytest.raises(sqlite3.OperationalError, match="unable to open database file"):
        async with manager.get_connection():
            pytest.fail("A directory cannot be opened as a database")

    assert len(connections) == 1
    await assert_closed(connections[0])
    await assert_slot_reusable(manager)


@pytest.mark.asyncio
async def test_connection_body_exit_closes_connection(database):
    manager, connections = database
    async with manager.get_connection() as connection:
        async with connection.execute("SELECT 1") as cursor:
            assert await cursor.fetchone() == (1,)

    await assert_closed(connections[0])
    await assert_slot_reusable(manager)

    with pytest.raises(RuntimeError, match="operation failed"):
        async with manager.get_connection():
            raise RuntimeError("operation failed")

    await assert_closed(connections[1])
    await assert_slot_reusable(manager)
