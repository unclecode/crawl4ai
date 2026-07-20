#!/usr/bin/env bash
# entrypoint.sh - resolve the socket-level egress/auth posture before supervisord.
#
# This is the authoritative socket-level guard (gunicorn binds the socket, not
# Python). It must agree with the in-process _resolve_auth() check in server.py.
set -euo pipefail

# --- Redis password: prefer a mounted secret, else an existing env var. ------
if [[ -z "${REDIS_PASSWORD:-}" && -f /run/secrets/redis_password ]]; then
    REDIS_PASSWORD="$(cat /run/secrets/redis_password)"
fi
if [[ -z "${REDIS_PASSWORD:-}" ]]; then
    # Generate an ephemeral in-container password so redis is never open even
    # if the operator forgot to mount one. (Loopback + requirepass.)
    REDIS_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    echo "entrypoint: no REDIS_PASSWORD provided; generated an ephemeral one." >&2
fi
export REDIS_PASSWORD

# --- API token: prefer a mounted secret, else an existing env var. -----------
if [[ -z "${CRAWL4AI_API_TOKEN:-}" && -f /run/secrets/api_token ]]; then
    export CRAWL4AI_API_TOKEN="$(cat /run/secrets/api_token)"
fi

# --- Bind resolution: loopback unless a credential is present. ---------------
DEFAULT_PORT="11235"
resolve_port() {
    local port="${CRAWL4AI_PORT:-$DEFAULT_PORT}"
    if [[ ! "$port" =~ ^[0-9]+$ ]]; then
        if [[ "$port" == tcp://* ]]; then
            echo "entrypoint: ignoring non-numeric CRAWL4AI_PORT='${port}' " \
                 "(looks like a Kubernetes service link); using ${DEFAULT_PORT}." >&2
            port="$DEFAULT_PORT"
        else
            echo "entrypoint: CRAWL4AI_PORT must be numeric, got '${port}'." >&2
            exit 1
        fi
    fi
    printf '%s\n' "$port"
}

if [[ -n "${CRAWL4AI_API_TOKEN:-}" || "${CRAWL4AI_JWT_ENABLED:-false}" == "true" ]]; then
    # A credential is configured -> the operator may expose all interfaces.
    if [[ -z "${GUNICORN_BIND:-}" ]]; then
        PORT="$(resolve_port)"
        GUNICORN_BIND="[::]:${PORT}"
    fi
else
    # No credential -> refuse to expose; serve loopback only.
    PORT="$(resolve_port)"
    GUNICORN_BIND="127.0.0.1:${PORT}"
    echo "entrypoint: no CRAWL4AI_API_TOKEN set; binding loopback only (${GUNICORN_BIND})." >&2
fi
export GUNICORN_BIND

exec supervisord -c supervisord.conf --pidfile /tmp/supervisord.pid
