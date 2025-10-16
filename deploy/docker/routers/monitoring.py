"""
Monitoring and Profiling Router

Provides endpoints for:
- Browser performance profiling
- Real-time crawler statistics
- System resource monitoring
- Session management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
import uuid
import asyncio
import json
import time
import psutil
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring & Profiling"],
    responses={
        404: {"description": "Session not found"},
        500: {"description": "Internal server error"}
    }
)

# ============================================================================
# Data Structures
# ============================================================================

# In-memory storage for profiling sessions
PROFILING_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Real-time crawler statistics
CRAWLER_STATS = {
    "active_crawls": 0,
    "total_crawls": 0,
    "successful_crawls": 0,
    "failed_crawls": 0,
    "total_bytes_processed": 0,
    "average_response_time_ms": 0.0,
    "last_updated": datetime.now().isoformat(),
}

# Per-URL statistics
URL_STATS: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
    "total_requests": 0,
    "success_count": 0,
    "failure_count": 0,
    "average_time_ms": 0.0,
    "last_accessed": None,
})


# ============================================================================
# Pydantic Models
# ============================================================================

class ProfilingStartRequest(BaseModel):
    """Request to start a profiling session."""
    url: str = Field(..., description="URL to profile")
    browser_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Browser configuration"
    )
    crawler_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Crawler configuration"
    )
    profile_duration: Optional[int] = Field(
        default=30,
        ge=5,
        le=300,
        description="Maximum profiling duration in seconds"
    )
    collect_network: bool = Field(
        default=True,
        description="Collect network performance data"
    )
    collect_memory: bool = Field(
        default=True,
        description="Collect memory usage data"
    )
    collect_cpu: bool = Field(
        default=True,
        description="Collect CPU usage data"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "profile_duration": 30,
                "collect_network": True,
                "collect_memory": True,
                "collect_cpu": True
            }
        }


class ProfilingSession(BaseModel):
    """Profiling session information."""
    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(..., description="Session status: running, completed, failed")
    url: str = Field(..., description="URL being profiled")
    start_time: str = Field(..., description="Session start time (ISO format)")
    end_time: Optional[str] = Field(None, description="Session end time (ISO format)")
    duration_seconds: Optional[float] = Field(None, description="Total duration in seconds")
    results: Optional[Dict[str, Any]] = Field(None, description="Profiling results")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "abc123",
                "status": "completed",
                "url": "https://example.com",
                "start_time": "2025-10-16T10:30:00",
                "end_time": "2025-10-16T10:30:30",
                "duration_seconds": 30.5,
                "results": {
                    "performance": {
                        "page_load_time_ms": 1234,
                        "dom_content_loaded_ms": 890,
                        "first_paint_ms": 567
                    }
                }
            }
        }


class CrawlerStats(BaseModel):
    """Current crawler statistics."""
    active_crawls: int = Field(..., description="Number of currently active crawls")
    total_crawls: int = Field(..., description="Total crawls since server start")
    successful_crawls: int = Field(..., description="Number of successful crawls")
    failed_crawls: int = Field(..., description="Number of failed crawls")
    success_rate: float = Field(..., description="Success rate percentage")
    total_bytes_processed: int = Field(..., description="Total bytes processed")
    average_response_time_ms: float = Field(..., description="Average response time")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    memory_usage_mb: float = Field(..., description="Current memory usage in MB")
    cpu_percent: float = Field(..., description="Current CPU usage percentage")
    last_updated: str = Field(..., description="Last update timestamp")


class URLStatistics(BaseModel):
    """Statistics for a specific URL pattern."""
    url_pattern: str
    total_requests: int
    success_count: int
    failure_count: int
    success_rate: float
    average_time_ms: float
    last_accessed: Optional[str]


class SessionListResponse(BaseModel):
    """List of profiling sessions."""
    total: int
    sessions: List[ProfilingSession]


# ============================================================================
# Helper Functions
# ============================================================================

def get_system_stats() -> Dict[str, Any]:
    """Get current system resource usage."""
    try:
        process = psutil.Process()
        
        return {
            "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(interval=0.1),
            "num_threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections()),
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {
            "memory_usage_mb": 0.0,
            "cpu_percent": 0.0,
            "num_threads": 0,
            "open_files": 0,
            "connections": 0,
        }


def cleanup_old_sessions(max_age_hours: int = 24):
    """Remove old profiling sessions to prevent memory leaks."""
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    
    to_remove = []
    for session_id, session in PROFILING_SESSIONS.items():
        try:
            start_time = datetime.fromisoformat(session["start_time"])
            if start_time < cutoff:
                to_remove.append(session_id)
        except (ValueError, KeyError):
            continue
    
    for session_id in to_remove:
        del PROFILING_SESSIONS[session_id]
        logger.info(f"Cleaned up old session: {session_id}")
    
    return len(to_remove)


# ============================================================================
# Profiling Endpoints
# ============================================================================

@router.post(
    "/profile/start",
    response_model=ProfilingSession,
    summary="Start profiling session",
    description="Start a new browser profiling session for performance analysis"
)
async def start_profiling_session(
    request: ProfilingStartRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new profiling session.
    
    Returns a session ID that can be used to retrieve results later.
    The profiling runs in the background and collects:
    - Page load performance metrics
    - Network requests and timing
    - Memory usage patterns
    - CPU utilization
    - Browser-specific metrics
    """
    session_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    session_data = {
        "session_id": session_id,
        "status": "running",
        "url": request.url,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "duration_seconds": None,
        "results": None,
        "error": None,
        "config": {
            "profile_duration": request.profile_duration,
            "collect_network": request.collect_network,
            "collect_memory": request.collect_memory,
            "collect_cpu": request.collect_cpu,
        }
    }
    
    PROFILING_SESSIONS[session_id] = session_data
    
    # Add background task to run profiling
    background_tasks.add_task(
        run_profiling_session,
        session_id,
        request
    )
    
    logger.info(f"Started profiling session {session_id} for {request.url}")
    
    return ProfilingSession(**session_data)


