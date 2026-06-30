"""
R7 container/deployment posture - static parse of the deployment artifacts.

These assert the hardening is declared in the Dockerfile / docker-compose.yml /
supervisord.conf. The RUNTIME acceptance gate (the hardened image builds,
Chromium starts without --no-sandbox under userns/seccomp, the read-only rootfs
+ tmpfs work, redis truly requires auth) needs an actual `docker build` + boot
and is tracked as build-gated; it is out of scope for this offline suite.
"""

import os
import re
import stat
import subprocess

import pytest

pytestmark = pytest.mark.posture

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _read(path):
    with open(path) as f:
        return f.read()


@pytest.fixture(scope="module")
def dockerfile():
    return _read(os.path.join(REPO_ROOT, "Dockerfile"))


@pytest.fixture(scope="module")
def compose():
    return _read(os.path.join(REPO_ROOT, "docker-compose.yml"))


@pytest.fixture(scope="module")
def supervisord():
    return _read(os.path.join(DOCKER_DIR, "supervisord.conf"))


class TestDockerfile:
    def test_no_redis_expose(self, dockerfile):
        # No active EXPOSE 6379 line (commented references are fine).
        for line in dockerfile.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert not re.match(r"EXPOSE\s+.*\b6379\b", stripped), \
                "redis port 6379 must not be EXPOSEd"

    def test_app_dir_root_owned_readonly(self, dockerfile):
        assert "chown -R root:root ${APP_HOME}" in dockerfile
        assert "chmod -R a-w ${APP_HOME}" in dockerfile

    def test_artifact_dir_created_0700(self, dockerfile):
        assert "/var/lib/crawl4ai/outputs" in dockerfile
        assert "chmod 700 /var/lib/crawl4ai/outputs" in dockerfile

    def test_runs_as_non_root(self, dockerfile):
        assert re.search(r"^USER\s+appuser", dockerfile, re.MULTILINE)


class TestSupervisord:
    def test_redis_requires_password(self, supervisord):
        assert "--requirepass" in supervisord

    def test_redis_bound_loopback(self, supervisord):
        assert "--bind 127.0.0.1" in supervisord

    def test_gunicorn_bind_is_env_driven(self, supervisord):
        # entrypoint.sh resolves GUNICORN_BIND (loopback unless a credential).
        assert "ENV_GUNICORN_BIND" in supervisord

    def test_gunicorn_request_limits(self, supervisord):
        assert "--limit-request-line" in supervisord


class TestCompose:
    def test_cap_drop_all(self, compose):
        assert "cap_drop" in compose and "ALL" in compose

    def test_no_new_privileges(self, compose):
        assert "no-new-privileges:true" in compose

    def test_read_only_rootfs(self, compose):
        assert re.search(r"read_only:\s*true", compose)

    def test_no_host_dev_shm_bind(self, compose):
        assert "/dev/shm:/dev/shm" not in compose
        assert "shm_size" in compose

    def test_pids_limit(self, compose):
        assert "pids_limit" in compose

    def test_read_only_runtime_tmpfs_are_appuser_owned(self, compose):
        assert "/var/lib/redis:uid=999,gid=999,mode=0700" in compose
        assert "/var/lib/crawl4ai/outputs:uid=999,gid=999,mode=0700" in compose
        assert "/home/appuser/.crawl4ai:uid=999,gid=999,mode=0700" in compose
        assert "/home/appuser/.gunicorn:uid=999,gid=999,mode=0700" in compose

    def test_playwright_cache_is_not_shadowed(self, compose):
        assert "/home/appuser/.cache\n" not in compose
        assert "/home/appuser/.cache/url_seeder:uid=999,gid=999,mode=0700" in compose


