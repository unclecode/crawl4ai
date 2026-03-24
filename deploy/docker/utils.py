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
                "--disable-web-security",
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

def setup_logging(config: Dict) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=config["logging"]["level"],
        format=config["logging"]["format"]
    )

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