@router.get(
    "/profile/{session_id}",
    response_model=ProfilingSession,
    summary="Get profiling results",
    description="Retrieve results from a profiling session"
)
async def get_profiling_results(session_id: str):
    """
    Get profiling session results.
    
    Returns the current status and results of a profiling session.
    If the session is still running, results will be None.
    """
    if session_id not in PROFILING_SESSIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Profiling session '{session_id}' not found"
        )
    
    session = PROFILING_SESSIONS[session_id]
    return ProfilingSession(**session)


@router.get(
    "/profile",
    response_model=SessionListResponse,
    summary="List profiling sessions",
    description="List all profiling sessions with optional filtering"
)
async def list_profiling_sessions(
    status: Optional[str] = Query(None, description="Filter by status: running, completed, failed"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of sessions to return")
):
    """
    List all profiling sessions.
    
    Can be filtered by status and limited in number.
    """
    sessions = list(PROFILING_SESSIONS.values())
    
    # Filter by status if provided
    if status:
        sessions = [s for s in sessions if s["status"] == status]
    
    # Sort by start time (newest first)
    sessions.sort(key=lambda x: x["start_time"], reverse=True)
    
    # Limit results
    sessions = sessions[:limit]
    
    return SessionListResponse(
        total=len(sessions),
        sessions=[ProfilingSession(**s) for s in sessions]
    )


@router.delete(
    "/profile/{session_id}",
    summary="Delete profiling session",
    description="Delete a profiling session and its results"
)
async def delete_profiling_session(session_id: str):
    """
    Delete a profiling session.
    
    Removes the session and all associated data from memory.
    """
    if session_id not in PROFILING_SESSIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Profiling session '{session_id}' not found"
        )
    
    session = PROFILING_SESSIONS.pop(session_id)
    logger.info(f"Deleted profiling session {session_id}")
    
    return {
        "success": True,
        "message": f"Session {session_id} deleted",
        "session": ProfilingSession(**session)
    }


@router.post(
    "/profile/cleanup",
    summary="Cleanup old sessions",
    description="Remove old profiling sessions to free memory"
)
async def cleanup_sessions(
    max_age_hours: int = Query(24, ge=1, le=168, description="Maximum age in hours")
):
    """
    Cleanup old profiling sessions.
    
    Removes sessions older than the specified age.
    """
    removed = cleanup_old_sessions(max_age_hours)
    
    return {
        "success": True,
        "removed_count": removed,
        "remaining_count": len(PROFILING_SESSIONS),
        "message": f"Removed {removed} sessions older than {max_age_hours} hours"
    }


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get(
    "/stats",
    response_model=CrawlerStats,
    summary="Get crawler statistics",
    description="Get current crawler statistics and system metrics"
)
async def get_crawler_stats():
    """
    Get current crawler statistics.
    
    Returns real-time metrics about:
    - Active and total crawls
    - Success/failure rates
    - Response times
    - System resource usage
    """
    system_stats = get_system_stats()
    
    total = CRAWLER_STATS["successful_crawls"] + CRAWLER_STATS["failed_crawls"]
    success_rate = (
        (CRAWLER_STATS["successful_crawls"] / total * 100)
        if total > 0 else 0.0
    )
    
    # Calculate uptime
    # In a real implementation, you'd track server start time
    uptime_seconds = 0.0  # Placeholder
    
    stats = CrawlerStats(
        active_crawls=CRAWLER_STATS["active_crawls"],
        total_crawls=CRAWLER_STATS["total_crawls"],
        successful_crawls=CRAWLER_STATS["successful_crawls"],
        failed_crawls=CRAWLER_STATS["failed_crawls"],
        success_rate=success_rate,
        total_bytes_processed=CRAWLER_STATS["total_bytes_processed"],
        average_response_time_ms=CRAWLER_STATS["average_response_time_ms"],
        uptime_seconds=uptime_seconds,
        memory_usage_mb=system_stats["memory_usage_mb"],
        cpu_percent=system_stats["cpu_percent"],
        last_updated=datetime.now().isoformat()
    )
    
    return stats


