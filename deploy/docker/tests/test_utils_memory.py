"""Unit tests for deploy/docker/utils.get_container_memory_percent().

Pure-function tests: no Docker, no network, no cgroup filesystem. The cgroup
paths and psutil host stats are injected, so the cgroup v2 "max" (unlimited)
handling and the v1 > 1e18 sentinel are both covered deterministically.
"""

import importlib
import sys
import types
from pathlib import Path

import pytest


def _stub_modules():
    """Return a dict of temporary stubs for modules that utils.py needs at import time.

    Only stubs modules that are NOT already in sys.modules (using setdefault)
    so that real installed packages are never overwritten.
    """
    stubs = {}
    for module_name in ("dns", "dns.resolver", "yaml", "fastapi", "psutil"):
        if module_name not in sys.modules:
            stub = types.ModuleType(module_name)
            stubs[module_name] = stub
    if "fastapi" not in sys.modules:
        stubs.setdefault("fastapi", types.ModuleType("fastapi"))
    if not hasattr(stubs.get("fastapi", sys.modules.get("fastapi")), "Request"):
        (stubs.get("fastapi") or sys.modules["fastapi"]).Request = object
    return stubs


@pytest.fixture()
def utils():
    """Import deploy/docker/utils.py with temporary stubs, cleaning up after."""
    # Capture modules that will be temporarily injected
    stubs = _stub_modules()
    added_modules = {}

    for name, mod in stubs.items():
        if name not in sys.modules:
            sys.modules[name] = mod
            added_modules[name] = mod

    # Ensure deploy/docker is on sys.path so `import utils` works
    docker_dir = str(Path(__file__).resolve().parents[1])
    path_inserted = docker_dir not in sys.path
    if path_inserted:
        sys.path.insert(0, docker_dir)

    try:
        # Force fresh import so monkeypatch on utils.Path works correctly
        if "utils" in sys.modules:
            mod = importlib.reload(sys.modules["utils"])
        else:
            mod = importlib.import_module("utils")
        yield mod
    finally:
        # Restore sys.modules — remove ONLY the stubs we added
        for name in added_modules:
            sys.modules.pop(name, None)
        # Remove deploy/docker/utils from sys.modules so next test gets fresh import
        sys.modules.pop("utils", None)
        if path_inserted:
            sys.path.remove(docker_dir)


HOST_TOTAL = 16 * 1024**3  # 16 GiB
HOST_PERCENT = 47.5


@pytest.fixture()
def host_memory(monkeypatch, utils):
    """Pin psutil.virtual_memory() so host-total fallbacks are deterministic."""
    psutil_mod = sys.modules.get("psutil")
    if psutil_mod is None:
        psutil_mod = types.ModuleType("psutil")
    monkeypatch.setattr(
        psutil_mod,
        "virtual_memory",
        lambda: types.SimpleNamespace(total=HOST_TOTAL, percent=HOST_PERCENT),
        raising=False,
    )
    return psutil_mod


def _patch_cgroup_files(monkeypatch, utils_mod, values, present):
    """Replace utils.Path with a fake whose files mirror a cgroup filesystem."""
    present_paths = set(present)

    def factory(path):
        fake = types.SimpleNamespace(path=str(path))
        fake.exists = lambda: fake.path in present_paths
        fake.read_text = lambda: utils_read(fake.path)
        return fake

    def utils_read(path):
        if path not in present_paths:
            raise FileNotFoundError(path)
        return values.get(path, "0")

    monkeypatch.setattr(utils_mod, "Path", factory)


def test_cgroup_v2_numeric_limit(monkeypatch, utils, host_memory):
    _patch_cgroup_files(
        monkeypatch,
        utils,
        {
            "/sys/fs/cgroup/memory.current": "524288000",
            "/sys/fs/cgroup/memory.max": "2147483648",
        },
        {"/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory.max"},
    )

    assert utils.get_container_memory_percent() == pytest.approx(524288000 / 2147483648 * 100)


def test_cgroup_v2_unlimited_max_counts_against_host_total(monkeypatch, utils, host_memory):
    # Regression for https://github.com/unclecode/crawl4ai/issues/2123:
    # int("max") used to raise ValueError, the bare except swallowed it, and the
    # guard reported the HOST's usage percent instead of container usage vs
    # host total (the intent of the existing "unlimited" branch).
    usage = 512 * 1024**2
    _patch_cgroup_files(
        monkeypatch,
        utils,
        {
            "/sys/fs/cgroup/memory.current": str(usage),
            "/sys/fs/cgroup/memory.max": "max\n",  # cgroup v2 "no limit" sentinel
        },
        {"/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory.max"},
    )

    assert utils.get_container_memory_percent() == pytest.approx(usage / HOST_TOTAL * 100)


def test_cgroup_v1_numeric_limit(monkeypatch, utils, host_memory):
    _patch_cgroup_files(
        monkeypatch,
        utils,
        {
            "/sys/fs/cgroup/memory/memory.usage_in_bytes": "262144000",
            "/sys/fs/cgroup/memory/memory.limit_in_bytes": "1073741824",
        },
        {
            "/sys/fs/cgroup/memory/memory.usage_in_bytes",
            "/sys/fs/cgroup/memory/memory.limit_in_bytes",
        },
    )

    assert utils.get_container_memory_percent() == pytest.approx(262144000 / 1073741824 * 100)


def test_cgroup_v1_unlimited_huge_limit_counts_against_host_total(monkeypatch, utils, host_memory):
    usage = 256 * 1024**2
    _patch_cgroup_files(
        monkeypatch,
        utils,
        {
            "/sys/fs/cgroup/memory/memory.usage_in_bytes": str(usage),
            "/sys/fs/cgroup/memory/memory.limit_in_bytes": str(2**63),  # v1 "no limit"
        },
        {
            "/sys/fs/cgroup/memory/memory.usage_in_bytes",
            "/sys/fs/cgroup/memory/memory.limit_in_bytes",
        },
    )

    assert utils.get_container_memory_percent() == pytest.approx(usage / HOST_TOTAL * 100)


def test_non_container_falls_back_to_host_percent(monkeypatch, utils, host_memory):
    _patch_cgroup_files(monkeypatch, utils, {}, set())

    assert utils.get_container_memory_percent() == pytest.approx(HOST_PERCENT)


def test_stubs_do_not_pollute_sys_modules():
    """Verify that after the utils fixture, no fake modules remain in sys.modules."""
    # This test itself imports utils via the fixture, which should clean up
    # The test body is intentionally empty — if the fixture cleanup is broken,
    # this test's own sys.modules will still have stubs, which is the bug we're testing for.
    # Instead, run a subprocess-like check:
    real_modules = {}
    for name in ("dns", "dns.resolver", "yaml", "fastapi", "psutil"):
        mod = sys.modules.get(name)
        real_modules[name] = mod  # Could be None (not installed) or real module

    # After the utils fixture teardown, stubs we added should be gone.
    # The only modules that should remain are ones that were there before.
    # Since we can't easily test "was this module here before this file loaded",
    # we just verify: if a stub module is in sys.modules, it should have been there already.
    # For this test, we don't use the utils fixture, so nothing should change.
    for name in ("dns", "dns.resolver", "yaml", "fastapi", "psutil"):
        after = sys.modules.get(name)
        if after is not None and isinstance(after, types.ModuleType) and not hasattr(after, "__file__"):
            # This is likely a stub we injected — but since we didn't use the fixture,
            # this means something else polluted. Flag it.
            assert False, f"Module '{name}' appears to be a stub in sys.modules without __file__"
