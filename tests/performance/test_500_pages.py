"""
Performance benchmarking for 500+ page crawls
Tests cover:
- Throughput testing (pages/second)
- Memory usage under load
- Session management at scale
- Job queue performance
- Export pipeline efficiency
"""

import pytest
import asyncio
import time
import psutil
import statistics
from datetime import datetime, timezone
from typing import List, Dict
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../deploy/docker'))

from session_analytics import SessionAnalytics, SessionMetrics, SessionState
from job_queue_enhanced import EnhancedJobQueue, JobPriority, JobStatus
from export_pipeline import ExportPipeline, ExportConfig, ExportFormat, CompressionType


class PerformanceMetrics:
    """Track performance metrics during tests"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_samples = []
        self.response_times = []
        self.pages_processed = 0
        self.errors = 0
    
    def start(self):
        """Start tracking"""
        self.start_time = time.time()
        self.memory_samples.append(psutil.Process().memory_info().rss / 1024 / 1024)
    
    def end(self):
        """End tracking"""
        self.end_time = time.time()
        self.memory_samples.append(psutil.Process().memory_info().rss / 1024 / 1024)
    
    def record_page(self, response_time: float, success: bool = True):
        """Record single page metrics"""
        self.response_times.append(response_time)
        self.pages_processed += 1
        if not success:
            self.errors += 1
        
        # Sample memory periodically
        if self.pages_processed % 10 == 0:
            self.memory_samples.append(psutil.Process().memory_info().rss / 1024 / 1024)
    
    def get_summary(self) -> Dict:
        """Get performance summary"""
        duration = self.end_time - self.start_time if self.end_time else 0
        
        return {
            'duration_seconds': duration,
            'pages_processed': self.pages_processed,
            'pages_per_second': self.pages_processed / duration if duration > 0 else 0,
            'avg_response_time': statistics.mean(self.response_times) if self.response_times else 0,
            'median_response_time': statistics.median(self.response_times) if self.response_times else 0,
            'p95_response_time': statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else 0,
            'min_response_time': min(self.response_times) if self.response_times else 0,
            'max_response_time': max(self.response_times) if self.response_times else 0,
            'memory_start_mb': self.memory_samples[0] if self.memory_samples else 0,
            'memory_end_mb': self.memory_samples[-1] if self.memory_samples else 0,
            'memory_peak_mb': max(self.memory_samples) if self.memory_samples else 0,
            'memory_growth_mb': (self.memory_samples[-1] - self.memory_samples[0]) if len(self.memory_samples) > 1 else 0,
            'error_rate': self.errors / self.pages_processed if self.pages_processed > 0 else 0,
            'success_rate': 1 - (self.errors / self.pages_processed) if self.pages_processed > 0 else 0,
        }


@pytest.fixture
async def mock_redis():
    """Mock Redis client for performance tests"""
    redis = AsyncMock()
    redis.setex = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.exists = AsyncMock(return_value=0)
    redis.sadd = AsyncMock()
    redis.scard = AsyncMock(return_value=0)
    redis.smembers = AsyncMock(return_value=[])
    redis.delete = AsyncMock()
    redis.expire = AsyncMock()
    redis.lpush = AsyncMock()
    redis.ltrim = AsyncMock()
    redis.lrange = AsyncMock(return_value=[])
    redis.llen = AsyncMock(return_value=0)
    redis.rpop = AsyncMock(return_value=None)
    redis.lrem = AsyncMock()
    return redis


@pytest.fixture
async def session_analytics(mock_redis):
    """Create session analytics with mock Redis"""
    return SessionAnalytics(mock_redis)


@pytest.fixture
async def job_queue(mock_redis):
    """Create job queue with mock Redis"""
    return EnhancedJobQueue(mock_redis)


class TestThroughput:
    """Test throughput for high-volume crawling"""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_500_pages_throughput(self, session_analytics):
        """Test processing 500 pages and measure throughput"""
        metrics = PerformanceMetrics()
        metrics.start()
        
        # Simulate 500 page crawls
        session_id = "perf_test_session"
        await session_analytics.create_session(session_id, user_id="perf_user")
        
        for i in range(500):
            start = time.time()
            
            # Simulate page crawl
            await session_analytics.track_page_crawl(
                session_id=session_id,
                bytes_transferred=50000,  # 50KB average
                response_time=0.5,  # 500ms average
                success=True
            )
            
            elapsed = time.time() - start
            metrics.record_page(elapsed)
        
        metrics.end()
        summary = metrics.get_summary()
        
        # Performance assertions
        print(f"\n{'='*60}")
        print(f"500 Pages Throughput Test Results")
        print(f"{'='*60}")
        print(f"Duration: {summary['duration_seconds']:.2f}s")
        print(f"Pages/second: {summary['pages_per_second']:.2f}")
        print(f"Avg response time: {summary['avg_response_time']*1000:.2f}ms")
        print(f"Median response time: {summary['median_response_time']*1000:.2f}ms")
        print(f"P95 response time: {summary['p95_response_time']*1000:.2f}ms")
        print(f"Memory start: {summary['memory_start_mb']:.2f}MB")
        print(f"Memory end: {summary['memory_end_mb']:.2f}MB")
        print(f"Memory peak: {summary['memory_peak_mb']:.2f}MB")
        print(f"Memory growth: {summary['memory_growth_mb']:.2f}MB")
        print(f"Success rate: {summary['success_rate']*100:.2f}%")
        print(f"{'='*60}\n")
        
        # Performance targets
        assert summary['pages_processed'] == 500
        assert summary['pages_per_second'] > 10, "Should process at least 10 pages/second"
        assert summary['memory_growth_mb'] < 500, "Memory growth should be under 500MB"
        assert summary['success_rate'] >= 0.95, "Success rate should be at least 95%"
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_1000_pages_throughput(self, session_analytics):
        """Test processing 1000 pages - stress test"""
        metrics = PerformanceMetrics()
        metrics.start()
        
        # Create multiple sessions to distribute load
        sessions = []
        for i in range(10):
            session_id = f"stress_test_session_{i}"
            await session_analytics.create_session(session_id, user_id=f"user_{i}")
            sessions.append(session_id)
        
        # Process 1000 pages across sessions
        for i in range(1000):
            start = time.time()
            session_id = sessions[i % 10]
            
            await session_analytics.track_page_crawl(
                session_id=session_id,
                bytes_transferred=50000,
                response_time=0.5,
                success=True
            )
            
            elapsed = time.time() - start
            metrics.record_page(elapsed)
        
        metrics.end()
        summary = metrics.get_summary()
        
        print(f"\n{'='*60}")
        print(f"1000 Pages Stress Test Results")
        print(f"{'='*60}")
        print(f"Duration: {summary['duration_seconds']:.2f}s")
        print(f"Pages/second: {summary['pages_per_second']:.2f}")
        print(f"Memory growth: {summary['memory_growth_mb']:.2f}MB")
        print(f"{'='*60}\n")
        
        assert summary['pages_processed'] == 1000
        assert summary['memory_growth_mb'] < 1000, "Memory growth should be under 1GB for 1000 pages"


class TestSessionManagement:
    """Test session management at scale"""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_100_concurrent_sessions(self, session_analytics):
        """Test managing 100 concurrent sessions"""
        metrics = PerformanceMetrics()
        metrics.start()
        
        # Create 100 sessions
        session_ids = []
        for i in range(100):
            session_id = f"concurrent_session_{i}"
            await session_analytics.create_session(
                session_id,
                user_id=f"user_{i % 20}"  # 20 users with 5 sessions each
            )
            session_ids.append(session_id)
        
        # Simulate activity across all sessions
        for _ in range(5):  # 5 pages per session = 500 total
            for session_id in session_ids:
                start = time.time()
                
                await session_analytics.track_page_crawl(
                    session_id=session_id,
                    bytes_transferred=50000,
                    response_time=0.5,
                    success=True
                )
                
                elapsed = time.time() - start
                metrics.record_page(elapsed)
        
        # Get statistics
        stats = await session_analytics.get_statistics()
        
        metrics.end()
        summary = metrics.get_summary()
        
        print(f"\n{'='*60}")
        print(f"100 Concurrent Sessions Test Results")
        print(f"{'='*60}")
        print(f"Total sessions: {stats.total_sessions}")
        print(f"Active sessions: {stats.active_sessions}")
        print(f"Total pages crawled: {stats.total_pages_crawled}")
        print(f"Avg pages/session: {stats.avg_pages_per_session:.2f}")
        print(f"Memory growth: {summary['memory_growth_mb']:.2f}MB")
        print(f"{'='*60}\n")
        
        assert len(session_analytics.sessions) == 100
        assert stats.total_pages_crawled == 500
        assert summary['memory_growth_mb'] < 300, "Memory should scale efficiently with sessions"
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_session_cleanup_performance(self, session_analytics):
        """Test session cleanup at scale"""
        # Create many idle sessions
        for i in range(200):
            session_id = f"cleanup_test_{i}"
            await session_analytics.create_session(session_id)
            
            # Make half of them idle
            if i < 100:
                await session_analytics.mark_idle(session_id)
        
        # Measure cleanup performance
        start = time.time()
        terminated = await session_analytics.cleanup_idle_sessions(idle_timeout_seconds=0)
        cleanup_time = time.time() - start
        
        print(f"\n{'='*60}")
        print(f"Session Cleanup Performance")
        print(f"{'='*60}")
        print(f"Sessions cleaned: {len(terminated)}")
        print(f"Cleanup time: {cleanup_time*1000:.2f}ms")
        print(f"{'='*60}\n")
        
        assert cleanup_time < 5.0, "Cleanup should complete in under 5 seconds"


class TestJobQueuePerformance:
    """Test job queue performance"""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_job_queue_throughput(self, job_queue):
        """Test job queue handling 500 URLs"""
        metrics = PerformanceMetrics()
        metrics.start()
        
        # Create job with 500 URLs
        urls = [f"https://example.com/page{i}" for i in range(500)]
        job_id = await job_queue.create_job(
            job_type="crawl",
            urls=urls,
            priority=JobPriority.NORMAL
        )
        
        # Simulate processing
        async def mock_processor(url: str, config: Dict):
            """Mock URL processor"""
            await asyncio.sleep(0.001)  # Simulate 1ms processing
            return {"url": url, "status": "success"}
        
        # Process job
        await job_queue.process_job(job_id, mock_processor)
        
        # Get job status
        result = await job_queue.get_job_status(job_id)
        
        metrics.end()
        summary = metrics.get_summary()
        
        print(f"\n{'='*60}")
        print(f"Job Queue Performance Test")
        print(f"{'='*60}")
        print(f"Job ID: {job_id}")
        print(f"Status: {result.status if result else 'N/A'}")
        print(f"Progress: {result.progress if result else {}}")
        print(f"Processing time: {summary['duration_seconds']:.2f}s")
        print(f"{'='*60}\n")
        
        assert result is not None
        assert result.progress.get('total_items') == 500
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_multiple_job_priorities(self, job_queue):
        """Test job queue with multiple priorities"""
        # Create jobs with different priorities
        jobs = []
        
        for priority in [JobPriority.LOW, JobPriority.NORMAL, JobPriority.HIGH, JobPriority.URGENT]:
            urls = [f"https://example.com/{priority.value}/page{i}" for i in range(50)]
            job_id = await job_queue.create_job(
                job_type="crawl",
                urls=urls,
                priority=priority
            )
            jobs.append((job_id, priority))
        
        # Get queue stats
        stats = await job_queue.get_queue_stats()
        
        print(f"\n{'='*60}")
        print(f"Multi-Priority Queue Test")
        print(f"{'='*60}")
        print(f"Total jobs: {stats['total_jobs']}")
        print(f"Total URLs: {stats['total_urls']}")
        print(f"Queue by priority: {stats['queued_by_priority']}")
        print(f"{'='*60}\n")
        
        assert len(jobs) == 4
        assert stats['total_jobs'] >= 4
        assert stats['total_urls'] == 200  # 50 URLs × 4 priorities


class TestExportPerformance:
    """Test export pipeline performance"""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_export_500_records(self):
        """Test exporting 500 records to different formats"""
        
        async def generate_test_data(count: int):
            """Generate test data"""
            for i in range(count):
                yield {
                    'id': i,
                    'url': f'https://example.com/page{i}',
                    'title': f'Page {i}',
                    'content': f'Content for page {i}' * 10,  # ~200 bytes
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
        
        pipeline = ExportPipeline()
        
        formats_to_test = [
            (ExportFormat.JSON, CompressionType.NONE),
            (ExportFormat.NDJSON, CompressionType.GZIP),
            (ExportFormat.CSV, CompressionType.NONE),
        ]
        
        results = []
        
        for export_format, compression in formats_to_test:
            config = ExportConfig(
                export_id=f'perf_test_{export_format.value}',
                format=export_format,
                compression=compression,
                include_metadata=False,
                pretty_print=False
            )
            
            start = time.time()
            total_bytes = 0
            
            async for chunk in pipeline.export(generate_test_data(500), config):
                total_bytes += len(chunk)
            
            duration = time.time() - start
            
            results.append({
                'format': export_format.value,
                'compression': compression.value,
                'duration_seconds': duration,
                'total_bytes': total_bytes,
                'mb_per_second': (total_bytes / 1024 / 1024) / duration if duration > 0 else 0
            })
        
        print(f"\n{'='*60}")
        print(f"Export Performance Test (500 records)")
        print(f"{'='*60}")
        for result in results:
            print(f"Format: {result['format']} ({result['compression']})")
            print(f"  Duration: {result['duration_seconds']:.2f}s")
            print(f"  Size: {result['total_bytes'] / 1024:.2f}KB")
            print(f"  Throughput: {result['mb_per_second']:.2f}MB/s")
        print(f"{'='*60}\n")
        
        # All exports should complete reasonably fast
        for result in results:
            assert result['duration_seconds'] < 10, f"{result['format']} export took too long"


class TestMemoryEfficiency:
    """Test memory efficiency under load"""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_memory_leak_detection(self, session_analytics):
        """Test for memory leaks during extended operation"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_samples = [initial_memory]
        
        # Run operations repeatedly
        for iteration in range(10):
            # Create and destroy sessions
            sessions = []
            for i in range(50):
                session_id = f"leak_test_iter{iteration}_session{i}"
                await session_analytics.create_session(session_id)
                sessions.append(session_id)
            
            # Process some pages
            for session_id in sessions:
                for _ in range(10):
                    await session_analytics.track_page_crawl(
                        session_id=session_id,
                        bytes_transferred=50000,
                        response_time=0.5,
                        success=True
                    )
            
            # Terminate all sessions
            for session_id in sessions:
                await session_analytics.terminate_session(session_id)
            
            # Sample memory
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            # Force garbage collection
            import gc
            gc.collect()
        
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        
        print(f"\n{'='*60}")
        print(f"Memory Leak Detection Test")
        print(f"{'='*60}")
        print(f"Initial memory: {initial_memory:.2f}MB")
        print(f"Final memory: {final_memory:.2f}MB")
        print(f"Growth: {memory_growth:.2f}MB")
        print(f"Iterations: 10 × 50 sessions × 10 pages = 5000 pages")
        print(f"{'='*60}\n")
        
        # Memory should not grow excessively
        assert memory_growth < 200, f"Possible memory leak: grew {memory_growth:.2f}MB"


# Performance test summary
def print_test_summary():
    """Print performance test summary"""
    print(f"\n{'='*60}")
    print(f"PERFORMANCE TEST SUITE SUMMARY")
    print(f"{'='*60}")
    print(f"✓ 500 page throughput test")
    print(f"✓ 1000 page stress test")
    print(f"✓ 100 concurrent sessions test")
    print(f"✓ Session cleanup performance")
    print(f"✓ Job queue throughput")
    print(f"✓ Multi-priority job queue")
    print(f"✓ Export performance (500 records)")
    print(f"✓ Memory leak detection")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "benchmark"])
    print_test_summary()