@router.get(
    "/stats/stream",
    summary="Stream crawler statistics",
    description="Server-Sent Events stream of real-time crawler statistics"
)
async def stream_crawler_stats(
    interval: int = Query(2, ge=1, le=60, description="Update interval in seconds")
):
    """
    Stream real-time crawler statistics.
    
    Returns an SSE (Server-Sent Events) stream that pushes
    statistics updates at the specified interval.
    
    Example:
        ```javascript
        const eventSource = new EventSource('/monitoring/stats/stream?interval=2');
        eventSource.onmessage = (event) => {
            const stats = JSON.parse(event.data);
            console.log('Stats:', stats);
        };
        ```
    """
    
    async def generate_stats() -> AsyncGenerator[str, None]:
        """Generate stats stream."""
        try:
            while True:
                # Get current stats
                stats = await get_crawler_stats()
                
                # Format as SSE
                data = json.dumps(stats.dict())
                yield f"data: {data}\n\n"
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            logger.info("Stats stream cancelled by client")
        except Exception as e:
            logger.error(f"Error in stats stream: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stats(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get(
    "/stats/urls",
    response_model=List[URLStatistics],
    summary="Get URL statistics",
    description="Get statistics for crawled URLs"
)
async def get_url_statistics(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of URLs to return"),
    sort_by: str = Query("total_requests", description="Sort field: total_requests, success_rate, average_time_ms")
):
    """
    Get statistics for crawled URLs.
    
    Returns metrics for each URL that has been crawled,
    including request counts, success rates, and timing.
    """
    stats_list = []
    
    for url, stats in URL_STATS.items():
        total = stats["total_requests"]
        success_rate = (stats["success_count"] / total * 100) if total > 0 else 0.0
        
        stats_list.append(URLStatistics(
            url_pattern=url,
            total_requests=stats["total_requests"],
            success_count=stats["success_count"],
            failure_count=stats["failure_count"],
            success_rate=success_rate,
            average_time_ms=stats["average_time_ms"],
            last_accessed=stats["last_accessed"]
        ))
    
    # Sort
    if sort_by == "success_rate":
        stats_list.sort(key=lambda x: x.success_rate, reverse=True)
    elif sort_by == "average_time_ms":
        stats_list.sort(key=lambda x: x.average_time_ms)
    else:  # total_requests
        stats_list.sort(key=lambda x: x.total_requests, reverse=True)
    
    return stats_list[:limit]


