"""
Session Analytics and Tracking System
Provides comprehensive session monitoring and analytics:
- Session lifecycle tracking
- Usage statistics per session
- Performance metrics
- Session cleanup analytics
- Multi-session support
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

from pydantic import BaseModel, Field
from redis import asyncio as aioredis
import json
import logging

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Session lifecycle states"""
    CREATED = "created"
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class SessionEvent(str, Enum):
    """Session event types"""
    CREATED = "created"
    ACTIVATED = "activated"
    PAGE_CRAWLED = "page_crawled"
    IDLE_WARNING = "idle_warning"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class SessionMetrics:
    """Real-time session metrics"""
    session_id: str
    user_id: Optional[str] = None
    state: SessionState = SessionState.CREATED
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    pages_crawled: int = 0
    total_bytes: int = 0
    avg_response_time: float = 0.0
    errors_count: int = 0
    browser_config_signature: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "state": self.state.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "pages_crawled": self.pages_crawled,
            "total_bytes": self.total_bytes,
            "avg_response_time": self.avg_response_time,
            "errors_count": self.errors_count,
            "browser_config_signature": self.browser_config_signature,
            "tags": list(self.tags),
            "duration_seconds": time.time() - self.created_at,
            "idle_seconds": time.time() - self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SessionMetrics":
        """Create from dictionary"""
        tags = set(data.get("tags", []))
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            state=SessionState(data.get("state", SessionState.CREATED.value)),
            created_at=data["created_at"],
            last_activity=data["last_activity"],
            pages_crawled=data.get("pages_crawled", 0),
            total_bytes=data.get("total_bytes", 0),
            avg_response_time=data.get("avg_response_time", 0.0),
            errors_count=data.get("errors_count", 0),
            browser_config_signature=data.get("browser_config_signature"),
            tags=tags
        )


class SessionEventLog(BaseModel):
    """Session event log entry"""
    timestamp: datetime
    session_id: str
    event_type: SessionEvent
    details: Optional[Dict] = None


class SessionStatistics(BaseModel):
    """Aggregated session statistics"""
    total_sessions: int = 0
    active_sessions: int = 0
    idle_sessions: int = 0
    expired_sessions: int = 0
    total_pages_crawled: int = 0
    total_bytes_transferred: int = 0
    avg_session_duration: float = 0.0
    avg_pages_per_session: float = 0.0
    avg_response_time: float = 0.0
    sessions_by_state: Dict[str, int] = Field(default_factory=dict)
    top_users: List[Dict] = Field(default_factory=list)


class SessionGroupConfig(BaseModel):
    """Configuration for session groups"""
    group_id: str
    max_sessions: int = 10
    max_pages_per_session: int = 100
    idle_timeout_seconds: int = 300
    tags: Set[str] = Field(default_factory=set)


