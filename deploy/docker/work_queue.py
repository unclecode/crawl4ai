"""
work_queue.py - bounded background-job execution with per-principal quotas.

/crawl/job and /llm/job used FastAPI BackgroundTasks with no bound: a client
could enqueue unlimited background jobs and exhaust memory / browser slots, and
one caller could starve others.

This replaces that with a fixed worker pool draining an asyncio.Queue, plus an
optional per-principal concurrency cap. Everything is configurable, and any
limit set to 0 (or null) means "unbounded" - i.e. the previous behavior is fully
recoverable:

    limits.queue.maxsize        0 => unbounded queue (never 503)
    limits.queue.workers        worker pool size (>=1)
    limits.queue.per_principal  0 => no per-caller cap (never 429)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Dict, Optional

logger = logging.getLogger("crawl4ai.workqueue")

JobFactory = Callable[[], Awaitable[None]]


class QueueFull(Exception):
    """The bounded job queue is full -> 503 Retry-After."""


class QuotaExceeded(Exception):
    """The principal has too many concurrent jobs -> 429."""


class WorkQueue:
    def __init__(self, maxsize: int = 0, workers: int = 4, per_principal: int = 0):
        self.maxsize = max(0, int(maxsize))          # 0 = unbounded
        self.workers = max(1, int(workers))
        self.per_principal = max(0, int(per_principal))  # 0 = unlimited
        self._q: Optional[asyncio.Queue] = None
        self._tasks: list = []
        self._counts: Dict[str, int] = {}

    @property
    def started(self) -> bool:
        return self._q is not None

    async def start(self) -> None:
        self._q = asyncio.Queue(maxsize=self.maxsize)
        self._tasks = [asyncio.create_task(self._worker()) for _ in range(self.workers)]
        logger.info(
            "work queue started (maxsize=%s, workers=%s, per_principal=%s)",
            self.maxsize or "unbounded", self.workers, self.per_principal or "unlimited",
        )

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        self._tasks = []
        self._q = None

    async def _worker(self) -> None:
        assert self._q is not None
        while True:
            principal, factory = await self._q.get()
            try:
                await factory()
            except Exception:
                logger.exception("background job failed")
            finally:
                self._release(principal)
                self._q.task_done()

    def _release(self, principal: Optional[str]) -> None:
        if not principal:
            return
        n = self._counts.get(principal, 0) - 1
        if n <= 0:
            self._counts.pop(principal, None)
        else:
            self._counts[principal] = n

    def submit(self, factory: JobFactory, principal: Optional[str] = None) -> None:
        """Enqueue a job. Raises QuotaExceeded / QueueFull (mapped to 429 / 503)."""
        if self._q is None:
            raise RuntimeError("work queue not started")
        if self.per_principal and principal:
            if self._counts.get(principal, 0) >= self.per_principal:
                raise QuotaExceeded()
        try:
            self._q.put_nowait((principal, factory))
        except asyncio.QueueFull:
            raise QueueFull()
        if principal:
            self._counts[principal] = self._counts.get(principal, 0) + 1


# Process-wide singleton, set at server boot.
_JOB_QUEUE: Optional[WorkQueue] = None


def set_job_queue(q: Optional[WorkQueue]) -> None:
    global _JOB_QUEUE
    _JOB_QUEUE = q


def get_job_queue() -> Optional[WorkQueue]:
    return _JOB_QUEUE
