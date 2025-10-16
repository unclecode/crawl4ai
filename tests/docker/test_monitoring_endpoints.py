"""
Integration tests for monitoring and profiling endpoints.

Tests all monitoring endpoints including profiling sessions, statistics,
health checks, and real-time streaming.
"""

import asyncio
import json
import time
from typing import Dict, List

import pytest
from httpx import AsyncClient

# Base URL for the Docker API server
BASE_URL = "http://localhost:11235"


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def client():
    """Create HTTP client for tests."""
    async with AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        yield client


class TestHealthEndpoint:
    """Tests for /monitoring/health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test basic health check returns OK."""
        response = await client.get("/monitoring/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


class TestStatsEndpoints:
    """Tests for /monitoring/stats/* endpoints."""

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, client: AsyncClient):
        """Test getting stats when no crawls have been performed."""
        # Reset stats first
        await client.post("/monitoring/stats/reset")
        
        response = await client.get("/monitoring/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        assert "active_crawls" in data
        assert "total_crawls" in data
        assert "successful_crawls" in data
        assert "failed_crawls" in data
        assert "success_rate" in data
        assert "avg_duration_ms" in data
        assert "total_bytes_processed" in data
        assert "system_stats" in data
        
        # Verify system stats
        system = data["system_stats"]
        assert "cpu_percent" in system
        assert "memory_percent" in system
        assert "memory_used_mb" in system
        assert "memory_available_mb" in system
        assert "disk_usage_percent" in system
        assert "active_processes" in system

    @pytest.mark.asyncio
    async def test_stats_after_crawl(self, client: AsyncClient):
        """Test stats are updated after performing a crawl."""
        # Reset stats
        await client.post("/monitoring/stats/reset")
        
        # Perform a simple crawl
        crawl_request = {
            "urls": ["https://www.example.com"],
            "crawler_config": {
                "word_count_threshold": 10
            }
        }
        crawl_response = await client.post("/crawl", json=crawl_request)
        assert crawl_response.status_code == 200
        
        # Get stats
        response = await client.get("/monitoring/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats are updated
        assert data["total_crawls"] >= 1
        assert data["successful_crawls"] >= 0
        assert data["failed_crawls"] >= 0
        assert data["total_crawls"] == data["successful_crawls"] + data["failed_crawls"]
        
        # Verify success rate calculation
        if data["total_crawls"] > 0:
            expected_rate = (data["successful_crawls"] / data["total_crawls"]) * 100
            assert abs(data["success_rate"] - expected_rate) < 0.01

    @pytest.mark.asyncio
    async def test_stats_reset(self, client: AsyncClient):
        """Test resetting stats clears all counters."""
        # Ensure we have some stats
        crawl_request = {
            "urls": ["https://www.example.com"],
            "crawler_config": {"word_count_threshold": 10}
        }
        await client.post("/crawl", json=crawl_request)
        
        # Reset stats
        reset_response = await client.post("/monitoring/stats/reset")
        assert reset_response.status_code == 200
        data = reset_response.json()
        assert data["status"] == "reset"
        assert "previous_stats" in data
        
        # Verify stats are cleared
        stats_response = await client.get("/monitoring/stats")
        stats = stats_response.json()
        assert stats["total_crawls"] == 0
        assert stats["successful_crawls"] == 0
        assert stats["failed_crawls"] == 0
        assert stats["active_crawls"] == 0

    @pytest.mark.asyncio
    async def test_url_specific_stats(self, client: AsyncClient):
        """Test getting URL-specific statistics."""
        # Reset and crawl
        await client.post("/monitoring/stats/reset")
        crawl_request = {
            "urls": ["https://www.example.com"],
            "crawler_config": {"word_count_threshold": 10}
        }
        await client.post("/crawl", json=crawl_request)
        
        # Get URL stats
        response = await client.get("/monitoring/stats/urls")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            url_stat = data[0]
            assert "url" in url_stat
            assert "total_requests" in url_stat
            assert "successful_requests" in url_stat
            assert "failed_requests" in url_stat
            assert "avg_duration_ms" in url_stat
            assert "total_bytes_processed" in url_stat
            assert "last_request_time" in url_stat


class TestStatsStreaming:
    """Tests for /monitoring/stats/stream SSE endpoint."""

    @pytest.mark.asyncio
    async def test_stats_stream_basic(self, client: AsyncClient):
        """Test SSE streaming of statistics."""
        # Start streaming (collect a few events then stop)
        events = []
        async with client.stream("GET", "/monitoring/stats/stream") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            
            # Collect first 3 events
            count = 0
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix
                    data = json.loads(data_str)
                    events.append(data)
                    count += 1
                    if count >= 3:
                        break
        
        # Verify we got events
        assert len(events) >= 3
        
        # Verify event structure
        for event in events:
            assert "active_crawls" in event
            assert "total_crawls" in event
            assert "successful_crawls" in event
            assert "system_stats" in event

    @pytest.mark.asyncio
    async def test_stats_stream_during_crawl(self, client: AsyncClient):
        """Test streaming updates during active crawl."""
        # Start streaming in background
        stream_task = None
        events = []
        
        async def collect_stream():
            async with client.stream("GET", "/monitoring/stats/stream") as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        data = json.loads(data_str)
                        events.append(data)
                        if len(events) >= 5:
                            break
        
        # Start stream collection
        stream_task = asyncio.create_task(collect_stream())
        
        # Wait a bit then start crawl
        await asyncio.sleep(1)
        crawl_request = {
            "urls": ["https://www.example.com"],
            "crawler_config": {"word_count_threshold": 10}
        }
        asyncio.create_task(client.post("/crawl", json=crawl_request))
        
        # Wait for events
        try:
            await asyncio.wait_for(stream_task, timeout=15.0)
        except asyncio.TimeoutError:
            stream_task.cancel()
        
        # Should have collected some events
        assert len(events) > 0


class TestProfilingEndpoints:
    """Tests for /monitoring/profile/* endpoints."""

    @pytest.mark.asyncio
    async def test_list_profiling_sessions_empty(self, client: AsyncClient):
        """Test listing profiling sessions when none exist."""
        response = await client.get("/monitoring/profile")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    @pytest.mark.asyncio
    async def test_start_profiling_session(self, client: AsyncClient):
        """Test starting a new profiling session."""
        request_data = {
            "urls": ["https://www.example.com", "https://www.python.org"],
            "duration_seconds": 2,
            "crawler_config": {
                "word_count_threshold": 10
            }
        }
        
        response = await client.post("/monitoring/profile/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert "status" in data
        assert data["status"] == "running"
        assert "started_at" in data
        assert "urls" in data
        assert len(data["urls"]) == 2
        
        return data["session_id"]

    @pytest.mark.asyncio
    async def test_get_profiling_session(self, client: AsyncClient):
        """Test retrieving a profiling session by ID."""
        # Start a session
        request_data = {
            "urls": ["https://www.example.com"],
            "duration_seconds": 2,
            "crawler_config": {"word_count_threshold": 10}
        }
        start_response = await client.post("/monitoring/profile/start", json=request_data)
        session_id = start_response.json()["session_id"]
        
        # Get session immediately (should be running)
        response = await client.get(f"/monitoring/profile/{session_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == session_id
        assert data["status"] in ["running", "completed"]
        assert "started_at" in data
        assert "urls" in data

    @pytest.mark.asyncio
    async def test_profiling_session_completion(self, client: AsyncClient):
        """Test profiling session completes and produces results."""
        # Start a short session
        request_data = {
            "urls": ["https://www.example.com"],
            "duration_seconds": 3,
            "crawler_config": {"word_count_threshold": 10}
        }
        start_response = await client.post("/monitoring/profile/start", json=request_data)
        session_id = start_response.json()["session_id"]
        
        # Wait for completion
        await asyncio.sleep(5)
        
        # Get completed session
        response = await client.get(f"/monitoring/profile/{session_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
        assert "completed_at" in data
        assert "duration_seconds" in data
        assert "results" in data
        
        # Verify results structure
        results = data["results"]
        assert "total_requests" in results
        assert "successful_requests" in results
        assert "failed_requests" in results
        assert "avg_response_time_ms" in results
        assert "system_metrics" in results

    @pytest.mark.asyncio
    async def test_profiling_session_not_found(self, client: AsyncClient):
        """Test retrieving non-existent session returns 404."""
        response = await client.get("/monitoring/profile/nonexistent-id-12345")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_profiling_session(self, client: AsyncClient):
        """Test deleting a profiling session."""
        # Start a session
        request_data = {
            "urls": ["https://www.example.com"],
            "duration_seconds": 1,
            "crawler_config": {"word_count_threshold": 10}
        }
        start_response = await client.post("/monitoring/profile/start", json=request_data)
        session_id = start_response.json()["session_id"]
        
        # Wait for completion
        await asyncio.sleep(2)
        
        # Delete session
        delete_response = await client.delete(f"/monitoring/profile/{session_id}")
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["status"] == "deleted"
        assert data["session_id"] == session_id
        
        # Verify it's gone
        get_response = await client.get(f"/monitoring/profile/{session_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_cleanup_old_sessions(self, client: AsyncClient):
        """Test cleaning up old profiling sessions."""
        # Start a few sessions
        for i in range(3):
            request_data = {
                "urls": ["https://www.example.com"],
                "duration_seconds": 1,
                "crawler_config": {"word_count_threshold": 10}
            }
            await client.post("/monitoring/profile/start", json=request_data)
        
        # Wait for completion
        await asyncio.sleep(2)
        
        # Cleanup sessions older than 0 seconds (all completed ones)
        cleanup_response = await client.post(
            "/monitoring/profile/cleanup",
            json={"max_age_seconds": 0}
        )
        assert cleanup_response.status_code == 200
        data = cleanup_response.json()
        assert "deleted_count" in data
        assert data["deleted_count"] >= 0

    @pytest.mark.asyncio
    async def test_list_sessions_after_operations(self, client: AsyncClient):
        """Test listing sessions shows correct state after various operations."""
        # Start a session
        request_data = {
            "urls": ["https://www.example.com"],
            "duration_seconds": 5,
            "crawler_config": {"word_count_threshold": 10}
        }
        start_response = await client.post("/monitoring/profile/start", json=request_data)
        session_id = start_response.json()["session_id"]
        
        # List sessions
        list_response = await client.get("/monitoring/profile")
        assert list_response.status_code == 200
        data = list_response.json()
        
        # Should have at least one session
        sessions = data["sessions"]
        assert len(sessions) >= 1
        
        # Find our session
        our_session = next((s for s in sessions if s["session_id"] == session_id), None)
        assert our_session is not None
        assert our_session["status"] in ["running", "completed"]


class TestProfilingWithCrawlConfig:
    """Tests for profiling with various crawler configurations."""

    @pytest.mark.asyncio
    async def test_profiling_with_extraction_strategy(self, client: AsyncClient):
        """Test profiling with extraction strategy configured."""
        request_data = {
            "urls": ["https://www.example.com"],
            "duration_seconds": 2,
            "crawler_config": {
                "word_count_threshold": 10,
                "extraction_strategy": "NoExtractionStrategy"
            }
        }
        
        response = await client.post("/monitoring/profile/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_profiling_with_browser_config(self, client: AsyncClient):
        """Test profiling with custom browser configuration."""
        request_data = {
            "urls": ["https://www.example.com"],
            "duration_seconds": 2,
            "browser_config": {
                "headless": True,
                "verbose": False
            },
            "crawler_config": {
                "word_count_threshold": 10
            }
        }
        
        response = await client.post("/monitoring/profile/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"


class TestIntegrationScenarios:
    """Integration tests for real-world monitoring scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_crawls_and_monitoring(self, client: AsyncClient):
        """Test monitoring multiple concurrent crawls."""
        # Reset stats
        await client.post("/monitoring/stats/reset")
        
        # Start multiple crawls concurrently
        crawl_tasks = []
        urls = [
            "https://www.example.com",
            "https://www.python.org",
            "https://www.github.com"
        ]
        
        for url in urls:
            crawl_request = {
                "urls": [url],
                "crawler_config": {"word_count_threshold": 10}
            }
            task = client.post("/crawl", json=crawl_request)
            crawl_tasks.append(task)
        
        # Execute concurrently
        responses = await asyncio.gather(*crawl_tasks, return_exceptions=True)
        
        # Get stats
        await asyncio.sleep(1)  # Give tracking time to update
        stats_response = await client.get("/monitoring/stats")
        stats = stats_response.json()
        
        # Should have tracked multiple crawls
        assert stats["total_crawls"] >= len(urls)

    @pytest.mark.asyncio
    async def test_profiling_and_stats_correlation(self, client: AsyncClient):
        """Test that profiling data correlates with statistics."""
        # Reset stats
        await client.post("/monitoring/stats/reset")
        
        # Start profiling session
        profile_request = {
            "urls": ["https://www.example.com"],
            "duration_seconds": 3,
            "crawler_config": {"word_count_threshold": 10}
        }
        profile_response = await client.post("/monitoring/profile/start", json=profile_request)
        session_id = profile_response.json()["session_id"]
        
        # Wait for completion
        await asyncio.sleep(5)
        
        # Get profiling results
        profile_data_response = await client.get(f"/monitoring/profile/{session_id}")
        profile_data = profile_data_response.json()
        
        # Get stats
        stats_response = await client.get("/monitoring/stats")
        stats = stats_response.json()
        
        # Stats should reflect profiling activity
        assert stats["total_crawls"] >= profile_data["results"]["total_requests"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
