"""Path-traversal regression tests for crawler file downloads.

Y4tacker reported an arbitrary-file-write -> RCE: a download filename taken
from an attacker-controlled Content-Disposition header (HTTP strategy) or the
browser's suggested filename (Playwright strategy) was joined to the downloads
dir with no confinement, so an absolute path or ``../`` sequence escaped it.

Both call sites now route through ``_safe_download_filepath``, which reduces
the name to a bare basename and re-checks containment. These tests exercise
that helper directly (offline, no network/browser).
"""

import os
import tempfile

import pytest

from crawl4ai.async_crawler_strategy import _safe_download_filepath, _nofollow_opener

pytestmark = pytest.mark.posture


@pytest.fixture
def downloads_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestDownloadPathConfinement:
    def test_plain_filename_kept(self, downloads_dir):
        p = _safe_download_filepath(downloads_dir, "report.pdf")
        assert p == os.path.join(os.path.realpath(downloads_dir), "report.pdf")

    @pytest.mark.parametrize(
        "evil",
        [
            "/etc/cron.d/evil",
            "/tmp/pwned_absolute.sh",
            "../../../.bashrc",
            "../../.ssh/authorized_keys",
            "../../../../etc/passwd",
            "..",
            ".",
            "",
            "foo/../../bar",
        ],
    )
    def test_escape_attempts_confined(self, downloads_dir, evil):
        """No input may produce a path outside the downloads root."""
        root = os.path.realpath(downloads_dir)
        p = _safe_download_filepath(downloads_dir, evil)
        assert os.path.commonpath([root, p]) == root
        # The resolved file sits directly inside the root (basename only).
        assert os.path.dirname(p) == root

    def test_absolute_path_does_not_win(self, downloads_dir):
        p = _safe_download_filepath(downloads_dir, "/etc/cron.d/evil")
        assert not p.startswith("/etc/")
        assert p.startswith(os.path.realpath(downloads_dir))

    def test_symlink_escape_rejected(self, downloads_dir):
        """If the basename is an existing symlink in the root pointing out,
        realpath resolves outside the root and the write must be rejected."""
        root = os.path.realpath(downloads_dir)
        outside_dir = tempfile.mkdtemp()
        outside_file = os.path.join(outside_dir, "target")
        link = os.path.join(root, "evil")
        os.symlink(outside_file, link)
        # filename "evil" -> root/evil is a symlink to outside -> rejected.
        with pytest.raises(ValueError):
            _safe_download_filepath(downloads_dir, "evil")


class TestNoFollowOpener:
    """The write must refuse to follow a symlink swapped in after path
    confinement (the TOCTOU window between realpath-check and open)."""

    def test_open_refuses_symlink_target(self, downloads_dir):
        import os
        outside = tempfile.mkdtemp()
        outside_file = os.path.join(outside, "secret")
        with open(outside_file, "w") as f:
            f.write("original")
        # Attacker swaps the confined target for a symlink pointing outside.
        target = os.path.join(downloads_dir, "report.pdf")
        os.symlink(outside_file, target)
        with pytest.raises(OSError):  # ELOOP from O_NOFOLLOW
            with open(target, "wb", opener=_nofollow_opener) as f:
                f.write(b"pwned")
        # The outside file was not overwritten through the symlink.
        with open(outside_file) as f:
            assert f.read() == "original"

    def test_open_writes_normal_file(self, downloads_dir):
        import os
        target = os.path.join(downloads_dir, "ok.bin")
        with open(target, "wb", opener=_nofollow_opener) as f:
            f.write(b"data")
        with open(target, "rb") as f:
            assert f.read() == b"data"
