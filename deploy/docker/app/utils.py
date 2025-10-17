import dns.resolver
import logging
import yaml
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from fastapi import Request, HTTPException
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

def load_config() -> Dict:
    """Load and return application configuration with environment variable overrides."""
    config_path = Path(__file__).parent.parent / "config.yml"
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
    
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


def get_llm_api_key(config: Dict, provider: Optional[str] = None) -> str:
    """Get the appropriate API key based on the LLM provider.
    
    Args:
        config: The application configuration dictionary
        provider: Optional provider override (e.g., "openai/gpt-4")
    
    Returns:
        The API key for the provider, or empty string if not found
    """
        
    # Use provided provider or fall back to config
    if not provider:
        provider = config["llm"]["provider"]
    
    # Check if direct API key is configured
    if "api_key" in config["llm"]:
        return config["llm"]["api_key"]
    
    # Fall back to the configured api_key_env if no match
    return os.environ.get(config["llm"].get("api_key_env", ""), "")


def validate_llm_provider(config: Dict, provider: Optional[str] = None) -> tuple[bool, str]:
    """Validate that the LLM provider has an associated API key.
    
    Args:
        config: The application configuration dictionary
        provider: Optional provider override (e.g., "openai/gpt-4")
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Use provided provider or fall back to config
    if not provider:
        provider = config["llm"]["provider"]
    
    # Get the API key for this provider
    api_key = get_llm_api_key(config, provider)
    
    if not api_key:
        return False, f"No API key found for provider '{provider}'. Please set the appropriate environment variable."
    
    return True, ""


def verify_email_domain(email: str) -> bool:
    try:
        domain = email.split('@')[1]
        # Try to resolve MX records for the domain.
        records = dns.resolver.resolve(domain, 'MX')
        return True if records else False
    except Exception as e:
        return False

def _ensure_within_base_dir(path: str, base_dir: str) -> None:
    """
    Ensure path is within base directory using new error handling system.

    Args:
        path: Path to validate
        base_dir: Base directory that path must be within

    Raises:
        HTTPException: If path is outside base directory
    """
    from core.error_context import ErrorContext

    base_dir_real = os.path.realpath(os.path.abspath(base_dir))
    path_real = os.path.realpath(os.path.abspath(path))

    if not os.path.isabs(base_dir_real):
        error_ctx = ErrorContext.security_error(
            violation_type="invalid_base_directory",
            attempted_action=f"Set base directory to: {base_dir}",
            allowed_scope="absolute directory paths only",
            message="Security restriction: base directory must be absolute."
        )
        raise error_ctx.to_http_exception(400)

    try:
        common = os.path.commonpath([base_dir_real, path_real])
    except ValueError:
        common = ""

    if common != base_dir_real:
        error_ctx = ErrorContext.security_error(
            violation_type="path_traversal",
            attempted_action=f"Access path: {path_real}",
            allowed_scope=base_dir_real,
            message=(
                f"Security restriction: output_path must be within {base_dir_real}. "
                f"Your path '{path_real}' is outside the allowed directory. "
                f"Example valid path: {base_dir_real}/myfile.json"
            )
        )
        raise error_ctx.to_http_exception(400)

