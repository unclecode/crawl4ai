from typing import Dict, Optional, List, Tuple
from .async_configs import CrawlerRunConfig
from .models import (
    CrawlResult,
    CrawlerTaskResult,
    CrawlStatus,
    DisplayMode,
    CrawlStats,
    DomainState,
)

from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich import box
from datetime import datetime, timedelta

import time
import psutil
import asyncio
import uuid

from urllib.parse import urlparse
import random
from abc import ABC, abstractmethod


class RateLimiter:
    def __init__(
        self,
        base_delay: Tuple[float, float] = (1.0, 3.0),
        max_delay: float = 60.0,
        max_retries: int = 3,
        rate_limit_codes: List[int] = None,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.rate_limit_codes = rate_limit_codes or [429, 503]
        self.domains: Dict[str, DomainState] = {}

    def get_domain(self, url: str) -> str:
        return urlparse(url).netloc

    async def wait_if_needed(self, url: str) -> None:
        domain = self.get_domain(url)
        state = self.domains.get(domain)

        if not state:
            self.domains[domain] = DomainState()
            state = self.domains[domain]

        now = time.time()
        if state.last_request_time:
            wait_time = max(0, state.current_delay - (now - state.last_request_time))
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        # Random delay within base range if no current delay
        if state.current_delay == 0:
            state.current_delay = random.uniform(*self.base_delay)

        state.last_request_time = time.time()

    def update_delay(self, url: str, status_code: int) -> bool:
        domain = self.get_domain(url)
        state = self.domains[domain]

        if status_code in self.rate_limit_codes:
            state.fail_count += 1
            if state.fail_count > self.max_retries:
                return False

            # Exponential backoff with random jitter
            state.current_delay = min(
                state.current_delay * 2 * random.uniform(0.75, 1.25), self.max_delay
            )
        else:
            # Gradually reduce delay on success
            state.current_delay = max(
                random.uniform(*self.base_delay), state.current_delay * 0.75
            )
            state.fail_count = 0

        return True


class CrawlerMonitor:
    def __init__(
        self,
        max_visible_rows: int = 15,
        display_mode: DisplayMode = DisplayMode.DETAILED,
    ):
        self.console = Console()
        self.max_visible_rows = max_visible_rows
        self.display_mode = display_mode
        self.stats: Dict[str, CrawlStats] = {}
        self.process = psutil.Process()
        self.start_time = datetime.now()
        self.live = Live(self._create_table(), refresh_per_second=2)

    def start(self):
        self.live.start()

    def stop(self):
        self.live.stop()

    def add_task(self, task_id: str, url: str):
        self.stats[task_id] = CrawlStats(
            task_id=task_id, url=url, status=CrawlStatus.QUEUED
        )
        self.live.update(self._create_table())

    def update_task(self, task_id: str, **kwargs):
        if task_id in self.stats:
            for key, value in kwargs.items():
                setattr(self.stats[task_id], key, value)
            self.live.update(self._create_table())

    def _create_aggregated_table(self) -> Table:
        """Creates a compact table showing only aggregated statistics"""
        table = Table(
            box=box.ROUNDED,
            title="Crawler Status Overview",
            title_style="bold magenta",
            header_style="bold blue",
            show_lines=True,
        )

        # Calculate statistics
        total_tasks = len(self.stats)
        queued = sum(
            1 for stat in self.stats.values() if stat.status == CrawlStatus.QUEUED
        )
        in_progress = sum(
            1 for stat in self.stats.values() if stat.status == CrawlStatus.IN_PROGRESS
        )
        completed = sum(
            1 for stat in self.stats.values() if stat.status == CrawlStatus.COMPLETED
        )
        failed = sum(
            1 for stat in self.stats.values() if stat.status == CrawlStatus.FAILED
        )

        # Memory statistics
        current_memory = self.process.memory_info().rss / (1024 * 1024)
        total_task_memory = sum(stat.memory_usage for stat in self.stats.values())
        peak_memory = max(
            (stat.peak_memory for stat in self.stats.values()), default=0.0
        )

        # Duration
        duration = datetime.now() - self.start_time

        # Create status row
        table.add_column("Status", style="bold cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        table.add_row("Total Tasks", str(total_tasks), "100%")
        table.add_row(
            "[yellow]In Queue[/yellow]",
            str(queued),
            f"{(queued/total_tasks*100):.1f}%" if total_tasks > 0 else "0%",
        )
        table.add_row(
            "[blue]In Progress[/blue]",
            str(in_progress),
            f"{(in_progress/total_tasks*100):.1f}%" if total_tasks > 0 else "0%",
        )
        table.add_row(
            "[green]Completed[/green]",
            str(completed),
            f"{(completed/total_tasks*100):.1f}%" if total_tasks > 0 else "0%",
        )
        table.add_row(
            "[red]Failed[/red]",
            str(failed),
            f"{(failed/total_tasks*100):.1f}%" if total_tasks > 0 else "0%",
        )

        # Add memory information
        table.add_section()
        table.add_row(
            "[magenta]Current Memory[/magenta]", f"{current_memory:.1f} MB", ""
        )
        table.add_row(
            "[magenta]Total Task Memory[/magenta]", f"{total_task_memory:.1f} MB", ""
        )
        table.add_row(
            "[magenta]Peak Task Memory[/magenta]", f"{peak_memory:.1f} MB", ""
        )
        table.add_row(
            "[yellow]Runtime[/yellow]",
            str(timedelta(seconds=int(duration.total_seconds()))),
            "",
        )

        return table

    def _create_detailed_table(self) -> Table:
        table = Table(
            box=box.ROUNDED,
            title="Crawler Performance Monitor",
            title_style="bold magenta",
            header_style="bold blue",
        )

        # Add columns
        table.add_column("Task ID", style="cyan", no_wrap=True)
        table.add_column("URL", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Memory (MB)", justify="right")
        table.add_column("Peak (MB)", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Info", style="italic")

        # Add summary row
        total_memory = sum(stat.memory_usage for stat in self.stats.values())
        active_count = sum(
            1 for stat in self.stats.values() if stat.status == CrawlStatus.IN_PROGRESS
        )
        completed_count = sum(
            1 for stat in self.stats.values() if stat.status == CrawlStatus.COMPLETED
        )
        failed_count = sum(
            1 for stat in self.stats.values() if stat.status == CrawlStatus.FAILED
        )

        table.add_row(
            "[bold yellow]SUMMARY",
            f"Total: {len(self.stats)}",
            f"Active: {active_count}",
            f"{total_memory:.1f}",
            f"{self.process.memory_info().rss / (1024 * 1024):.1f}",
            str(
                timedelta(
                    seconds=int((datetime.now() - self.start_time).total_seconds())
                )
            ),
            f"✓{completed_count} ✗{failed_count}",
            style="bold",
        )

        table.add_section()

        # Add rows for each task
        visible_stats = sorted(
            self.stats.values(),
            key=lambda x: (
                x.status != CrawlStatus.IN_PROGRESS,
                x.status != CrawlStatus.QUEUED,
                x.end_time or datetime.max,
            ),
        )[: self.max_visible_rows]

        for stat in visible_stats:
            status_style = {
                CrawlStatus.QUEUED: "white",
                CrawlStatus.IN_PROGRESS: "yellow",
                CrawlStatus.COMPLETED: "green",
                CrawlStatus.FAILED: "red",
            }[stat.status]

            table.add_row(
                stat.task_id[:8],  # Show first 8 chars of task ID
                stat.url[:40] + "..." if len(stat.url) > 40 else stat.url,
                f"[{status_style}]{stat.status.value}[/{status_style}]",
                f"{stat.memory_usage:.1f}",
                f"{stat.peak_memory:.1f}",
                stat.duration,
                stat.error_message[:40] if stat.error_message else "",
            )

        return table

    def _create_table(self) -> Table:
        """Creates the appropriate table based on display mode"""
        if self.display_mode == DisplayMode.AGGREGATED:
            return self._create_aggregated_table()
        return self._create_detailed_table()


class BaseDispatcher(ABC):
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        monitor: Optional[CrawlerMonitor] = None,
    ):
        self.crawler = None
        self._domain_last_hit: Dict[str, float] = {}
        self.concurrent_sessions = 0
        self.rate_limiter = rate_limiter
        self.monitor = monitor

    @abstractmethod
    async def crawl_url(
        self,
        url: str,
        config: CrawlerRunConfig,
        task_id: str,
        monitor: Optional[CrawlerMonitor] = None,
    ) -> CrawlerTaskResult:
        pass

    @abstractmethod
    async def run_urls(
        self,
        urls: List[str],
        crawler: "AsyncWebCrawler",  # noqa: F821
        config: CrawlerRunConfig,
        monitor: Optional[CrawlerMonitor] = None,
    ) -> List[CrawlerTaskResult]:
        pass


class MemoryAdaptiveDispatcher(BaseDispatcher):
    def __init__(
        self,
        memory_threshold_percent: float = 90.0,
        check_interval: float = 1.0,
        max_session_permit: int = 20,
        memory_wait_timeout: float = 300.0,  # 5 minutes default timeout
        rate_limiter: Optional[RateLimiter] = None,
        monitor: Optional[CrawlerMonitor] = None,
    ):
        super().__init__(rate_limiter, monitor)
        self.memory_threshold_percent = memory_threshold_percent
        self.check_interval = check_interval
        self.max_session_permit = max_session_permit
        self.memory_wait_timeout = memory_wait_timeout

    async def crawl_url(
        self,
        url: str,
        config: CrawlerRunConfig,
        task_id: str,
    ) -> CrawlerTaskResult:
        start_time = datetime.now()
        error_message = ""
        memory_usage = peak_memory = 0.0

        try:
            if self.monitor:
                self.monitor.update_task(
                    task_id, status=CrawlStatus.IN_PROGRESS, start_time=start_time
                )
            self.concurrent_sessions += 1

            if self.rate_limiter:
                await self.rate_limiter.wait_if_needed(url)

            process = psutil.Process()
            start_memory = process.memory_info().rss / (1024 * 1024)
            result = await self.crawler.arun(url, config=config, session_id=task_id)
            end_memory = process.memory_info().rss / (1024 * 1024)

            memory_usage = peak_memory = end_memory - start_memory

            if self.rate_limiter and result.status_code:
                if not self.rate_limiter.update_delay(url, result.status_code):
                    error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"
                    if self.monitor:
                        self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
                    return CrawlerTaskResult(
                        task_id=task_id,
                        url=url,
                        result=result,
                        memory_usage=memory_usage,
                        peak_memory=peak_memory,
                        start_time=start_time,
                        end_time=datetime.now(),
                        error_message=error_message,
                    )

            if not result.success:
                error_message = result.error_message
                if self.monitor:
                    self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
            elif self.monitor:
                self.monitor.update_task(task_id, status=CrawlStatus.COMPLETED)

        except Exception as e:
            error_message = str(e)
            if self.monitor:
                self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
            result = CrawlResult(
                url=url, html="", metadata={}, success=False, error_message=str(e)
            )

        finally:
            end_time = datetime.now()
            if self.monitor:
                self.monitor.update_task(
                    task_id,
                    end_time=end_time,
                    memory_usage=memory_usage,
                    peak_memory=peak_memory,
                    error_message=error_message,
                )
            self.concurrent_sessions -= 1

        return CrawlerTaskResult(
            task_id=task_id,
            url=url,
            result=result,
            memory_usage=memory_usage,
            peak_memory=peak_memory,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
        )

    async def run_urls(
        self,
        urls: List[str],
        crawler: "AsyncWebCrawler",  # noqa: F821
        config: CrawlerRunConfig,
    ) -> List[CrawlerTaskResult]:
        self.crawler = crawler

        if self.monitor:
            self.monitor.start()

        try:
            pending_tasks = []
            active_tasks = []
            task_queue = []

            for url in urls:
                task_id = str(uuid.uuid4())
                if self.monitor:
                    self.monitor.add_task(task_id, url)
                task_queue.append((url, task_id))

            while task_queue or active_tasks:
                wait_start_time = time.time()
                while len(active_tasks) < self.max_session_permit and task_queue:
                    if psutil.virtual_memory().percent >= self.memory_threshold_percent:
                        # Check if we've exceeded the timeout
                        if time.time() - wait_start_time > self.memory_wait_timeout:
                            raise MemoryError(
                                f"Memory usage above threshold ({self.memory_threshold_percent}%) for more than {self.memory_wait_timeout} seconds"
                            )
                        await asyncio.sleep(self.check_interval)
                        continue

                    url, task_id = task_queue.pop(0)
                    task = asyncio.create_task(self.crawl_url(url, config, task_id))
                    active_tasks.append(task)

                if not active_tasks:
                    await asyncio.sleep(self.check_interval)
                    continue

                done, pending = await asyncio.wait(
                    active_tasks, return_when=asyncio.FIRST_COMPLETED
                )

                pending_tasks.extend(done)
                active_tasks = list(pending)

            return await asyncio.gather(*pending_tasks)
        finally:
            if self.monitor:
                self.monitor.stop()


class SemaphoreDispatcher(BaseDispatcher):
    def __init__(
        self,
        semaphore_count: int = 5,
        max_session_permit: int = 20,
        rate_limiter: Optional[RateLimiter] = None,
        monitor: Optional[CrawlerMonitor] = None,
    ):
        super().__init__(rate_limiter, monitor)
        self.semaphore_count = semaphore_count
        self.max_session_permit = max_session_permit

    async def crawl_url(
        self,
        url: str,
        config: CrawlerRunConfig,
        task_id: str,
        semaphore: asyncio.Semaphore = None,
    ) -> CrawlerTaskResult:
        start_time = datetime.now()
        error_message = ""
        memory_usage = peak_memory = 0.0

        try:
            if self.monitor:
                self.monitor.update_task(
                    task_id, status=CrawlStatus.IN_PROGRESS, start_time=start_time
                )

            if self.rate_limiter:
                await self.rate_limiter.wait_if_needed(url)

            async with semaphore:
                process = psutil.Process()
                start_memory = process.memory_info().rss / (1024 * 1024)
                result = await self.crawler.arun(url, config=config, session_id=task_id)
                end_memory = process.memory_info().rss / (1024 * 1024)

                memory_usage = peak_memory = end_memory - start_memory

                if self.rate_limiter and result.status_code:
                    if not self.rate_limiter.update_delay(url, result.status_code):
                        error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"
                        if self.monitor:
                            self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
                        return CrawlerTaskResult(
                            task_id=task_id,
                            url=url,
                            result=result,
                            memory_usage=memory_usage,
                            peak_memory=peak_memory,
                            start_time=start_time,
                            end_time=datetime.now(),
                            error_message=error_message,
                        )

                if not result.success:
                    error_message = result.error_message
                    if self.monitor:
                        self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
                elif self.monitor:
                    self.monitor.update_task(task_id, status=CrawlStatus.COMPLETED)

        except Exception as e:
            error_message = str(e)
            if self.monitor:
                self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
            result = CrawlResult(
                url=url, html="", metadata={}, success=False, error_message=str(e)
            )

        finally:
            end_time = datetime.now()
            if self.monitor:
                self.monitor.update_task(
                    task_id,
                    end_time=end_time,
                    memory_usage=memory_usage,
                    peak_memory=peak_memory,
                    error_message=error_message,
                )

        return CrawlerTaskResult(
            task_id=task_id,
            url=url,
            result=result,
            memory_usage=memory_usage,
            peak_memory=peak_memory,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
        )

    async def run_urls(
        self,
        crawler: "AsyncWebCrawler",  # noqa: F821
        urls: List[str],
        config: CrawlerRunConfig,
    ) -> List[CrawlerTaskResult]:
        self.crawler = crawler
        if self.monitor:
            self.monitor.start()

        try:
            semaphore = asyncio.Semaphore(self.semaphore_count)
            tasks = []

            for url in urls:
                task_id = str(uuid.uuid4())
                if self.monitor:
                    self.monitor.add_task(task_id, url)
                task = asyncio.create_task(
                    self.crawl_url(url, config, task_id, semaphore)
                )
                tasks.append(task)

            return await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            if self.monitor:
                self.monitor.stop()
