from typing import Dict, Optional, List, Tuple
from enum import Enum, auto
from datetime import datetime
from email.utils import parsedate_to_datetime

from .async_configs import CrawlerRunConfig
from .models import (
    CrawlResult,
    CrawlResultContainer,
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

class RateLimitStatus(Enum):
    """Enum for rate limit status."""

    NO_RETRY = auto()
    RETRY = auto()
    CONTINUE = auto()


class RateLimiter:
    def __init__(
        self,
        base_delay: Tuple[float, float] = (1.0, 3.0),
        max_delay: float = 60.0,
        max_retries: int = 3,
        rate_limit_codes: Optional[List[int]] = None,
    ):
        """Initialize the rate limiter.

        :param base_delay: Base delay range (min, max) in seconds.
        :type base_delay: Tuple[float, float]
        :param max_delay: Maximum delay in seconds for exponential backoff. Rate limit headers can exceed this.
        :type max_delay: float
        :param max_retries: Maximum number of retries before giving up.
        :type max_retries: int
        :param rate_limit_codes: List of HTTP status codes that indicate rate limiting (default: 429 and 503).
        :type rate_limit_codes: Optional[List[int]]
        """
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

    def update_delay(self, result: CrawlResultContainer) -> RateLimitStatus:
        """Update the delay based on the status code.

        :param result: The result of the crawl.
        :type result: CrawlResultContainer
        :return: Status indicating whether to retry, stop retrying, or continue.
        :rtype: RateLimitStatus
        """
        domain = self.get_domain(result.url)
        state: DomainState = self.domains[domain]

        if result.status_code in self.rate_limit_codes:
            state.fail_count += 1
            if state.fail_count > self.max_retries:
                return RateLimitStatus.NO_RETRY

            state.current_delay = self.retry_after(state.current_delay, result.response_headers)
            return RateLimitStatus.RETRY

        # Gradually reduce delay on success
        state.current_delay = max(random.uniform(*self.base_delay), state.current_delay * 0.75)
        state.fail_count = 0

        return RateLimitStatus.CONTINUE


    def limit_value(self, headers: dict[str, str], header: str, default: float = 0) -> float:
        """Return a float representation of the header value.

        This function attempts to convert the header value to a float.
        If the conversion fails, it returns the default value.

        :param headers: The headers dictionary.
        :type headers: dict[str, str]
        :param header: The header key to look for.
        :type header: str
        :param default: The default value to return if the header is not found or cannot be converted.
        :type default: float
        :return: The float value from the header or the default value.
        :rtype: float
        """
        value: Optional[str] = headers.get(header)
        if value is None:
            return default

        try:
            return float(value)
        except ValueError:
            return default

    def limit_delay(self, headers: dict[str, str], header: str, now: float, default: float = 0) -> float:
        """Return limit delay from headers.

        This function attempts to convert the header value to delay relative to the
        current time. It handles HTTP date times (RFC 2616) and unix epoch timestamps
        in seconds or milliseconds.

        If all conversions fail, it returns the default value.

        :param headers: The headers dictionary.
        :type headers: dict[str, str]
        :param header: The header key to look for.
        :type header: str
        :param now: The current time in seconds since the epoch.
        :type now: float
        :param default: The default value to return if the header is not found or cannot be converted.
        :type default: float
        :return: The float value from the header or the default value.
        :rtype: float
        """
        value: Optional[str] = headers.get(header)
        if value is None:
            return default

        try:
            delay: float = float(value)
            if delay > now:
                # Timestamp, convert to delay.
                if delay / 1000 > now:
                    # Delay is in milliseconds, convert to seconds.
                    delay /= 1000

                return delay - now

            return delay
        except ValueError:
            try:
                dt: datetime = parsedate_to_datetime(value)
                return dt.timestamp() - now
            except ValueError:
                return default

    def remaining_reset(self, headers: dict[str, str], now: float, remaining_header: str, reset_header: str) -> float:
        """Return the remaining time until reset.

        :param headers: The headers dictionary.
        :type headers: dict[str, str]
        :param now: The current time in seconds since the epoch.
        :type now: float
        :param remaining_header: The header key for remaining requests.
        :type remaining_header: str
        :param reset_header: The header key for reset time.
        :type reset_header: str
        :return: The remaining time until reset in seconds or -1 if not applicable.
        """
        # We use a default value of 1 to handle missing remaining header.
        if (value := self.limit_value(headers, remaining_header, 1)) <= 0:
            if (value := self.limit_delay(headers, reset_header, now)) > 0:
                return value

        return -1

    def retry_after(self, current_delay: float, headers: Optional[dict[str, str]]) -> float:
        """Return the delay to wait before retrying.

        This function checks the headers for rate limit information and calculates
        the delay based on the values found. If no relevant headers are found, it
        falls back to an exponential backoff strategy.

        :param current_delay: The current delay to use for exponential backoff.
        :type current_delay: float
        :param headers: The headers dictionary.
        :type headers: Optional[dict[str, str]]
        :return: The delay in seconds to wait before retrying.
        :rtype: float
        """
        if headers is not None:
            # Check for know rate limit headers.
            # https://medium.com/@guillaume.viguierjust/rate-limiting-your-restful-api-3148f8e77248
            # https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
            now: float = time.time()
            value: float

            # https://datatracker.ietf.org/doc/html/rfc7231#section-7.1.3
            if (value := self.limit_delay(headers, "retry-after", now)) > 0:
                return value

            # https://ioggstream.github.io/draft-polli-ratelimit-headers/draft-polli-ratelimit-headers.html
            # We use a default value of 1 to handle missing remaining header.
            if (value := self.limit_value(headers, "ratelimit-remaining", 1)) <= 0:
                if (value := self.limit_delay(headers, "ratelimit-reset", now)) > 0:
                    return value

            # Handle missing remaining header.
            # https://ioggstream.github.io/draft-polli-ratelimit-headers/draft-polli-ratelimit-headers.html#name-missing-remaining-informati
            elif (value := self.limit_delay(headers, "ratelimit-reset", now)) > 0:
                return value

            # GitHub style headers.
            if (value := self.remaining_reset(headers, now, "x-ratelimit-remaining", "x-ratelimit-reset")) > 0:
                return value

            # Twitter style headers.
            if (value := self.remaining_reset(headers, now, "x-rate-limit-remaining", "x-rate-limit-reset")) > 0:
                return value

            # https://github.com/wraithgar/hapi-rate-limit/blob/main/README.md
            if (value := self.remaining_reset(headers, now, "x-ratelimit-userremaining", "x-ratelimit-userreset")) > 0:
                return value

            if (
                value := self.remaining_reset(
                    headers, now, "x-ratelimit-userpathremaining", "x-ratelimit-userpathreset"
                )
            ) > 0:
                return value

        # Fallback to exponential backoff with random jitter.
        return min(current_delay * 2 * random.uniform(0.75, 1.25), self.max_delay)

class BaseDispatcher(ABC):
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        monitor: Optional[CrawlerMonitor] = None,
    ):
        self._domain_last_hit: Dict[str, float] = {}
        self.concurrent_sessions = 0
        self.rate_limiter = rate_limiter
        self.monitor = monitor

    @abstractmethod
    async def run_urls(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> List[CrawlerTaskResult]:
        pass

    @abstractmethod
    async def run_urls_stream(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlerTaskResult, None]:
        yield NotImplemented


class MemoryAdaptiveDispatcher(BaseDispatcher):
    def __init__(
        self,
        memory_threshold_percent: float = 90.0,
        critical_threshold_percent: float = 95.0,  # New critical threshold
        recovery_threshold_percent: float = 85.0,  # New recovery threshold
        check_interval: float = 1.0,
        max_session_permit: int = 20,
        fairness_timeout: float = 600.0,  # 10 minutes before prioritizing long-waiting URLs
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
        self.result_queue = asyncio.Queue()
        self.task_queue = asyncio.PriorityQueue()  # Priority queue for better management
        self.memory_pressure_mode = False  # Flag to indicate when we're in memory pressure mode
        self.current_memory_percent = 0.0  # Track current memory usage
        
    async def _memory_monitor_task(self):
        """Background task to continuously monitor memory usage and update state"""
        while True:
            self.current_memory_percent = psutil.virtual_memory().percent
            
            # Enter memory pressure mode if we cross the threshold
            if not self.memory_pressure_mode and self.current_memory_percent >= self.memory_threshold_percent:
                self.memory_pressure_mode = True
                if self.monitor:
                    self.monitor.update_memory_status("PRESSURE")
            
            # Exit memory pressure mode if we go below recovery threshold
            elif self.memory_pressure_mode and self.current_memory_percent <= self.recovery_threshold_percent:
                self.memory_pressure_mode = False
                if self.monitor:
                    self.monitor.update_memory_status("NORMAL")
            
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

    async def _crawl_url(
        self,
        crawler: AsyncWebCrawler,
        url: str,
        config: CrawlerRunConfig,
        task_id: str,
        retry_count: int = 0,
    ) -> Optional[CrawlerTaskResult]:
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
                await self._requeue_task(
                    url,
                    task_id,
                    reason="Requeued due to critical memory pressure",
                    start_time=start_time,
                    retry_count=retry_count,
                )
                return None

            # Execute the crawl
            result: CrawlResultContainer = await crawler.arun(url, config=config, session_id=task_id)

            # Measure memory usage
            end_memory = process.memory_info().rss / (1024 * 1024)
            memory_usage = peak_memory = end_memory - start_memory
            
            # Handle rate limiting
            if self.rate_limiter and result.status_code:
                status: RateLimitStatus = self.rate_limiter.update_delay(result)
                if status == RateLimitStatus.NO_RETRY:
                    error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"
                    if self.monitor:
                        self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
                elif status == RateLimitStatus.RETRY:
                    # Requeue the task with increased priority
                    await self._requeue_task(
                        url=url,
                        task_id=task_id,
                        reason="Requeued due to rate limit",
                        start_time=start_time,
                        retry_count=retry_count,
                    )
                    return None

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
            result = CrawlResultContainer(
                CrawlResult(
                    url=url, html="", metadata={}, success=False, error_message=str(e)
                )
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
            error_message=error_message or "",
            retry_count=retry_count
        )

    async def _requeue_task(
        self, url: str, task_id: str, reason: str, start_time: float, retry_count: int
    ) -> None:
        """Requeue the task with increased priority and retry count.

        :param url: The URL to requeue.
        :type url: str
        :param task_id: The ID of the task.
        :type task_id: str
        :param reason: The reason for requeuing.
        :type reason: str
        :param start_time: The time the task started.
        :type start_time: float
        :param retry_count: The current retry count.
        :type retry_count: int
        """
        enqueue_time: float = time.time()
        retry_count += 1
        priority = self._get_priority_score(enqueue_time - start_time, retry_count)
        await self.task_queue.put((priority, (url, task_id, retry_count, enqueue_time)))

        if self.monitor:
            self.monitor.update_task(task_id, status=CrawlStatus.QUEUED, error_message=reason)

    async def run_urls(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> List[CrawlerTaskResult]:
        # Start the memory monitor task
        memory_monitor = asyncio.create_task(self._memory_monitor_task())
        
        if self.monitor:
            self.monitor.start()

        results: List[CrawlerTaskResult] = []

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
                # If memory pressure is low, start new tasks
                if not self.memory_pressure_mode and len(active_tasks) < self.max_session_permit:
                    try:
                        # Try to get a task with timeout to avoid blocking indefinitely
                        priority, (url, task_id, retry_count, enqueue_time) = await asyncio.wait_for(
                            self.task_queue.get(), timeout=0.1
                        )
                        
                        # Create and start the task
                        task = asyncio.create_task(
                            self._crawl_url(crawler, url, config, task_id, retry_count)
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
                        result: Optional[CrawlerTaskResult] = await completed_task
                        if result is not None:
                            results.append(result)

                    # Update active tasks list
                    active_tasks = list(pending)
                else:
                    # If no active tasks but still waiting, sleep briefly
                    await asyncio.sleep(self.check_interval / 2)
                    
                # Update priorities for waiting tasks if needed
                await self._update_queue_priorities()
        except Exception as e:
            if self.monitor:
                self.monitor.update_memory_status(f"QUEUE_ERROR: {str(e)}")                
        
        finally:
            # Clean up
            memory_monitor.cancel()
            if self.monitor:
                self.monitor.stop()

        return results

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
            if self.monitor:
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
                # If memory pressure is low, start new tasks
                if not self.memory_pressure_mode and len(active_tasks) < self.max_session_permit:
                    try:
                        # Try to get a task with timeout
                        priority, (url, task_id, retry_count, enqueue_time) = await asyncio.wait_for(
                            self.task_queue.get(), timeout=0.1
                        )
                        
                        # Create and start the task
                        task = asyncio.create_task(
                            self._crawl_url(crawler, url, config, task_id, retry_count)
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
                        result: Optional[CrawlerTaskResult] = await completed_task
                        if result is not None:
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

    async def _crawl_url(
        self,
        crawler: AsyncWebCrawler,
        url: str,
        config: CrawlerRunConfig,
        task_id: str,
        semaphore: Optional[asyncio.Semaphore] = None,
    ) -> Optional[CrawlerTaskResult]:
        start_time = time.time()
        error_message = ""
        memory_usage = peak_memory = 0.0

        try:
            if semaphore is None:
                raise ValueError(f"Semaphore must be provided to {self.__class__.__name__}")

            if self.monitor:
                self.monitor.update_task(
                    task_id, status=CrawlStatus.IN_PROGRESS, start_time=start_time
                )

            if self.rate_limiter:
                await self.rate_limiter.wait_if_needed(url)

            async with semaphore:
                process = psutil.Process()
                start_memory = process.memory_info().rss / (1024 * 1024)
                result: CrawlResultContainer = await crawler.arun(url, config=config, session_id=task_id)
                end_memory = process.memory_info().rss / (1024 * 1024)

                memory_usage = peak_memory = end_memory - start_memory

                if self.rate_limiter and result.status_code:
                    status: RateLimitStatus = self.rate_limiter.update_delay(result)
                    if status == RateLimitStatus.NO_RETRY:
                        error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"

                        if self.monitor:
                            self.monitor.update_task(task_id, status=CrawlStatus.FAILED)
                    elif status == RateLimitStatus.RETRY:
                        # TODO: Requeue for retry
                        if self.monitor:
                            self.monitor.update_task(task_id, status=CrawlStatus.QUEUED, error_message="Requeued due to rate limit")

                        return None

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
            result = CrawlResultContainer(
                CrawlResult(
                    url=url, html="", metadata={}, success=False, error_message=str(e)
                )
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
            error_message=error_message or "",
        )

    async def run_urls(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> List[CrawlerTaskResult]:
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
                    self._crawl_url(crawler, url, config, task_id, semaphore)
                )
                tasks.append(task)

            results: List[Optional[CrawlerTaskResult]] = await asyncio.gather(*tasks)
            return [result for result in results if result is not None]
        finally:
            if self.monitor:
                self.monitor.stop()

    async def run_urls_stream(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlerTaskResult, None]:
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
                    self._crawl_url(crawler, url, config, task_id, semaphore)
                )
                tasks.append(task)

            for task in asyncio.as_completed(tasks):
                result: Optional[CrawlerTaskResult] = await task
                if result is not None:
                    yield result
        finally:
            if self.monitor:
                self.monitor.stop()
