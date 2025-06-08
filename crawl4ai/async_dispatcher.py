from typing import Dict, Optional, List, Tuple
from .async_configs import CrawlerRunConfig
from .models import (
    CrawlResult,
    CrawlerTaskResult,
    CrawlStatus,
    DomainState,
)

from .components.crawler_monitor import CrawlerMonitor

from .types import AsyncWebCrawler

from collections.abc import AsyncGenerator

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
        crawler: AsyncWebCrawler,  # noqa: F821
        config: CrawlerRunConfig,
        monitor: Optional[CrawlerMonitor] = None,
    ) -> List[CrawlerTaskResult]:
        pass


class MemoryAdaptiveDispatcher(BaseDispatcher):
    def __init__(
        self,
        memory_threshold_percent: float = 90.0,
        critical_threshold_percent: float = 95.0,  # New critical threshold
        recovery_threshold_percent: float = 85.0,  # New recovery threshold
        check_interval: float = 1.0,
        max_session_permit: int = 20,
        fairness_timeout: float = 600.0,  # 10 minutes before prioritizing long-waiting URLs
        memory_wait_timeout: Optional[float] = 600.0,
        rate_limiter: Optional[RateLimiter] = None,
        monitor: Optional[CrawlerMonitor] = None,
    ):
        super().__init__(rate_limiter, monitor)
        self.memory_threshold_percent = memory_threshold_percent
        self.critical_threshold_percent = critical_threshold_percent
        self.recovery_threshold_percent = recovery_threshold_percent
        self.check_interval = check_interval
        self.max_session_permit = max_session_permit
        self.fairness_timeout = fairness_timeout
        self.memory_wait_timeout = memory_wait_timeout
        self.result_queue = asyncio.Queue()
        self.task_queue = asyncio.PriorityQueue()  # Priority queue for better management
        self.memory_pressure_mode = False  # Flag to indicate when we're in memory pressure mode
        self.current_memory_percent = 0.0  # Track current memory usage
        self._high_memory_start_time: Optional[float] = None
        
    async def _memory_monitor_task(self):
        """Background task to continuously monitor memory usage and update state"""
        while True:
            self.current_memory_percent = psutil.virtual_memory().percent

            # Enter memory pressure mode if we cross the threshold
            if self.current_memory_percent >= self.memory_threshold_percent:
                if not self.memory_pressure_mode:
                    self.memory_pressure_mode = True
                    self._high_memory_start_time = time.time()
                    if self.monitor:
                        self.monitor.update_memory_status("PRESSURE")
                else:
                    if self._high_memory_start_time is None:
                        self._high_memory_start_time = time.time()
                    if (
                        self.memory_wait_timeout is not None
                        and self._high_memory_start_time is not None
                        and time.time() - self._high_memory_start_time >= self.memory_wait_timeout
                    ):
                        raise MemoryError(
                            "Memory usage exceeded threshold for"
                            f" {self.memory_wait_timeout} seconds"
                        )

            # Exit memory pressure mode if we go below recovery threshold
            elif self.memory_pressure_mode and self.current_memory_percent <= self.recovery_threshold_percent:
                self.memory_pressure_mode = False
                self._high_memory_start_time = None
                if self.monitor:
                    self.monitor.update_memory_status("NORMAL")
            elif self.current_memory_percent < self.memory_threshold_percent:
                self._high_memory_start_time = None
            
            # In critical mode, we might need to take more drastic action
            if self.current_memory_percent >= self.critical_threshold_percent:
                if self.monitor:
                    self.monitor.update_memory_status("CRITICAL")
                # We could implement additional memory-saving measures here
                
            await asyncio.sleep(self.check_interval)
    
    def _get_priority_score(self, wait_time: float, retry_count: int) -> float:
        """Calculate priority score (lower is higher priority)
        - URLs waiting longer than fairness_timeout get higher priority
        - More retry attempts decreases priority
        """
        if wait_time > self.fairness_timeout:
            # High priority for long-waiting URLs
            return -wait_time
        # Standard priority based on retries
        return retry_count
    
    async def crawl_url(
        self,
        url: str,
        config: CrawlerRunConfig,
        task_id: str,
        retry_count: int = 0,
    ) -> CrawlerTaskResult:
        start_time = time.time()
        error_message = ""
        memory_usage = peak_memory = 0.0
        
        # Get starting memory for accurate measurement
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024 * 1024)
        
        try:
            if self.monitor:
                self.monitor.update_task(
                    task_id, 
                    status=CrawlStatus.IN_PROGRESS, 
                    start_time=start_time,
                    retry_count=retry_count
                )
                
            self.concurrent_sessions += 1
            
            if self.rate_limiter:
                await self.rate_limiter.wait_if_needed(url)
                
            # Check if we're in critical memory state
            if self.current_memory_percent >= self.critical_threshold_percent:
                # Requeue this task with increased priority and retry count
                enqueue_time = time.time()
                priority = self._get_priority_score(enqueue_time - start_time, retry_count + 1)
                await self.task_queue.put((priority, (url, task_id, retry_count + 1, enqueue_time)))
                
                # Update monitoring
                if self.monitor:
                    self.monitor.update_task(
                        task_id,
                        status=CrawlStatus.QUEUED,
                        error_message="Requeued due to critical memory pressure"
                    )
                
                # Return placeholder result with requeued status
                return CrawlerTaskResult(
                    task_id=task_id,
                    url=url,
                    result=CrawlResult(
                        url=url, html="", metadata={"status": "requeued"}, 
                        success=False, error_message="Requeued due to critical memory pressure"
                    ),
                    memory_usage=0,
                    peak_memory=0,
                    start_time=start_time,
                    end_time=time.time(),
                    error_message="Requeued due to critical memory pressure",
                    retry_count=retry_count + 1
                )
            
            # Execute the crawl
            result = await self.crawler.arun(url, config=config, session_id=task_id)
            
            # Measure memory usage
            end_memory = process.memory_info().rss / (1024 * 1024)
            memory_usage = peak_memory = end_memory - start_memory
            
            # Handle rate limiting
            if self.rate_limiter and result.status_code:
                if not self.rate_limiter.update_delay(url, result.status_code):
                    error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"
                    if self.monitor:
                        self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
                        
            # Update status based on result
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
            end_time = time.time()
            if self.monitor:
                self.monitor.update_task(
                    task_id,
                    end_time=end_time,
                    memory_usage=memory_usage,
                    peak_memory=peak_memory,
                    error_message=error_message,
                    retry_count=retry_count
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
            retry_count=retry_count
        )
        
    async def run_urls(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> List[CrawlerTaskResult]:
        self.crawler = crawler
        
        # Start the memory monitor task
        memory_monitor = asyncio.create_task(self._memory_monitor_task())
        
        if self.monitor:
            self.monitor.start()
            
        results = []

        try:
            # Initialize task queue
            for url in urls:
                task_id = str(uuid.uuid4())
                if self.monitor:
                    self.monitor.add_task(task_id, url)
                # Add to queue with initial priority 0, retry count 0, and current time
                await self.task_queue.put((0, (url, task_id, 0, time.time())))

            active_tasks = []

            # Process until both queues are empty
            while not self.task_queue.empty() or active_tasks:
                if memory_monitor.done():
                    exc = memory_monitor.exception()
                    if exc:
                        for t in active_tasks:
                            t.cancel()
                        raise exc

                # If memory pressure is low, start new tasks
                if not self.memory_pressure_mode and len(active_tasks) < self.max_session_permit:
                    try:
                        # Try to get a task with timeout to avoid blocking indefinitely
                        priority, (url, task_id, retry_count, enqueue_time) = await asyncio.wait_for(
                            self.task_queue.get(), timeout=0.1
                        )
                        
                        # Create and start the task
                        task = asyncio.create_task(
                            self.crawl_url(url, config, task_id, retry_count)
                        )
                        active_tasks.append(task)
                        
                        # Update waiting time in monitor
                        if self.monitor:
                            wait_time = time.time() - enqueue_time
                            self.monitor.update_task(
                                task_id, 
                                wait_time=wait_time,
                                status=CrawlStatus.IN_PROGRESS
                            )
                            
                    except asyncio.TimeoutError:
                        # No tasks in queue, that's fine
                        pass
                        
                # Wait for completion even if queue is starved
                if active_tasks:
                    done, pending = await asyncio.wait(
                        active_tasks, timeout=0.1, return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Process completed tasks
                    for completed_task in done:
                        result = await completed_task
                        results.append(result)
                        
                    # Update active tasks list
                    active_tasks = list(pending)
                else:
                    # If no active tasks but still waiting, sleep briefly
                    await asyncio.sleep(self.check_interval / 2)
                    
                # Update priorities for waiting tasks if needed
                await self._update_queue_priorities()
                
            return results

        except Exception as e:
            if self.monitor:
                self.monitor.update_memory_status(f"QUEUE_ERROR: {str(e)}")                
        
        finally:
            # Clean up
            memory_monitor.cancel()
            if self.monitor:
                self.monitor.stop()
                
    async def _update_queue_priorities(self):
        """Periodically update priorities of items in the queue to prevent starvation"""
        # Skip if queue is empty
        if self.task_queue.empty():
            return
            
        # Use a drain-and-refill approach to update all priorities
        temp_items = []
        
        # Drain the queue (with a safety timeout to prevent blocking)
        try:
            drain_start = time.time()
            while not self.task_queue.empty() and time.time() - drain_start < 5.0:  # 5 second safety timeout
                try:
                    # Get item from queue with timeout
                    priority, (url, task_id, retry_count, enqueue_time) = await asyncio.wait_for(
                        self.task_queue.get(), timeout=0.1
                    )
                    
                    # Calculate new priority based on current wait time
                    current_time = time.time()
                    wait_time = current_time - enqueue_time
                    new_priority = self._get_priority_score(wait_time, retry_count)
                    
                    # Store with updated priority
                    temp_items.append((new_priority, (url, task_id, retry_count, enqueue_time)))
                    
                    # Update monitoring stats for this task
                    if self.monitor and task_id in self.monitor.stats:
                        self.monitor.update_task(task_id, wait_time=wait_time)
                        
                except asyncio.TimeoutError:
                    # Queue might be empty or very slow
                    break
        except Exception as e:
            # If anything goes wrong, make sure we refill the queue with what we've got
            self.monitor.update_memory_status(f"QUEUE_ERROR: {str(e)}")
        
        # Calculate queue statistics
        if temp_items and self.monitor:
            total_queued = len(temp_items)
            wait_times = [item[1][3] for item in temp_items]
            highest_wait_time = time.time() - min(wait_times) if wait_times else 0
            avg_wait_time = sum(time.time() - t for t in wait_times) / len(wait_times) if wait_times else 0
            
            # Update queue statistics in monitor
            self.monitor.update_queue_statistics(
                total_queued=total_queued,
                highest_wait_time=highest_wait_time,
                avg_wait_time=avg_wait_time
            )
        
        # Sort by priority (lowest number = highest priority)
        temp_items.sort(key=lambda x: x[0])
        
        # Refill the queue with updated priorities
        for item in temp_items:
            await self.task_queue.put(item)
                
    async def run_urls_stream(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlerTaskResult, None]:
        self.crawler = crawler
        
        # Start the memory monitor task
        memory_monitor = asyncio.create_task(self._memory_monitor_task())
        
        if self.monitor:
            self.monitor.start()
            
        try:
            # Initialize task queue
            for url in urls:
                task_id = str(uuid.uuid4())
                if self.monitor:
                    self.monitor.add_task(task_id, url)
                # Add to queue with initial priority 0, retry count 0, and current time
                await self.task_queue.put((0, (url, task_id, 0, time.time())))
                
            active_tasks = []
            completed_count = 0
            total_urls = len(urls)

            while completed_count < total_urls:
                if memory_monitor.done():
                    exc = memory_monitor.exception()
                    if exc:
                        for t in active_tasks:
                            t.cancel()
                        raise exc
                # If memory pressure is low, start new tasks
                if not self.memory_pressure_mode and len(active_tasks) < self.max_session_permit:
                    try:
                        # Try to get a task with timeout
                        priority, (url, task_id, retry_count, enqueue_time) = await asyncio.wait_for(
                            self.task_queue.get(), timeout=0.1
                        )
                        
                        # Create and start the task
                        task = asyncio.create_task(
                            self.crawl_url(url, config, task_id, retry_count)
                        )
                        active_tasks.append(task)
                        
                        # Update waiting time in monitor
                        if self.monitor:
                            wait_time = time.time() - enqueue_time
                            self.monitor.update_task(
                                task_id, 
                                wait_time=wait_time,
                                status=CrawlStatus.IN_PROGRESS
                            )
                            
                    except asyncio.TimeoutError:
                        # No tasks in queue, that's fine
                        pass
                        
                # Process completed tasks and yield results
                if active_tasks:
                    done, pending = await asyncio.wait(
                        active_tasks, timeout=0.1, return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for completed_task in done:
                        result = await completed_task
                        
                        # Only count as completed if it wasn't requeued
                        if "requeued" not in result.error_message:
                            completed_count += 1
                            yield result
                        
                    # Update active tasks list
                    active_tasks = list(pending)
                else:
                    # If no active tasks but still waiting, sleep briefly
                    await asyncio.sleep(self.check_interval / 2)
                
                # Update priorities for waiting tasks if needed
                await self._update_queue_priorities()
                
        finally:
            # Clean up
            memory_monitor.cancel()
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
        start_time = time.time()
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
                            end_time=time.time(),
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
            end_time = time.time()
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
        crawler: AsyncWebCrawler,  # noqa: F821
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