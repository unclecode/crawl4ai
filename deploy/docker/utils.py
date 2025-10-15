import dns.resolver
import logging
import yaml
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from fastapi import Request
from typing import Dict, Optional, Any

# Import dispatchers from crawl4ai
from crawl4ai.async_dispatcher import (
    BaseDispatcher,
    MemoryAdaptiveDispatcher,
    SemaphoreDispatcher,
)

# Import chunking strategies from crawl4ai
from crawl4ai.chunking_strategy import (
    ChunkingStrategy,
    IdentityChunking,
    RegexChunking,
    NlpSentenceChunking,
    TopicSegmentationChunking,
    FixedLengthWordChunking,
    SlidingWindowChunking,
    OverlappingWindowChunking,
)

# Import dispatchers from crawl4ai
from crawl4ai.async_dispatcher import (
    BaseDispatcher,
    MemoryAdaptiveDispatcher,
    SemaphoreDispatcher,
)

class TaskStatus(str, Enum):
    PROCESSING = "processing"
    FAILED = "failed"
    COMPLETED = "completed"

class FilterType(str, Enum):
    RAW = "raw"
    FIT = "fit"
    BM25 = "bm25"
    LLM = "llm"


# ============================================================================
# Dispatcher Configuration and Factory
# ============================================================================

# Default dispatcher configurations (hardcoded, no env variables)
DISPATCHER_DEFAULTS = {
    "memory_adaptive": {
        "memory_threshold_percent": 70.0,
        "critical_threshold_percent": 85.0,
        "recovery_threshold_percent": 65.0,
        "check_interval": 1.0,
        "max_session_permit": 20,
        "fairness_timeout": 600.0,
        "memory_wait_timeout": None,  # Disable memory timeout for testing
    },
    "semaphore": {
        "semaphore_count": 5,
        "max_session_permit": 10,
    }
}

DEFAULT_DISPATCHER_TYPE = "memory_adaptive"


def create_dispatcher(dispatcher_type: str) -> BaseDispatcher:
    """
    Factory function to create dispatcher instances.
    
    Args:
        dispatcher_type: Type of dispatcher to create ("memory_adaptive" or "semaphore")
        
    Returns:
        BaseDispatcher instance
        
    Raises:
        ValueError: If dispatcher type is unknown
    """
    dispatcher_type = dispatcher_type.lower()
    
    if dispatcher_type == "memory_adaptive":
        config = DISPATCHER_DEFAULTS["memory_adaptive"]
        return MemoryAdaptiveDispatcher(
            memory_threshold_percent=config["memory_threshold_percent"],
            critical_threshold_percent=config["critical_threshold_percent"],
            recovery_threshold_percent=config["recovery_threshold_percent"],
            check_interval=config["check_interval"],
            max_session_permit=config["max_session_permit"],
            fairness_timeout=config["fairness_timeout"],
            memory_wait_timeout=config["memory_wait_timeout"],
        )
    elif dispatcher_type == "semaphore":
        config = DISPATCHER_DEFAULTS["semaphore"]
        return SemaphoreDispatcher(
            semaphore_count=config["semaphore_count"],
            max_session_permit=config["max_session_permit"],
        )
    else:
        raise ValueError(f"Unknown dispatcher type: {dispatcher_type}")


def get_dispatcher_config(dispatcher_type: str) -> Dict:
    """
    Get configuration for a dispatcher type.
    
    Args:
        dispatcher_type: Type of dispatcher ("memory_adaptive" or "semaphore")
        
    Returns:
        Dictionary containing dispatcher configuration
        
    Raises:
        ValueError: If dispatcher type is unknown
    """
    dispatcher_type = dispatcher_type.lower()
    if dispatcher_type not in DISPATCHER_DEFAULTS:
        raise ValueError(f"Unknown dispatcher type: {dispatcher_type}")
    return DISPATCHER_DEFAULTS[dispatcher_type].copy()


def get_available_dispatchers() -> Dict[str, Dict]:
    """
    Get information about all available dispatchers.
    
    Returns:
        Dictionary mapping dispatcher types to their metadata
    """
    return {
        "memory_adaptive": {
            "name": "Memory Adaptive Dispatcher",
            "description": "Dynamically adjusts concurrency based on system memory usage. "
                          "Monitors memory pressure and adapts crawl sessions accordingly.",
            "config": DISPATCHER_DEFAULTS["memory_adaptive"],
            "features": [
                "Dynamic concurrency adjustment",
                "Memory pressure monitoring",
                "Automatic task requeuing under high memory",
                "Fairness timeout for long-waiting URLs"
            ]
        },
        "semaphore": {
            "name": "Semaphore Dispatcher",
            "description": "Fixed concurrency limit using semaphore-based control. "
                          "Simple and predictable for controlled crawling.",
            "config": DISPATCHER_DEFAULTS["semaphore"],
            "features": [
                "Fixed concurrency limit",
                "Simple semaphore-based control",
                "Predictable resource usage"
            ]
        }
    }

# ============================================================================
# End Dispatcher Configuration
# ============================================================================


def load_config() -> Dict:
    """Load and return application configuration with environment variable overrides."""
    config_path = Path(__file__).parent / "config.yml"
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


def create_chunking_strategy(config: Optional[Dict[str, Any]] = None) -> Optional[ChunkingStrategy]:
    """
    Factory function to create chunking strategy instances from configuration.
    
    Args:
        config: Dictionary containing 'type' and 'params' keys
               Example: {"type": "RegexChunking", "params": {"patterns": ["\\n\\n+"]}}
    
    Returns:
        ChunkingStrategy instance or None if config is None
        
    Raises:
        ValueError: If chunking strategy type is unknown or config is invalid
    """
    if config is None:
        return None
    
    if not isinstance(config, dict):
        raise ValueError(f"Chunking strategy config must be a dictionary, got {type(config)}")
    
    if "type" not in config:
        raise ValueError("Chunking strategy config must contain 'type' field")
    
    strategy_type = config["type"]
    params = config.get("params", {})
    
    # Validate params is a dict
    if not isinstance(params, dict):
        raise ValueError(f"Chunking strategy params must be a dictionary, got {type(params)}")
    
    # Strategy factory mapping
    strategies = {
        "IdentityChunking": IdentityChunking,
        "RegexChunking": RegexChunking,
        "NlpSentenceChunking": NlpSentenceChunking,
        "TopicSegmentationChunking": TopicSegmentationChunking,
        "FixedLengthWordChunking": FixedLengthWordChunking,
        "SlidingWindowChunking": SlidingWindowChunking,
        "OverlappingWindowChunking": OverlappingWindowChunking,
    }
    
    if strategy_type not in strategies:
        available = ", ".join(strategies.keys())
        raise ValueError(f"Unknown chunking strategy type: {strategy_type}. Available: {available}")
    
    try:
        return strategies[strategy_type](**params)
    except Exception as e:
        raise ValueError(f"Failed to create {strategy_type} with params {params}: {str(e)}")