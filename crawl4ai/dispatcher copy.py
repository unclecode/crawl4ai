from typing import Dict, Optional, Any, List, Tuple
from .models import CrawlResult
from .async_webcrawler import AsyncWebCrawler
from .async_configs import BrowserConfig, CrawlerRunConfig
from .markdown_generation_strategy import DefaultMarkdownGenerator
from .content_filter_strategy import PruningContentFilter
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.style import Style
from rich import box
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import time
import psutil
import asyncio
import uuid
from urllib.parse import urlparse
import random


@dataclass
class DomainState:
    last_request_time: float = 0
    current_delay: float = 0
    fail_count: int = 0

@dataclass
class CrawlerTaskResult:
    task_id: str
    url: str
    result: CrawlResult
    memory_usage: float
    peak_memory: float
    start_time: datetime
    end_time: datetime
    error_message: str = ""

class CrawlStatus(Enum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class CrawlStats:
    task_id: str
    url: str
    status: CrawlStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    memory_usage: float = 0.0
    peak_memory: float = 0.0
    error_message: str = ""
    
    @property
    def duration(self) -> str:
        if not self.start_time:
            return "0:00"
        end = self.end_time or datetime.now()
        duration = end - self.start_time
        return str(timedelta(seconds=int(duration.total_seconds())))

class DisplayMode(Enum):
    DETAILED = "DETAILED"
    AGGREGATED = "AGGREGATED"

class RateLimiter:
    def __init__(
        self,
        base_delay: Tuple[float, float] = (1.0, 3.0),
        max_delay: float = 60.0,
        max_retries: int = 3,
        rate_limit_codes: List[int] = [429, 503]
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.rate_limit_codes = rate_limit_codes
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
                state.current_delay * 2 * random.uniform(0.75, 1.25),
                self.max_delay
            )
        else:
            # Gradually reduce delay on success
            state.current_delay = max(
                random.uniform(*self.base_delay),
                state.current_delay * 0.75
            )
            state.fail_count = 0
            
        return True

class CrawlerMonitor:
    def __init__(self, max_visible_rows: int = 15, display_mode: DisplayMode = DisplayMode.DETAILED):
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
        self.stats[task_id] = CrawlStats(task_id=task_id, url=url, status=CrawlStatus.QUEUED)
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
            show_lines=True
        )
        
        # Calculate statistics
        total_tasks = len(self.stats)
        queued = sum(1 for stat in self.stats.values() if stat.status == CrawlStatus.QUEUED)
        in_progress = sum(1 for stat in self.stats.values() if stat.status == CrawlStatus.IN_PROGRESS)
        completed = sum(1 for stat in self.stats.values() if stat.status == CrawlStatus.COMPLETED)
        failed = sum(1 for stat in self.stats.values() if stat.status == CrawlStatus.FAILED)
        
        # Memory statistics
        current_memory = self.process.memory_info().rss / (1024 * 1024)
        total_task_memory = sum(stat.memory_usage for stat in self.stats.values())
        peak_memory = max((stat.peak_memory for stat in self.stats.values()), default=0.0)
        
        # Duration
        duration = datetime.now() - self.start_time
        
        # Create status row
        table.add_column("Status", style="bold cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        
        table.add_row(
            "Total Tasks",
            str(total_tasks),
            "100%"
        )
        table.add_row(
            "[yellow]In Queue[/yellow]",
            str(queued),
            f"{(queued/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
        )
        table.add_row(
            "[blue]In Progress[/blue]",
            str(in_progress),
            f"{(in_progress/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
        )
        table.add_row(
            "[green]Completed[/green]",
            str(completed),
            f"{(completed/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
        )
        table.add_row(
            "[red]Failed[/red]",
            str(failed),
            f"{(failed/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
        )
        
        # Add memory information
        table.add_section()
        table.add_row(
            "[magenta]Current Memory[/magenta]",
            f"{current_memory:.1f} MB",
            ""
        )
        table.add_row(
            "[magenta]Total Task Memory[/magenta]",
            f"{total_task_memory:.1f} MB",
            ""
        )
        table.add_row(
            "[magenta]Peak Task Memory[/magenta]",
            f"{peak_memory:.1f} MB",
            ""
        )
        table.add_row(
            "[yellow]Runtime[/yellow]",
            str(timedelta(seconds=int(duration.total_seconds()))),
            ""
        )
        
        return table

    def _create_detailed_table(self) -> Table:
        table = Table(
            box=box.ROUNDED,
            title="Crawler Performance Monitor",
            title_style="bold magenta",
            header_style="bold blue"
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
        active_count = sum(1 for stat in self.stats.values() 
                         if stat.status == CrawlStatus.IN_PROGRESS)
        completed_count = sum(1 for stat in self.stats.values() 
                            if stat.status == CrawlStatus.COMPLETED)
        failed_count = sum(1 for stat in self.stats.values() 
                         if stat.status == CrawlStatus.FAILED)
        
        table.add_row(
            "[bold yellow]SUMMARY",
            f"Total: {len(self.stats)}",
            f"Active: {active_count}",
            f"{total_memory:.1f}",
            f"{self.process.memory_info().rss / (1024 * 1024):.1f}",
            str(timedelta(seconds=int((datetime.now() - self.start_time).total_seconds()))),
            f"✓{completed_count} ✗{failed_count}",
            style="bold"
        )
        
        table.add_section()
        
        # Add rows for each task
        visible_stats = sorted(
            self.stats.values(),
            key=lambda x: (
                x.status != CrawlStatus.IN_PROGRESS,
                x.status != CrawlStatus.QUEUED,
                x.end_time or datetime.max
            )
        )[:self.max_visible_rows]
        
        for stat in visible_stats:
            status_style = {
                CrawlStatus.QUEUED: "white",
                CrawlStatus.IN_PROGRESS: "yellow",
                CrawlStatus.COMPLETED: "green",
                CrawlStatus.FAILED: "red"
            }[stat.status]
            
            table.add_row(
                stat.task_id[:8],  # Show first 8 chars of task ID
                stat.url[:40] + "..." if len(stat.url) > 40 else stat.url,
                f"[{status_style}]{stat.status.value}[/{status_style}]",
                f"{stat.memory_usage:.1f}",
                f"{stat.peak_memory:.1f}",
                stat.duration,
                stat.error_message[:40] if stat.error_message else ""
            )
        
        return table

    def _create_table(self) -> Table:
        """Creates the appropriate table based on display mode"""
        if self.display_mode == DisplayMode.AGGREGATED:
            return self._create_aggregated_table()
        return self._create_detailed_table()

class MemoryAdaptiveDispatcher:
    def __init__(
        self,
        crawler: AsyncWebCrawler,
        memory_threshold_percent: float = 70.0,
        check_interval: float = 1.0,
        max_session_permit: int = 20,
        enable_rate_limiting: bool = False,
        rate_limit_config: Optional[Dict[str, Any]] = None
    ):
        self.crawler = crawler
        self.memory_threshold_percent = memory_threshold_percent
        self.check_interval = check_interval
        self.max_session_permit = max_session_permit
        self.concurrent_sessions = 0
        self.enable_rate_limiting = enable_rate_limiting
        self.rate_limiter = RateLimiter(**(rate_limit_config or {})) if enable_rate_limiting else None

    async def crawl_url(
        self, 
        url: str, 
        config: CrawlerRunConfig, 
        task_id: str,
        monitor: Optional[CrawlerMonitor] = None
    ) -> CrawlerTaskResult:
        start_time = datetime.now()
        error_message = ""
        memory_usage = peak_memory = 0.0
        
        try:
            if monitor:
                monitor.update_task(task_id, status=CrawlStatus.IN_PROGRESS, start_time=start_time)
            self.concurrent_sessions += 1
            
            if self.enable_rate_limiting:
                await self.rate_limiter.wait_if_needed(url)
            
            process = psutil.Process()
            start_memory = process.memory_info().rss / (1024 * 1024)
            result = await self.crawler.arun(url, config=config, session_id=task_id)
            end_memory = process.memory_info().rss / (1024 * 1024)
            
            memory_usage = peak_memory = end_memory - start_memory
            
            if self.enable_rate_limiting and result.status_code:
                if not self.rate_limiter.update_delay(url, result.status_code):
                    error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"
                    if monitor:
                        monitor.update_task(task_id, status=CrawlStatus.FAILED)
                    return CrawlerTaskResult(
                        task_id=task_id,
                        url=url,
                        result=result,
                        memory_usage=memory_usage,
                        peak_memory=peak_memory,
                        start_time=start_time,
                        end_time=datetime.now(),
                        error_message=error_message
                    )
            
            if not result.success:
                error_message = result.error_message
                if monitor:
                    monitor.update_task(task_id, status=CrawlStatus.FAILED)
            elif monitor:
                monitor.update_task(task_id, status=CrawlStatus.COMPLETED)
                
        except Exception as e:
            error_message = str(e)
            if monitor:
                monitor.update_task(task_id, status=CrawlStatus.FAILED)
            result = CrawlResult(url = url, html = "", metadata = {}, success=False, error_message=str(e))
            
        finally:
            end_time = datetime.now()
            if monitor:
                monitor.update_task(
                    task_id,
                    end_time=end_time,
                    memory_usage=memory_usage,
                    peak_memory=peak_memory,
                    error_message=error_message
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
            error_message=error_message
        )

    async def run_urls(
        self, 
        urls: List[str], 
        config: CrawlerRunConfig,
        monitor: Optional[CrawlerMonitor] = None
    ) -> List[CrawlerTaskResult]:
        if monitor:
            monitor.start()
            
        try:
            pending_tasks = []
            active_tasks = []
            task_queue = []

            # Queue all tasks
            for url in urls:
                task_id = str(uuid.uuid4())
                if monitor:
                    monitor.add_task(task_id, url)
                task_queue.append((url, task_id))

            while task_queue or active_tasks:
                # Fill up to max_session_permit
                while len(active_tasks) < self.max_session_permit and task_queue:
                    if psutil.virtual_memory().percent >= self.memory_threshold_percent:
                        break
                        
                    url, task_id = task_queue.pop(0)
                    task = asyncio.create_task(self.crawl_url(url, config, task_id, monitor))
                    active_tasks.append(task)
                    
                if not active_tasks:
                    await asyncio.sleep(self.check_interval)
                    continue
                    
                done, pending = await asyncio.wait(
                    active_tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                pending_tasks.extend(done)
                active_tasks = list(pending)

            return await asyncio.gather(*pending_tasks)
        finally:
            if monitor:
                monitor.stop()        

async def main():
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48)
        ),
        cache_mode=CacheMode.BYPASS
    )
    
    urls = ["https://example.com/page1"] * 10

    async with AsyncWebCrawler(config=browser_config) as crawler:
        dispatcher = MemoryAdaptiveDispatcher(
            crawler=crawler,
            memory_threshold_percent=70.0,
            check_interval=1.0,
            max_session_permit=10
        )
        dispatcher = MemoryAdaptiveDispatcher(
            crawler=crawler,
            enable_rate_limiting=True,
            rate_limit_config={
                'base_delay': (1.0, 3.0),  # Random range
                'max_delay': 60.0,
                'max_retries': 3,
                'rate_limit_codes': [429, 503]
            }
        )
        
        # Optional monitor
        monitor = CrawlerMonitor(max_visible_rows=15, display_mode=DisplayMode.DETAILED)
        results = await dispatcher.run_urls(urls, run_config, monitor=monitor)

if __name__ == "__main__":
    asyncio.run(main())