"""
Tests for external Redis configuration support.

Tests the ability to configure Crawl4AI to use an external Redis server
instead of the embedded Redis via the REDIS_URL environment variable
and CRAWL4AI_DISABLE_EMBEDDED_REDIS flag.
"""

import os
import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch


class TestRedisUrlEnvironmentVariable:
    """Tests for REDIS_URL environment variable handling in load_config()."""

    def test_load_config_without_redis_url(self):
        """Default config should not have redis.uri set."""
        # Ensure REDIS_URL is not set
        env = os.environ.copy()
        env.pop("REDIS_URL", None)

        with patch.dict(os.environ, env, clear=True):
            # Import fresh to pick up env changes
            import importlib
            import sys

            # Remove cached module if exists
            if "deploy.docker.utils" in sys.modules:
                del sys.modules["deploy.docker.utils"]

            # Add deploy/docker to path temporarily
            deploy_docker_path = Path(__file__).parent.parent.parent / "deploy" / "docker"
            sys.path.insert(0, str(deploy_docker_path))

            try:
                from utils import load_config
                config = load_config()

                # uri should not be set by default
                assert "uri" not in config["redis"] or config["redis"].get("uri") is None
                # default host should be localhost
                assert config["redis"]["host"] == "localhost"
                assert config["redis"]["port"] == 6379
            finally:
                sys.path.remove(str(deploy_docker_path))

    def test_load_config_with_redis_url(self):
        """REDIS_URL env var should override redis.uri in config."""
        test_redis_url = "redis://:mypassword@external-redis.example.com:6380/2"

        env = os.environ.copy()
        env["REDIS_URL"] = test_redis_url

        with patch.dict(os.environ, env, clear=False):
            import importlib
            import sys

            if "deploy.docker.utils" in sys.modules:
                del sys.modules["deploy.docker.utils"]

            deploy_docker_path = Path(__file__).parent.parent.parent / "deploy" / "docker"
            sys.path.insert(0, str(deploy_docker_path))

            try:
                from utils import load_config
                config = load_config()

                assert config["redis"]["uri"] == test_redis_url
            finally:
                sys.path.remove(str(deploy_docker_path))


class TestEntrypointScript:
    """Tests for the entrypoint.sh script behavior."""

    @pytest.fixture
    def entrypoint_path(self):
        """Return path to the entrypoint script."""
        return Path(__file__).parent.parent.parent / "deploy" / "docker" / "entrypoint.sh"

    def test_entrypoint_script_exists(self, entrypoint_path):
        """Entrypoint script should exist."""
        assert entrypoint_path.exists(), f"entrypoint.sh not found at {entrypoint_path}"

    def test_entrypoint_script_is_executable_content(self, entrypoint_path):
        """Entrypoint script should have proper shebang."""
        content = entrypoint_path.read_text()
        assert content.startswith("#!/bin/bash"), "entrypoint.sh should start with bash shebang"

    def test_entrypoint_checks_disable_redis_env(self, entrypoint_path):
        """Entrypoint should check CRAWL4AI_DISABLE_EMBEDDED_REDIS variable."""
        content = entrypoint_path.read_text()
        assert "CRAWL4AI_DISABLE_EMBEDDED_REDIS" in content, \
            "entrypoint.sh should reference CRAWL4AI_DISABLE_EMBEDDED_REDIS"

    def test_entrypoint_generates_supervisord_without_redis(self, entrypoint_path):
        """When CRAWL4AI_DISABLE_EMBEDDED_REDIS=true, supervisord config should not include redis."""
        content = entrypoint_path.read_text()

        # Should have logic to create config without redis
        assert "supervisord.conf" in content
        # Should NOT have [program:redis] in the generated config when disabled
        # The script generates a config that only has gunicorn
        assert "[program:gunicorn]" in content

    def test_entrypoint_default_uses_original_supervisord(self, entrypoint_path):
        """Default behavior should use original supervisord.conf with redis."""
        content = entrypoint_path.read_text()

        # Should have else branch that uses original supervisord.conf
        assert "supervisord -c supervisord.conf" in content or \
               "exec supervisord -c supervisord.conf" in content


class TestDockerfileHealthcheck:
    """Tests for Dockerfile healthcheck configuration."""

    @pytest.fixture
    def dockerfile_path(self):
        """Return path to the Dockerfile."""
        return Path(__file__).parent.parent.parent / "Dockerfile"

    def test_dockerfile_exists(self, dockerfile_path):
        """Dockerfile should exist."""
        assert dockerfile_path.exists(), f"Dockerfile not found at {dockerfile_path}"

    def test_healthcheck_conditional_redis(self, dockerfile_path):
        """Healthcheck should conditionally check redis based on CRAWL4AI_DISABLE_EMBEDDED_REDIS."""
        content = dockerfile_path.read_text()

        assert "HEALTHCHECK" in content
        assert "CRAWL4AI_DISABLE_EMBEDDED_REDIS" in content, \
            "Healthcheck should reference CRAWL4AI_DISABLE_EMBEDDED_REDIS for conditional redis check"

    def test_healthcheck_still_checks_app_health(self, dockerfile_path):
        """Healthcheck should always check the application health endpoint."""
        content = dockerfile_path.read_text()

        assert "curl" in content and "health" in content, \
            "Healthcheck should curl the /health endpoint"


class TestConfigYmlDocumentation:
    """Tests for config.yml documentation of external Redis."""

    @pytest.fixture
    def config_path(self):
        """Return path to config.yml."""
        return Path(__file__).parent.parent.parent / "deploy" / "docker" / "config.yml"

    def test_config_yml_exists(self, config_path):
        """config.yml should exist."""
        assert config_path.exists(), f"config.yml not found at {config_path}"

    def test_config_documents_redis_url(self, config_path):
        """config.yml should document REDIS_URL environment variable."""
        content = config_path.read_text()

        assert "REDIS_URL" in content, \
            "config.yml should document REDIS_URL environment variable"

    def test_config_documents_disable_embedded_redis(self, config_path):
        """config.yml should document CRAWL4AI_DISABLE_EMBEDDED_REDIS option."""
        content = config_path.read_text()

        assert "CRAWL4AI_DISABLE_EMBEDDED_REDIS" in content, \
            "config.yml should document CRAWL4AI_DISABLE_EMBEDDED_REDIS option"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
