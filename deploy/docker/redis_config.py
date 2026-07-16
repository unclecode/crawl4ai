"""Redis URL helpers for the Docker API server.

The Docker entrypoint protects the in-container Redis with a password. These
helpers keep every Redis client (the app and optional rate-limit storage) using
the same authenticated URL shape.
"""

import os
from urllib.parse import quote, urlsplit, urlunsplit


def redis_auth_from_config(config: dict) -> tuple[str, str]:
    """Return Redis ACL username/password from config and environment."""
    rc = config.get("redis", {})
    username = os.environ.get("REDIS_USERNAME", rc.get("username", "default")) or "default"
    password = os.environ.get("REDIS_PASSWORD", rc.get("password", "")) or ""
    return str(username), str(password)


def redis_auth_netloc(username: str, password: str) -> str:
    """Build a URL-safe Redis AUTH fragment for redis-py/limits clients.

    Redis 6+ HELLO AUTH requires both username and password when negotiating
    RESP3. Supplying the explicit default ACL username avoids clients issuing an
    unauthenticated HELLO against a password-protected Redis instance.
    """
    if not password:
        return ""
    return f"{quote(username, safe='')}:{quote(password, safe='')}@"


def build_redis_url(config: dict) -> str:
    """Build Redis URL from config fields and environment variables."""
    rc = config.get("redis", {})
    host = os.environ.get("REDIS_HOST", rc.get("host", "localhost"))
    port = os.environ.get("REDIS_PORT", rc.get("port", 6379))
    username, password = redis_auth_from_config(config)
    db = rc.get("db", 0)
    scheme = "rediss" if rc.get("ssl", False) else "redis"
    auth = redis_auth_netloc(username, password)
    return f"{scheme}://{auth}{host}:{port}/{db}"


def build_rate_limit_storage_uri(config: dict) -> str:
    """Return a rate-limit storage URI that can auth to protected Redis.

    Older/self-managed Docker configs may set rate_limiting.storage_uri to an
    unauthenticated Redis URL such as redis://localhost:6379. Since the Docker
    entrypoint now always protects the in-container Redis with REDIS_PASSWORD,
    SlowAPI/limits would fail before route handlers with Redis HELLO auth errors.
    If the storage URI is Redis-like and has no credentials, reuse the configured
    Redis ACL credentials. Explicit credentials and non-Redis backends are left
    unchanged.
    """
    storage_uri = config.get("rate_limiting", {}).get("storage_uri", "memory://")
    if not isinstance(storage_uri, str):
        return "memory://"
    parsed = urlsplit(storage_uri)
    if parsed.scheme not in {"redis", "rediss", "redis+sentinel"}:
        return storage_uri
    if parsed.username or parsed.password:
        return storage_uri

    username, password = redis_auth_from_config(config)
    if not password:
        return storage_uri

    auth = redis_auth_netloc(username, password)
    return urlunsplit((
        parsed.scheme,
        f"{auth}{parsed.netloc}",
        parsed.path,
        parsed.query,
        parsed.fragment,
    ))
