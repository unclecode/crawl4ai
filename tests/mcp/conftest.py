"""MCP test configuration and collection controls.

- Prevent pytest from collecting manual smoke scripts.
- Provide shared fixtures so E2E tests pick up directory setup/cleanup.
- Start shared FastAPI+MCP server for all xdist workers on ephemeral port.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
import contextlib
import socket
import time
from pathlib import Path
from types import SimpleNamespace
import logging
import multiprocessing as mp
import pytest

# 1) Do not collect manual scripts
collect_ignore = [
    "test_mcp_socket.py",
    "test_mcp_http_listing.py",
    "test_mcp_js_exec.py",
    "test_backward_compatibility.py",
]


@pytest.fixture(autouse=True)
def _mcp_exports_dir_guard():
    """Ensure export dir exists and gets cleaned between tests.

    Mirrors the behavior previously in test_config.py but applies to all tests
    in this directory by living in conftest.py.
    """
    export_dir = os.environ.get("MCP_EXPORT_DIR", "/tmp/crawl4ai-exports")
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    yield
    # Clean up e2e-*-prefixed artifacts to avoid clutter
    p = Path(export_dir)
    if p.exists():
        for file in p.rglob("e2e-*"):
            try:
                file.unlink()
            except Exception:
                pass


# 2b) Async mode configuration for pytest-asyncio
# pytest-asyncio uses asyncio by default, no configuration needed


# 2c) Ephemeral FastAPI server for REST and MCP
def _pick_free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_http(url: str, timeout_s: float = 20.0) -> None:
    try:
        import httpx
    except Exception:  # pragma: no cover
        raise RuntimeError("httpx required for E2E tests")

    start = time.time()
    with httpx.Client(timeout=2.0) as client:
        while True:
            try:
                resp = client.get(f"{url}/mcp/schema")
                if resp.status_code == 200:
                    return
            except Exception:
                pass
            if time.time() - start > timeout_s:
                raise TimeoutError(f"Server not reachable at {url}")
            time.sleep(0.2)


def _serve_child(host: str, port: int, verbose: bool) -> None:
    """Run server in subprocess with coverage tracking."""
    import os, sys, contextlib, logging as clog
    from pathlib import Path

    # Ensure project root is in sys.path for child process
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Start coverage BEFORE importing any deploy.docker modules
    try:
        import coverage
        cov = coverage.Coverage(data_suffix=True, auto_data=True)
        cov.start()
    except ImportError:
        cov = None

    base_url = f"http://{host}:{port}"

    if not verbose:
        clog.disable(clog.CRITICAL)

    # Import server modules AFTER coverage starts
    from uvicorn import Config, Server
    with open(os.devnull, 'w') as _devnull:
        with contextlib.redirect_stdout(_devnull), contextlib.redirect_stderr(_devnull):
            from deploy.docker import server as _srv  # type: ignore
            try:
                _srv.mcp_service.base_url = base_url
                if hasattr(_srv, "config") and isinstance(_srv.config, dict):
                    _srv.config.get("app", {}).update({"port": port, "host": host})
            except Exception:
                pass
            from deploy.docker.server import app  # type: ignore

    config = Config(app=app, host=host, port=port,
                    log_level="info" if verbose else "critical",
                    access_log=bool(verbose))
    server = Server(config)

    try:
        if verbose:
            server.run()
        else:
            with open(os.devnull, 'w') as _devnull2:
                with contextlib.redirect_stdout(_devnull2), contextlib.redirect_stderr(_devnull2):
                    server.run()
    finally:
        # Stop coverage and save data
        if cov:
            cov.stop()
            cov.save()


def _start_server_on_master() -> tuple[str, mp.Process] | None:
    try:
        from uvicorn import Config, Server
    except Exception:
        return None

    verbose = os.getenv("C4AI_E2E_VERBOSE", "0").lower() in ("1", "true", "yes", "debug")

    host = "127.0.0.1"
    port = _pick_free_port()
    base_url = f"http://{host}:{port}"

    proc = mp.Process(target=_serve_child, args=(host, port, verbose), name="uvicorn-shared", daemon=True)
    proc.start()

    try:
        import time, httpx
        if not verbose:
            logging.getLogger("httpx").setLevel(logging.ERROR)
        for _ in range(50):
            try:
                r = httpx.get(f"{base_url}/mcp/schema", timeout=1.0)
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.1)
    except Exception:
        pass

    desired = {
        "core.mcp_service": logging.INFO if verbose else logging.WARNING,
        "mcp.server.streamable_http_manager": logging.INFO if verbose else logging.WARNING,
        "mcp.server.lowlevel.server": logging.INFO if verbose else logging.WARNING,
        "mcp.server.streamable_http": logging.INFO if verbose else logging.WARNING,
        "deploy.docker.server": logging.INFO if verbose else logging.WARNING,
        "app.api": logging.INFO if verbose else logging.WARNING,
        "httpx": logging.INFO if verbose else logging.WARNING,
        "uvicorn": logging.INFO if verbose else logging.ERROR,
        "core.error_context": logging.ERROR if verbose else logging.CRITICAL,
    }
    for name, level in desired.items():
        try:
            lg = logging.getLogger(name)
            lg.setLevel(level)
            lg.handlers[:] = []
            lg.propagate = True
        except Exception:
            pass

    return base_url, proc


@pytest.fixture(scope="session")
def server_url() -> str:
    """Session-wide base URL for MCP/REST tests.

    - If MCP_BASE_URL is set (shared server started by master), yield it.
    - Otherwise, start an ephemeral uvicorn server and yield its base URL.
    """
    base = os.environ.get("MCP_BASE_URL")
    if base:
        yield base.rstrip("/")
        return

    try:
        from uvicorn import Config, Server
    except Exception as e:  # pragma: no cover
        pytest.skip("uvicorn is required for E2E tests; install it in the venv")

    verbose = os.getenv("C4AI_E2E_VERBOSE", "0").lower() in ("1", "true", "yes", "debug")

    if verbose:
        from deploy.docker.server import app  # type: ignore
    else:
        with open(os.devnull, 'w') as _devnull:
            with contextlib.redirect_stdout(_devnull), contextlib.redirect_stderr(_devnull):
                from deploy.docker.server import app  # type: ignore
    try:
        from deploy.docker import server as _srv  # type: ignore
    except Exception:
        _srv = None

    port = _pick_free_port()
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    config = Config(
        app=app,
        host=host,
        port=port,
        log_level="info" if verbose else "critical",
        access_log=bool(verbose),
    )
    server = Server(config)

    # Wrap server.run with coverage tracking
    def _run_with_coverage():
        try:
            import coverage
            cov = coverage.Coverage(data_suffix=True, auto_data=True, concurrency=["thread"])
            cov.start()
        except ImportError:
            cov = None

        try:
            if verbose:
                server.run()
            else:
                with open(os.devnull, 'w') as _devnull2:
                    with contextlib.redirect_stdout(_devnull2), contextlib.redirect_stderr(_devnull2):
                        server.run()
        finally:
            if cov:
                cov.stop()
                cov.save()

    t = __import__("threading").Thread(target=_run_with_coverage, name="uvicorn-test-server", daemon=True)
    t.start()

    _wait_for_http(url)
    if _srv is not None and getattr(_srv, "mcp_service", None) is not None:
        try:
            _srv.mcp_service.base_url = url
            if hasattr(_srv, "config") and isinstance(_srv.config, dict):
                _srv.config.get("app", {}).update({"port": port, "host": host})
        except Exception:
            pass
    try:
        yield url
    finally:
        server.should_exit = True
        t.join(timeout=5)


@pytest.fixture(scope="session")
def mcp_url(server_url: str) -> str:
    return f"{server_url}/mcp"


# 3) Centralized test data fixtures (pythonic and typed)

@dataclass(frozen=True)
class McpURLs:
    playground: str
    playground_index: str
    example: str


@pytest.fixture
def mcp_urls(server_url: str) -> McpURLs:
    """Central URLs used by E2E tests, derived from server_url."""
    return McpURLs(
        playground=f"{server_url}/playground",
        playground_index=f"{server_url}/playground/index.html",
        example="https://example.com",
    )


@pytest.fixture
def js_snippets() -> dict[str, list[str]]:
    """Common JS snippets for execute_js tests."""
    return {
        "title_only": ["document.title"],
        "simple_values": [
            "document.title",
            "document.body.tagName",
        ],
    }


@pytest.fixture
def make_export_path():
    """Factory to create unique, per-test export paths under the allowed base dir.

    Ensures xdist-safe paths by segregating by worker id and test nodeid.
    """
    base_dir = Path(os.environ.get("MCP_EXPORT_DIR", "/tmp/crawl4ai-exports"))
    worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0")

    def factory(request, filename: str) -> str:
        safe_nodeid = request.node.nodeid.replace(os.sep, "_").replace("::", "_")
        dir_path = base_dir / f"pytest-{worker}"
        dir_path.mkdir(parents=True, exist_ok=True)
        return str(dir_path / f"e2e-{safe_nodeid}-{filename}")

    return factory


# Pytest hooks for xdist coordination
def pytest_configure(config):
    if getattr(config, "workerinput", None) is None:
        pre_base = os.getenv("MCP_BASE_URL")
        if pre_base:
            base_url = pre_base.rstrip("/")
            os.environ["MCP_BASE_URL"] = base_url
            config._c4ai_base_url = base_url
        else:
            started = _start_server_on_master()
            if started:
                base_url, proc = started
                os.environ["MCP_BASE_URL"] = base_url
                config._c4ai_proc = proc
                config._c4ai_base_url = base_url


def pytest_sessionstart(session):
    wi = getattr(session.config, "workerinput", None)
    if wi and "c4ai_base_url" in wi:
        os.environ["MCP_BASE_URL"] = wi["c4ai_base_url"]


def pytest_unconfigure(config):
    if getattr(config, "workerinput", None) is None:
        proc = getattr(config, "_c4ai_proc", None)
        if proc is not None:
            try:
                proc.terminate()
            except Exception:
                pass
            try:
                proc.join(timeout=5)
            except Exception:
                pass


# xdist-specific hook - conditionally defined
def pytest_addhooks(pluginmanager):
    """Dynamically register xdist hooks only if xdist is loaded."""
    from pytest import hookimpl

    class XDistHooks:
        @hookimpl
        def pytest_configure_node(self, node):
            """xdist hook: pass base_url to workers."""
            base_url = getattr(node.config, "_c4ai_base_url", None)
            if base_url:
                node.workerinput["c4ai_base_url"] = base_url

    if pluginmanager.has_plugin("xdist"):
        pluginmanager.register(XDistHooks(), "crawl4ai_xdist_hooks")
