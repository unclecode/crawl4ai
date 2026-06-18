"""
AuthGateMiddleware - the single, fail-closed authentication boundary.

The previous design decided auth in a per-route FastAPI dependency that, when
`jwt_enabled` was false (the default), returned `lambda: None` - so every
`Depends(token_dep)` was decorative and the whole API was open. Static mounts,
the MCP transports and the Prometheus endpoint were never covered at all.

This middleware moves auth to the outermost ASGI layer so it covers EVERY
route, mount and sub-app (HTTP + WebSocket) uniformly, and it fails closed: a
request without a valid credential is rejected before it reaches any handler.

Accepted credentials:
  * the static operator API token (constant-time compared) -> admin scope, or
  * a valid HS256 JWT minted by this server -> the token's own scope claim.

Public paths (the health check and the token-issuing endpoint) pass through.
On failure: HTTP 401 JSON, or WebSocket close 4401.
On success: the validated principal is attached at scope["state"]["principal"]
(readable downstream as request.state.principal) for scope/ownership checks.
"""

from __future__ import annotations

import json
from typing import Callable, Dict, Iterable, Optional
from urllib.parse import parse_qs

import jwt

from auth import constant_time_eq, decode_token


class AuthGateMiddleware:
    def __init__(
        self,
        app,
        *,
        token_provider: Callable[[], str],
        public_paths: Iterable[str] = (),
    ):
        self.app = app
        self._token_provider = token_provider
        self.public_paths = set(public_paths)

    # ─────────────────────────── ASGI entry ───────────────────────────
    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        if scope.get("path", "") in self.public_paths:
            await self.app(scope, receive, send)
            return

        principal = self._authenticate(scope)
        if principal is None:
            await self._reject(scope, receive, send)
            return

        # Expose the principal to downstream handlers/dependencies.
        state = scope.setdefault("state", {})
        state["principal"] = principal
        await self.app(scope, receive, send)

    # ──────────────────────────── helpers ─────────────────────────────
    def _authenticate(self, scope) -> Optional[Dict]:
        token = self._extract_token(scope)
        if not token:
            return None

        # 1) static operator token -> admin scope
        static_token = self._token_provider() or ""
        if static_token and constant_time_eq(token, static_token):
            return {"sub": "operator", "scope": "admin", "via": "api_token"}

        # 2) HS256 JWT minted by this server
        try:
            claims = decode_token(token)
        except jwt.InvalidTokenError:
            return None
        claims.setdefault("scope", "data")
        return claims

    @staticmethod
    def _extract_token(scope) -> Optional[str]:
        # Authorization: Bearer <token>
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                raw = value.decode("latin-1")
                if raw[:7].lower() == "bearer ":
                    return raw[7:].strip()
                return None
        # WebSocket clients that cannot set headers may pass ?token=
        if scope["type"] == "websocket":
            qs = parse_qs(scope.get("query_string", b"").decode("latin-1"))
            vals = qs.get("token")
            if vals:
                return vals[0]
        return None

    async def _reject(self, scope, receive, send):
        if scope["type"] == "websocket":
            # Close before accept; 4401 = application "unauthorized".
            await send({"type": "websocket.close", "code": 4401})
            return
        body = json.dumps({"detail": "Authentication required"}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"www-authenticate", b"Bearer"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
