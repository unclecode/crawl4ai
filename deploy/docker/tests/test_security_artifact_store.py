"""
R4 artifact-store behavioral tests: the server owns the directory, names and
bytes. Writes are O_EXCL|O_NOFOLLOW 0600; retrieval requires a 32-hex id,
refuses symlinks/non-regular files, and enforces a TTL.
"""

import os
import time

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Point the artifact store at an isolated temp dir and reload it."""
    monkeypatch.setenv("CRAWL4AI_ARTIFACT_DIR", str(tmp_path / "art"))
    monkeypatch.setenv("CRAWL4AI_MAX_ARTIFACT_BYTES", "1024")
    monkeypatch.setenv("CRAWL4AI_ARTIFACT_QUOTA_BYTES", "4096")
    monkeypatch.setenv("CRAWL4AI_ARTIFACT_TTL_SECONDS", "3600")
    import importlib
    import artifacts
    importlib.reload(artifacts)
    artifacts.init_store()
    yield artifacts
    importlib.reload(artifacts)  # restore defaults for other tests


pytestmark = pytest.mark.posture


class TestWrite:
    def test_write_returns_hex_id_and_meta(self, store):
        meta = store.write_artifact("png", b"\x89PNG data")
        assert len(meta["artifact_id"]) == 32 and all(c in "0123456789abcdef" for c in meta["artifact_id"])
        assert meta["mime"] == "image/png" and meta["size"] == len(b"\x89PNG data")

    def test_dir_is_0700_and_file_0600(self, store):
        meta = store.write_artifact("pdf", b"%PDF-1.4")
        assert oct(os.stat(store.ARTIFACT_DIR).st_mode)[-3:] == "700"
        path, _ = store.resolve_artifact(meta["artifact_id"])
        assert oct(os.stat(path).st_mode)[-3:] == "600"

    def test_oversize_rejected(self, store):
        with pytest.raises(store.ArtifactTooLarge):
            store.write_artifact("png", b"x" * 2048)  # cap is 1024

    def test_quota_enforced(self, store):
        for _ in range(4):
            store.write_artifact("png", b"x" * 1000)
        with pytest.raises(store.QuotaExceeded):
            store.write_artifact("png", b"x" * 1000)  # would exceed 4096


class TestResolve:
    def test_roundtrip(self, store):
        meta = store.write_artifact("png", b"hello")
        path, mime = store.resolve_artifact(meta["artifact_id"])
        assert mime == "image/png"
        with open(path, "rb") as f:
            assert f.read() == b"hello"

    @pytest.mark.parametrize("bad", ["../etc/passwd", "..", "g" * 32, "abc", "/etc/passwd", "a" * 31])
    def test_non_hex_or_traversal_404(self, store, bad):
        with pytest.raises(store.ArtifactNotFound):
            store.resolve_artifact(bad)

    def test_symlink_not_followed(self, store):
        # Plant a symlink named like a valid artifact pointing at a secret.
        secret = os.path.join(store.ARTIFACT_DIR, "secret.txt")
        with open(secret, "wb") as f:
            f.write(b"TOPSECRET")
        fake_id = "a" * 32
        link = os.path.join(store.ARTIFACT_DIR, fake_id + ".png")
        os.symlink(secret, link)
        with pytest.raises(store.ArtifactNotFound):
            store.resolve_artifact(fake_id)  # lstat sees a symlink -> refuse

    def test_ttl_expired_404_and_reaped(self, store):
        meta = store.write_artifact("png", b"old")
        path, _ = store.resolve_artifact(meta["artifact_id"])
        old = time.time() - 7200  # 2h ago, TTL is 1h
        os.utime(path, (old, old))
        with pytest.raises(store.ArtifactNotFound):
            store.resolve_artifact(meta["artifact_id"])
        assert not os.path.exists(path)  # resolve reaped it


class TestWriteIsExclusiveAndNoFollow:
    def test_write_uses_oexcl_nofollow(self, store):
        import inspect
        src = inspect.getsource(store.write_artifact)
        assert "O_EXCL" in src and "O_NOFOLLOW" in src


class TestJanitor:
    def test_janitor_removes_symlinks_and_expired(self, store):
        meta = store.write_artifact("png", b"keep")
        # expired regular file
        old_meta = store.write_artifact("pdf", b"old")
        op, _ = store.resolve_artifact(old_meta["artifact_id"])
        past = time.time() - 7200
        os.utime(op, (past, past))
        # a planted symlink
        os.symlink("/etc/passwd", os.path.join(store.ARTIFACT_DIR, "deadbeef" * 4 + ".png"))
        reaped = store.janitor()
        assert reaped >= 2
        # the fresh one survives
        store.resolve_artifact(meta["artifact_id"])
