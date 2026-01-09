"""
Claude Code/Agent SDK provider for LiteLLM integration.

This provider enables using Claude Code CLI authentication for LLM completions,
allowing users with Claude Code subscriptions to leverage their existing auth
without needing separate API keys.

IMPORTANT: Uses LOCAL Claude Code CLI authentication.
Each user must have their own Claude Code CLI installed and authenticated.

Usage:
    from crawl4ai.async_configs import LLMConfig

    # Use your Claude Code subscription
    config = LLMConfig(provider="claude-code/claude-sonnet-4-20250514")

Supported models:
    - claude-code/claude-sonnet-4-20250514 (recommended)
    - claude-code/claude-opus-4-20250514
    - claude-code/claude-haiku-3-5-latest
"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from litellm import CustomLLM
from litellm.types.utils import Choices, Message, ModelResponse, Usage

logger = logging.getLogger(__name__)


class ClaudeCodeError(Exception):
    """Base exception for Claude Code provider errors."""
    pass


class ClaudeCodeProvider(CustomLLM):
    """
    Custom LiteLLM provider for Claude Code/Agent SDK.

    This provider wraps the Claude Agent SDK to provide LLM completions
    using the user's local Claude Code CLI authentication.
    """

    def _extract_model(self, model: str) -> str:
        """
        Extract model name from provider string.

        Args:
            model: Provider string like "claude-code/claude-sonnet-4-20250514"

        Returns:
            Model name like "claude-sonnet-4-20250514"
        """
        if "/" in model:
            return model.split("/", 1)[1]
        return model

    def _convert_messages_to_prompt(self, messages: List[Dict]) -> str:
        """
        Convert LiteLLM message format to single prompt string.

        The Claude Agent SDK expects a single prompt string, not a messages
        array. This method converts the standard messages format to a
        formatted prompt string.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            Formatted prompt string

        Raises:
            ValueError: If messages is empty or has invalid format
            TypeError: If message content is not a string
        """
        if not messages:
            return ""

        parts = []
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise TypeError(
                    f"Message at index {i} must be a dict, got {type(msg).__name__}"
                )

            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Validate content is a string (not multimodal)
            if content is not None and not isinstance(content, str):
                raise TypeError(
                    f"Message at index {i} has non-string content (type: {type(content).__name__}). "
                    "Multimodal content is not supported by claude-code provider."
                )

            if role == "system":
                parts.append(f"System: {content}")
            elif role == "user":
                parts.append(content or "")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")

        return "\n\n".join(parts)

    async def _collect_response(
        self, prompt: str, model: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Call Claude Agent SDK and collect the full response.

        Args:
            prompt: The prompt string to send
            model: The model name to use

        Returns:
            Tuple of (response_text, usage_info)

        Raises:
            ImportError: If claude-agent-sdk is not installed
            ClaudeCodeError: If the SDK returns an error or empty response
        """
        try:
            from claude_agent_sdk import (
                AssistantMessage,
                ClaudeAgentOptions,
                ResultMessage,
                TextBlock,
                query,
            )
        except ImportError:
            raise ImportError(
                "claude-agent-sdk is not installed. "
                "Install with: pip install crawl4ai[claude-code]"
            )

        options = ClaudeAgentOptions(
            model=model,
            max_turns=1,  # Single turn for extraction tasks
            allowed_tools=[],  # No tools needed for text completion
        )

        logger.debug(f"Sending prompt to Claude Code: model={model}, prompt_length={len(prompt)}")

        collected_text = []
        usage_info = None

        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            collected_text.append(block.text)
                elif isinstance(message, ResultMessage):
                    usage_info = {
                        "session_id": message.session_id,
                        "duration_ms": message.duration_ms,
                        "input_tokens": message.usage.get("input_tokens", 0)
                        if message.usage
                        else 0,
                        "output_tokens": message.usage.get("output_tokens", 0)
                        if message.usage
                        else 0,
                    }
                else:
                    logger.debug(f"Received unexpected message type: {type(message).__name__}")
        except ConnectionError as e:
            raise ClaudeCodeError(
                f"Failed to connect to Claude Code service: {e}. "
                "Ensure the Claude Code CLI is installed and authenticated."
            ) from e
        except Exception as e:
            # Re-raise ImportError as-is
            if isinstance(e, ImportError):
                raise
            raise ClaudeCodeError(
                f"Claude Code SDK error: {e}. "
                "Verify your Claude Code CLI is properly installed and authenticated "
                "by running 'claude' in your terminal."
            ) from e

        response_text = "".join(collected_text)

        logger.debug(f"Received response: length={len(response_text)}, usage={usage_info}")

        # Warn if response is empty (but don't fail - the SDK may have valid reasons)
        if not response_text.strip():
            logger.warning(
                "Claude Code returned an empty response. This may indicate an "
                "authentication issue, rate limiting, or API error."
            )

        return response_text, usage_info

    async def acompletion(
        self,
        model: str,
        messages: List[Dict],
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        optional_params: Optional[Dict] = None,
        timeout: Optional[float] = None,
        client=None,
        **kwargs,
    ) -> ModelResponse:
        """
        Async completion using Claude Code SDK.

        Args:
            model: Model string like "claude-code/claude-sonnet-4-20250514"
            messages: List of message dicts with 'role' and 'content'
            api_base: Not used (Claude Code uses local auth)
            api_key: Not used (Claude Code uses local auth)
            optional_params: Additional parameters (currently unused)
            timeout: Request timeout (not currently enforced - SDK handles timeouts)
            client: HTTP client (not used)
            **kwargs: Additional arguments

        Returns:
            LiteLLM ModelResponse object
        """
        model_name = self._extract_model(model)
        prompt = self._convert_messages_to_prompt(messages)

        logger.info(f"Claude Code completion: model={model_name}, messages={len(messages)}")

        response_text, usage_info = await self._collect_response(prompt, model_name)

        # Calculate token counts
        input_tokens = usage_info.get("input_tokens", 0) if usage_info else 0
        output_tokens = usage_info.get("output_tokens", 0) if usage_info else 0

        # Generate response ID
        response_id = (
            usage_info.get("session_id") if usage_info
            else f"claude-code-{int(time.time())}"
        )

        return ModelResponse(
            id=response_id,
            choices=[
                Choices(
                    message=Message(role="assistant", content=response_text),
                    index=0,
                    finish_reason="stop",
                )
            ],
            created=int(time.time()),
            model=model_name,
            usage=Usage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
            object="chat.completion",
        )

    def completion(
        self,
        model: str,
        messages: List[Dict],
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        optional_params: Optional[Dict] = None,
        timeout: Optional[float] = None,
        client=None,
        **kwargs,
    ) -> ModelResponse:
        """
        Sync completion - runs async version in event loop.

        Args:
            Same as acompletion

        Returns:
            LiteLLM ModelResponse object
        """
        # Check if we're in an async context by looking for a running event loop
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as e:
            # Only catch the specific "no running event loop" error
            if "no running event loop" not in str(e).lower():
                raise

        if loop and loop.is_running():
            # We're in an async context, need to use a new thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.acompletion(
                        model=model,
                        messages=messages,
                        api_base=api_base,
                        api_key=api_key,
                        optional_params=optional_params,
                        timeout=timeout,
                        client=client,
                        **kwargs,
                    ),
                )
                try:
                    return future.result()
                except Exception as e:
                    raise ClaudeCodeError(f"Claude Code completion failed: {e}") from e
        else:
            return asyncio.run(
                self.acompletion(
                    model=model,
                    messages=messages,
                    api_base=api_base,
                    api_key=api_key,
                    optional_params=optional_params,
                    timeout=timeout,
                    client=client,
                    **kwargs,
                )
            )
