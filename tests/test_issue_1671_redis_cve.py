"""
Tests for issue #1671: Redis CVE-2025-49844 in Docker image

Verifies that the Dockerfile correctly:
1. Installs curl/gnupg before adding the Redis apt repo
2. Adds the official Redis repository
3. Pins redis-server and redis-tools to a CVE-patched version
4. Holds packages to prevent upgrades by subsequent apt-get calls
"""

import re
import pytest


@pytest.fixture(scope="module")
def dockerfile_content():
    with open("Dockerfile", "r") as f:
        return f.read()


class TestRedisRepoSetup:
    """Test that the official Redis apt repository is properly configured."""

    def test_curl_gnupg_installed_before_repo(self, dockerfile_content):
        """curl and gnupg must be installed before adding the Redis repo."""
        curl_install = dockerfile_content.find("apt-get install -y --no-install-recommends curl gnupg")
        repo_add = dockerfile_content.find("packages.redis.io/gpg")
        assert curl_install != -1, "curl/gnupg pre-install step missing"
        assert repo_add != -1, "Redis repo GPG key import missing"
        assert curl_install < repo_add, "curl/gnupg must be installed BEFORE adding Redis repo"

    def test_redis_gpg_key_added(self, dockerfile_content):
        """Redis GPG key must be imported for signed repo."""
        assert "packages.redis.io/gpg" in dockerfile_content
        assert "redis-archive-keyring.gpg" in dockerfile_content

    def test_redis_apt_repo_added(self, dockerfile_content):
        """Official Redis apt repo must be configured."""
        assert "packages.redis.io/deb" in dockerfile_content
        assert "bookworm main" in dockerfile_content


class TestRedisVersionPinning:
    """Test that Redis is pinned to a CVE-patched version."""

    def test_redis_version_arg_defined(self, dockerfile_content):
        """REDIS_VERSION build arg must be defined with a patched version."""
        match = re.search(r'ARG REDIS_VERSION="([^"]+)"', dockerfile_content)
        assert match is not None, "REDIS_VERSION ARG not found"
        version = match.group(1)
        # Must be >= 7.2.7 (first version patching CVE-2025-49844)
        ver_match = re.search(r'7\.2\.(\d+)', version)
        assert ver_match is not None, f"Version {version} is not a 7.2.x release"
        patch = int(ver_match.group(1))
        assert patch >= 7, f"Version 7.2.{patch} is below 7.2.7 (CVE patch)"

    def test_redis_server_uses_version_arg(self, dockerfile_content):
        """redis-server install must reference REDIS_VERSION."""
        assert "redis-server${REDIS_VERSION:+=$REDIS_VERSION}" in dockerfile_content

    def test_redis_tools_pinned_too(self, dockerfile_content):
        """redis-tools must also be pinned to avoid dependency conflicts."""
        assert "redis-tools${REDIS_VERSION:+=$REDIS_VERSION}" in dockerfile_content

    def test_redis_packages_held(self, dockerfile_content):
        """Redis packages must be held to prevent upgrades by playwright install --with-deps."""
        assert "apt-mark hold redis-server redis-tools" in dockerfile_content


class TestDockerfileIntegrity:
    """Test that the Dockerfile doesn't have structural issues."""

    def test_no_duplicate_redis_install(self, dockerfile_content):
        """Redis should only be installed once."""
        count = dockerfile_content.count("redis-server${REDIS_VERSION")
        assert count == 1, f"redis-server installed {count} times, expected 1"

    def test_redis_version_comment_present(self, dockerfile_content):
        """Documentation comment about REDIS_VERSION should exist."""
        assert "CVE-patched" in dockerfile_content or "CVE" in dockerfile_content

    def test_version_override_documented(self, dockerfile_content):
        """Build arg override syntax should be documented."""
        assert "--build-arg REDIS_VERSION" in dockerfile_content
