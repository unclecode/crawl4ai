"""
artifacts.py - sandboxed, opaque-ID artifact store.

The screenshot/PDF endpoints used to accept a caller-supplied `output_path` and
write to it. `validate_output_path` was string-only (no realpath / O_NOFOLLOW),
so a symlink or a sibling-prefix name (".../outputs-evil") bypassed it and gave
an arbitrary write -> root RCE (e.g. /etc/cron.d) since /app was writable.

The fix: callers never name a path. The server owns the directory, the names,
and the bytes. Each artifact gets a server-generated opaque id; writes are
O_EXCL|O_NOFOLLOW 0600 into a 0700 dir off /tmp, size-capped and dir-quota'd;
retrieval validates a 32-hex id, lstat()s a non-symlink regular file, and
enforces a TTL. A janitor reaps expired/over-quota files.
"""

from __future__ import annotations

import os
import re
import time
import uuid
from typing import Dict, Tuple

ARTIFACT_DIR = os.environ.get("CRAWL4AI_ARTIFACT_DIR", "/var/lib/crawl4ai/outputs")
MAX_ARTIFACT_BYTES = int(os.environ.get("CRAWL4AI_MAX_ARTIFACT_BYTES", str(50 * 1024 * 1024)))
ARTIFACT_QUOTA_BYTES = int(os.environ.get("CRAWL4AI_ARTIFACT_QUOTA_BYTES", str(2 * 1024 * 1024 * 1024)))
ARTIFACT_TTL_SECONDS = int(os.environ.get("CRAWL4AI_ARTIFACT_TTL_SECONDS", "3600"))

_HEX32 = re.compile(r"^[0-9a-f]{32}$")
_KIND = {
    "png": (".png", "image/png"),
    "pdf": (".pdf", "application/pdf"),
}


class ArtifactError(Exception):
    pass


class ArtifactTooLarge(ArtifactError):
    pass


class QuotaExceeded(ArtifactError):
    pass


class ArtifactNotFound(ArtifactError):
    pass


def init_store() -> None:
    """Create the artifact dir 0700 (idempotent)."""
    os.makedirs(ARTIFACT_DIR, mode=0o700, exist_ok=True)
    try:
        os.chmod(ARTIFACT_DIR, 0o700)
    except OSError:
        pass


def _dir_size() -> int:
    total = 0
    try:
        with os.scandir(ARTIFACT_DIR) as it:
            for entry in it:
                try:
                    st = entry.stat(follow_symlinks=False)
                    if os.path.stat.S_ISREG(st.st_mode):
                        total += st.st_size
                except OSError:
                    continue
    except FileNotFoundError:
        return 0
    return total


def write_artifact(kind: str, data: bytes) -> Dict:
    """Write bytes under a server-generated opaque id. Returns metadata."""
    ext, mime = _KIND.get(kind, (".bin", "application/octet-stream"))
    if len(data) > MAX_ARTIFACT_BYTES:
        raise ArtifactTooLarge(f"artifact exceeds {MAX_ARTIFACT_BYTES} bytes")
    init_store()
    if _dir_size() + len(data) > ARTIFACT_QUOTA_BYTES:
        raise QuotaExceeded("artifact storage quota exceeded")

    artifact_id = uuid.uuid4().hex  # 32 hex chars, unguessable
    path = os.path.join(ARTIFACT_DIR, artifact_id + ext)
    # O_EXCL: never follow/overwrite an existing entry; O_NOFOLLOW: refuse a
    # symlink at the final component. Server-chosen name => no traversal.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return {"artifact_id": artifact_id, "mime": mime, "size": len(data)}


def resolve_artifact(artifact_id: str) -> Tuple[str, str]:
    """Map an opaque id to (path, mime), enforcing hex-id, no-symlink, TTL.

    Raises ArtifactNotFound for an invalid id, a non-regular/symlink file, a
    missing file, or an expired artifact (so existence is never revealed).
    """
    if not isinstance(artifact_id, str) or not _HEX32.match(artifact_id):
        raise ArtifactNotFound()
    for ext, mime in _KIND.values():
        path = os.path.join(ARTIFACT_DIR, artifact_id + ext)
        try:
            st = os.lstat(path)  # do NOT follow symlinks
        except FileNotFoundError:
            continue
        if not os.path.stat.S_ISREG(st.st_mode):
            raise ArtifactNotFound()  # symlink / special file
        if time.time() - st.st_mtime > ARTIFACT_TTL_SECONDS:
            try:
                os.unlink(path)
            except OSError:
                pass
            raise ArtifactNotFound()
        return path, mime
    raise ArtifactNotFound()


def janitor() -> int:
    """Reap expired artifacts; if still over quota, reap oldest first."""
    init_store()
    now = time.time()
    reaped = 0
    entries = []
    try:
        with os.scandir(ARTIFACT_DIR) as it:
            for entry in it:
                try:
                    st = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                if not os.path.stat.S_ISREG(st.st_mode):
                    # remove anything that is not a regular file (e.g. a symlink)
                    try:
                        os.unlink(entry.path)
                        reaped += 1
                    except OSError:
                        pass
                    continue
                if now - st.st_mtime > ARTIFACT_TTL_SECONDS:
                    try:
                        os.unlink(entry.path)
                        reaped += 1
                    except OSError:
                        pass
                    continue
                entries.append((st.st_mtime, st.st_size, entry.path))
    except FileNotFoundError:
        return reaped

    total = sum(sz for _, sz, _ in entries)
    if total > ARTIFACT_QUOTA_BYTES:
        for _mtime, sz, path in sorted(entries):  # oldest first
            if total <= ARTIFACT_QUOTA_BYTES:
                break
            try:
                os.unlink(path)
                total -= sz
                reaped += 1
            except OSError:
                pass
    return reaped
