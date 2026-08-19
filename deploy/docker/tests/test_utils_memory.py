"""Unit tests for deploy/docker/utils.get_container_memory_percent().

Pure-function tests: no Docker, no network, no cgroup filesystem. The cgroup
paths and psutil host stats are injected, so the cgroup v2 "max" (unlimited)
handling and the v1 > 1e18 sentinel are both covered deterministically.
"""

import sys
import types
from pathlib import Path

import pytest

# utils.py imports third-party modules (fastapi, dnspython, yaml, psutil) at
# module top. When they are not installed (bare pytest run), stub them so the
# import works; setdefault keeps the real modules when the Docker dev
# environment provides them.
def _install_import_stubs() -> None:
    for module_name in ("dns", "dns.resolver", "yaml", "fastapi", "psutil"):
        if module_name not in sys.modules:
            sys.modules[module_name] = types.ModuleType(module_name)
    if not hasattr(sys.modules["fastapi"], "Request"):
        sys.modules["fastapi"].Request = object  # only `Request` is used


_install_import_stubs()

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import utils  # noqa: E402


HOST_TOTAL = 16 * 1024**3  # 16 GiB
HOST_PERCENT = 47.5


@pytest.fixture()
def host_memory(monkeypatch):
    """Pin psutil.virtual_memory() so host-total fallbacks are deterministic."""
    psutil = sys.modules["psutil"]
    monkeypatch.setattr(
        psutil,
        "virtual_memory",
        lambda: types.SimpleNamespace(total=HOST_TOTAL, percent=HOST_PERCENT),
        raising=False,
    )
    return psutil


def _patch_cgroup_files(monkeypatch, values, present):
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

    monkeypatch.setattr(utils, "Path", factory)


def test_cgroup_v2_numeric_limit(monkeypatch, host_memory):
    _patch_cgroup_files(
        monkeypatch,
        {
            "/sys/fs/cgroup/memory.current": "524288000",
            "/sys/fs/cgroup/memory.max": "2147483648",
        },
        {"/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory.max"},
    )

    assert utils.get_container_memory_percent() == pytest.approx(524288000 / 2147483648 * 100)


def test_cgroup_v2_unlimited_max_counts_against_host_total(monkeypatch, host_memory):
    # Regression for https://github.com/unclecode/crawl4ai/issues/2123:
    # int("max") used to raise ValueError, the bare except swallowed it, and the
    # guard reported the HOST's usage percent instead of container usage vs
    # host total (the intent of the existing "unlimited" branch).
    usage = 512 * 1024**2
    _patch_cgroup_files(
        monkeypatch,
        {
            "/sys/fs/cgroup/memory.current": str(usage),
            "/sys/fs/cgroup/memory.max": "max\n",  # cgroup v2 "no limit" sentinel
        },
        {"/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory.max"},
    )

    assert utils.get_container_memory_percent() == pytest.approx(usage / HOST_TOTAL * 100)


def test_cgroup_v1_numeric_limit(monkeypatch, host_memory):
    _patch_cgroup_files(
        monkeypatch,
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


def test_cgroup_v1_unlimited_huge_limit_counts_against_host_total(monkeypatch, host_memory):
    usage = 256 * 1024**2
    _patch_cgroup_files(
        monkeypatch,
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


def test_non_container_falls_back_to_host_percent(monkeypatch, host_memory):
    _patch_cgroup_files(monkeypatch, {}, set())

    assert utils.get_container_memory_percent() == pytest.approx(HOST_PERCENT)
