import dns.resolver
import logging
import yaml
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from fastapi import Request
from typing import Dict, Optional

class TaskStatus(str, Enum):
    PROCESSING = "processing"
    FAILED = "failed"
    COMPLETED = "completed"

class FilterType(str, Enum):
    RAW = "raw"
    FIT = "fit"
    BM25 = "bm25"
    LLM = "llm"

DEFAULT_CONFIG = {
    "app": {
        "title": "Crawl4AI API",
        "version": "1.0.0",
        "host": "0.0.0.0",
        "port": 11235,
        "reload": False,
        "workers": 1,
        "timeout_keep_alive": 300,
    },
    "llm": {
        "provider": "openai/gpt-4o-mini",
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": "",
        "task_ttl_seconds": 3600,
        "ssl": False,
    },
    "rate_limiting": {
        "enabled": True,
        "default_limit": "1000/minute",
        "trusted_proxies": [],
        "storage_uri": "memory://",
    },
    "security": {
        "enabled": False,
        "jwt_enabled": False,
        "api_token": "",
        "https_redirect": False,
        "trusted_hosts": ["*"],
        "headers": {
            "x_content_type_options": "nosniff",
            "x_frame_options": "DENY",
            "content_security_policy": "default-src 'self'",
            "strict_transport_security": "max-age=63072000; includeSubDomains",
        },
    },
    "crawler": {
        "base_config": {"simulate_user": True},
        "memory_threshold_percent": 95.0,
        "rate_limiter": {"enabled": True, "base_delay": [1.0, 2.0]},
        "timeouts": {"stream_init": 30.0, "batch_process": 300.0},
        "pool": {"max_pages": 40, "idle_ttl_sec": 300},
        "browser": {
            "kwargs": {"headless": True, "text_mode": True},
            "extra_args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--allow-insecure-localhost",
                "--ignore-certificate-errors",
            ],
        },
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "observability": {
        "prometheus": {"enabled": True, "endpoint": "/metrics"},
        "health_check": {"endpoint": "/health"},
    },
    "webhooks": {
        "enabled": True,
        "default_url": None,
        "data_in_payload": False,
        "retry": {
            "max_attempts": 5,
            "initial_delay_ms": 1000,
            "max_delay_ms": 32000,
            "timeout_ms": 30000,
        },
        "headers": {"User-Agent": "Crawl4AI-Webhook/1.0"},
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override values take precedence."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config() -> Dict:
    """Load and return application configuration with environment variable overrides."""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, "r") as config_file:
        user_config = yaml.safe_load(config_file) or {}

    # Deep-merge user config on top of defaults so missing keys get safe values
    config = _deep_merge(DEFAULT_CONFIG, user_config)

    for section in DEFAULT_CONFIG:
        if section not in user_config:
            logging.warning(
                f"Config section '{section}' missing from config.yml, using defaults"
            )
    
    # Override LLM provider from environment if set
    llm_provider = os.environ.get("LLM_PROVIDER")
    if llm_provider:
        config["llm"]["provider"] = llm_provider
        logging.info(f"LLM provider overridden from environment: {llm_provider}")
    
    # Also support direct API key from environment if the provider-specific key isn't set
    llm_api_key = os.environ.get("LLM_API_KEY")
    if llm_api_key and "api_key" not in config["llm"]:
        config["llm"]["api_key"] = llm_api_key
        logging.info("LLM API key loaded from LLM_API_KEY environment variable")

    # Override Redis task TTL from environment if set
    redis_task_ttl = os.environ.get("REDIS_TASK_TTL")
    if redis_task_ttl:
        try:
            config["redis"]["task_ttl_seconds"] = int(redis_task_ttl)
            logging.info(f"Redis task TTL overridden from REDIS_TASK_TTL: {redis_task_ttl}s")
        except ValueError:
            logging.warning(f"Invalid REDIS_TASK_TTL value: {redis_task_ttl}, using default")

    return config

class CRLFSafeFilter(logging.Filter):
    """Strip CR/LF/control chars from log records (log-injection / forging).

    A crawl URL or error reflected into a log line could otherwise inject
    newlines and forge additional log entries."""

    _BAD = {ord(c): None for c in "\r\n"} | {i: None for i in range(0, 32) if i != 9}

    def filter(self, record: "logging.LogRecord") -> bool:
        try:
            msg = record.getMessage()
            cleaned = msg.translate(self._BAD)
            if cleaned != msg:
                record.msg = cleaned
                record.args = ()
        except Exception:
            pass
        return True


def setup_logging(config: Dict) -> None:
    """Configure application logging with CRLF-safe records."""
    logging.basicConfig(
        level=config["logging"]["level"],
        format=config["logging"]["format"]
    )
    crlf = CRLFSafeFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(crlf)

def get_base_url(request: Request) -> str:
    """Get base URL including scheme and host."""
    return f"{request.url.scheme}://{request.url.netloc}"

def is_task_id(value: str) -> bool:
    """Check if the value matches task ID pattern."""
    return value.startswith("llm_") and "_" in value

def datetime_handler(obj: any) -> Optional[str]:
    """Handle datetime serialization for JSON."""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def should_cleanup_task(created_at: str, ttl_seconds: int = 3600) -> bool:
    """Check if task should be cleaned up based on creation time."""
    created = datetime.fromisoformat(created_at)
    return (datetime.now() - created).total_seconds() > ttl_seconds

def decode_redis_hash(hash_data: Dict[bytes, bytes]) -> Dict[str, str]:
    """Decode Redis hash data from bytes to strings."""
    return {k.decode('utf-8'): v.decode('utf-8') for k, v in hash_data.items()}


def get_redis_task_ttl(config: Dict) -> int:
    """Get Redis task TTL in seconds from config.

    Args:
        config: The application configuration dictionary

    Returns:
        TTL in seconds (default 3600). Returns 0 if TTL is disabled.
    """
    return config.get("redis", {}).get("task_ttl_seconds", 3600)


def get_llm_api_key(config: Dict, provider: Optional[str] = None) -> Optional[str]:
    """Get the appropriate API key based on the LLM provider.
    
    Args:
        config: The application configuration dictionary
        provider: Optional provider override (e.g., "openai/gpt-4")
    
    Returns:
        The API key if directly configured, otherwise None to let litellm handle it
    """
    # Check if direct API key is configured (for backward compatibility)
    if "api_key" in config["llm"]:
        return config["llm"]["api_key"]
    
    # Return None - litellm will automatically find the right environment variable
    return None


def validate_llm_provider(config: Dict, provider: Optional[str] = None) -> tuple[bool, str]:
    """Validate that the LLM provider has an associated API key.
    
    Args:
        config: The application configuration dictionary
        provider: Optional provider override (e.g., "openai/gpt-4")
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # If a direct API key is configured, validation passes
    if "api_key" in config["llm"]:
        return True, ""
    
    # Otherwise, trust that litellm will find the appropriate environment variable
    # We can't easily validate this without reimplementing litellm's logic
    return True, ""


def get_llm_temperature(config: Dict, provider: Optional[str] = None) -> Optional[float]:
    """Get temperature setting based on the LLM provider.
    
    Priority order:
    1. Provider-specific environment variable (e.g., OPENAI_TEMPERATURE)
    2. Global LLM_TEMPERATURE environment variable
    3. None (to use litellm/provider defaults)
    
    Args:
        config: The application configuration dictionary
        provider: Optional provider override (e.g., "openai/gpt-4")
    
    Returns:
        The temperature setting if configured, otherwise None
    """
    # Check provider-specific temperature first
    if provider:
        provider_name = provider.split('/')[0].upper()
        provider_temp = os.environ.get(f"{provider_name}_TEMPERATURE")
        if provider_temp:
            try:
                return float(provider_temp)
            except ValueError:
                logging.warning(f"Invalid temperature value for {provider_name}: {provider_temp}")
    
    # Check global LLM_TEMPERATURE
    global_temp = os.environ.get("LLM_TEMPERATURE")
    if global_temp:
        try:
            return float(global_temp)
        except ValueError:
            logging.warning(f"Invalid global temperature value: {global_temp}")
    
    # Return None to use litellm/provider defaults
    return None


def get_llm_base_url(config: Dict, provider: Optional[str] = None) -> Optional[str]:
    """Get base URL setting based on the LLM provider.
    
    Priority order:
    1. Provider-specific environment variable (e.g., OPENAI_BASE_URL)
    2. Global LLM_BASE_URL environment variable
    3. None (to use default endpoints)
    
    Args:
        config: The application configuration dictionary
        provider: Optional provider override (e.g., "openai/gpt-4")
    
    Returns:
        The base URL if configured, otherwise None
    """
    # Check provider-specific base URL first
    if provider:
        provider_name = provider.split('/')[0].upper()
        provider_url = os.environ.get(f"{provider_name}_BASE_URL")
        if provider_url:
            return provider_url
    
    # Check global LLM_BASE_URL
    return os.environ.get("LLM_BASE_URL")


# ── Security utilities ──────────────────────────────────────

ALLOWED_OUTPUT_DIR = os.environ.get("CRAWL4AI_OUTPUT_DIR", "/tmp/crawl4ai-outputs")


def validate_output_path(user_path: str) -> str:
    """Resolve and restrict output_path to ALLOWED_OUTPUT_DIR.

    Hardened against the symlink/TOCTOU bypass: in addition to the string
    containment check, the REAL path (symlinks resolved) of the target and its
    parent must also stay inside the allowed dir, so a symlink planted inside
    the dir cannot redirect the write elsewhere. The final write must also use
    O_NOFOLLOW (see write_output_file)."""
    from fastapi import HTTPException
    safe_path = os.path.normpath(user_path).lstrip(os.sep)
    abs_path = os.path.abspath(os.path.join(ALLOWED_OUTPUT_DIR, safe_path))
    abs_allowed = os.path.abspath(ALLOWED_OUTPUT_DIR) + os.sep
    # Resolve symlinks on the parent dir (the file itself may not exist yet) and
    # re-check containment; this defeats a symlinked path component. The trailing
    # os.sep on both sides also rejects sibling-prefix names ("...-evil").
    real_parent = os.path.realpath(os.path.dirname(abs_path))
    real_path = os.path.join(real_parent, os.path.basename(abs_path))
    string_ok = abs_path.startswith(abs_allowed)
    real_ok = (real_path + os.sep).startswith(abs_allowed)
    if not (string_ok and real_ok):
        raise HTTPException(
            status_code=400,
            detail=f"output_path must resolve within {ALLOWED_OUTPUT_DIR}",
        )
    return real_path


def write_output_file(abs_path: str, data: bytes) -> None:
    """Write bytes to a validated output path without following a symlink at the
    final component (defends the symlink-TOCTOU write)."""
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(abs_path, flags, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)


import ipaddress
import socket
from urllib.parse import urlparse

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_BLOCKED_HOSTNAMES = {
    "localhost", "metadata.google.internal", "metadata",
    "kubernetes.default", "kubernetes.default.svc",
}


ALLOW_INTERNAL_URLS = os.environ.get("CRAWL4AI_ALLOW_INTERNAL_URLS", "false").lower() == "true"


def validate_url_destination(url: str) -> None:
    """Block crawl URLs targeting internal/private networks (SSRF protection).
    Skipped when CRAWL4AI_ALLOW_INTERNAL_URLS=true.
    Skipped for raw: URLs (inline HTML, no network fetch)."""
    if ALLOW_INTERNAL_URLS:
        return
    if str(url).startswith(("raw:", "raw://")):
        return
    try:
        validate_webhook_url(url)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"URL blocked (SSRF protection): {e}")


_NAT64_NETWORK = ipaddress.ip_network("64:ff9b::/96")
_6TO4_NETWORK = ipaddress.ip_network("2002::/16")
_V4COMPAT_NETWORK = ipaddress.ip_network("::/96")


def _expand_ip_candidates(ip):
    """Return [ip] plus any IPv4 form embedded inside the IPv6 address.
    SSRF guards must check the unwrapped form because ::ffff:169.254.169.254,
    NAT64 64:ff9b::a9fe:a9fe, and 6to4 2002:a9fe:a9fe:: all route to an internal
    IPv4 that would not match an IPv6-only check."""
    candidates = [ip]
    if isinstance(ip, ipaddress.IPv6Address):
        mapped = ip.ipv4_mapped
        if mapped is not None:
            candidates.append(mapped)
        elif ip in _NAT64_NETWORK or ip in _V4COMPAT_NETWORK:
            candidates.append(ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF))
        elif ip in _6TO4_NETWORK:
            candidates.append(ipaddress.IPv4Address((int(ip) >> 80) & 0xFFFFFFFF))
    return candidates


def validate_webhook_url(url: str) -> None:
    """Reject webhook/crawl URLs targeting non-global (internal/private/reserved)
    networks (SSRF protection).

    One rule: reject any resolved IP where not ip.is_global, evaluated on every
    embedded IPv4 transition form (v4-mapped, NAT64, 6to4, v4-compat). This
    closes the gaps in the old explicit blocklist (the IPv6 unspecified ::,
    NAT64, 6to4). The error is opaque - it never echoes the resolved internal
    IP (which would be a DNS/oracle leak)."""
    parsed = urlparse(str(url))
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a valid hostname")
    hostname_lower = hostname.lower()
    if hostname_lower in _BLOCKED_HOSTNAMES or hostname_lower.startswith("host.docker.internal"):
        raise ValueError("URL host is blocked")
    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError("Cannot resolve URL host")
    for _, _, _, _, sockaddr in resolved:
        ip = ipaddress.ip_address(sockaddr[0])
        for candidate in _expand_ip_candidates(ip):
            if not candidate.is_global:
                # opaque: do not leak the resolved internal IP
                raise ValueError("URL resolves to a blocked address")


# Chromium launch flags that can redirect/route egress or remap DNS, enabling
# the same SSRF as a proxy field. Stripped from caller-supplied extra_args.
_DANGEROUS_BROWSER_ARGS = (
    "--proxy-server", "--proxy-pac-url", "--proxy-bypass-list",
    "--host-resolver-rules",
)


def validate_proxy_destination(server: str) -> None:
    """Reject a proxy server whose host is non-global (SSRF via proxy_config).

    The crawl-target SSRF check is applied to the URL being fetched, but a proxy
    address is also attacker-controllable and is handed to Chromium's
    --proxy-server. Validate it with the same not-is_global rule. Honors
    CRAWL4AI_ALLOW_INTERNAL_URLS. Raises ValueError (opaque) on a blocked host."""
    if ALLOW_INTERNAL_URLS or not server:
        return
    s = str(server)
    # proxy strings may be "scheme://host:port" or bare "host:port"
    parsed = urlparse(s if "://" in s else "//" + s)
    host = parsed.hostname
    if not host:
        raise ValueError("Invalid proxy server")
    # Reuse the destination check (resolve + not-is_global on transition forms).
    validate_webhook_url(f"http://{host}")


def scrub_browser_extra_args(extra_args):
    """Drop egress/DNS-redirecting Chromium flags from caller-supplied args.

    The supported way to set a proxy is proxy_config (validated). Raw
    --proxy-*/--host-resolver-rules flags bypass that validation and re-enable
    the SSRF, so they are removed. Returns the filtered list."""
    if not extra_args:
        return extra_args
    return [
        a for a in extra_args
        if not any(str(a).startswith(bad) for bad in _DANGEROUS_BROWSER_ARGS)
    ]


def verify_email_domain(email: str) -> bool:
    try:
        domain = email.split('@')[1]
        # Try to resolve MX records for the domain.
        records = dns.resolver.resolve(domain, 'MX')
        return True if records else False
    except Exception as e:
        return False

def get_container_memory_percent() -> float:
    """Get actual container memory usage vs limit (cgroup v1/v2 aware)."""
    try:
        # Try cgroup v2 first
        usage_path = Path("/sys/fs/cgroup/memory.current")
        limit_path = Path("/sys/fs/cgroup/memory.max")
        if not usage_path.exists():
            # Fall back to cgroup v1
            usage_path = Path("/sys/fs/cgroup/memory/memory.usage_in_bytes")
            limit_path = Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")

        usage = int(usage_path.read_text())
        limit = int(limit_path.read_text())

        # Handle unlimited (v2: "max", v1: > 1e18)
        if limit > 1e18:
            import psutil
            limit = psutil.virtual_memory().total

        return (usage / limit) * 100
    except:
        # Non-container or unsupported: fallback to host
        import psutil
        return psutil.virtual_memory().percent