class SessionAnalytics:
    """Session analytics and tracking system"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.sessions: Dict[str, SessionMetrics] = {}
        self.session_groups: Dict[str, SessionGroupConfig] = {}
        self.lock = asyncio.Lock()
        
        # Redis key prefixes
        self.session_prefix = "session:metrics:"
        self.event_prefix = "session:events:"
        self.stats_prefix = "session:stats:"
        self.group_prefix = "session:group:"
    
    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        browser_config_signature: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ) -> SessionMetrics:
        """Create and track new session"""
        async with self.lock:
            metrics = SessionMetrics(
                session_id=session_id,
                user_id=user_id,
                state=SessionState.CREATED,
                browser_config_signature=browser_config_signature,
                tags=tags or set()
            )
            
            self.sessions[session_id] = metrics
            
            # Store in Redis
            await self._save_session_to_redis(metrics)
            
            # Log creation event
            await self._log_event(
                session_id,
                SessionEvent.CREATED,
                {"user_id": user_id, "tags": list(tags or [])}
            )
            
            logger.info(f"Session created: {session_id} (user: {user_id})")
            return metrics
    
    async def activate_session(self, session_id: str):
        """Mark session as active"""
        async with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].state = SessionState.ACTIVE
                self.sessions[session_id].last_activity = time.time()
                
                await self._save_session_to_redis(self.sessions[session_id])
                await self._log_event(session_id, SessionEvent.ACTIVATED)
    
    async def track_page_crawl(
        self,
        session_id: str,
        bytes_transferred: int,
        response_time: float,
        success: bool = True
    ):
        """Track page crawl in session"""
        async with self.lock:
            if session_id not in self.sessions:
                logger.warning(f"Session not found: {session_id}")
                return
            
            metrics = self.sessions[session_id]
            metrics.pages_crawled += 1
            metrics.total_bytes += bytes_transferred
            metrics.last_activity = time.time()
            
            # Update average response time
            if metrics.pages_crawled == 1:
                metrics.avg_response_time = response_time
            else:
                metrics.avg_response_time = (
                    (metrics.avg_response_time * (metrics.pages_crawled - 1) + response_time) 
                    / metrics.pages_crawled
                )
            
            if not success:
                metrics.errors_count += 1
                await self._log_event(session_id, SessionEvent.ERROR)
            
            if metrics.state != SessionState.ACTIVE:
                metrics.state = SessionState.ACTIVE
            
            await self._save_session_to_redis(metrics)
            await self._log_event(
                session_id,
                SessionEvent.PAGE_CRAWLED,
                {
                    "bytes": bytes_transferred,
                    "response_time": response_time,
                    "success": success
                }
            )
    
    async def mark_idle(self, session_id: str):
        """Mark session as idle"""
        async with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].state = SessionState.IDLE
                await self._save_session_to_redis(self.sessions[session_id])
                await self._log_event(session_id, SessionEvent.IDLE_WARNING)
    
    async def expire_session(self, session_id: str):
        """Expire session"""
        async with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].state = SessionState.EXPIRED
                await self._save_session_to_redis(self.sessions[session_id])
                await self._log_event(session_id, SessionEvent.EXPIRED)
    
    async def terminate_session(self, session_id: str) -> Optional[SessionMetrics]:
        """Terminate session and return final metrics"""
        async with self.lock:
            if session_id not in self.sessions:
                return None
            
            metrics = self.sessions[session_id]
            metrics.state = SessionState.TERMINATED
            
            await self._save_session_to_redis(metrics)
            await self._log_event(
                session_id,
                SessionEvent.TERMINATED,
                metrics.to_dict()
            )
            
            # Archive to Redis with longer TTL
            await self._archive_session(metrics)
            
            # Remove from active tracking
            del self.sessions[session_id]
            
            logger.info(f"Session terminated: {session_id} (pages: {metrics.pages_crawled})")
            return metrics
    
    async def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for specific session"""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Try loading from Redis
        return await self._load_session_from_redis(session_id)
    
    async def get_all_sessions(self) -> List[SessionMetrics]:
        """Get all active sessions"""
        return list(self.sessions.values())
    
    async def get_user_sessions(self, user_id: str) -> List[SessionMetrics]:
        """Get all sessions for a user"""
        return [
            metrics for metrics in self.sessions.values()
            if metrics.user_id == user_id
        ]
    
    async def get_statistics(self) -> SessionStatistics:
        """Get aggregated session statistics"""
        sessions = list(self.sessions.values())
        
        if not sessions:
            return SessionStatistics()
        
        total_duration = sum(time.time() - s.created_at for s in sessions)
        total_pages = sum(s.pages_crawled for s in sessions)
        total_bytes = sum(s.total_bytes for s in sessions)
        
        # Count sessions by state
        state_counts = defaultdict(int)
        for session in sessions:
            state_counts[session.state.value] += 1
        
        # Top users by session count
        user_sessions = defaultdict(int)
        for session in sessions:
            if session.user_id:
                user_sessions[session.user_id] += 1
        
        top_users = [
            {"user_id": user_id, "session_count": count}
            for user_id, count in sorted(user_sessions.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return SessionStatistics(
            total_sessions=len(sessions),
            active_sessions=state_counts[SessionState.ACTIVE.value],
            idle_sessions=state_counts[SessionState.IDLE.value],
            expired_sessions=state_counts[SessionState.EXPIRED.value],
            total_pages_crawled=total_pages,
            total_bytes_transferred=total_bytes,
            avg_session_duration=total_duration / len(sessions) if sessions else 0,
            avg_pages_per_session=total_pages / len(sessions) if sessions else 0,
            avg_response_time=sum(s.avg_response_time for s in sessions) / len(sessions) if sessions else 0,
            sessions_by_state=dict(state_counts),
            top_users=top_users
        )
    
    async def cleanup_idle_sessions(self, idle_timeout_seconds: int = 300) -> List[str]:
        """Cleanup idle sessions and return terminated IDs"""
        current_time = time.time()
        terminated = []
        
        async with self.lock:
            for session_id, metrics in list(self.sessions.items()):
                idle_time = current_time - metrics.last_activity
                
                if idle_time > idle_timeout_seconds:
                    if metrics.state != SessionState.IDLE:
                        await self.mark_idle(session_id)
                    
                    # Expire if idle for 2x timeout
                    if idle_time > idle_timeout_seconds * 2:
                        await self.expire_session(session_id)
                        terminated.append(session_id)
        
        return terminated
    
    async def create_session_group(
        self,
        group_id: str,
        config: SessionGroupConfig
    ):
        """Create session group with shared configuration"""
        self.session_groups[group_id] = config
        
        # Store in Redis
        key = f"{self.group_prefix}{group_id}"
        await self.redis.setex(
            key,
            86400,  # 24 hours
            json.dumps(config.model_dump())
        )
        
        logger.info(f"Session group created: {group_id}")
    
    async def get_session_group(self, group_id: str) -> Optional[SessionGroupConfig]:
        """Get session group configuration"""
        if group_id in self.session_groups:
            return self.session_groups[group_id]
        
        # Load from Redis
        key = f"{self.group_prefix}{group_id}"
        data = await self.redis.get(key)
        
        if data:
            return SessionGroupConfig.model_validate_json(data)
        
        return None
    
    async def get_session_events(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[SessionEventLog]:
        """Get event log for session"""
        key = f"{self.event_prefix}{session_id}"
        events = await self.redis.lrange(key, 0, limit - 1)
        
        return [SessionEventLog.model_validate_json(event) for event in events]
    
    # Private helper methods
    
    async def _save_session_to_redis(self, metrics: SessionMetrics):
        """Save session metrics to Redis"""
        key = f"{self.session_prefix}{metrics.session_id}"
        await self.redis.setex(
            key,
            3600,  # 1 hour TTL
            json.dumps(metrics.to_dict())
        )
    
    async def _load_session_from_redis(self, session_id: str) -> Optional[SessionMetrics]:
        """Load session metrics from Redis"""
        key = f"{self.session_prefix}{session_id}"
        data = await self.redis.get(key)
        
        if data:
            return SessionMetrics.from_dict(json.loads(data))
        
        return None
    
    async def _archive_session(self, metrics: SessionMetrics):
        """Archive terminated session with longer TTL"""
        key = f"session:archive:{metrics.session_id}"
        await self.redis.setex(
            key,
            86400 * 7,  # 7 days
            json.dumps(metrics.to_dict())
        )
    
    async def _log_event(
        self,
        session_id: str,
        event_type: SessionEvent,
        details: Optional[Dict] = None
    ):
        """Log session event"""
        event = SessionEventLog(
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            event_type=event_type,
            details=details
        )
        
        key = f"{self.event_prefix}{session_id}"
        await self.redis.lpush(key, event.model_dump_json())
        await self.redis.ltrim(key, 0, 999)  # Keep last 1000 events
        await self.redis.expire(key, 86400)  # 24 hours


class SessionMonitor:
    """Background task for session monitoring"""
    
    def __init__(self, analytics: SessionAnalytics):
        self.analytics = analytics
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self, check_interval: int = 60):
        """Start monitoring background task"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitor_loop(check_interval))
        logger.info("Session monitor started")
    
    async def stop(self):
        """Stop monitoring background task"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Session monitor stopped")
    
    async def _monitor_loop(self, check_interval: int):
        """Monitor loop for session cleanup"""
        while self.running:
            try:
                # Cleanup idle sessions
                terminated = await self.analytics.cleanup_idle_sessions()
                
                if terminated:
                    logger.info(f"Cleaned up {len(terminated)} idle sessions")
                
                # Log statistics
                stats = await self.analytics.get_statistics()
                logger.debug(
                    f"Session stats - Active: {stats.active_sessions}, "
                    f"Idle: {stats.idle_sessions}, "
                    f"Total pages: {stats.total_pages_crawled}"
                )
                
            except Exception as e:
                logger.error(f"Error in session monitor: {e}")
            
            await asyncio.sleep(check_interval)

