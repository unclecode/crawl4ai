"""
Custom LLM providers for Crawl4AI.

This module provides custom LLM provider integrations beyond what LiteLLM
offers out of the box.
"""

_providers_registered = False


def register_custom_providers():
    """
    Register custom LLM providers with LiteLLM.

    This function registers all custom providers defined in this package
    with LiteLLM's custom_provider_map. It is idempotent - calling it
    multiple times has no additional effect.

    Currently registered providers:
    - claude-code: Uses Claude Code CLI for LLM completions (requires local auth)
    """
    global _providers_registered
    if _providers_registered:
        return

    import litellm

    # Initialize custom_provider_map if it doesn't exist
    if litellm.custom_provider_map is None:
        litellm.custom_provider_map = []

    # Try to register Claude Code provider (optional dependency)
    try:
        from .claude_code_provider import ClaudeCodeProvider

        # Check if already registered
        existing_providers = [p.get("provider") for p in litellm.custom_provider_map]
        if "claude-code" not in existing_providers:
            litellm.custom_provider_map.append({
                "provider": "claude-code",
                "custom_handler": ClaudeCodeProvider()
            })
    except ImportError:
        # claude-agent-sdk not installed, skip registration
        pass

    _providers_registered = True
