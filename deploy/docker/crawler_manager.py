# crawler_manager.py
import asyncio
import time
import uuid
import psutil
import os
import resource  # For FD limit
import random
import math
from typing import Optional, Tuple, Any, List, Dict, AsyncGenerator
from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
import logging

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, AsyncLogger
# Assuming api.py handlers are accessible or refactored slightly if needed
# We might need to import the specific handler functions if we call them directly
# from api import handle_crawl_request, handle_stream_crawl_request, _get_memory_mb, stream_results

# --- Custom Exceptions ---
class PoolTimeoutError(Exception):
    """Raised when waiting for a crawler resource times out."""
    pass

class PoolConfigurationError(Exception):
    """Raised for configuration issues."""
    pass

class NoHealthyCrawlerError(Exception):
    """Raised when no healthy crawler is available."""
    pass


# --- Configuration Models ---
class CalculationParams(BaseModel):
    mem_headroom_mb: int = 512
    avg_page_mem_mb: int = 150
    fd_per_page: int = 20
    core_multiplier: int = 4
    min_pool_size: int = 1 # Min safe pages should be at least 1
    max_pool_size: int = 16

    # V2 validation for avg_page_mem_mb
    @field_validator('avg_page_mem_mb')
    @classmethod
    def check_avg_page_mem(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("avg_page_mem_mb must be positive")
        return v

    # V2 validation for fd_per_page
    @field_validator('fd_per_page')
    @classmethod
    def check_fd_per_page(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("fd_per_page must be positive")
        return v

# crawler_manager.py
# ... (imports including BaseModel, Field from pydantic) ...
from pydantic import BaseModel, Field, field_validator # <-- Import field_validator

# --- Configuration Models (Pydantic V2 Syntax) ---
class CalculationParams(BaseModel):
    mem_headroom_mb: int = 512
    avg_page_mem_mb: int = 150
    fd_per_page: int = 20
    core_multiplier: int = 4
    min_pool_size: int = 1 # Min safe pages should be at least 1
    max_pool_size: int = 16

    # V2 validation for avg_page_mem_mb
    @field_validator('avg_page_mem_mb')
    @classmethod
    def check_avg_page_mem(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("avg_page_mem_mb must be positive")
        return v

    # V2 validation for fd_per_page
    @field_validator('fd_per_page')
    @classmethod
    def check_fd_per_page(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("fd_per_page must be positive")
        return v

class CrawlerManagerConfig(BaseModel):
    enabled: bool = True
    auto_calculate_size: bool = True
    calculation_params: CalculationParams = Field(default_factory=CalculationParams) # Use Field for default_factory
    backup_pool_size: int = Field(1, ge=0) # Allow 0 backups
    max_wait_time_s: float = 30.0
    throttle_threshold_percent: float = Field(70.0, ge=0, le=100)
    throttle_delay_min_s: float = 0.1
    throttle_delay_max_s: float = 0.5
    browser_config: Dict[str, Any] = Field(default_factory=lambda: {"headless": True, "verbose": False}) # Use Field for default_factory
    primary_reload_delay_s: float = 60.0

# --- Crawler Manager ---
class CrawlerManager:
    """Manages shared AsyncWebCrawler instances, concurrency, and failover."""

    def __init__(self, config: CrawlerManagerConfig, logger = None):
        if not config.enabled:
            self.logger.warning("CrawlerManager is disabled by configuration.")
            # Set defaults to allow server to run, but manager won't function
            self.config = config
            self._initialized = False,
            return

        self.config = config
        self._primary_crawler: Optional[AsyncWebCrawler] = None
        self._secondary_crawlers: List[AsyncWebCrawler] = []
        self._active_crawler_index: int = 0 # 0 for primary, 1+ for secondary index
        self._primary_healthy: bool = False
        self._secondary_healthy_flags: List[bool] = []

        self._safe_pages: int = 1 # Default, calculated in initialize
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._state_lock = asyncio.Lock() # Protects active_crawler, health flags
        self._reload_tasks: List[Optional[asyncio.Task]] = [] # Track reload background tasks

        self._initialized = False
        self._shutting_down = False
        
        # Initialize logger if provided
        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger

        self.logger.info("CrawlerManager initialized with config.")
        self.logger.debug(f"Config: {self.config.model_dump_json(indent=2)}")

    def is_enabled(self) -> bool:
        return self.config.enabled and self._initialized

    def _get_system_resources(self) -> Tuple[int, int, int]:
        """Gets RAM, CPU cores, and FD limit."""
        total_ram_mb = 0
        cpu_cores = 0
        try:
            mem_info = psutil.virtual_memory()
            total_ram_mb = mem_info.total // (1024 * 1024)
            cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) # Prefer physical cores
        except Exception as e:
            self.logger.warning(f"Could not get RAM/CPU info via psutil: {e}")
            total_ram_mb = 2048 # Default fallback
            cpu_cores = 2      # Default fallback

        fd_limit = 1024 # Default fallback
        try:
            soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            fd_limit = soft_limit # Use the soft limit
        except (ImportError, ValueError, OSError, AttributeError) as e:
            self.logger.warning(f"Could not get file descriptor limit (common on Windows): {e}. Using default: {fd_limit}")

        self.logger.info(f"System Resources: RAM={total_ram_mb}MB, Cores={cpu_cores}, FD Limit={fd_limit}")
        return total_ram_mb, cpu_cores, fd_limit

    def _calculate_safe_pages(self) -> int:
        """Calculates the safe number of concurrent pages based on resources."""
        if not self.config.auto_calculate_size:
            # If auto-calc is off, use max_pool_size as the hard limit
            # This isn't ideal based on the prompt, but provides *some* manual override
            # A dedicated `manual_safe_pages` might be better. Let's use max_pool_size for now.
             self.logger.warning("Auto-calculation disabled. Using max_pool_size as safe_pages limit.")
             return self.config.calculation_params.max_pool_size

        params = self.config.calculation_params
        total_ram_mb, cpu_cores, fd_limit = self._get_system_resources()

        available_ram_mb = total_ram_mb - params.mem_headroom_mb
        if available_ram_mb <= 0:
            self.logger.error(f"Not enough RAM ({total_ram_mb}MB) after headroom ({params.mem_headroom_mb}MB). Cannot calculate safe pages.")
            return params.min_pool_size # Fallback to minimum

        try:
            # Calculate limits from each resource
            mem_limit = available_ram_mb // params.avg_page_mem_mb if params.avg_page_mem_mb > 0 else float('inf')
            fd_limit_pages = fd_limit // params.fd_per_page if params.fd_per_page > 0 else float('inf')
            cpu_limit = cpu_cores * params.core_multiplier if cpu_cores > 0 else float('inf')

            # Determine the most constraining limit
            calculated_limit = math.floor(min(mem_limit, fd_limit_pages, cpu_limit))

        except ZeroDivisionError:
             self.logger.error("Division by zero in safe_pages calculation (avg_page_mem_mb or fd_per_page is zero).")
             calculated_limit = params.min_pool_size # Fallback

        # Clamp the result within min/max bounds
        safe_pages = max(params.min_pool_size, min(calculated_limit, params.max_pool_size))

        self.logger.info(f"Calculated safe pages: MemoryLimit={mem_limit}, FDLimit={fd_limit_pages}, CPULimit={cpu_limit} -> RawCalc={calculated_limit} -> Clamped={safe_pages}")
        return safe_pages

    async def _create_and_start_crawler(self, crawler_id: str) -> Optional[AsyncWebCrawler]:
        """Creates, starts, and returns a crawler instance."""
        try:
            # Create BrowserConfig from the dictionary in manager config
            browser_conf = BrowserConfig(**self.config.browser_config)
            crawler = AsyncWebCrawler(config=browser_conf)
            await crawler.start()
            self.logger.info(f"Successfully started crawler instance: {crawler_id}")
            return crawler
        except Exception as e:
            self.logger.error(f"Failed to start crawler instance {crawler_id}: {e}", exc_info=True)
            return None

    async def initialize(self):
        """Initializes crawlers and semaphore. Called at server startup."""
        if not self.config.enabled or self._initialized:
            return

        self.logger.info("Initializing CrawlerManager...")
        self._safe_pages = self._calculate_safe_pages()
        self._semaphore = asyncio.Semaphore(self._safe_pages)

        self._primary_crawler = await self._create_and_start_crawler("Primary")
        if self._primary_crawler:
            self._primary_healthy = True
        else:
            self._primary_healthy = False
            self.logger.critical("Primary crawler failed to initialize!")

        self._secondary_crawlers = []
        self._secondary_healthy_flags = []
        self._reload_tasks = [None] * (1 + self.config.backup_pool_size) # For primary + backups

        for i in range(self.config.backup_pool_size):
            sec_id = f"Secondary-{i+1}"
            crawler = await self._create_and_start_crawler(sec_id)
            self._secondary_crawlers.append(crawler) # Add even if None
            self._secondary_healthy_flags.append(crawler is not None)
            if crawler is None:
                 self.logger.error(f"{sec_id} crawler failed to initialize!")

        # Set initial active crawler (prefer primary)
        if self._primary_healthy:
            self._active_crawler_index = 0
            self.logger.info("Primary crawler is active.")
        else:
            # Find the first healthy secondary
            found_healthy_backup = False
            for i, healthy in enumerate(self._secondary_healthy_flags):
                if healthy:
                    self._active_crawler_index = i + 1 # 1-based index for secondaries
                    self.logger.warning(f"Primary failed, Secondary-{i+1} is active.")
                    found_healthy_backup = True
                    break
            if not found_healthy_backup:
                 self.logger.critical("FATAL: No healthy crawlers available after initialization!")
                 # Server should probably refuse connections in this state

        self._initialized = True
        self.logger.info(f"CrawlerManager initialized. Safe Pages: {self._safe_pages}. Active Crawler Index: {self._active_crawler_index}")

    async def shutdown(self):
        """Shuts down all crawler instances. Called at server shutdown."""
        if not self._initialized or self._shutting_down:
            return

        self._shutting_down = True
        self.logger.info("Shutting down CrawlerManager...")

        # Cancel any ongoing reload tasks
        for i, task in enumerate(self._reload_tasks):
            if task and not task.done():
                try:
                    task.cancel()
                    await task # Wait for cancellation
                    self.logger.info(f"Cancelled reload task for crawler index {i}.")
                except asyncio.CancelledError:
                    self.logger.info(f"Reload task for crawler index {i} was already cancelled.")
                except Exception as e:
                    self.logger.warning(f"Error cancelling reload task for crawler index {i}: {e}")
        self._reload_tasks = []


        # Close primary
        if self._primary_crawler:
            try:
                self.logger.info("Closing primary crawler...")
                await self._primary_crawler.close()
                self._primary_crawler = None
            except Exception as e:
                self.logger.error(f"Error closing primary crawler: {e}", exc_info=True)

        # Close secondaries
        for i, crawler in enumerate(self._secondary_crawlers):
             if crawler:
                 try:
                     self.logger.info(f"Closing secondary crawler {i+1}...")
                     await crawler.close()
                 except Exception as e:
                     self.logger.error(f"Error closing secondary crawler {i+1}: {e}", exc_info=True)
        self._secondary_crawlers = []

        self._initialized = False
        self.logger.info("CrawlerManager shut down complete.")

    @asynccontextmanager
    async def get_crawler(self) -> AsyncGenerator[AsyncWebCrawler, None]:
        """Acquires semaphore, yields active crawler, handles throttling & failover."""
        if not self.is_enabled():
            raise NoHealthyCrawlerError("CrawlerManager is disabled or not initialized.")

        if self._shutting_down:
             raise NoHealthyCrawlerError("CrawlerManager is shutting down.")

        active_crawler: Optional[AsyncWebCrawler] = None
        acquired = False
        request_id = uuid.uuid4()
        start_wait = time.time()

        # --- Throttling ---
        try:
            # Check semaphore value without acquiring
            current_usage = self._safe_pages - self._semaphore._value
            usage_percent = (current_usage / self._safe_pages) * 100 if self._safe_pages > 0 else 0

            if usage_percent >= self.config.throttle_threshold_percent:
                delay = random.uniform(self.config.throttle_delay_min_s, self.config.throttle_delay_max_s)
                self.logger.debug(f"Throttling: Usage {usage_percent:.1f}% >= {self.config.throttle_threshold_percent}%. Delaying {delay:.3f}s")
                await asyncio.sleep(delay)
        except Exception as e:
             self.logger.warning(f"Error during throttling check: {e}") # Continue attempt even if throttle check fails

        # --- Acquire Semaphore ---
        try:
            # self.logger.debug(f"Attempting to acquire semaphore (Available: {self._semaphore._value}/{self._safe_pages}). Wait Timeout: {self.config.max_wait_time_s}s")
            
            # --- Logging Before Acquire ---
            sem_value = self._semaphore._value if self._semaphore else 'N/A'
            sem_waiters = len(self._semaphore._waiters) if self._semaphore and self._semaphore._waiters else 0
            self.logger.debug(f"Req {request_id}: Attempting acquire. Available={sem_value}/{self._safe_pages}, Waiters={sem_waiters}, Timeout={self.config.max_wait_time_s}s")            

            await asyncio.wait_for(
                self._semaphore.acquire(), timeout=self.config.max_wait_time_s
            )
            acquired = True
            wait_duration = time.time() - start_wait
            if wait_duration > 1:
                self.logger.warning(f"Semaphore acquired after {wait_duration:.3f}s. (Available: {self._semaphore._value}/{self._safe_pages})")
                
            self.logger.debug(f"Semaphore acquired successfully after {wait_duration:.3f}s. (Available: {self._semaphore._value}/{self._safe_pages})")

            # --- Select Active Crawler (Critical Section) ---
            async with self._state_lock:
                current_active_index = self._active_crawler_index
                is_primary_active = (current_active_index == 0)

                if is_primary_active:
                    if self._primary_healthy and self._primary_crawler:
                        active_crawler = self._primary_crawler
                    else:
                        # Primary is supposed to be active but isn't healthy
                        self.logger.warning("Primary crawler unhealthy, attempting immediate failover...")
                        if not await self._try_failover_sync(): # Try to switch active crawler NOW
                             raise NoHealthyCrawlerError("Primary unhealthy and no healthy backup available.")
                        # If failover succeeded, active_crawler_index is updated
                        current_active_index = self._active_crawler_index
                        # Fall through to select the new active secondary

                # Check if we need to use a secondary (either initially or after failover)
                if current_active_index > 0:
                     secondary_idx = current_active_index - 1
                     if secondary_idx < len(self._secondary_crawlers) and \
                        self._secondary_healthy_flags[secondary_idx] and \
                        self._secondary_crawlers[secondary_idx]:
                          active_crawler = self._secondary_crawlers[secondary_idx]
                     else:
                         self.logger.error(f"Selected Secondary-{current_active_index} is unhealthy or missing.")
                         # Attempt failover to *another* secondary if possible? (Adds complexity)
                         # For now, raise error if the selected one isn't good.
                         raise NoHealthyCrawlerError(f"Selected Secondary-{current_active_index} is unavailable.")

            if active_crawler is None:
                 # This shouldn't happen if logic above is correct, but safeguard
                 raise NoHealthyCrawlerError("Failed to select a healthy active crawler.")

            # --- Yield Crawler ---
            try:
                yield active_crawler
            except Exception as crawl_error:
                self.logger.error(f"Error during crawl execution using {active_crawler}: {crawl_error}", exc_info=True)
                # Determine if this error warrants failover
                # For now, let's assume any exception triggers a health check/failover attempt
                await self._handle_crawler_failure(active_crawler)
                raise # Re-raise the original error for the API handler

        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for semaphore after {self.config.max_wait_time_s}s.")
            raise PoolTimeoutError(f"Timed out waiting for available crawler resource after {self.config.max_wait_time_s}s")
        except NoHealthyCrawlerError:
            # Logged within the selection logic
             raise # Re-raise for API handler
        except Exception as e:
             self.logger.error(f"Unexpected error in get_crawler context manager: {e}", exc_info=True)
             raise # Re-raise potentially unknown errors
        finally:
            if acquired:
                self._semaphore.release()
                self.logger.debug(f"Semaphore released. (Available: {self._semaphore._value}/{self._safe_pages})")


    async def _try_failover_sync(self) -> bool:
        """Synchronous part of failover logic (must be called under state_lock). Finds next healthy secondary."""
        if not self._primary_healthy: # Only failover if primary is already marked down
            found_healthy_backup = False
            start_idx = (self._active_crawler_index % (self.config.backup_pool_size +1)) # Start check after current
            for i in range(self.config.backup_pool_size):
                 check_idx = (start_idx + i) % self.config.backup_pool_size # Circular check
                 if self._secondary_healthy_flags[check_idx] and self._secondary_crawlers[check_idx]:
                     self._active_crawler_index = check_idx + 1
                     self.logger.warning(f"Failover successful: Switched active crawler to Secondary-{self._active_crawler_index}")
                     found_healthy_backup = True
                     break # Found one
            if not found_healthy_backup:
                 # If primary is down AND no backups are healthy, mark primary as active index (0) but it's still unhealthy
                 self._active_crawler_index = 0
                 self.logger.error("Failover failed: No healthy secondary crawlers available.")
                 return False
            return True
        return True # Primary is healthy, no failover needed

    async def _handle_crawler_failure(self, failed_crawler: AsyncWebCrawler):
        """Handles marking a crawler as unhealthy and initiating recovery."""
        if self._shutting_down: return # Don't handle failures during shutdown

        async with self._state_lock:
            crawler_index = -1
            is_primary = False

            if failed_crawler is self._primary_crawler and self._primary_healthy:
                self.logger.warning("Primary crawler reported failure.")
                self._primary_healthy = False
                is_primary = True
                crawler_index = 0
                # Try immediate failover within the lock
                await self._try_failover_sync()
                # Start reload task if not already running for primary
                if self._reload_tasks[0] is None or self._reload_tasks[0].done():
                     self.logger.info("Initiating primary crawler reload task.")
                     self._reload_tasks[0] = asyncio.create_task(self._reload_crawler(0))

            else:
                 # Check if it was one of the secondaries
                 for i, crawler in enumerate(self._secondary_crawlers):
                     if failed_crawler is crawler and self._secondary_healthy_flags[i]:
                         self.logger.warning(f"Secondary-{i+1} crawler reported failure.")
                         self._secondary_healthy_flags[i] = False
                         is_primary = False
                         crawler_index = i + 1
                         # If this *was* the active crawler, trigger failover check
                         if self._active_crawler_index == crawler_index:
                              self.logger.warning(f"Active secondary {crawler_index} failed, attempting failover...")
                              await self._try_failover_sync()
                         # Start reload task for this secondary
                         if self._reload_tasks[crawler_index] is None or self._reload_tasks[crawler_index].done():
                              self.logger.info(f"Initiating Secondary-{i+1} crawler reload task.")
                              self._reload_tasks[crawler_index] = asyncio.create_task(self._reload_crawler(crawler_index))
                         break # Found the failed secondary

            if crawler_index == -1:
                 self.logger.debug("Failure reported by an unknown or already unhealthy crawler instance. Ignoring.")


    async def _reload_crawler(self, crawler_index_to_reload: int):
        """Background task to close, recreate, and start a specific crawler."""
        is_primary = (crawler_index_to_reload == 0)
        crawler_id = "Primary" if is_primary else f"Secondary-{crawler_index_to_reload}"
        original_crawler = self._primary_crawler if is_primary else self._secondary_crawlers[crawler_index_to_reload - 1]

        self.logger.info(f"Starting reload process for {crawler_id}...")

        # 1. Delay before attempting reload (e.g., allow transient issues to clear)
        if not is_primary: # Maybe shorter delay for backups?
            await asyncio.sleep(self.config.primary_reload_delay_s / 2)
        else:
             await asyncio.sleep(self.config.primary_reload_delay_s)


        # 2. Attempt to close the old instance cleanly
        if original_crawler:
            try:
                self.logger.info(f"Attempting to close existing {crawler_id} instance...")
                await original_crawler.close()
                self.logger.info(f"Successfully closed old {crawler_id} instance.")
            except Exception as e:
                self.logger.warning(f"Error closing old {crawler_id} instance during reload: {e}")

        # 3. Create and start a new instance
        self.logger.info(f"Attempting to start new {crawler_id} instance...")
        new_crawler = await self._create_and_start_crawler(crawler_id)

        # 4. Update state if successful
        async with self._state_lock:
            if new_crawler:
                self.logger.info(f"Successfully reloaded {crawler_id}. Marking as healthy.")
                if is_primary:
                    self._primary_crawler = new_crawler
                    self._primary_healthy = True
                    # Switch back to primary if no other failures occurred
                    # Check if ANY secondary is currently active
                    secondary_is_active = self._active_crawler_index > 0
                    if not secondary_is_active or not self._secondary_healthy_flags[self._active_crawler_index - 1]:
                         self.logger.info("Switching active crawler back to primary.")
                         self._active_crawler_index = 0
                else: # Is secondary
                    secondary_idx = crawler_index_to_reload - 1
                    self._secondary_crawlers[secondary_idx] = new_crawler
                    self._secondary_healthy_flags[secondary_idx] = True
                    # Potentially switch back if primary is still down and this was needed?
                    if not self._primary_healthy and self._active_crawler_index == 0:
                         self.logger.info(f"Primary still down, activating reloaded Secondary-{crawler_index_to_reload}.")
                         self._active_crawler_index = crawler_index_to_reload

            else:
                self.logger.error(f"Failed to reload {crawler_id}. It remains unhealthy.")
                # Keep the crawler marked as unhealthy
                if is_primary:
                    self._primary_healthy = False # Ensure it stays false
                else:
                    self._secondary_healthy_flags[crawler_index_to_reload - 1] = False


            # Clear the reload task reference for this index
            self._reload_tasks[crawler_index_to_reload] = None


    async def get_status(self) -> Dict:
        """Returns the current status of the manager."""
        if not self.is_enabled():
            return {"status": "disabled"}

        async with self._state_lock:
             active_id = "Primary" if self._active_crawler_index == 0 else f"Secondary-{self._active_crawler_index}"
             primary_status = "Healthy" if self._primary_healthy else "Unhealthy"
             secondary_statuses = [f"Secondary-{i+1}: {'Healthy' if healthy else 'Unhealthy'}"
                                   for i, healthy in enumerate(self._secondary_healthy_flags)]
             semaphore_available = self._semaphore._value if self._semaphore else 'N/A'
             semaphore_locked = len(self._semaphore._waiters) if self._semaphore and self._semaphore._waiters else 0

             return {
                 "status": "enabled",
                 "safe_pages": self._safe_pages,
                 "semaphore_available": semaphore_available,
                 "semaphore_waiters": semaphore_locked,
                 "active_crawler": active_id,
                 "primary_status": primary_status,
                 "secondary_statuses": secondary_statuses,
                 "reloading_tasks": [i for i, t in enumerate(self._reload_tasks) if t and not t.done()]
             }