class TestEntrypoint:
    def test_entrypoint_exists_and_resolves_bind(self):
        src = _read(os.path.join(DOCKER_DIR, "entrypoint.sh"))
        assert "GUNICORN_BIND" in src and "REDIS_PASSWORD" in src
        assert "127.0.0.1" in src  # loopback default when no credential

    def _run_entrypoint(self, tmp_path, extra_env):
        fake_supervisord = tmp_path / "supervisord"
        fake_supervisord.write_text(
            "#!/usr/bin/env sh\n"
            "echo \"GUNICORN_BIND=${GUNICORN_BIND}\"\n"
            "echo \"REDIS_PASSWORD_SET=${REDIS_PASSWORD:+yes}\"\n",
            encoding="utf-8",
        )
        fake_supervisord.chmod(
            fake_supervisord.stat().st_mode | stat.S_IXUSR
        )

        env = os.environ.copy()
        for key in (
            "CRAWL4AI_API_TOKEN",
            "CRAWL4AI_JWT_ENABLED",
            "CRAWL4AI_PORT",
            "GUNICORN_BIND",
            "REDIS_PASSWORD",
        ):
            env.pop(key, None)
        env.update(extra_env)
        env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"

        return subprocess.run(
            ["bash", os.path.join(DOCKER_DIR, "entrypoint.sh")],
            cwd=DOCKER_DIR,
            env=env,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )

    def test_entrypoint_preserves_ipv6_wildcard_when_token_allows_exposure(self, tmp_path):
        result = self._run_entrypoint(
            tmp_path,
            {
                "CRAWL4AI_API_TOKEN": "test-token",
                "CRAWL4AI_JWT_ENABLED": "false",
                "CRAWL4AI_PORT": "11235",
            },
        )
        assert result.returncode == 0, result.stderr
        assert "GUNICORN_BIND=[::]:11235" in result.stdout

    def test_entrypoint_ignores_kubernetes_service_link_port_env(self, tmp_path):
        result = self._run_entrypoint(
            tmp_path,
            {
                "CRAWL4AI_API_TOKEN": "test-token",
                "CRAWL4AI_JWT_ENABLED": "false",
                "CRAWL4AI_PORT": "tcp://10.0.101.25:80",
            },
        )
        assert result.returncode == 0, result.stderr
        assert "GUNICORN_BIND=[::]:11235" in result.stdout
        assert "ignoring non-numeric CRAWL4AI_PORT" in result.stderr

    def test_entrypoint_ignores_service_link_port_env_without_token(self, tmp_path):
        result = self._run_entrypoint(
            tmp_path,
            {
                "CRAWL4AI_JWT_ENABLED": "false",
                "CRAWL4AI_PORT": "tcp://10.0.101.25:80",
            },
        )
        assert result.returncode == 0, result.stderr
        assert "GUNICORN_BIND=127.0.0.1:11235" in result.stdout
        assert "ignoring non-numeric CRAWL4AI_PORT" in result.stderr

    def test_entrypoint_preserves_explicit_gunicorn_bind(self, tmp_path):
        result = self._run_entrypoint(
            tmp_path,
            {
                "CRAWL4AI_API_TOKEN": "test-token",
                "CRAWL4AI_JWT_ENABLED": "false",
                "CRAWL4AI_PORT": "not-a-port",
                "GUNICORN_BIND": "0.0.0.0:9999",
            },
        )
        assert result.returncode == 0, result.stderr
        assert "GUNICORN_BIND=0.0.0.0:9999" in result.stdout

    def test_entrypoint_rejects_other_non_numeric_port_env(self, tmp_path):
        result = self._run_entrypoint(
            tmp_path,
            {
                "CRAWL4AI_API_TOKEN": "test-token",
                "CRAWL4AI_JWT_ENABLED": "false",
                "CRAWL4AI_PORT": "http://10.0.101.25:80",
            },
        )
        assert result.returncode == 1
        assert "CRAWL4AI_PORT must be numeric" in result.stderr


class TestSandboxOptOut:
    def test_default_keeps_no_sandbox(self, server_module, monkeypatch):
        monkeypatch.setattr(server_module, "CHROMIUM_SANDBOX", False)
        assert "--no-sandbox" in server_module._browser_extra_args()

    def test_opt_in_drops_no_sandbox(self, server_module, monkeypatch):
        # CRAWL4AI_CHROMIUM_SANDBOX=true -> run the renderer sandboxed.
        monkeypatch.setattr(server_module, "CHROMIUM_SANDBOX", True)
        assert "--no-sandbox" not in server_module._browser_extra_args()
        # other flags are preserved
        assert "--disable-dev-shm-usage" in server_module._browser_extra_args()
