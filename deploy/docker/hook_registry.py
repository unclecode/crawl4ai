"""
Declarative hook registry - the safe replacement for the exec-based hook system.

The old hook_manager.py compiled and exec()'d user-supplied Python at crawl hook
points. Its sandbox was unsound (escapable via __subclasses__ MRO walks, injected
module __globals__, frame inspection), giving unauthenticated RCE when hooks were
enabled. There is no safe way to run attacker Python in-process.

Instead, a request may only choose from a fixed set of declarative ACTIONS whose
parameters are schema-validated scalars. Each action maps to a server-authored
async function that calls exactly one specific Playwright API - no user string
ever reaches an interpreter. This covers the documented hook use cases (block
assets, inject auth cookies/headers, scroll for lazy content, wait).

Power users who genuinely need arbitrary hook code use a self-hosted in-process
build where crawler_strategy.set_hook(...) remains available and trusted.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List

from pydantic import BaseModel, Field, field_validator


class HookValidationError(ValueError):
    """A declarative hook spec was invalid. The Docker layer maps this to 400."""


_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")
_ALLOWED_RESOURCE_TYPES = {"image", "stylesheet", "font", "media"}
_MAX_SCROLL_STEPS = 50
_MAX_SCROLL_DELAY_MS = 5000
_MAX_WAIT_MS = 60_000
_MAX_COOKIES = 20
_MAX_HEADERS = 20


# ───────────────────────── per-action parameter schemas ─────────────────────────
class BlockResourcesParams(BaseModel):
    resource_types: List[str] = Field(..., min_length=1)

    @field_validator("resource_types")
    @classmethod
    def _check(cls, v):
        bad = sorted(set(v) - _ALLOWED_RESOURCE_TYPES)
        if bad:
            raise ValueError(f"unsupported resource_types {bad}; allowed: {sorted(_ALLOWED_RESOURCE_TYPES)}")
        return v


class _Cookie(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    value: str = Field(..., max_length=4096)
    domain: str = Field(..., min_length=1, max_length=253)
    path: str = "/"
    secure: bool = True
    httpOnly: bool = False


class AddCookiesParams(BaseModel):
    cookies: List[_Cookie] = Field(..., min_length=1, max_length=_MAX_COOKIES)


class SetHeadersParams(BaseModel):
    headers: Dict[str, str]

    @field_validator("headers")
    @classmethod
    def _check(cls, v):
        if len(v) > _MAX_HEADERS:
            raise ValueError(f"too many headers (max {_MAX_HEADERS})")
        for name, value in v.items():
            if not _HEADER_NAME_RE.match(name):
                raise ValueError(f"invalid header name {name!r}")
            if any(c in value for c in "\r\n\x00"):
                raise ValueError(f"control characters in value for header {name!r}")
        return v


class ScrollToBottomParams(BaseModel):
    max_steps: int = Field(10, ge=1, le=_MAX_SCROLL_STEPS)
    delay_ms: int = Field(500, ge=0, le=_MAX_SCROLL_DELAY_MS)


class WaitForTimeoutParams(BaseModel):
    timeout_ms: int = Field(..., ge=0, le=_MAX_WAIT_MS)


# ───────────────────────── server-authored hook factories ─────────────────────────
def _factory_block_resources(p: BlockResourcesParams):
    types = set(p.resource_types)

    async def hook(page, **kwargs):
        context = kwargs.get("context")

        async def _route(route):
            try:
                if route.request.resource_type in types:
                    await route.abort()
                else:
                    await route.continue_()
            except Exception:
                # never let a routing decision crash the crawl
                await route.continue_()

        if context is not None:
            await context.route("**/*", _route)
        return page

    return hook


def _factory_add_cookies(p: AddCookiesParams):
    cookies = [c.model_dump() for c in p.cookies]

    async def hook(page, **kwargs):
        context = kwargs.get("context")
        if context is not None:
            await context.add_cookies(cookies)
        return page

    return hook


def _factory_set_headers(p: SetHeadersParams):
    headers = dict(p.headers)

    async def hook(page, **kwargs):
        await page.set_extra_http_headers(headers)
        return page

    return hook


def _factory_scroll_to_bottom(p: ScrollToBottomParams):
    max_steps, delay_ms = p.max_steps, p.delay_ms

    async def hook(page, **kwargs):
        for _ in range(max_steps):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            if delay_ms:
                await page.wait_for_timeout(delay_ms)
        return page

    return hook


def _factory_wait_for_timeout(p: WaitForTimeoutParams):
    timeout_ms = p.timeout_ms

    async def hook(page, **kwargs):
        await page.wait_for_timeout(timeout_ms)
        return page

    return hook


# action name -> (hook_point, params model, factory, human description)
HOOK_REGISTRY: Dict[str, dict] = {
    "block_resources": {
        "hook_point": "on_page_context_created",
        "params_model": BlockResourcesParams,
        "factory": _factory_block_resources,
        "description": "Abort matching resource types (image/stylesheet/font/media).",
    },
    "add_cookies": {
        "hook_point": "on_page_context_created",
        "params_model": AddCookiesParams,
        "factory": _factory_add_cookies,
        "description": "Add cookies to the browser context before navigation (auth).",
    },
    "set_headers": {
        "hook_point": "before_goto",
        "params_model": SetHeadersParams,
        "factory": _factory_set_headers,
        "description": "Set extra HTTP request headers before navigating.",
    },
    "scroll_to_bottom": {
        "hook_point": "before_retrieve_html",
        "params_model": ScrollToBottomParams,
        "factory": _factory_scroll_to_bottom,
        "description": "Scroll to the page bottom in bounded steps (lazy-load).",
    },
    "wait_for_timeout": {
        "hook_point": "before_retrieve_html",
        "params_model": WaitForTimeoutParams,
        "factory": _factory_wait_for_timeout,
        "description": "Wait a bounded number of milliseconds before retrieving HTML.",
    },
}


def build_declarative_hooks(specs: List[Any]) -> Dict[str, Callable]:
    """Validate declarative hook specs and return {hook_point: composed async hook}.

    Each spec is an object/dict with `action` and `params`. Multiple specs that
    target the same hook point are composed and run in order. Raises
    HookValidationError on an unknown action or invalid params.
    """
    if not specs:
        return {}
    if len(specs) > 10:
        raise HookValidationError("too many hooks (max 10)")

    grouped: Dict[str, List[Callable]] = {}
    for spec in specs:
        action = spec.get("action") if isinstance(spec, dict) else getattr(spec, "action", None)
        raw_params = (spec.get("params", {}) if isinstance(spec, dict) else getattr(spec, "params", {})) or {}
        entry = HOOK_REGISTRY.get(action)
        if entry is None:
            raise HookValidationError(
                f"unknown hook action {action!r}; allowed: {sorted(HOOK_REGISTRY)}"
            )
        try:
            params = entry["params_model"](**raw_params)
        except Exception as e:
            raise HookValidationError(f"invalid params for hook '{action}': {e}")
        sub_hook = entry["factory"](params)
        grouped.setdefault(entry["hook_point"], []).append(sub_hook)

    hooks: Dict[str, Callable] = {}
    for hook_point, sub_hooks in grouped.items():
        def _compose(sub_hooks):
            async def composed(page, **kwargs):
                for fn in sub_hooks:
                    await fn(page, **kwargs)
                return page
            return composed
        hooks[hook_point] = _compose(sub_hooks)
    return hooks


def describe_registry() -> dict:
    """Enumerate the available declarative actions for /hooks/info."""
    return {
        action: {
            "hook_point": entry["hook_point"],
            "description": entry["description"],
            "params_schema": entry["params_model"].model_json_schema(),
        }
        for action, entry in HOOK_REGISTRY.items()
    }
