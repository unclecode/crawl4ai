"""
Enhanced Job Queue System for High-Volume Crawling
Provides:
- Batch crawl progress tracking
- Job resumption after failures
- Per-job performance metrics
- Priority queue support
- Distributed crawling capability
- Automatic retry with exponential backoff
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from redis import asyncio as aioredis
import json
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status states"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    """Job priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RetryStrategy(str, Enum):
    """Retry strategy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


@dataclass
class JobProgress:
    """Job progress tracking"""
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    current_item: Optional[str] = None
    progress_percent: float = 0.0
    items_per_second: float = 0.0
    estimated_time_remaining: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
            "skipped_items": self.skipped_items,
            "current_item": self.current_item,
            "progress_percent": self.progress_percent,
            "items_per_second": self.items_per_second,
            "estimated_time_remaining": self.estimated_time_remaining
        }


class JobMetrics(BaseModel):
    """Per-job performance metrics"""
    job_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    total_bytes_transferred: int = 0
    avg_response_time: float = 0.0
    peak_memory_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    retry_count: int = 0
    error_count: int = 0


class JobConfig(BaseModel):
    """Job configuration"""
    job_id: str
    job_type: str
    priority: JobPriority = JobPriority.NORMAL
    urls: List[str] = Field(default_factory=list)
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    retry_delay_seconds: int = 1
    timeout_seconds: int = 300
    enable_resume: bool = True
    checkpoint_interval: int = 10
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JobResult(BaseModel):
    """Job result with detailed information"""
    job_id: str
    status: JobStatus
    progress: Dict
    metrics: JobMetrics
    results: List[Dict] = Field(default_factory=list)
    errors: List[Dict] = Field(default_factory=list)
    checkpoint: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime


class JobCheckpoint(BaseModel):
    """Job checkpoint for resumption"""
    job_id: str
    completed_urls: List[str] = Field(default_factory=list)
    failed_urls: List[str] = Field(default_factory=list)
    pending_urls: List[str] = Field(default_factory=list)
    state: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class EnhancedJobQueue:
    """Enhanced job queue with advanced features"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.jobs: Dict[str, JobConfig] = {}
        self.progress: Dict[str, JobProgress] = {}
        self.metrics: Dict[str, JobMetrics] = {}
        self.workers: Dict[str, asyncio.Task] = {}
        self.lock = asyncio.Lock()
        
        # Redis key prefixes
        self.job_prefix = "job:config:"
        self.progress_prefix = "job:progress:"
        self.metrics_prefix = "job:metrics:"
        self.checkpoint_prefix = "job:checkpoint:"
        self.result_prefix = "job:result:"
        self.queue_prefix = "job:queue:"
    
    async def create_job(
        self,
        job_type: str,
        urls: List[str],
        priority: JobPriority = JobPriority.NORMAL,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new job and add to queue"""
        job_id = f"{job_type}_{uuid.uuid4().hex[:12]}"
        
        job_config = JobConfig(
            job_id=job_id,
            job_type=job_type,
            priority=priority,
            urls=urls,
            metadata=config or {}
        )
        
        # Initialize progress
        progress = JobProgress(total_items=len(urls))
        
        # Initialize metrics
        metrics = JobMetrics(job_id=job_id)
        
        async with self.lock:
            self.jobs[job_id] = job_config
            self.progress[job_id] = progress
            self.metrics[job_id] = metrics
        
        # Save to Redis
        await self._save_job_to_redis(job_config)
        await self._save_progress_to_redis(job_id, progress)
        await self._save_metrics_to_redis(metrics)
        
        # Add to priority queue
        await self._enqueue_job(job_id, priority)
        
        logger.info(f"Job created: {job_id} ({len(urls)} URLs, priority: {priority.value})")
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[JobResult]:
        """Get job status and results"""
        job_config = await self._load_job_from_redis(job_id)
        if not job_config:
            return None
        
        progress = await self._load_progress_from_redis(job_id)
        metrics = await self._load_metrics_from_redis(job_id)
        results = await self._load_results_from_redis(job_id)
        checkpoint = await self._load_checkpoint_from_redis(job_id)
        
        # Determine status
        if progress.completed_items + progress.failed_items == progress.total_items:
            status = JobStatus.COMPLETED if progress.failed_items == 0 else JobStatus.FAILED
        elif job_id in self.workers and not self.workers[job_id].done():
            status = JobStatus.PROCESSING
        else:
            status = JobStatus.QUEUED
        
        return JobResult(
            job_id=job_id,
            status=status,
            progress=progress.to_dict() if progress else {},
            metrics=metrics,
            results=results,
            errors=[],
            checkpoint=checkpoint.model_dump() if checkpoint else None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    async def update_progress(
        self,
        job_id: str,
        completed: int = 0,
        failed: int = 0,
        current_item: Optional[str] = None
    ):
        """Update job progress"""
        async with self.lock:
            if job_id not in self.progress:
                logger.warning(f"Job progress not found: {job_id}")
                return
            
            progress = self.progress[job_id]
            progress.completed_items += completed
            progress.failed_items += failed
            progress.current_item = current_item
            
            # Calculate progress percentage
            total_processed = progress.completed_items + progress.failed_items + progress.skipped_items
            if progress.total_items > 0:
                progress.progress_percent = (total_processed / progress.total_items) * 100
            
            # Calculate items per second (if we have metrics)
            if job_id in self.metrics and self.metrics[job_id].start_time:
                elapsed = (datetime.now(timezone.utc) - self.metrics[job_id].start_time).total_seconds()
                if elapsed > 0:
                    progress.items_per_second = total_processed / elapsed
                    
                    # Estimate time remaining
                    remaining_items = progress.total_items - total_processed
                    if progress.items_per_second > 0:
                        progress.estimated_time_remaining = remaining_items / progress.items_per_second
        
        await self._save_progress_to_redis(job_id, progress)
    
    async def save_checkpoint(
        self,
        job_id: str,
        completed_urls: List[str],
        failed_urls: List[str],
        pending_urls: List[str],
        state: Optional[Dict] = None
    ):
        """Save job checkpoint for resumption"""
        checkpoint = JobCheckpoint(
            job_id=job_id,
            completed_urls=completed_urls,
            failed_urls=failed_urls,
            pending_urls=pending_urls,
            state=state or {},
            timestamp=datetime.now(timezone.utc)
        )
        
        key = f"{self.checkpoint_prefix}{job_id}"
        await self.redis.setex(
            key,
            86400 * 7,  # 7 days
            checkpoint.model_dump_json()
        )
        
        logger.info(f"Checkpoint saved for job: {job_id}")
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume job from checkpoint"""
        checkpoint = await self._load_checkpoint_from_redis(job_id)
        if not checkpoint:
            logger.warning(f"No checkpoint found for job: {job_id}")
            return False
        
        job_config = await self._load_job_from_redis(job_id)
        if not job_config:
            logger.warning(f"Job config not found: {job_id}")
            return False
        
        # Update job URLs to only process pending + failed
        job_config.urls = checkpoint.pending_urls + checkpoint.failed_urls
        
        # Re-enqueue
        await self._enqueue_job(job_id, job_config.priority)
        
        logger.info(f"Job resumed: {job_id} ({len(job_config.urls)} URLs remaining)")
        return True
    
    async def cancel_job(self, job_id: str):
        """Cancel running or queued job"""
        # Cancel worker if running
        if job_id in self.workers:
            self.workers[job_id].cancel()
            try:
                await self.workers[job_id]
            except asyncio.CancelledError:
                pass
            del self.workers[job_id]
        
        # Remove from queue
        await self._dequeue_job(job_id)
        
        # Update status
        async with self.lock:
            if job_id in self.progress:
                # Mark remaining as cancelled
                progress = self.progress[job_id]
                remaining = progress.total_items - progress.completed_items - progress.failed_items
                progress.skipped_items = remaining
        
        logger.info(f"Job cancelled: {job_id}")
    
    async def retry_failed_items(self, job_id: str) -> bool:
        """Retry failed items in a job"""
        checkpoint = await self._load_checkpoint_from_redis(job_id)
        if not checkpoint or not checkpoint.failed_urls:
            return False
        
        # Create new job for failed items
        job_config = await self._load_job_from_redis(job_id)
        if not job_config:
            return False
        
        new_job_id = await self.create_job(
            job_type=f"{job_config.job_type}_retry",
            urls=checkpoint.failed_urls,
            priority=job_config.priority,
            config=job_config.metadata
        )
        
        logger.info(f"Created retry job: {new_job_id} (from {job_id})")
        return True
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "total_jobs": len(self.jobs),
            "active_workers": len(self.workers),
            "queued_by_priority": {},
            "total_urls": 0,
            "completed_urls": 0,
            "failed_urls": 0
        }
        
        # Count by priority
        for priority in JobPriority:
            queue_key = f"{self.queue_prefix}{priority.value}"
            count = await self.redis.llen(queue_key)
            stats["queued_by_priority"][priority.value] = count
        
        # Aggregate progress
        for progress in self.progress.values():
            stats["total_urls"] += progress.total_items
            stats["completed_urls"] += progress.completed_items
            stats["failed_urls"] += progress.failed_items
        
        return stats
    
    async def process_job(
        self,
        job_id: str,
        processor: Callable[[str, Dict], Any]
    ):
        """Process job with custom processor function"""
        job_config = await self._load_job_from_redis(job_id)
        if not job_config:
            logger.error(f"Job config not found: {job_id}")
            return
        
        # Update metrics
        async with self.lock:
            if job_id in self.metrics:
                self.metrics[job_id].start_time = datetime.now(timezone.utc)
                await self._save_metrics_to_redis(self.metrics[job_id])
        
        results = []
        completed_urls = []
        failed_urls = []
        pending_urls = list(job_config.urls)
        
        try:
            for idx, url in enumerate(job_config.urls):
                try:
                    # Process URL
                    result = await processor(url, job_config.metadata)
                    results.append({"url": url, "result": result})
                    completed_urls.append(url)
                    pending_urls.remove(url)
                    
                    # Update progress
                    await self.update_progress(
                        job_id,
                        completed=1,
                        current_item=url
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    failed_urls.append(url)
                    pending_urls.remove(url)
                    
                    await self.update_progress(
                        job_id,
                        failed=1,
                        current_item=url
                    )
                
                # Save checkpoint every N items
                if (idx + 1) % job_config.checkpoint_interval == 0:
                    await self.save_checkpoint(
                        job_id,
                        completed_urls,
                        failed_urls,
                        pending_urls
                    )
            
            # Save final results
            await self._save_results_to_redis(job_id, results)
            
            # Save final checkpoint
            await self.save_checkpoint(
                job_id,
                completed_urls,
                failed_urls,
                pending_urls
            )
            
        finally:
            # Update metrics
            async with self.lock:
                if job_id in self.metrics:
                    self.metrics[job_id].end_time = datetime.now(timezone.utc)
                    if self.metrics[job_id].start_time:
                        duration = (
                            self.metrics[job_id].end_time - self.metrics[job_id].start_time
                        ).total_seconds()
                        self.metrics[job_id].duration_seconds = duration
                    
                    await self._save_metrics_to_redis(self.metrics[job_id])
    
    # Private helper methods
    
    async def _save_job_to_redis(self, job_config: JobConfig):
        """Save job configuration to Redis"""
        key = f"{self.job_prefix}{job_config.job_id}"
        await self.redis.setex(
            key,
            86400 * 7,  # 7 days
            job_config.model_dump_json()
        )
    
    async def _load_job_from_redis(self, job_id: str) -> Optional[JobConfig]:
        """Load job configuration from Redis"""
        key = f"{self.job_prefix}{job_id}"
        data = await self.redis.get(key)
        
        if data:
            return JobConfig.model_validate_json(data)
        
        return None
    
    async def _save_progress_to_redis(self, job_id: str, progress: JobProgress):
        """Save progress to Redis"""
        key = f"{self.progress_prefix}{job_id}"
        await self.redis.setex(
            key,
            86400,  # 24 hours
            json.dumps(progress.to_dict())
        )
    
    async def _load_progress_from_redis(self, job_id: str) -> Optional[JobProgress]:
        """Load progress from Redis"""
        key = f"{self.progress_prefix}{job_id}"
        data = await self.redis.get(key)
        
        if data:
            data_dict = json.loads(data)
            return JobProgress(**data_dict)
        
        return None
    
    async def _save_metrics_to_redis(self, metrics: JobMetrics):
        """Save metrics to Redis"""
        key = f"{self.metrics_prefix}{metrics.job_id}"
        await self.redis.setex(
            key,
            86400 * 7,  # 7 days
            metrics.model_dump_json()
        )
    
    async def _load_metrics_from_redis(self, job_id: str) -> Optional[JobMetrics]:
        """Load metrics from Redis"""
        key = f"{self.metrics_prefix}{job_id}"
        data = await self.redis.get(key)
        
        if data:
            return JobMetrics.model_validate_json(data)
        
        return None
    
    async def _save_results_to_redis(self, job_id: str, results: List[Dict]):
        """Save results to Redis"""
        key = f"{self.result_prefix}{job_id}"
        await self.redis.setex(
            key,
            86400 * 7,  # 7 days
            json.dumps(results)
        )
    
    async def _load_results_from_redis(self, job_id: str) -> List[Dict]:
        """Load results from Redis"""
        key = f"{self.result_prefix}{job_id}"
        data = await self.redis.get(key)
        
        if data:
            return json.loads(data)
        
        return []
    
    async def _load_checkpoint_from_redis(self, job_id: str) -> Optional[JobCheckpoint]:
        """Load checkpoint from Redis"""
        key = f"{self.checkpoint_prefix}{job_id}"
        data = await self.redis.get(key)
        
        if data:
            return JobCheckpoint.model_validate_json(data)
        
        return None
    
    async def _enqueue_job(self, job_id: str, priority: JobPriority):
        """Add job to priority queue"""
        queue_key = f"{self.queue_prefix}{priority.value}"
        await self.redis.lpush(queue_key, job_id)
    
    async def _dequeue_job(self, job_id: str):
        """Remove job from all priority queues"""
        for priority in JobPriority:
            queue_key = f"{self.queue_prefix}{priority.value}"
            await self.redis.lrem(queue_key, 0, job_id)
    
    async def _get_next_job(self) -> Optional[str]:
        """Get next job from priority queue"""
        # Check priorities from highest to lowest
        for priority in [JobPriority.URGENT, JobPriority.HIGH, JobPriority.NORMAL, JobPriority.LOW]:
            queue_key = f"{self.queue_prefix}{priority.value}"
            job_id = await self.redis.rpop(queue_key)
            
            if job_id:
                return job_id.decode()
        
        return None

