from dataclasses import dataclass
import logging
from typing import Dict, Optional, List, TypeVar
from enum import Enum, auto
from datetime import datetime
from email.utils import parsedate_to_datetime
from math import ceil


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
from abc import ABC, abstractmethod

_LOGGER = logging.getLogger(__name__)

class RateLimitStatus(Enum):
    """Enum for rate limit status."""

    NO_RETRY = auto()
    RETRY = auto()
    CONTINUE = auto()

@dataclass
class RateLimitHeaders:
    """Class to hold rate limit headers."""
    remaining: str
    reset: str
    limit: str

def default_ratelimit_headers() -> List[RateLimitHeaders]:
    """Return a list of default rate limit headers.
    This function returns a list of common rate limit headers used by various APIs.

    :return: List of RateLimitHeaders.
    :rtype: List[RateLimitHeaders]
    """
    return [
        # GitHub style headers.
        RateLimitHeaders(
            remaining="x-ratelimit-remaining",
            reset="x-ratelimit-reset",
            limit="x-ratelimit-limit"
        ),
        # Twitter style headers.
        RateLimitHeaders(
            remaining="x-rate-limit-remaining",
            reset="x-rate-limit-reset",
            limit="x-rate-limit-limit"
        ),
        # https://ioggstream.github.io/draft-polli-ratelimit-headers/draft-polli-ratelimit-headers.html
        RateLimitHeaders(
            remaining="ratelimit-remaining",
            reset="ratelimit-reset",
            limit="ratelimit-limit"
        ),
        # https://github.com/wraithgar/hapi-rate-limit/blob/main/README.md
        RateLimitHeaders(
            remaining="x-ratelimit-userremaining",
            reset="x-ratelimit-userreset",
            limit="x-ratelimit-userlimit"
        ),
        RateLimitHeaders(
            remaining="x-ratelimit-userpathremaining",
            reset="x-ratelimit-userpathreset",
            limit="x-ratelimit-userpathlimit"
        ),
    ]

WorstValT = TypeVar('WorstValT', int, float)

