"""
Authentication primitives for the Crawl4AI Docker server.

This module is PyJWT-only. The previous dual dependency on the GehirnInc `jwt`
package *and* `PyJWT` (both install a top-level `jwt` module) meant the meaning
of `import jwt` depended on install order, and the security tests could exercise
a different code path than production. We now depend on PyJWT exclusively.

Auth is decided in one place: the AuthGateMiddleware (auth_gate.py), which runs
as the outermost ASGI layer and fails closed. The helpers here are what that
gate (and the /token endpoint) call:

  * create_access_token  - mint an HS256 JWT carrying a scope claim
  * decode_token         - verify an HS256 JWT (algorithms passed as a LIST,
                           which kills the substring-match bug and rejects
                           alg:none / other algorithms)
  * constant_time_eq     - timing-safe comparison for the static API token
  * resolve_secret_key   - fail fast when a real secret is required but missing
"""

import hmac
import logging
import os
import secrets as _secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import jwt
from fastapi import HTTPException, Request
from pydantic import BaseModel, EmailStr

ACCESS_TOKEN_EXPIRE_MINUTES = 60
ALGORITHM = "HS256"
_ALGORITHMS = [ALGORITHM]  # a LIST on purpose: no substring matching, no alg:none

_WEAK_SECRETS = {"mysecret", "secret", "password", "changeme", "test", "12345678"}
_MIN_SECRET_LEN = 32

_log = logging.getLogger("crawl4ai.security")


def resolve_secret_key(*, required: bool) -> str:
    """Resolve and validate SECRET_KEY.

    required=True  -> fail fast (RuntimeError) if unset/weak/short. Used when a
                      real auth deployment is in effect; an ephemeral key would
                      silently invalidate every issued token on restart.
    required=False -> auto-generate an ephemeral key (and warn) when unset, so
                      loopback/dev still works. A set-but-weak key still fails.
    """
    key = os.environ.get("SECRET_KEY", "")
    if key:
        if key.lower() in _WEAK_SECRETS:
            raise RuntimeError(
                "FATAL: SECRET_KEY is a known weak value. Generate a strong one: "
                'python3 -c "import secrets; print(secrets.token_hex(32))"'
            )
        if len(key) < _MIN_SECRET_LEN:
            raise RuntimeError(
                f"FATAL: SECRET_KEY must be at least {_MIN_SECRET_LEN} characters. "
                'Generate one: python3 -c "import secrets; print(secrets.token_hex(32))"'
            )
        return key

    if required:
        raise RuntimeError(
            "FATAL: authentication is enabled but SECRET_KEY is not set. "
            'Set it: SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")'
        )

    generated = _secrets.token_hex(32)
    _log.warning(
        "No SECRET_KEY set. Auto-generated an ephemeral key (changes on restart, "
        "invalidating issued tokens). Set SECRET_KEY for any real deployment."
    )
    return generated


# Module-level key, resolved leniently at import. The server's startup
# _resolve_auth() performs the fail-fast check when a real deployment is
# detected (credential set and/or non-loopback bind).
SECRET_KEY = resolve_secret_key(required=False)


def create_access_token(
    data: dict,
    *,
    scope: str = "data",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Mint an HS256 JWT. `scope` is "data" (normal) or "admin"."""
    to_encode = dict(data)
    to_encode["scope"] = scope
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict:
    """Verify an HS256 JWT and return its claims.

    Raises jwt.InvalidTokenError (incl. ExpiredSignatureError) on any failure.
    `algorithms` is a list, so alg:none and every non-HS256 algorithm are
    rejected outright.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=_ALGORITHMS)


def constant_time_eq(a: str, b: str) -> bool:
    """Timing-safe string comparison for the static API token."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def get_principal(request: Request) -> Optional[Dict]:
    """The principal the AuthGateMiddleware already validated (or None)."""
    return getattr(request.state, "principal", None)


def get_token_dependency(config: Dict):
    """Backward-compatible dependency factory.

    Auth enforcement now lives in the AuthGateMiddleware (the outermost ASGI
    layer); by the time any route dependency runs, the request was already
    authenticated by the gate or rejected with 401. This dependency simply
    surfaces the validated principal to handlers that declared `_td`.
    """

    def _principal(request: Request) -> Optional[Dict]:
        return get_principal(request)

    return _principal


def require_admin(request: Request) -> Dict:
    """Dependency: require an admin-scope principal (destructive actions)."""
    principal = get_principal(request)
    if not principal or principal.get("scope") != "admin":
        raise HTTPException(status_code=403, detail="Admin scope required")
    return principal


class TokenRequest(BaseModel):
    email: EmailStr
    api_token: Optional[str] = None
