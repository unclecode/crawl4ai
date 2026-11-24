"""crawl4ai-setup and crawl4ai-doctor: a failure gets the real fix and a real exit code, never the cloud."""

import subprocess

import pytest

from crawl4ai import cloud_notice, install


class _Installs:
    """Stands in for subprocess.check_call: records each command and fails the ones asked to fail."""

    def __init__(self, fail_with_deps=False, fail_alone=False):
        self.commands = []
        self.fail_with_deps = fail_with_deps
        self.fail_alone = fail_alone

    def __call__(self, command):
        self.commands.append(command)
        with_deps = "--with-deps" in command
        if (with_deps and self.fail_with_deps) or (not with_deps and self.fail_alone):
            raise subprocess.CalledProcessError(1, command)
        return 0


def test_the_browser_installs_with_its_system_libraries(monkeypatch):
    installs = _Installs()
    monkeypatch.setattr(install.subprocess, "check_call", installs)
    assert install._install_chromium("playwright") is True
    assert len(installs.commands) == 1 and "--with-deps" in installs.commands[0]


def test_without_root_the_browser_installs_alone(monkeypatch):
    installs = _Installs(fail_with_deps=True)
    monkeypatch.setattr(install.subprocess, "check_call", installs)
    assert install._install_chromium("playwright") is True
    assert "--with-deps" not in installs.commands[1], "the second try needs no root"


def test_nothing_installs_returns_false(monkeypatch):
    monkeypatch.setattr(install.subprocess, "check_call", _Installs(fail_with_deps=True, fail_alone=True))
    assert install._install_chromium("playwright") is False


def test_a_failed_setup_exits_1_and_shows_no_banner(monkeypatch):
    banners = []
    monkeypatch.delenv("CRAWL4AI_MODE", raising=False)
    monkeypatch.setattr(install, "setup_home_directory", lambda: None)
    monkeypatch.setattr(install, "run_migration", lambda: None)
    monkeypatch.setattr(install, "install_playwright", lambda: False)
    monkeypatch.setattr(cloud_notice, "_print", lambda lines, logger=None: banners.append(lines))
    with pytest.raises(SystemExit) as exit_info:
        install.post_install()
    assert exit_info.value.code == 1
    assert banners == []


def test_a_good_setup_shows_the_banner(monkeypatch):
    banners = []
    monkeypatch.delenv("CRAWL4AI_MODE", raising=False)
    monkeypatch.delenv(cloud_notice._ENV_OFF, raising=False)
    monkeypatch.setattr(install, "setup_home_directory", lambda: None)
    monkeypatch.setattr(install, "run_migration", lambda: None)
    monkeypatch.setattr(install, "install_playwright", lambda: True)
    monkeypatch.setattr(cloud_notice, "_print", lambda lines, logger=None: banners.append(lines))
    install.post_install()
    assert banners == [cloud_notice.LINES]


@pytest.mark.parametrize("passed, code", [(True, 0), (False, 1)])
def test_the_doctor_exit_code_follows_the_test_and_hides_the_cloud(monkeypatch, passed, code):
    # setenv first, so pytest restores the variable after doctor() writes it
    monkeypatch.setenv(cloud_notice._ENV_OFF, "0")

    async def fake_doctor():
        return passed

    monkeypatch.setattr(install, "run_doctor", fake_doctor)
    with pytest.raises(SystemExit) as exit_info:
        install.doctor()
    assert exit_info.value.code == code
    assert cloud_notice.is_off()
