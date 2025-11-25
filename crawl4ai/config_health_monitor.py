from __future__ import annotations

import asyncio
import copy
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Union,
)

from .async_configs import BrowserConfig, CrawlerRunConfig
from .async_logger import AsyncLogger, LogLevel
from .async_webcrawler import AsyncWebCrawler
from .cache_context import CacheMode


# ============================================================================
# ConfigHealthMonitor Supporting Types
# ============================================================================

@dataclass
class ResolutionResult:
    """Result of a resolution strategy execution."""
    success: bool
    action: str  # Human-readable description of action taken
    modified_config: Optional[CrawlerRunConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigHealthState:
    """Health state for a monitored configuration."""
    config_id: str
    config: CrawlerRunConfig
    test_url: str
    status: Literal["healthy", "degraded", "failed", "resolving"] = "healthy"
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_check_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_error: Optional[str] = None
    resolution_attempts: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def copy(self) -> ConfigHealthState:
        """Create a copy of this state."""
        return ConfigHealthState(
            config_id=self.config_id,
            config=self.config,
            test_url=self.test_url,
            status=self.status,
            consecutive_failures=self.consecutive_failures,
            consecutive_successes=self.consecutive_successes,
            last_check_time=self.last_check_time,
            last_success_time=self.last_success_time,
            last_error=self.last_error,
            resolution_attempts=self.resolution_attempts,
            metrics=self.metrics.copy()
        )


# Type alias for resolution strategies
ResolutionStrategy = Callable[
    [ConfigHealthState, "ConfigHealthMonitor"],
    Awaitable[ResolutionResult]
]


class _ErrorTrackingLogger:
    """Lightweight proxy that records error logs for health checks."""

    __slots__ = ("_base_logger", "_error_events")

    def __init__(self, base_logger):
        object.__setattr__(self, "_base_logger", base_logger)
        object.__setattr__(self, "_error_events", deque(maxlen=500))

    def _record_error(self, message: str, tag: str, params: Optional[Dict[str, Any]]):
        formatted_message = message
        if params:
            try:
                formatted_message = message.format(**params)
            except Exception:
                pass
        self._error_events.append({
            "timestamp": time.time(),
            "tag": tag,
            "message": formatted_message,
        })

    def poll_errors(self, since_ts: float) -> List[Dict[str, Any]]:
        """Return error logs emitted since the provided timestamp."""
        if since_ts is None:
            return list(self._error_events)

        recent = [event for event in self._error_events if event["timestamp"] >= since_ts]

        # Keep deque trimmed to the last few minutes to avoid unbounded memory use
        cutoff = max(since_ts - 300.0, 0.0)
        while self._error_events and self._error_events[0]["timestamp"] < cutoff:
            self._error_events.popleft()

        return recent

    def debug(self, message: str, tag: str = "DEBUG", **kwargs):
        return self._base_logger.debug(message, tag=tag, **kwargs)

    def info(self, message: str, tag: str = "INFO", **kwargs):
        return self._base_logger.info(message, tag=tag, **kwargs)

    def success(self, message: str, tag: str = "SUCCESS", **kwargs):
        return self._base_logger.success(message, tag=tag, **kwargs)

    def warning(self, message: str, tag: str = "WARNING", **kwargs):
        return self._base_logger.warning(message, tag=tag, **kwargs)

    def error(self, message: str, tag: str = "ERROR", **kwargs):
        self._record_error(message, tag, kwargs.get("params"))
        return self._base_logger.error(message, tag=tag, **kwargs)

    def critical(self, message: str, tag: str = "CRITICAL", **kwargs):
        self._record_error(message, tag, kwargs.get("params"))
        return self._base_logger.critical(message, tag=tag, **kwargs)

    def exception(self, message: str, tag: str = "EXCEPTION", **kwargs):
        self._record_error(message, tag, kwargs.get("params"))
        return self._base_logger.exception(message, tag=tag, **kwargs)

    def fatal(self, message: str, tag: str = "FATAL", **kwargs):
        self._record_error(message, tag, kwargs.get("params"))
        return self._base_logger.fatal(message, tag=tag, **kwargs)

    def alert(self, message: str, tag: str = "ALERT", **kwargs):
        self._record_error(message, tag, kwargs.get("params"))
        return self._base_logger.alert(message, tag=tag, **kwargs)

    def error_status(self, url: str, error: str, tag: str = "ERROR", url_length: int = 100):
        self._record_error(error, tag, None)
        return self._base_logger.error_status(url, error, tag=tag, url_length=url_length)

    def url_status(self, url: str, success: bool, timing: float, tag: str = "FETCH", url_length: int = 100):
        return self._base_logger.url_status(url, success, timing, tag=tag, url_length=url_length)

    def __getattr__(self, item):
        return getattr(self._base_logger, item)

    def __setattr__(self, key, value):
        if key in self.__slots__:
            object.__setattr__(self, key, value)
        else:
            setattr(self._base_logger, key, value)


# ============================================================================
# ConfigHealthMonitor Class
# ============================================================================

class ConfigHealthMonitor:
    """
    Monitors health of crawler configurations and applies resolution strategies.
    
    Features:
    - Periodic health checks for multiple configs
    - Configurable failure thresholds
    - Built-in and custom resolution strategies
    - Metrics collection and reporting
    - Graceful shutdown and cleanup
    """
    
    def __init__(
        self,
        browser_config: Optional[BrowserConfig] = None,
        check_interval: float = 60.0,
        failure_threshold: int = 3,
        resolution_retry_limit: int = 2,
        enable_metrics: bool = True,
        logger: Optional[AsyncLogger] = None
    ):
        """
        Args:
            browser_config: Shared browser configuration for all health checks
            check_interval: Seconds between health checks (default: 60s)
            failure_threshold: Consecutive failures before triggering resolution
            resolution_retry_limit: Max resolution attempts before marking as failed
            enable_metrics: Collect and report performance metrics
            logger: Custom logger instance
        """
        # Configuration
        self.browser_config = browser_config
        self.check_interval = max(10.0, check_interval)  # Minimum 10s
        self.failure_threshold = max(1, failure_threshold)
        self.resolution_retry_limit = max(0, resolution_retry_limit)
        self.enable_metrics = enable_metrics
        
        # Logger
        if logger is None:
            self.logger = AsyncLogger(
                log_level=LogLevel.INFO,
                verbose=False
            )
        else:
            self.logger = logger

        if not isinstance(self.logger, _ErrorTrackingLogger):
            self.logger = _ErrorTrackingLogger(self.logger)
        
        # State management
        self._health_states: Dict[str, ConfigHealthState] = {}
        self._resolution_strategies: Dict[str, ResolutionStrategy] = {}
        self._default_resolution_strategy: Optional[ResolutionStrategy] = None
        self._state_lock = asyncio.Lock()
        
        # Crawler instance (shared across all health checks)
        self._crawler: Optional[AsyncWebCrawler] = None
        
        # Monitoring control
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Metrics
        self._metrics = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "total_resolutions": 0,
            "successful_resolutions": 0,
            "start_time": None,
        }
        self._config_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self._last_check_times: Dict[str, float] = {}
        
        self.logger.info(
            "ConfigHealthMonitor initialized",
            tag="HEALTH_MONITOR",
            params={
                "check_interval": self.check_interval,
                "failure_threshold": self.failure_threshold,
                "resolution_retry_limit": self.resolution_retry_limit,
                "enable_metrics": self.enable_metrics,
            }
        )
    
    # ========================================================================
    # Properties
    # ========================================================================
    
    @property
    def is_running(self) -> bool:
        """Check if monitoring is active."""
        return self._running
    
    @property
    def registered_count(self) -> int:
        """Number of registered configurations."""
        return len(self._health_states)
    
    @property
    def uptime(self) -> Optional[float]:
        """Monitor uptime in seconds."""
        if self._metrics["start_time"] is None:
            return None
        return time.time() - self._metrics["start_time"]
    
    # ========================================================================
    # Lifecycle Methods
    # ========================================================================
    
    async def start(self) -> None:
        """Initialize crawler and start monitoring loop."""
        if self._running:
            self.logger.warning(
                "ConfigHealthMonitor already running",
                tag="HEALTH_MONITOR"
            )
            return
        
        try:
            
            # Initialize crawler
            self._crawler = AsyncWebCrawler(
                config=self.browser_config,
                logger=self.logger
            )
            await self._crawler.__aenter__()
            
            # Start monitoring
            self._running = True
            self._metrics["start_time"] = time.time()
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.success(
                "ConfigHealthMonitor started",
                tag="HEALTH_MONITOR",
                params={"registered_configs": self.registered_count}
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to start ConfigHealthMonitor: {e}",
                tag="HEALTH_MONITOR"
            )
            await self._cleanup()
            raise
    
    async def stop(self) -> None:
        """Gracefully stop monitoring and cleanup resources."""
        if not self._running:
            self.logger.warning(
                "ConfigHealthMonitor not running",
                tag="HEALTH_MONITOR"
            )
            return
        
        self.logger.info(
            "Stopping ConfigHealthMonitor...",
            tag="HEALTH_MONITOR"
        )
        
        self._running = False
        
        # Cancel monitoring task
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup resources
        await self._cleanup()
        
        self.logger.success(
            "ConfigHealthMonitor stopped",
            tag="HEALTH_MONITOR",
            params={
                "total_checks": self._metrics["total_checks"],
                "uptime_seconds": self.uptime,
            }
        )
    
    async def _cleanup(self) -> None:
        """Cleanup internal resources."""
        if self._crawler:
            try:
                await self._crawler.__aexit__(None, None, None)
            except Exception as e:
                self.logger.error(
                    f"Error during crawler cleanup: {e}",
                    tag="HEALTH_MONITOR"
                )
            finally:
                self._crawler = None
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()
        return False
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _generate_config_id(self) -> str:
        """Generate a unique config ID."""
        return f"config_{uuid.uuid4().hex[:8]}"
    
    def _update_metrics(
        self,
        state: ConfigHealthState,
        status_override: Optional[str] = None
    ) -> None:
        """Update internal metrics based on state."""
        if not self.enable_metrics:
            return
        
        config_id = state.config_id
        
        # Initialize config metrics if needed
        if config_id not in self._config_metrics:
            self._config_metrics[config_id] = {
                "total_checks": 0,
                "successful_checks": 0,
                "failed_checks": 0,
                "total_response_time": 0.0,
                "min_response_time": float('inf'),
                "max_response_time": 0.0,
                "resolution_attempts": 0,
                "last_status": "unknown",
            }
        
        # Update config-specific metrics
        metrics = self._config_metrics[config_id]
        metrics["total_checks"] += 1
        status = status_override or state.status
        metrics["last_status"] = status
        
        if status == "healthy":
            metrics["successful_checks"] += 1
        else:
            metrics["failed_checks"] += 1
        
        # Update response time metrics if available
        if "response_time" in state.metrics:
            rt = state.metrics["response_time"]
            metrics["total_response_time"] += rt
            metrics["min_response_time"] = min(metrics["min_response_time"], rt)
            metrics["max_response_time"] = max(metrics["max_response_time"], rt)
        
        metrics["resolution_attempts"] = state.resolution_attempts
    
    def _record_check_result(
        self,
        state: ConfigHealthState,
        status_label: str,
        is_healthy: bool
    ) -> None:
        """Record the outcome of a single health check."""
        if not self.enable_metrics:
            return
        
        self._metrics["total_checks"] += 1
        if is_healthy:
            self._metrics["successful_checks"] += 1
        else:
            self._metrics["failed_checks"] += 1
        
        self._update_metrics(state, status_override=status_label)
    
    # ========================================================================
    # Configuration Management
    # ========================================================================
    
    def register_config(
        self,
        config: CrawlerRunConfig,
        test_url: str,
        config_id: Optional[str] = None,
        resolution_strategy: Optional[ResolutionStrategy] = None
    ) -> str:
        """
        Register a configuration to monitor.
        
        Args:
            config: The CrawlerRunConfig to monitor
            test_url: URL to use for health checks
            config_id: Unique identifier (auto-generated if None)
            resolution_strategy: Custom resolution function for this config
            
        Returns:
            config_id: The assigned configuration ID
            
        Raises:
            ValueError: If config_id already exists
        """
        if config_id is None:
            config_id = self._generate_config_id()
        
        if config_id in self._health_states:
            raise ValueError(f"Config ID '{config_id}' already registered")
        
        # Validate test_url
        if not test_url or not test_url.strip():
            raise ValueError("test_url cannot be empty")
        
        # Create health state
        state = ConfigHealthState(
            config_id=config_id,
            config=config,
            test_url=test_url.strip(),
            status="healthy",
        )
        
        self._health_states[config_id] = state
        
        # Register resolution strategy if provided
        if resolution_strategy:
            self._resolution_strategies[config_id] = resolution_strategy
        
        self.logger.info(
            f"Registered config '{config_id}'",
            tag="HEALTH_MONITOR",
            params={
                "config_id": config_id,
                "test_url": test_url,
                "has_custom_strategy": resolution_strategy is not None,
                "total_configs": self.registered_count,
            }
        )
        
        return config_id
    
    def unregister_config(self, config_id: str) -> bool:
        """
        Remove a configuration from monitoring.
        
        Args:
            config_id: The configuration ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if config_id not in self._health_states:
            self.logger.warning(
                f"Config '{config_id}' not found for unregistration",
                tag="HEALTH_MONITOR"
            )
            return False
        
        # Remove state and strategy
        del self._health_states[config_id]
        self._resolution_strategies.pop(config_id, None)
        self._config_metrics.pop(config_id, None)
        self._last_check_times.pop(config_id, None)
        
        self.logger.info(
            f"Unregistered config '{config_id}'",
            tag="HEALTH_MONITOR",
            params={"remaining_configs": self.registered_count}
        )
        
        return True
    
    def set_resolution_strategy(
        self,
        strategy: ResolutionStrategy,
        config_id: Optional[str] = None
    ) -> None:
        """
        Set resolution strategy for specific config or as global default.
        
        Args:
            strategy: Resolution callable
            config_id: Target config (None = set as global default)
            
        Raises:
            ValueError: If config_id specified but not found
        """
        if config_id is None:
            # Set as default strategy
            self._default_resolution_strategy = strategy
            self.logger.info(
                "Set default resolution strategy",
                tag="HEALTH_MONITOR"
            )
        else:
            # Set for specific config
            if config_id not in self._health_states:
                raise ValueError(f"Config ID '{config_id}' not registered")
            
            self._resolution_strategies[config_id] = strategy
            self.logger.info(
                f"Set resolution strategy for config '{config_id}'",
                tag="HEALTH_MONITOR"
            )
    
    # ========================================================================
    # Health Checking
    # ========================================================================
    
    async def check_health(self, config_id: str) -> bool:
        """
        Perform a single health check for a configuration.
        
        Args:
            config_id: The configuration to check
            
        Returns:
            True if healthy, False otherwise
            
        Raises:
            ValueError: If config_id not found
        """
        if config_id not in self._health_states:
            raise ValueError(f"Config ID '{config_id}' not registered")
        
        async with self._state_lock:
            state = self._health_states[config_id]
            is_healthy = await self._perform_health_check(state)
            
            # Update state
            if is_healthy:
                state.status = "healthy"
                state.consecutive_failures = 0
                state.consecutive_successes += 1
                state.last_success_time = datetime.now()
                state.resolution_attempts = 0
            else:
                state.consecutive_failures += 1
                state.consecutive_successes = 0
                state.status = (
                    "degraded"
                    if state.consecutive_failures < self.failure_threshold
                    else "failed"
                )
            
            state.last_check_time = datetime.now()
            
            # Update metrics
            if self.enable_metrics:
                self._record_check_result(state, state.status, is_healthy)
            
            return is_healthy
    
    async def _perform_health_check(self, state: ConfigHealthState) -> bool:
        """
        Execute health check crawl.
        
        Args:
            state: The configuration state to check
            
        Returns:
            True if healthy, False otherwise
        """
        if not self._crawler:
            state.last_error = "Crawler not initialized"
            return False
        
        start_time = time.time()
        error_window_start = start_time
        
        try:
            # Create lightweight config for health check
            health_config = copy.deepcopy(state.config)
            health_config.cache_mode = CacheMode.BYPASS  # Always fresh for health checks
            
            # Perform crawl
            result = await self._crawler.arun(
                url=state.test_url,
                config=health_config,
                session_id=f"health_check_{state.config_id}"
            )
            
            # Record metrics
            response_time = time.time() - start_time
            state.metrics["response_time"] = response_time
            state.metrics["status_code"] = result.status_code
            state.metrics["html_length"] = len(result.html) if result.html else 0
            state.metrics["success"] = result.success

            recent_errors: List[Dict[str, Any]] = []
            if hasattr(self.logger, "poll_errors"):
                recent_errors = self.logger.poll_errors(error_window_start)

            had_logger_errors = bool(recent_errors)
            if had_logger_errors:
                state.metrics["logger_errors"] = [event["message"] for event in recent_errors]
            else:
                state.metrics.pop("logger_errors", None)
            
            # Evaluate health criteria
            is_healthy = (
                result.success
                and result.status_code in [200, 201, 202, 203, 206]
                and len(result.html or "") > 100  # Minimum content threshold
            ) and not had_logger_errors

            if had_logger_errors:
                self.logger.warning(
                    f"Logger reported {len(recent_errors)} errors during health check for '{state.config_id}'",
                    tag="HEALTH_CHECK",
                    params={
                        "config_id": state.config_id,
                        "last_error": recent_errors[-1]["message"],
                    }
                )
            
            if not is_healthy:
                log_error_msg = recent_errors[-1]["message"] if had_logger_errors else None
                state.last_error = log_error_msg or result.error_message or "Health check failed"
                self.logger.warning(
                    f"Health check failed for '{state.config_id}'",
                    tag="HEALTH_CHECK",
                    params={
                        "config_id": state.config_id,
                        "status_code": result.status_code,
                        "error": state.last_error,
                        "consecutive_failures": state.consecutive_failures + 1,
                    }
                )
            else:
                self.logger.debug(
                    f"Health check passed for '{state.config_id}'",
                    tag="HEALTH_CHECK",
                    params={
                        "config_id": state.config_id,
                        "response_time": round(response_time, 2),
                        "status_code": result.status_code,
                    }
                )
            
            return is_healthy
            
        except Exception as e:
            response_time = time.time() - start_time
            state.last_error = str(e)
            state.metrics["response_time"] = response_time
            state.metrics["exception"] = type(e).__name__
            
            self.logger.error(
                f"Health check exception for '{state.config_id}': {e}",
                tag="HEALTH_CHECK",
                params={
                    "config_id": state.config_id,
                    "exception_type": type(e).__name__,
                }
            )
            
            return False
    
    # ========================================================================
    # Resolution Management
    # ========================================================================
    
    async def _apply_resolution(self, config_id: str) -> bool:
        """
        Apply resolution strategy for a failing config.
        
        Args:
            config_id: The configuration to resolve
            
        Returns:
            True if resolution succeeded, False otherwise
        """
        state = self._health_states[config_id]
        state.status = "resolving"
        state.resolution_attempts += 1
        
        # Get resolution strategy (config-specific or default)
        strategy = self._resolution_strategies.get(
            config_id,
            self._default_resolution_strategy
        )
        
        if strategy is None:
            self.logger.warning(
                f"No resolution strategy for '{config_id}'",
                tag="RESOLUTION",
                params={"config_id": config_id}
            )
            return False
        
        try:
            self.logger.info(
                f"Applying resolution for '{config_id}'",
                tag="RESOLUTION",
                params={
                    "config_id": config_id,
                    "attempt": state.resolution_attempts,
                    "consecutive_failures": state.consecutive_failures,
                }
            )
            
            # Execute resolution strategy
            result = await strategy(state, self)
            
            # Update metrics
            if self.enable_metrics:
                self._metrics["total_resolutions"] += 1
                if result.success:
                    self._metrics["successful_resolutions"] += 1
            
            if result.success:
                self.logger.success(
                    f"Resolution succeeded for '{config_id}': {result.action}",
                    tag="RESOLUTION",
                    params={
                        "config_id": config_id,
                        "action": result.action,
                        "metadata": result.metadata,
                    }
                )
                
                # Apply modified config if provided
                if result.modified_config:
                    state.config = result.modified_config
                    self.logger.info(
                        f"Applied modified config for '{config_id}'",
                        tag="RESOLUTION"
                    )
                
                # Reset failure counters on successful resolution
                state.consecutive_failures = 0
                state.resolution_attempts = 0
                
                return True
            else:
                self.logger.warning(
                    f"Resolution failed for '{config_id}': {result.action}",
                    tag="RESOLUTION",
                    params={
                        "config_id": config_id,
                        "action": result.action,
                    }
                )
                return False
                
        except Exception as e:
            self.logger.error(
                f"Resolution exception for '{config_id}': {e}",
                tag="RESOLUTION",
                params={
                    "config_id": config_id,
                    "exception_type": type(e).__name__,
                }
            )
            return False
    
    async def _handle_permanent_failure(self, config_id: str) -> None:
        """
        Handle config that has exceeded resolution retry limit.
        
        Args:
            config_id: The permanently failed configuration
        """
        state = self._health_states[config_id]
        
        self.logger.error(
            f"Config '{config_id}' marked as permanently failed",
            tag="HEALTH_MONITOR",
            params={
                "config_id": config_id,
                "consecutive_failures": state.consecutive_failures,
                "resolution_attempts": state.resolution_attempts,
                "last_error": state.last_error,
            }
        )
        
        # Emit alert or notification here
        # Could integrate with external alerting systems
    
    # ========================================================================
    # Monitoring Loop
    # ========================================================================
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop (runs in background task)."""
        self.logger.info(
            "Monitoring loop started",
            tag="HEALTH_MONITOR",
            params={"check_interval": self.check_interval}
        )
        
        while self._running:
            try:
                # Check all registered configs
                config_ids = list(self._health_states.keys())
                
                if not config_ids:
                    # No configs to monitor, wait and continue
                    await asyncio.sleep(self.check_interval)
                    continue
                
                for config_id in config_ids:
                    if not self._running:
                        break
                    
                    try:
                        await self._check_and_resolve(config_id)
                    except Exception as e:
                        self.logger.error(
                            f"Error checking config '{config_id}': {e}",
                            tag="HEALTH_MONITOR"
                        )
                
                # Wait for next interval
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                self.logger.info(
                    "Monitoring loop cancelled",
                    tag="HEALTH_MONITOR"
                )
                break
            except Exception as e:
                self.logger.error(
                    f"Monitoring loop error: {e}",
                    tag="HEALTH_MONITOR"
                )
                # Brief pause before retry
                await asyncio.sleep(5)
        
        self.logger.info(
            "Monitoring loop stopped",
            tag="HEALTH_MONITOR"
        )
    
    async def _check_and_resolve(self, config_id: str) -> None:
        """
        Check health and apply resolution if needed.
        
        Args:
            config_id: The configuration to check and potentially resolve
        """
        async with self._state_lock:
            state = self._health_states.get(config_id)
            if not state:
                return
            
            # Perform health check
            is_healthy = await self._perform_health_check(state)
            
            if is_healthy:
                if state.status != "healthy":
                    self.logger.success(
                        f"Config '{config_id}' recovered",
                        tag="HEALTH_MONITOR"
                    )
                state.status = "healthy"
                state.consecutive_failures = 0
                state.consecutive_successes += 1
                state.last_success_time = datetime.now()
                state.resolution_attempts = 0
                self._record_check_result(state, "healthy", True)
            else:
                state.consecutive_failures += 1
                state.consecutive_successes = 0
                status_label = (
                    "degraded"
                    if state.consecutive_failures < self.failure_threshold
                    else "failed"
                )
                state.status = status_label
                self._record_check_result(state, status_label, False)
                
                if status_label == "failed":
                    if state.resolution_attempts < self.resolution_retry_limit:
                        resolution_success = await self._apply_resolution(config_id)
                        
                        if resolution_success:
                            is_healthy_after = await self._perform_health_check(state)
                            
                            if is_healthy_after:
                                state.status = "healthy"
                                state.consecutive_failures = 0
                                state.consecutive_successes = 1
                                state.last_success_time = datetime.now()
                                state.resolution_attempts = 0
                                self._record_check_result(state, "healthy", True)
                            else:
                                state.consecutive_failures += 1
                                state.consecutive_successes = 0
                                status_label = (
                                    "degraded"
                                    if state.consecutive_failures < self.failure_threshold
                                    else "failed"
                                )
                                state.status = status_label
                                self._record_check_result(state, status_label, False)
                    else:
                        await self._handle_permanent_failure(config_id)
            
            state.last_check_time = datetime.now()
    
    # ========================================================================
    # Status and Metrics Queries
    # ========================================================================
    
    def get_health_status(
        self,
        config_id: Optional[str] = None
    ) -> Union[ConfigHealthState, Dict[str, ConfigHealthState]]:
        """
        Get health status for one or all configs.
        
        Args:
            config_id: Specific config ID, or None for all configs
            
        Returns:
            Single ConfigHealthState or dict of all states
            
        Raises:
            ValueError: If config_id specified but not found
        """
        if config_id is None:
            # Return all states (as copies for thread safety)
            return {
                cid: state.copy()
                for cid, state in self._health_states.items()
            }
        else:
            if config_id not in self._health_states:
                raise ValueError(f"Config ID '{config_id}' not registered")
            
            return self._health_states[config_id].copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated metrics across all configs.
        
        Returns:
            Dictionary containing comprehensive metrics
        """
        metrics = self._metrics.copy()
        
        # Calculate derived metrics
        total_checks = metrics["total_checks"]
        if total_checks > 0:
            metrics["success_rate"] = metrics["successful_checks"] / total_checks
        else:
            metrics["success_rate"] = 0.0
        
        total_resolutions = metrics["total_resolutions"]
        if total_resolutions > 0:
            metrics["resolution_success_rate"] = (
                metrics["successful_resolutions"] / total_resolutions
            )
        else:
            metrics["resolution_success_rate"] = 0.0
        
        # Add uptime
        metrics["uptime_seconds"] = self.uptime
        
        # Add per-config metrics
        config_metrics = {}
        for config_id, state in self._health_states.items():
            config_stats = self._config_metrics.get(config_id, {})
            
            # Calculate per-config derived metrics
            total = config_stats.get("total_checks", 0)
            if total > 0:
                uptime_percent = (
                    config_stats.get("successful_checks", 0) / total * 100
                )
                avg_response_time = (
                    config_stats.get("total_response_time", 0.0) / total
                )
            else:
                uptime_percent = 0.0
                avg_response_time = 0.0
            
            config_metrics[config_id] = {
                "status": state.status,
                "uptime_percent": round(uptime_percent, 2),
                "avg_response_time": round(avg_response_time, 3),
                "min_response_time": config_stats.get("min_response_time", 0.0),
                "max_response_time": config_stats.get("max_response_time", 0.0),
                "total_checks": total,
                "successful_checks": config_stats.get("successful_checks", 0),
                "failed_checks": config_stats.get("failed_checks", 0),
                "consecutive_failures": state.consecutive_failures,
                "resolution_attempts": state.resolution_attempts,
                "last_check": (
                    state.last_check_time.isoformat()
                    if state.last_check_time else None
                ),
                "last_success": (
                    state.last_success_time.isoformat()
                    if state.last_success_time else None
                ),
                "last_error": state.last_error,
            }
        
        metrics["configs"] = config_metrics
        
        return metrics