class RateLimiter:
    def __init__(
        self,
        default_rate: float = 5,
        max_burst: int = 20,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: Optional[int] = None,
        rate_limit_codes: Optional[List[int]] = None,
        rate_limit_headers: Optional[List[RateLimitHeaders]] = None,
    ):
        """Initialize the rate limiter.

        :param default_rate: Default rate limit (requests per second).
        :type default_rate: int
        :param max_burst: Maximum burst size (number of requests allowed in a burst).
        :type max_burst: int
        :param base_delay: Base delay for exponential backoff (in seconds).
        :type base_delay: float
        :param max_delay: Maximum delay for exponential backoff (in seconds).
        :type max_delay: float
        :param max_retries: Maximum number of domain retries before failing a request (default: no limit).
        :type max_retries: Optional[int]
        :param rate_limit_codes: List of HTTP status codes that indicate rate limiting (default: 429 and 503).
        :type rate_limit_codes: Optional[List[int]]
        :param rate_limit_headers: List of rate limit headers to check for rate limiting (default: `default_ratelimit_headers()`).
        :type rate_limit_headers: Optional[List[RateLimitHeaders]]
        :raises ValueError: If any of the parameters are invalid.
        """
        if max_retries is not None and max_retries < max_burst:
            raise ValueError("max_retries must be greater than or equal to max_burst")

        if max_burst <= 0:
            raise ValueError("max_burst must be positive")

        if default_rate <= 0:
            raise ValueError("default_rate must be positive")

        if base_delay <= 0:
            raise ValueError("base_delay must be positive")

        if max_delay <= 0:
            raise ValueError("max_delay must be positive")

        if max_delay < base_delay:
            raise ValueError("max_delay must be greater than or equal to base_delay")

        self._max_retries: Optional[int] = max_retries
        self._base_delay: float = base_delay
        self._max_delay: float = max_delay
        self._rate_limit_codes: List[int] = rate_limit_codes or [429, 503]
        self._domains: Dict[str, DomainState] = {}
        self._default_rate: float = default_rate
        self._default_capacity: int = max_burst
        self._rate_limit_headers: List[RateLimitHeaders] = rate_limit_headers or default_ratelimit_headers()

    def _domain(self, url: str) -> DomainState:
        """Get the domain state for the given URL.

        :param url: The URL to get the domain state for.
        :type url: str
        :return: The domain state.
        :rtype: DomainState
        """
        domain: str = urlparse(url).netloc
        state: Optional[DomainState] = self._domains.get(domain)
        if not state:
            state = DomainState(
                rate=self._default_rate,
                max_burst=self._default_capacity,
                base_delay=self._base_delay,
                max_delay=self._max_delay,
            )
            self._domains[domain] = state

        return state

    async def wait_if_needed(self, url: str) -> None:
        """Wait for the rate limit to be available for the given URL."""
        state: DomainState = self._domain(url)
        await state.acquire()

    async def update(self, result: CrawlResultContainer) -> RateLimitStatus:
        """Update the rate limit based on details from the crawl result.

        :param result: The result of the crawl.
        :type result: CrawlResultContainer
        :return: Status indicating whether to retry, stop retrying, or continue.
        :rtype: RateLimitStatus
        """
        # We might have been redirected, so prefer that url to ensure that we
        # don't register stats against the wrong domain.
        state: DomainState = self._domain(result.redirected_url or result.url)
        if result.status_code in self._rate_limit_codes:
            failures: int = await self._update_state(state, result, True)
            if self._max_retries is not None and failures >= self._max_retries:
                return RateLimitStatus.NO_RETRY

            return RateLimitStatus.RETRY

        await self._update_state(state, result, False)

        return RateLimitStatus.CONTINUE


    def _count(self, headers: dict[str, str], header: str) -> Optional[int]:
        """Update the state remaining field from header.

        This function attempts to update the remaining field of state from
        the header value converted to a int.

        If the conversion fails, it returns the default value and does not
        update the state.

        :param headers: The headers dictionary.
        :type headers: dict[str, str]
        :param header: The header key to look for.
        :type header: str
        :param default: The default value to return if the header is not found or cannot be converted.
        :type default: float
        :return: The float value from the header or the default value.
        :rtype: Optional[int]
        """
        value: Optional[str] = headers.get(header)
        if value is None:
            return None

        try:
            return int(value)
        except ValueError:
            return None

    def _reset_delay(self, headers: dict[str, str], header: str, now: float) -> Optional[int]:
        """Return the reset delay determined from the header.

        This function attempts to determine the reset delay from the header value.
        It handles HTTP date times (RFC 2616) and unix epoch timestamps in seconds,
        milliseconds, microseconds, and nanoseconds.

        If all conversions fail, it returns the default value.

        :param headers: The headers dictionary.
        :type headers: dict[str, str]
        :param header: The header key to look for.
        :type header: str
        :param now: The current time in seconds since the epoch.
        :type now: float
        :param default: The default value to return if the header is not found or cannot be converted.
        :type default: int
        :return: The float value relative to now as determined from the header or the default value.
        :rtype: int
        """
        value: Optional[str] = headers.get(header)
        if value is None:
            return None

        try:
            delay: float = float(value)
            # Validated using https://www.epochconverter.com/
            if delay >= 1e16:
                # Timestamp in nanoseconds.
                return ceil(delay / 1e9 - now)

            if delay >= 1e14:
                # Timestamp in microseconds.
                return ceil(delay / 1e6 - now)

            if delay >= 1e11:
                # Timestamp in milliseconds.
                return ceil(delay / 1000 - now)

            if delay >= 1e9:
                # Timestamp in seconds.
                return ceil(delay - now)

            # Delay in seconds.
            return ceil(delay)
        except ValueError:
            # Try to parse as HTTP date time.
            try:
                dt: datetime = parsedate_to_datetime(value)
                return ceil(dt.timestamp() - now)
            except ValueError:
                return None

    async def _update_state(self, state: DomainState, result: CrawlResultContainer, limited: bool) -> int:
        """Update the state of the domain based on the headers if needed.

        :param state: The current state of the domain.
        :type state: DomainState
        :param headers: The headers dictionary.
        :type headers: dict[str, str]
        :param limited: Whether the request was rate limited.
        :type limited: bool
        :return: The number of failures.
        :rtype: int
        """
        # TODO: Remove this just to check basic exponential backoff works.
        #return await state.update(failure=failure)

        if result.response_headers is None:
            return await state.update(limited=limited)

        # Check for know rate limit headers.
        # Some useful references:
        # https://medium.com/@guillaume.viguierjust/rate-limiting-your-restful-api-3148f8e77248
        # https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/
        # https://developer.okta.com/docs/reference/rl-best-practices/
        limit: Optional[int] = None
        remaining: Optional[int] = None
        reset: Optional[int] = None
        rate: Optional[float] = None
        now: float = time.time()
        headers: dict[str, str] = result.response_headers

        # Find the worst case values for limit, remaining, reset and rate.
        for rate_limit_headers in self._rate_limit_headers:
            limit = self._min(limit, self._count(headers, rate_limit_headers.limit))
            remaining = self._min(remaining, self._count(headers, rate_limit_headers.remaining))
            reset = self._max(reset, self._reset_delay(headers, rate_limit_headers.reset, now))
            rate = self._min(rate, limit / reset if reset and limit else None)

        # Retry-After should only be present if we were rate limited
        # but we always check it to keep the code simple.
        # https://datatracker.ietf.org/doc/html/rfc7231#section-7.1.3
        retry_after: Optional[int] = self._reset_delay(headers, "retry-after", now)
        if retry_after:
            # Ensure Retry-After is obeyed.
            remaining = 0
            retry_after = max(reset or 0, retry_after)
        elif remaining is not None and remaining <= 0 and reset:
            retry_after = reset

        _LOGGER.debug(
            "Rate limit for %s: limit=%s, remaining=%s, reset=%s, rate=%s, retry_after=%s, limited=%s status_code=%s",
            result.redirected_url or result.url,
            limit,
            remaining,
            reset,
            rate,
            retry_after,
            limited,
            result.status_code,
        )
        return await state.update(limit=limit, remaining=remaining, retry_after=retry_after, rate=rate, limited=limited)

    def _min(self, a: Optional[WorstValT], b: Optional[WorstValT]) -> Optional[WorstValT]:
        """Return the minimum of two values or None if both are None."""
        return min([x for x in [a, b] if x is not None], default=None)

    def _max(self, a: Optional[WorstValT], b: Optional[WorstValT]) -> Optional[WorstValT]:
        """Return the maximum of two values or None if both are None."""
        return max([x for x in [a, b] if x is not None], default=None)

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

    def _start(self) -> None:
        """
        Start the dispatcher. This method should be called before running any tasks.
        It initializes the monitor if provided.
        """
        if self.monitor:
            self.monitor.start()

    def _stop(self) -> None:
        """
        Stop the dispatcher. This method should be called after all tasks are completed.
        It stops the monitor if configured.
        """
        if self.monitor:
            self.monitor.stop()

    def _add_task(self, task_id: str, url: str):
        """
        Register a new task with the monitor if configured.

        Args:
            task_id: Unique identifier for the task
            url: URL being crawled

        The task is initialized with:
            - status: QUEUED
            - url: The URL to crawl
            - enqueue_time: Current time
            - memory_usage: 0
            - peak_memory: 0
            - wait_time: 0
            - retry_count: 0
        """
        if self.monitor:
            self.monitor.add_task(task_id, url)

    def _update_task(
        self,
        task_id: str,
        status: Optional[CrawlStatus] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        memory_usage: Optional[float] = None,
        peak_memory: Optional[float] = None,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None,
        wait_time: Optional[float] = None
    ):
        """
        Update monitor statistics for a specific task if configured.

        Args:
            task_id: Unique identifier for the task
            status: New status (QUEUED, IN_PROGRESS, COMPLETED, FAILED)
            start_time: When task execution started
            end_time: When task execution ended
            memory_usage: Current memory usage in MB
            peak_memory: Maximum memory usage in MB
            error_message: Error description if failed
            retry_count: Number of retry attempts
            wait_time: Time spent in queue

        Updates task statistics and updates status counts.
        If status changes, decrements old status count and
        increments new status count.
        """
        if self.monitor:
            self.monitor.update_task(
                task_id,
                status=status,
                start_time=start_time,
                end_time=end_time,
                memory_usage=memory_usage,
                peak_memory=peak_memory,
                error_message=error_message,
                retry_count=retry_count,
                wait_time=wait_time,
            )

    def _update_memory_status(self, status: str):
        """
        Update the current memory status.

        Args:
            status: Memory status (NORMAL, PRESSURE, CRITICAL, or custom)

        Also updates the UI to reflect the new status.
        """
        if self.monitor:
            self.monitor.update_memory_status(status)

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
                self._update_memory_status("PRESSURE")

            # Exit memory pressure mode if we go below recovery threshold
            elif self.memory_pressure_mode and self.current_memory_percent <= self.recovery_threshold_percent:
                self.memory_pressure_mode = False
                self._update_memory_status("NORMAL")

            # In critical mode, we might need to take more drastic action
            if self.current_memory_percent >= self.critical_threshold_percent:
                self._update_memory_status("CRITICAL")
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
            self._update_task(
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
            if self.rate_limiter:
                status: RateLimitStatus = await self.rate_limiter.update(result)
                if status == RateLimitStatus.NO_RETRY:
                    error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"
                    self._update_task(task_id, status=CrawlStatus.FAILED)
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
                self._update_task(task_id, status=CrawlStatus.FAILED)
            else:
                self._update_task(task_id, status=CrawlStatus.COMPLETED)

        except Exception as e:
            error_message = str(e)
            self._update_task(task_id, status=CrawlStatus.FAILED, error_message=error_message)
            result = CrawlResultContainer(
                CrawlResult(
                    url=url, html="", metadata={}, success=False, error_message=str(e)
                )
            )
            
        finally:
            end_time = time.time()
            self._update_task(
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
        self._update_task(task_id, status=CrawlStatus.QUEUED, error_message=reason)

    async def run_urls(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> List[CrawlerTaskResult]:
        # Start the memory monitor task
        memory_monitor = asyncio.create_task(self._memory_monitor_task())
        self._start()

        results: List[CrawlerTaskResult] = []

        try:
            # Initialize task queue
            for url in urls:
                task_id = str(uuid.uuid4())
                self._add_task(task_id, url)
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
                        self._update_task(
                            task_id,
                            wait_time=time.time() - enqueue_time,
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
            self._update_memory_status(f"QUEUE_ERROR: {str(e)}")

        finally:
            # Clean up
            memory_monitor.cancel()
            self._stop()

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
                    self._update_task(task_id, wait_time=wait_time)

                except asyncio.TimeoutError:
                    # Queue might be empty or very slow
                    break
        except Exception as e:
            # If anything goes wrong, make sure we refill the queue with what we've got
            self._update_memory_status(f"QUEUE_ERROR: {str(e)}")

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

        self._start()

        try:
            # Initialize task queue
            for url in urls:
                task_id = str(uuid.uuid4())
                self._add_task(task_id, url)
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
                        self._update_task(
                            task_id,
                            wait_time=time.time() - enqueue_time,
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
            self._stop()


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

            self._update_task(
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

                if self.rate_limiter:
                    status: RateLimitStatus = await self.rate_limiter.update(result)
                    if status == RateLimitStatus.NO_RETRY:
                        error_message = f"Rate limit retry count exceeded for domain {urlparse(url).netloc}"

                        self._update_task(task_id, status=CrawlStatus.FAILED)
                    elif status == RateLimitStatus.RETRY:
                        # TODO: Requeue for retry
                        self._update_task(task_id, status=CrawlStatus.QUEUED, error_message="Requeued due to rate limit")

                        return None

                if not result.success:
                    error_message = result.error_message
                    self._update_task(task_id, status=CrawlStatus.FAILED)
                else:
                    self._update_task(task_id, status=CrawlStatus.COMPLETED)

        except Exception as e:
            error_message = str(e)
            self._update_task(task_id, status=CrawlStatus.FAILED, error_message=error_message)
            result = CrawlResultContainer(
                CrawlResult(
                    url=url, html="", metadata={}, success=False, error_message=str(e)
                )
            )

        finally:
            end_time: float = time.time()
            self._update_task(
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
        self._start()

        try:
            semaphore = asyncio.Semaphore(self.semaphore_count)
            tasks = []

            for url in urls:
                task_id = str(uuid.uuid4())
                self._add_task(task_id, url)
                task = asyncio.create_task(
                    self._crawl_url(crawler, url, config, task_id, semaphore)
                )
                tasks.append(task)

            results: List[Optional[CrawlerTaskResult]] = await asyncio.gather(*tasks)
            return [result for result in results if result is not None]
        finally:
            self._stop()

    async def run_urls_stream(
        self,
        urls: List[str],
        crawler: AsyncWebCrawler,
        config: CrawlerRunConfig,
    ) -> AsyncGenerator[CrawlerTaskResult, None]:
        self._start()

        try:
            semaphore = asyncio.Semaphore(self.semaphore_count)
            tasks = []

            for url in urls:
                task_id = str(uuid.uuid4())
                self._add_task(task_id, url)
                task = asyncio.create_task(
                    self._crawl_url(crawler, url, config, task_id, semaphore)
                )
                tasks.append(task)

            for task in asyncio.as_completed(tasks):
                result: Optional[CrawlerTaskResult] = await task
                if result is not None:
                    yield result
        finally:
            self._stop()
