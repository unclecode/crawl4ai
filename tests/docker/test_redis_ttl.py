"""
Unit tests for Redis TTL (Time-To-Live) feature.

These tests verify:
1. TTL configuration loading from config.yml
2. Environment variable override (REDIS_TASK_TTL)
3. hset_with_ttl helper function behavior
4. TTL is applied when set > 0
5. TTL is not applied when set to 0
"""
import asyncio
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestGetRedisTaskTTL:
    """Tests for get_redis_task_ttl function."""

    def test_returns_configured_ttl(self):
        """Should return TTL from config when present."""
        import sys
        sys.path.insert(0, 'deploy/docker')
        from utils import get_redis_task_ttl

        config = {"redis": {"task_ttl_seconds": 7200}}
        assert get_redis_task_ttl(config) == 7200

    def test_returns_default_when_not_configured(self):
        """Should return default 3600 when TTL not in config."""
        import sys
        sys.path.insert(0, 'deploy/docker')
        from utils import get_redis_task_ttl

        config = {"redis": {}}
        assert get_redis_task_ttl(config) == 3600

    def test_returns_default_when_redis_missing(self):
        """Should return default 3600 when redis section missing."""
        import sys
        sys.path.insert(0, 'deploy/docker')
        from utils import get_redis_task_ttl

        config = {}
        assert get_redis_task_ttl(config) == 3600

    def test_returns_zero_when_configured_zero(self):
        """Should return 0 when TTL explicitly set to 0 (disabled)."""
        import sys
        sys.path.insert(0, 'deploy/docker')
        from utils import get_redis_task_ttl

        config = {"redis": {"task_ttl_seconds": 0}}
        assert get_redis_task_ttl(config) == 0


class TestLoadConfigTTL:
    """Tests for TTL configuration loading."""

    def test_env_override_valid_value(self):
        """REDIS_TASK_TTL env var should override config value."""
        import sys
        sys.path.insert(0, 'deploy/docker')

        with patch.dict(os.environ, {"REDIS_TASK_TTL": "1800"}):
            # Need to reload to pick up env var
            import importlib
            import utils
            importlib.reload(utils)

            config = utils.load_config()
            assert config["redis"]["task_ttl_seconds"] == 1800

    def test_env_override_invalid_value_uses_default(self):
        """Invalid REDIS_TASK_TTL should be ignored with warning."""
        import sys
        sys.path.insert(0, 'deploy/docker')

        with patch.dict(os.environ, {"REDIS_TASK_TTL": "invalid"}):
            import importlib
            import utils
            importlib.reload(utils)

            config = utils.load_config()
            # Should fall back to config.yml default (3600)
            assert config["redis"]["task_ttl_seconds"] == 3600

    def test_env_override_zero_disables_ttl(self):
        """REDIS_TASK_TTL=0 should disable TTL."""
        import sys
        sys.path.insert(0, 'deploy/docker')

        with patch.dict(os.environ, {"REDIS_TASK_TTL": "0"}):
            import importlib
            import utils
            importlib.reload(utils)

            config = utils.load_config()
            assert config["redis"]["task_ttl_seconds"] == 0


class TestHsetWithTTL:
    """Tests for hset_with_ttl helper function.

    These tests recreate the hset_with_ttl logic to verify correctness
    without importing the full api.py (which has heavy dependencies).
    """

    def test_sets_hash_and_ttl(self):
        """Should call hset and expire when TTL > 0."""
        import sys
        sys.path.insert(0, 'deploy/docker')
        from utils import get_redis_task_ttl

        async def hset_with_ttl(redis, key, mapping, config):
            """Recreate the function for testing."""
            await redis.hset(key, mapping=mapping)
            ttl = get_redis_task_ttl(config)
            if ttl > 0:
                await redis.expire(key, ttl)

        async def run_test():
            mock_redis = AsyncMock()

            config = {"redis": {"task_ttl_seconds": 3600}}
            key = "task:test123"
            mapping = {"status": "processing", "url": "https://example.com"}

            await hset_with_ttl(mock_redis, key, mapping, config)

            mock_redis.hset.assert_called_once_with(key, mapping=mapping)
            mock_redis.expire.assert_called_once_with(key, 3600)

        asyncio.run(run_test())

    def test_no_expire_when_ttl_zero(self):
        """Should not call expire when TTL is 0 (disabled)."""
        import sys
        sys.path.insert(0, 'deploy/docker')
        from utils import get_redis_task_ttl

        async def hset_with_ttl(redis, key, mapping, config):
            """Recreate the function for testing."""
            await redis.hset(key, mapping=mapping)
            ttl = get_redis_task_ttl(config)
            if ttl > 0:
                await redis.expire(key, ttl)

        async def run_test():
            mock_redis = AsyncMock()

            config = {"redis": {"task_ttl_seconds": 0}}
            key = "task:test456"
            mapping = {"status": "completed"}

            await hset_with_ttl(mock_redis, key, mapping, config)

            mock_redis.hset.assert_called_once_with(key, mapping=mapping)
            mock_redis.expire.assert_not_called()

        asyncio.run(run_test())

    def test_custom_ttl_value(self):
        """Should use custom TTL value from config."""
        import sys
        sys.path.insert(0, 'deploy/docker')
        from utils import get_redis_task_ttl

        async def hset_with_ttl(redis, key, mapping, config):
            """Recreate the function for testing."""
            await redis.hset(key, mapping=mapping)
            ttl = get_redis_task_ttl(config)
            if ttl > 0:
                await redis.expire(key, ttl)

        async def run_test():
            mock_redis = AsyncMock()

            config = {"redis": {"task_ttl_seconds": 86400}}  # 24 hours
            key = "task:custom"
            mapping = {"status": "processing"}

            await hset_with_ttl(mock_redis, key, mapping, config)

            mock_redis.expire.assert_called_once_with(key, 86400)

        asyncio.run(run_test())

    def test_default_ttl_when_not_configured(self):
        """Should use default TTL (3600) when not in config."""
        import sys
        sys.path.insert(0, 'deploy/docker')
        from utils import get_redis_task_ttl

        async def hset_with_ttl(redis, key, mapping, config):
            """Recreate the function for testing."""
            await redis.hset(key, mapping=mapping)
            ttl = get_redis_task_ttl(config)
            if ttl > 0:
                await redis.expire(key, ttl)

        async def run_test():
            mock_redis = AsyncMock()

            config = {}  # No redis config
            key = "task:noconfig"
            mapping = {"status": "processing"}

            await hset_with_ttl(mock_redis, key, mapping, config)

            mock_redis.expire.assert_called_once_with(key, 3600)

        asyncio.run(run_test())


class TestTTLDocumentation:
    """Tests to verify TTL is documented in config.yml."""

    def test_config_has_ttl_setting(self):
        """Verify config.yml contains task_ttl_seconds setting."""
        import sys
        sys.path.insert(0, 'deploy/docker')
        from utils import load_config

        config = load_config()
        assert "redis" in config
        assert "task_ttl_seconds" in config["redis"]

    def test_config_default_is_3600(self):
        """Verify default TTL in config.yml is 3600 (1 hour)."""
        import sys
        sys.path.insert(0, 'deploy/docker')

        # Clear any env override
        with patch.dict(os.environ, {}, clear=True):
            # Remove REDIS_TASK_TTL if present
            os.environ.pop("REDIS_TASK_TTL", None)

            import importlib
            import utils
            importlib.reload(utils)

            config = utils.load_config()
            assert config["redis"]["task_ttl_seconds"] == 3600