@router.post(
    "/stats/reset",
    summary="Reset statistics",
    description="Reset all crawler statistics to zero"
)
async def reset_statistics():
    """
    Reset all statistics.
    
    Clears all accumulated statistics but keeps the server running.
    Useful for testing or starting fresh measurements.
    """
    global CRAWLER_STATS, URL_STATS
    
    CRAWLER_STATS = {
        "active_crawls": 0,
        "total_crawls": 0,
        "successful_crawls": 0,
        "failed_crawls": 0,
        "total_bytes_processed": 0,
        "average_response_time_ms": 0.0,
        "last_updated": datetime.now().isoformat(),
    }
    
    URL_STATS.clear()
    
    logger.info("All statistics reset")
    
    return {
        "success": True,
        "message": "All statistics have been reset",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Background Tasks
# ============================================================================

async def run_profiling_session(session_id: str, request: ProfilingStartRequest):
    """
    Background task to run profiling session.
    
    This performs the actual profiling work:
    1. Creates a crawler with profiling enabled
    2. Crawls the target URL
    3. Collects performance metrics
    4. Stores results in the session
    """
    start_time = time.time()
    
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        from crawl4ai.browser_profiler import BrowserProfiler
        
        logger.info(f"Starting profiling for session {session_id}")
        
        # Create profiler
        profiler = BrowserProfiler()
        
        # Configure browser and crawler
        browser_config = BrowserConfig.load(request.browser_config)
        crawler_config = CrawlerRunConfig.load(request.crawler_config)
        
        # Enable profiling options
        browser_config.profiling_enabled = True
        
        results = {}
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Start profiling
            profiler.start()
            
            # Collect system stats before
            stats_before = get_system_stats()
            
            # Crawl with timeout
            try:
                result = await asyncio.wait_for(
                    crawler.arun(request.url, config=crawler_config),
                    timeout=request.profile_duration
                )
                
                crawl_success = result.success
                
            except asyncio.TimeoutError:
                logger.warning(f"Profiling session {session_id} timed out")
                crawl_success = False
                result = None
            
            # Stop profiling
            profiler_results = profiler.stop()
            
            # Collect system stats after
            stats_after = get_system_stats()
            
            # Build results
            results = {
                "crawl_success": crawl_success,
                "url": request.url,
                "performance": profiler_results if profiler_results else {},
                "system": {
                    "before": stats_before,
                    "after": stats_after,
                    "delta": {
                        "memory_mb": stats_after["memory_usage_mb"] - stats_before["memory_usage_mb"],
                        "cpu_percent": stats_after["cpu_percent"] - stats_before["cpu_percent"],
                    }
                }
            }
            
            if result:
                results["content"] = {
                    "markdown_length": len(result.markdown) if result.markdown else 0,
                    "html_length": len(result.html) if result.html else 0,
                    "links_count": len(result.links["internal"]) + len(result.links["external"]),
                    "media_count": len(result.media["images"]) + len(result.media["videos"]),
                }
        
        # Update session with results
        end_time = time.time()
        duration = end_time - start_time
        
        PROFILING_SESSIONS[session_id].update({
            "status": "completed",
            "end_time": datetime.now().isoformat(),
            "duration_seconds": duration,
            "results": results
        })
        
        logger.info(f"Profiling session {session_id} completed in {duration:.2f}s")
        
    except Exception as e:
        logger.error(f"Profiling session {session_id} failed: {str(e)}")
        
        PROFILING_SESSIONS[session_id].update({
            "status": "failed",
            "end_time": datetime.now().isoformat(),
            "duration_seconds": time.time() - start_time,
            "error": str(e)
        })


# ============================================================================
# Middleware Integration Points
# ============================================================================

def track_crawl_start():
    """Call this when a crawl starts."""
    CRAWLER_STATS["active_crawls"] += 1
    CRAWLER_STATS["total_crawls"] += 1
    CRAWLER_STATS["last_updated"] = datetime.now().isoformat()


def track_crawl_end(url: str, success: bool, duration_ms: float, bytes_processed: int = 0):
    """Call this when a crawl ends."""
    CRAWLER_STATS["active_crawls"] = max(0, CRAWLER_STATS["active_crawls"] - 1)
    
    if success:
        CRAWLER_STATS["successful_crawls"] += 1
    else:
        CRAWLER_STATS["failed_crawls"] += 1
    
    CRAWLER_STATS["total_bytes_processed"] += bytes_processed
    
    # Update average response time (running average)
    total = CRAWLER_STATS["successful_crawls"] + CRAWLER_STATS["failed_crawls"]
    current_avg = CRAWLER_STATS["average_response_time_ms"]
    CRAWLER_STATS["average_response_time_ms"] = (
        (current_avg * (total - 1) + duration_ms) / total
    )
    
    # Update URL stats
    url_stat = URL_STATS[url]
    url_stat["total_requests"] += 1
    
    if success:
        url_stat["success_count"] += 1
    else:
        url_stat["failure_count"] += 1
    
    # Update average time for this URL
    total_url = url_stat["total_requests"]
    current_avg_url = url_stat["average_time_ms"]
    url_stat["average_time_ms"] = (
        (current_avg_url * (total_url - 1) + duration_ms) / total_url
    )
    url_stat["last_accessed"] = datetime.now().isoformat()
    
    CRAWLER_STATS["last_updated"] = datetime.now().isoformat()


# ============================================================================
# Health Check
# ============================================================================

@router.get(
    "/health",
    summary="Health check",
    description="Check if monitoring system is operational"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns status of the monitoring system.
    """
    system_stats = get_system_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len([s for s in PROFILING_SESSIONS.values() if s["status"] == "running"]),
        "total_sessions": len(PROFILING_SESSIONS),
        "system": system_stats
    }
