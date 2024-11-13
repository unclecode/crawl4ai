from __future__ import annotations
import asyncio
import psutil
import logging
import time
import sqlite3
import aiosqlite
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set, Type
from typing import Awaitable
from pathlib import Path
import json
from datetime import datetime
from typing import ClassVar, Type, Union
import inspect

# Imports from your crawler package
from .async_crawler_strategy import AsyncCrawlerStrategy, AsyncPlaywrightCrawlerStrategy
from .chunking_strategy import ChunkingStrategy, RegexChunking
from .extraction_strategy import ExtractionStrategy
from .models import CrawlResult
from .config import MIN_WORD_THRESHOLD
from .async_webcrawler import AsyncWebCrawler
from .config import MAX_METRICS_HISTORY

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# self.logger.error(f"Executor {self.__class__.__name__}: Error message", exc_info=True)
# self.logger.info(f"Executor {self.__class__.__name__}: Info message")
# self.logger.warning(f"Executor {self.__class__.__name__}: Warning message")


# Enums and Constants
class ExecutionMode(Enum):
    """Execution mode for the crawler executor."""
    SPEED = "speed"
    RESOURCE = "resource"

class TaskState(Enum):
    """Possible states for a crawling task."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

# Types of callbacks we should support
class CallbackType(Enum):
    PRE_EXECUTION = "pre_execution"      # Before processing a URL
    POST_EXECUTION = "post_execution"    # After successful processing
    ON_ERROR = "on_error"               # When an error occurs
    ON_RETRY = "on_retry"               # Before retrying a failed URL
    ON_BATCH_START = "on_batch_start"   # Before starting a batch
    ON_BATCH_END = "on_batch_end"       # After completing a batch
    ON_COMPLETE = "on_complete"         # After all URLs are processed

 
@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    available_memory: int
    timestamp: float

    @classmethod
    def capture(cls) -> 'SystemMetrics':
        """Capture current system metrics."""
        return cls(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            available_memory=psutil.virtual_memory().available,
            timestamp=time.time()
        )

@dataclass
class TaskMetadata:
    """Metadata for a crawling task."""
    url: str
    state: TaskState
    attempts: int = 0
    last_attempt: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Any] = None

@dataclass
class ExecutorMetrics:
    """Performance and resource metrics for the executor."""
    # Performance metrics
    total_urls: int = 0
    completed_urls: int = 0
    failed_urls: int = 0
    start_time: Optional[float] = None
    total_retries: int = 0
    response_times: List[float] = field(default_factory=list)
    
    # Resource metrics
    system_metrics: List[SystemMetrics] = field(default_factory=list)
    active_connections: int = 0
    
    def capture_system_metrics(self):
        """Capture system metrics and enforce history size limit."""
        metrics = SystemMetrics.capture()
        self.system_metrics.append(metrics)
        if len(self.system_metrics) > MAX_METRICS_HISTORY:
            self.system_metrics.pop(0)  # Remove the oldest metric
    
    @property
    def urls_per_second(self) -> float:
        """Calculate URLs processed per second."""
        if not self.start_time or not self.completed_urls:
            return 0.0
        duration = time.time() - self.start_time
        return self.completed_urls / duration if duration > 0 else 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if not self.total_urls:
            return 0.0
        return (self.completed_urls / self.total_urls) * 100
    
    @property
    def retry_rate(self) -> float:
        """Calculate retry rate as percentage."""
        if not self.total_urls:
            return 0.0
        return (self.total_retries / self.total_urls) * 100
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time in seconds."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            "performance": {
                "urls_per_second": self.urls_per_second,
                "success_rate": self.success_rate,
                "retry_rate": self.retry_rate,
                "average_response_time": self.average_response_time,
                "total_urls": self.total_urls,
                "completed_urls": self.completed_urls,
                "failed_urls": self.failed_urls
            },
            "resources": {
                "cpu_utilization": self.system_metrics[-1].cpu_percent if self.system_metrics else 0,
                "memory_usage": self.system_metrics[-1].memory_percent if self.system_metrics else 0,
                "active_connections": self.active_connections
            }
        }

class ResourceMonitor:
    """Monitors and manages system resources."""

    def __init__(self, mode: ExecutionMode):
        self.mode = mode
        self.metrics_history: List[SystemMetrics] = []
        self._setup_thresholds()

    def _setup_thresholds(self):
        """Set up resource thresholds based on execution mode."""
        if self.mode == ExecutionMode.SPEED:
            self.memory_threshold = 80  # 80% memory usage limit
            self.cpu_threshold = 90     # 90% CPU usage limit
        else:
            self.memory_threshold = 40  # 40% memory usage limit
            self.cpu_threshold = 30     # 30% CPU usage limit

    async def check_resources(self) -> bool:
        """Check if system resources are within acceptable limits."""
        metrics = SystemMetrics.capture()
        self.metrics_history.append(metrics)

        # Keep only last hour of metrics
        cutoff_time = time.time() - 3600
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        return (metrics.cpu_percent < self.cpu_threshold and
                metrics.memory_percent < self.memory_threshold)

    def get_optimal_batch_size(self, total_urls: int) -> int:
        metrics = SystemMetrics.capture()
        if self.mode == ExecutionMode.SPEED:
            base_size = min(1000, total_urls)

            # Adjust based on resource usage
            cpu_factor = max(0.0, (self.cpu_threshold - metrics.cpu_percent) / self.cpu_threshold)
            mem_factor = max(0.0, (self.memory_threshold - metrics.memory_percent) / self.memory_threshold)

            min_factor = min(cpu_factor, mem_factor)
            adjusted_size = max(1, int(base_size * min_factor))
            return min(total_urls, adjusted_size)
        else:
            # For resource optimization, use a conservative batch size based on resource usage
            cpu_factor = max(0.1, (self.cpu_threshold - metrics.cpu_percent) / self.cpu_threshold)
            mem_factor = max(0.1, (self.memory_threshold - metrics.memory_percent) / self.memory_threshold)

            min_factor = min(cpu_factor, mem_factor)
            adjusted_size = max(1, int(50 * min_factor))
            return min(total_urls, adjusted_size)

class ExecutorControl:
    """Control interface for the executor."""
    
    def __init__(self):
        self._paused = False
        self._cancelled = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially
        self._lock = asyncio.Lock()  # Lock to protect shared state
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    async def pause(self):
        """Pause the execution."""
        async with self._lock:
            self._paused = True
            self._pause_event.clear()
            
    async def resume(self):
        """Resume the execution."""
        async with self._lock:
            self._paused = False
            self._pause_event.set()
            
    async def cancel(self):
        """Cancel all pending operations."""
        async with self._lock:
            self._cancelled = True
            self._pause_event.set()  # Release any paused operations
            
    async def is_paused(self) -> bool:
        """Check if execution is paused."""
        async with self._lock:
            return self._paused
        
    async def is_cancelled(self) -> bool:
        """Check if execution is cancelled."""
        async with self._lock:
            return self._cancelled
        
    async def wait_if_paused(self, timeout: Optional[float] = None):
        """Wait if execution is paused, with an optional timeout."""
        try:
            await asyncio.wait_for(self._pause_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # Timeout occurred, handle as needed
            async with self._lock:
                self._paused = False  # Optionally reset the paused state
                self._pause_event.set()
            # Optionally log a warning
            self.logger.warning(f"ExecutorControl: wait_if_paused() timed out after {timeout} seconds. Proceeding with execution.")
                
    async def reset(self):
        """Reset control state."""
        async with self._lock:
            self._paused = False
            self._cancelled = False
            self._pause_event.set()


class ExecutorStrategy(ABC):
    """Abstract Base class for executor strategies.
    
    Callbacks:
        - PRE_EXECUTION: Callable[[str, Dict[str, Any]], None]
        - POST_EXECUTION: Callable[[str, Any, Dict[str, Any]], None]
        - ON_ERROR: Callable[[str, Exception, Dict[str, Any]], None]
        - ON_RETRY: Callable[[str, int, Dict[str, Any]], None]
        - ON_BATCH_START: Callable[[List[str], Dict[str, Any]], None]
        - ON_BATCH_END: Callable[[List[str], Dict[str, Any]], None]
        - ON_COMPLETE: Callable[[Dict[str, Any], Dict[str, Any]], None]
    """

    def __init__(
        self,
        crawler: AsyncWebCrawler,
        mode: ExecutionMode,
        # callbacks: Optional[Dict[CallbackType, Callable]] = None,
        callbacks: Optional[Dict[CallbackType, Callable[[Any], Union[Awaitable[None], None]]]] = None,
        persistence_path: Optional[Path] = None,
        **crawl_config_kwargs
    ):
        self.crawler = crawler
        self.mode = mode
        self.callbacks = callbacks or {}
        self.resource_monitor = ResourceMonitor(mode)
        self.tasks: Dict[str, TaskMetadata] = {}
        self.active_tasks: Set[str] = set()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.metrics = ExecutorMetrics()
        self.control = ExecutorControl()
        self.crawl_config_kwargs = crawl_config_kwargs  # Store parameters for arun

    async def get_status(self) -> Dict[str, Any]:
        """Get current executor status and metrics."""
        return {
            "status": {
                "paused": await self.control.is_paused(),
                "cancelled": await self.control.is_cancelled(),
                "active_tasks": len(self.active_tasks)
            },
            "metrics": self.metrics.to_dict()
        }

    async def clear_state(self):
        """Reset executor state."""
        self.tasks.clear()
        self.active_tasks.clear()
        self.metrics = ExecutorMetrics()
        await self.control.reset()
        await self.persistence.clear()  # Implement this method

    async def _execute_callback(
        self,
        callback_type: CallbackType,
        *args,
        **kwargs
    ):
        """Execute callback if it exists."""
        if callback := self.callbacks.get(callback_type):
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                # self.logger.error(f"Callback {callback_type} failed: {e}")
                self.logger.error(f"Executor {self.__class__.__name__}: Callback {callback_type.value} failed: {e}", exc_info=True)

    async def _process_url(self, url: str) -> CrawlResult:
        max_retries = self.crawl_config_kwargs.get('max_retries', 3)
        backoff_factor = self.crawl_config_kwargs.get('backoff_factor', 1)
        attempts = 0

        while attempts <= max_retries:
            # Invoke PRE_EXECUTION callback
            await self._execute_callback(CallbackType.PRE_EXECUTION, url, self.metrics.to_dict())

            """Process a single URL using the crawler."""
            # Wait if execution is paused
            await self.control.wait_if_paused(timeout=300)

            # Check if cancelled
            if await self.control.is_cancelled():
                raise asyncio.CancelledError("Execution was cancelled")

            start_time = time.time()
            self.metrics.active_connections += 1

            try:
                result = await self.crawler.arun(url, **self.crawl_config_kwargs)
                self.metrics.completed_urls += 1
                self.metrics.response_times.append(time.time() - start_time)
                # Invoke POST_EXECUTION callback
                await self._execute_callback(CallbackType.POST_EXECUTION, url, result, self.metrics.to_dict())
                
                return result

            except Exception as e:
                attempts += 1
                self.metrics.failed_urls += 1
                # self.logger.error(f"Error processing URL {url}: {e}")
                self.logger.error(f"Executor {self.__class__.__name__}: Error processing URL {url}: {e}", exc_info=True)
                # Invoke ON_ERROR callback
                await self._execute_callback(CallbackType.ON_ERROR, url, e, self.metrics.to_dict())

                if attempts <= max_retries:
                    # Invoke ON_RETRY callback
                    await self._execute_callback(CallbackType.ON_RETRY, url, attempts, self.metrics.to_dict())
                    # Wait before retrying
                    await asyncio.sleep(backoff_factor * attempts)
                else:
                    raise e

            finally:
                self.metrics.active_connections -= 1
                # Update system metrics
                # INFO: Uncomment this line if you want to capture system metrics after each URL, but it causes a performance hit
                # self.metrics.system_metrics.append(SystemMetrics.capture())
                # Exit the loop if successful or retries exceeded
                if attempts > max_retries:
                    break                

    async def execute(self, urls: List[str]) -> Dict[str, Any]:
        """Execute crawling tasks."""
        # Initialize metrics
        self.metrics.total_urls = len(urls)
        self.metrics.start_time = time.time()

        # Create context with metrics (used for callbacks)
        context = {
            "mode": self.mode,
            "start_time": self.metrics.start_time,
            "total_urls": self.metrics.total_urls
        }

        # Invoke ON_BATCH_START callback
        await self._execute_callback(CallbackType.ON_BATCH_START, urls, context)

        results = {}
        batch_errors = []

        # Use the crawler within an async context manager
        async with self.crawler:
            # Check for cancellation before starting
            if await self.control.is_cancelled():
                raise asyncio.CancelledError("Execution was cancelled")

            # Wait if paused
            await self.control.wait_if_paused(timeout=300)

            # Prepare list of batches
            batches = []
            total_urls_remaining = len(urls)
            index = 0

            while index < len(urls):
                batch_size = self.resource_monitor.get_optimal_batch_size(total_urls_remaining)
                batch_urls = urls[index:index + batch_size]
                batches.append(batch_urls)
                index += batch_size
                total_urls_remaining -= batch_size

            # Process each batch
            for batch_urls in batches:
                # Check for cancellation
                if await self.control.is_cancelled():
                    raise asyncio.CancelledError("Execution was cancelled")

                # Wait if paused
                await self.control.wait_if_paused(timeout=300)

                try:
                    # Process the batch
                    batch_results = await self.process_batch(batch_urls)
                    # Update results
                    results.update(batch_results)
                    # Capture system metrics after each batch
                    self.metrics.capture_system_metrics()
                    # Update system metrics after each batch
                    # self.metrics.system_metrics.append(SystemMetrics.capture()) # Has memory leak issue
                    # Invoke ON_BATCH_END callback
                    await self._execute_callback(CallbackType.ON_BATCH_END, batch_urls, context)
                except Exception as e:
                    # Handle batch-level exceptions
                    self.logger.error(f"Error processing batch: {e}")
                    await self._execute_callback(CallbackType.ON_ERROR, "batch", e, context)
                    # Collect the error
                    batch_errors.append((batch_urls, e))
                    # Continue to next batch instead of raising
                    continue

        # Execution complete
        await self._execute_callback(CallbackType.ON_COMPLETE, results, context)

        # Log final metrics and batch errors if any
        final_status = await self.get_status()
        # self.logger.info(f"Execution completed. Metrics: {final_status}")
        self.logger.info(f"Executor {self.__class__.__name__}: Execution completed. Metrics: {final_status}")

        if batch_errors:
            # self.logger.warning(f"Execution completed with errors in {len(batch_errors)} batches.")
            self.logger.warning(f"Executor {self.__class__.__name__}: Execution completed with errors in {len(batch_errors)} batches.")

        return results


    @abstractmethod
    async def process_batch(self, batch_urls: List[str]) -> Dict[str, Any]:
        """Process a batch of URLs."""
        pass

class SpeedOptimizedExecutor(ExecutorStrategy):
    """Executor optimized for speed."""

    def __init__(
        self,
        crawler: AsyncWebCrawler,
        callbacks: Optional[Dict[CallbackType, Callable]] = None,
        persistence_path: Optional[Path] = None,
        word_count_threshold=MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = None,
        bypass_cache: bool = False,
        css_selector: str = None,
        screenshot: bool = False,
        user_agent: str = None,
        verbose=True,
        connection_pool_size: int = 1000,
        dns_cache_size: int = 10000,
        backoff_factor: int = 1,
        **kwargs
    ):
        if chunking_strategy is None:
            chunking_strategy = RegexChunking()

        super().__init__(
            crawler=crawler,
            mode=ExecutionMode.SPEED,
            callbacks=callbacks,
            persistence_path=persistence_path,
            word_count_threshold=word_count_threshold,
            extraction_strategy=extraction_strategy,
            chunking_strategy=chunking_strategy,
            bypass_cache=bypass_cache,
            css_selector=css_selector,
            screenshot=screenshot,
            user_agent=user_agent,
            verbose=verbose,
            **kwargs
        )

        self.connection_pool_size = connection_pool_size
        self.dns_cache_size = dns_cache_size
        self.backoff_factor = backoff_factor

        self.logger.info(
            # "Initialized speed-optimized executor with:"
            f"Executor {self.__class__.__name__}: Initialized with:"
            f" connection_pool_size={self.connection_pool_size},"
            f" dns_cache_size={self.dns_cache_size}"
        )

    async def process_batch(self, batch_urls: List[str]) -> Dict[str, Any]:
        """Process a batch of URLs concurrently."""
        batch_tasks = [self._process_url(url) for url in batch_urls]

        # Execute batch with concurrency control
        batch_results_list = await asyncio.gather(*batch_tasks, return_exceptions=True)

        batch_results = {}
        for url, result in zip(batch_urls, batch_results_list):
            if isinstance(result, Exception):
                batch_results[url] = {"success": False, "error": str(result)}
            else:
                batch_results[url] = {"success": True, "result": result}

        return batch_results

class ResourceOptimizedExecutor(ExecutorStrategy):
    """Executor optimized for resource usage."""

    def __init__(
        self,
        crawler: AsyncWebCrawler,
        callbacks: Optional[Dict[CallbackType, Callable]] = None,
        persistence_path: Optional[Path] = None,
        word_count_threshold=MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = None,
        bypass_cache: bool = False,
        css_selector: str = None,
        screenshot: bool = False,
        user_agent: str = None,
        verbose=True,
        connection_pool_size: int = 50,
        dns_cache_size: int = 1000,
        backoff_factor: int = 5,
        max_concurrent_tasks: int = 5,
        **kwargs
    ):
        if chunking_strategy is None:
            chunking_strategy = RegexChunking()

        super().__init__(
            crawler=crawler,
            mode=ExecutionMode.RESOURCE,
            callbacks=callbacks,
            persistence_path=persistence_path,
            word_count_threshold=word_count_threshold,
            extraction_strategy=extraction_strategy,
            chunking_strategy=chunking_strategy,
            bypass_cache=bypass_cache,
            css_selector=css_selector,
            screenshot=screenshot,
            user_agent=user_agent,
            verbose=verbose,
            **kwargs
        )

        self.connection_pool_size = connection_pool_size
        self.dns_cache_size = dns_cache_size
        self.backoff_factor = backoff_factor
        self.max_concurrent_tasks = max_concurrent_tasks

        self.logger.info(
            # "Initialized resource-optimized executor with:"
            f"Executor {self.__class__.__name__}: Initialized with:"
            f" connection_pool_size={self.connection_pool_size},"
            f" dns_cache_size={self.dns_cache_size},"
            f" max_concurrent_tasks={self.max_concurrent_tasks}"
        )

    async def process_batch(self, batch_urls: List[str]) -> Dict[str, Any]:
        """Process a batch of URLs with resource optimization."""
        batch_results = {}
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

        # Wait until resources are available before processing batch
        while not await self.resource_monitor.check_resources():
            # self.logger.warning("Resource limits reached, waiting...")
            self.logger.warning(f"Executor {self.__class__.__name__}: Resource limits reached, waiting...")
            await asyncio.sleep(self.backoff_factor)
            # Check for cancellation
            if await self.control.is_cancelled():
                raise asyncio.CancelledError("Execution was cancelled")

        async def process_url_with_semaphore(url):
            async with semaphore:
                # Check for cancellation
                if await self.control.is_cancelled():
                    raise asyncio.CancelledError("Execution was cancelled")
                # Wait if paused
                await self.control.wait_if_paused(timeout=300)

                try:
                    result = await self._process_url(url)
                    batch_results[url] = {"success": True, "result": result}
                except Exception as e:
                    batch_results[url] = {"success": False, "error": str(e)}
                finally:
                    # Update system metrics after each URL
                    # INFO: Uncomment this line if you want to capture system metrics after each URL, but it causes a performance hit
                    # self.metrics.system_metrics.append(SystemMetrics.capture())
                    # Controlled delay between URLs
                    await asyncio.sleep(0.1)  # Small delay for resource management

        tasks = [process_url_with_semaphore(url) for url in batch_urls]
        await asyncio.gather(*tasks)

        return batch_results
    




async def main():
    # Sample callback functions
    async def pre_execution_callback(url: str, context: Dict[str, Any]):
        print(f"Pre-execution callback: About to process URL {url}")

    async def post_execution_callback(url: str, result: Any, context: Dict[str, Any]):
        print(f"Post-execution callback: Successfully processed URL {url}")

    async def on_error_callback(url: str, error: Exception, context: Dict[str, Any]):
        print(f"Error callback: Error processing URL {url}: {error}")

    async def on_retry_callback(url: str, attempt: int, context: Dict[str, Any]):
        print(f"Retry callback: Retrying URL {url}, attempt {attempt}")

    async def on_batch_start_callback(urls: List[str], context: Dict[str, Any]):
        print(f"Batch start callback: Starting batch with {len(urls)} URLs")

    async def on_batch_end_callback(urls: List[str], context: Dict[str, Any]):
        print(f"Batch end callback: Completed batch with {len(urls)} URLs")

    async def on_complete_callback(results: Dict[str, Any], context: Dict[str, Any]):
        print(f"Complete callback: Execution completed with {len(results)} results")

    # Sample URLs to crawl
    urls = [
        "https://www.example.com",
        "https://www.python.org",
        "https://www.asyncio.org",
        # Add more URLs as needed
    ]

    # Instantiate the crawler
    crawler = AsyncWebCrawler()

    # Set up callbacks
    callbacks = {
        CallbackType.PRE_EXECUTION: pre_execution_callback,
        CallbackType.POST_EXECUTION: post_execution_callback,
        CallbackType.ON_ERROR: on_error_callback,
        CallbackType.ON_RETRY: on_retry_callback,
        CallbackType.ON_BATCH_START: on_batch_start_callback,
        CallbackType.ON_BATCH_END: on_batch_end_callback,
        CallbackType.ON_COMPLETE: on_complete_callback,
    }

    # Instantiate the executors
    speed_executor = SpeedOptimizedExecutor(
        crawler=crawler,
        callbacks=callbacks,
        max_retries=2,  # Example additional config
    )

    resource_executor = ResourceOptimizedExecutor(
        crawler=crawler,
        callbacks=callbacks,
        max_concurrent_tasks=3,  # Limit concurrency
        max_retries=2,           # Example additional config
    )

    # Choose which executor to use
    executor = speed_executor  # Or resource_executor

    # Start the execution in a background task
    execution_task = asyncio.create_task(executor.execute(urls))

    # Simulate control operations
    await asyncio.sleep(2)  # Let it run for a bit
    print("Pausing execution...")
    await executor.control.pause()
    await asyncio.sleep(2)  # Wait while paused
    print("Resuming execution...")
    await executor.control.resume()

    # Wait for execution to complete
    results = await execution_task

    # Print the results
    print("Execution results:")
    for url, result in results.items():
        print(f"{url}: {result}")

    # Get and print final metrics
    final_status = await executor.get_status()
    print("Final executor status and metrics:")
    print(final_status)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())