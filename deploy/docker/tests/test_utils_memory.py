from types import SimpleNamespace

import psutil
import pytest

import utils


def test_unlimited_cgroup_v2_uses_container_usage(monkeypatch):
    values = {
        "/sys/fs/cgroup/memory.current": "805306368\n",
        "/sys/fs/cgroup/memory.max": "max\n",
    }

    class FakeCgroupPath:
        def __init__(self, path):
            self.path = path

        def exists(self):
            return self.path in values

        def read_text(self):
            return values[self.path]

    monkeypatch.setattr(utils, "Path", FakeCgroupPath)
    monkeypatch.setattr(
        psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=16 * 1024**3, percent=50.3),
    )

    assert utils.get_container_memory_percent() == pytest.approx(4.6875)
