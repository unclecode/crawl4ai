# deploy/docker/mcp_bridge.py

from __future__ import annotations

import inspect
import json
import logging
import re
import urllib.parse
from contextlib import asynccontextmanager
from enum import Enum
from typing import Callable, Dict, List, Optional, get_args, get_origin

import httpx

from fastapi import HTTPException
from fastapi.params import Param
from fastmcp import FastMCP
from pydantic import BaseModel


logger = logging.getLogger(__name__)

def mcp_resource(name: str | None = None):
    """Decorator to mark FastAPI route as MCP resource.

    Args:
        name: Optional custom name for the resource.

    Returns:
        Decorated function with MCP metadata.
    """
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "resource", name
        return fn
    return deco

def mcp_template(name: str | None = None):
    """Decorator to mark FastAPI route as MCP template.

    Args:
        name: Optional custom name for the template.

    Returns:
        Decorated function with MCP metadata.
    """
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "template", name
        return fn
    return deco

def mcp_tool(name: str | None = None):
    """Decorator to mark FastAPI route as MCP tool.

    Args:
        name: Optional custom name for the tool.

    Returns:
        Decorated function with MCP metadata.
    """
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "tool", name
        return fn
    return deco

def _make_http_proxy(base_url: str, route):
    """Create HTTP proxy function for FastAPI route.

    Args:
        base_url: Base URL of the FastAPI server.
        route: FastAPI route object to proxy.

    Returns:
        Async function that proxies requests to the route.
    """
    methods = route.methods - {"HEAD", "OPTIONS"}
    method = next(iter(methods)) if methods else "GET"

    async def proxy(**kwargs):
        path = route.path
        json_body = {}

        # Check for unwrapped Pydantic body
        if "_pydantic_body" in kwargs:
            kwargs.pop("_param_name", None)  # Not needed in proxy
            pydantic_data = kwargs.pop("_pydantic_body")
            # FastAPI expects Pydantic model data as the root JSON body, not wrapped
            json_body = pydantic_data
        else:
            # Process each parameter normally
            for k, v in list(kwargs.items()):
                # Path parameter - support typed params e.g. {k:path}; preserve slashes for :path
                typed_match = re.search(r"\{" + re.escape(k) + r":([^}]*)\}", path)
                safe_chars = "/" if typed_match and typed_match.group(1) == "path" else ""
                encoded_value = urllib.parse.quote(str(v), safe=safe_chars)
                pattern = re.compile(r"\{" + re.escape(k) + r"(?:\:[^}]*)?\}")
                if pattern.search(path):
                    path = pattern.sub(encoded_value, path)
                    kwargs.pop(k)
                elif hasattr(v, "model_dump"):
                    # Pydantic model serialization
                    json_body[k] = v.model_dump()
                    kwargs.pop(k)

            # Remaining kwargs are query/body params
            if kwargs:
                json_body.update(kwargs)

        url = base_url.rstrip("/") + path

        # Use longer timeout for LLM operations (can take 30+ seconds)
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                r = (
                    await client.get(url, params=json_body)
                    if method == "GET"
                    else await client.request(method, url, json=json_body)
                )
                r.raise_for_status()
                # Try to parse JSON for both GET and other methods to avoid double-encoding
                try:
                    return r.json()
                except (ValueError, TypeError):
                    # Fallback to text if JSON parsing fails
                    return r.text
            except httpx.HTTPStatusError as e:
                raise HTTPException(e.response.status_code, e.response.text) from e
    return proxy


def _sanitize_tool_name(raw_name: str) -> str:
    sanitized = re.sub(r"[^0-9a-zA-Z_]", "_", raw_name).strip("_")
    if not sanitized or not re.match(r"[A-Za-z_]", sanitized):
        sanitized = f"tool_{sanitized}" if sanitized else "tool"
    return sanitized


def create_mcp_server(
    *,
    name: str | None = None,
    routes: list,
    base_url: str,
) -> FastMCP:
    """Create FastMCP server instance with registered tools."""

    server_name = name or "FastAPI-MCP"
    mcp = FastMCP(name=server_name)
    register_tools_from_routes(mcp_server=mcp, routes=routes, base_url=base_url)
    return mcp



def combine_lifespans(mcp_lifespan, existing_lifespan):
    """Combine MCP and existing lifespans into a single context manager."""

    @asynccontextmanager
    async def combined(app):
        # Run both lifespans - MCP outer, existing inner
        if mcp_lifespan is None and existing_lifespan is None:
            yield
            return
        if mcp_lifespan is None:
            async with existing_lifespan(app):
                yield
            return
        if existing_lifespan is None:
            async with mcp_lifespan(app):
                yield
            return

        async with mcp_lifespan(app):
            async with existing_lifespan(app):
                yield

    return combined



def register_tools_from_routes(mcp_server: FastMCP, routes: list, base_url: str):
    """Register tools to an existing FastMCP server from FastAPI routes."""

    tool_count = 0
    for route in routes:
        fn = getattr(route, "endpoint", None)
        kind = getattr(fn, "__mcp_kind__", None)

        if kind != "tool":
            continue

        tool_count += 1
        raw_name = fn.__mcp_name__ or route.path
        tool_name = _sanitize_tool_name(raw_name)
        proxy_fn = _make_http_proxy(base_url, route)
        description = inspect.getdoc(fn) or f"Tool for {route.path}"

        try:
            wrapper_fn = _build_tool_wrapper(
                fn=fn,
                proxy_fn=proxy_fn,
                tool_name=tool_name,
            )
        except ValueError as error:
            logger.warning("Skipping tool %s: %s", tool_name, error)
            continue
        except Exception:  # pragma: no cover - log unexpected wrapper failures
            logger.exception("Error creating wrapper for %s", tool_name)
            raise

        mcp_server.tool(name=tool_name, description=description)(wrapper_fn)

    logger.info("Registered %d MCP tools", tool_count)


def _build_tool_wrapper(
    *, fn: Callable[..., object], proxy_fn: Callable[..., object], tool_name: str
) -> Callable[..., object]:
    """Build an async wrapper for a FastAPI endpoint without using exec."""

    sig = inspect.signature(fn)
    usable_params: Dict[str, inspect.Parameter] = {}
    pydantic_model: Optional[type[BaseModel]] = None
    pydantic_param_name: Optional[str] = None

    for name, param in sig.parameters.items():
        if param.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
            continue

        annotation = param.annotation
        if annotation is inspect.Parameter.empty or annotation is type(None):  # noqa: E721
            continue

        if getattr(annotation, "__name__", "") == "Request":
            continue

        if "Depends" in str(annotation) or "Depends" in str(param.default):
            continue

        usable_params[name] = param

        if (
            pydantic_model is None
            and inspect.isclass(annotation)
            and issubclass(annotation, BaseModel)
        ):
            pydantic_model = annotation
            pydantic_param_name = name

    if not usable_params:
        raise ValueError("No MCP-exposable parameters found")

    if pydantic_model and pydantic_param_name:
        return _build_pydantic_wrapper(
            proxy_fn=proxy_fn,
            tool_name=tool_name,
            model=pydantic_model,
            param_name=pydantic_param_name,
        )

    return _build_parameter_wrapper(
        proxy_fn=proxy_fn,
        tool_name=tool_name,
        params=usable_params,
    )


def _normalize_annotation(annotation: object) -> object:
    """Normalize annotation but preserve List/typing information for FastMCP schema generation."""
    if inspect.isclass(annotation) and issubclass(annotation, Enum):
        for base in annotation.__mro__[1:]:
            if base in {str, int, float, bool}:
                return base
    # Preserve List[T] and other typing constructs - don't normalize them away
    return annotation


def _annotation_is_list(annotation: object) -> bool:
    origin = get_origin(annotation)
    return origin in (list, List)


def _annotation_has_numeric(annotation: object, target: type) -> bool:
    if annotation is target:
        return True
    origin = get_origin(annotation)
    if not origin:
        return False
    return any(_annotation_has_numeric(arg, target) for arg in get_args(annotation))


def _build_pydantic_wrapper(
    *,
    proxy_fn: Callable[..., object],
    tool_name: str,
    model: type[BaseModel],
    param_name: str,
) -> Callable[..., object]:
    field_annotations: Dict[str, object] = {}
    parameters: List[inspect.Parameter] = []
    list_fields: set[str] = set()
    numeric_int_fields: set[str] = set()
    numeric_float_fields: set[str] = set()
    list_fields: set[str] = set()

    for field_name, field_info in model.model_fields.items():
        annotation = _normalize_annotation(field_info.annotation)
        if _annotation_is_list(field_info.annotation):
            list_fields.add(field_name)
        if _annotation_has_numeric(field_info.annotation, int):
            numeric_int_fields.add(field_name)
        if _annotation_has_numeric(field_info.annotation, float):
            numeric_float_fields.add(field_name)

        field_annotations[field_name] = annotation
        if field_info.is_required():
            default = inspect._empty
        else:
            if field_info.default_factory is not None:
                default = field_info.default_factory()
            else:
                default = field_info.default
        parameters.append(
            inspect.Parameter(
                name=field_name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=annotation,
            )
        )

    async def wrapper(**kwargs):
        model_data: Dict[str, object] = {}
        for key in field_annotations:
            if key not in kwargs:
                continue
            value = kwargs[key]
            if value == "" or value is None:
                continue
            if key in list_fields and isinstance(value, str):
                value = [value]
            if key in numeric_int_fields and isinstance(value, str):
                try:
                    value = int(value.strip())
                except (TypeError, ValueError):
                    pass
            if key in numeric_float_fields and isinstance(value, str):
                try:
                    value = float(value.strip())
                except (TypeError, ValueError):
                    pass
            model_data[key] = value

        result = await proxy_fn(_pydantic_body=model_data, _param_name=param_name)
        return json.dumps(result, default=str)

    wrapper.__name__ = f"{tool_name}_wrapper"
    wrapper.__annotations__ = {**field_annotations, "return": str}
    wrapper.__signature__ = inspect.Signature(
        parameters,
        return_annotation=str,
    )
    return wrapper


def _build_parameter_wrapper(
    *,
    proxy_fn: Callable[..., object],
    tool_name: str,
    params: Dict[str, inspect.Parameter],
) -> Callable[..., object]:
    param_annotations: Dict[str, object] = {}
    numeric_int_fields: set[str] = set()
    numeric_float_fields: set[str] = set()
    list_fields: set[str] = set()
    parameters: List[inspect.Parameter] = []

    for name, param in params.items():
        annotation = _normalize_annotation(param.annotation)
        param_annotations[name] = annotation

        if _annotation_has_numeric(param.annotation, int):
            numeric_int_fields.add(name)
        if _annotation_has_numeric(param.annotation, float):
            numeric_float_fields.add(name)
        if _annotation_is_list(param.annotation):
            list_fields.add(name)

        if param.default is inspect.Parameter.empty:
            default = inspect._empty
        else:
            default_candidate = param.default
            if isinstance(default_candidate, Param):
                default = (
                    default_candidate.default
                    if default_candidate.default is not inspect._empty
                    else inspect._empty
                )
            else:
                default = default_candidate
        parameters.append(
            inspect.Parameter(
                name=name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=annotation,
            )
        )

    async def wrapper(**kwargs):
        prepared: Dict[str, object] = {}
        for key in param_annotations:
            if key not in kwargs:
                continue
            value = kwargs[key]
            if value == "" or value is None:
                continue
            if key in numeric_int_fields and isinstance(value, str):
                try:
                    value = int(value.strip())
                except (TypeError, ValueError):
                    pass
            if key in numeric_float_fields and isinstance(value, str):
                try:
                    value = float(value.strip())
                except (TypeError, ValueError):
                    pass
            if key in list_fields and isinstance(value, str):
                value = [value]
            prepared[key] = value

        result = await proxy_fn(**prepared)
        return json.dumps(result, default=str)

    wrapper.__name__ = f"{tool_name}_wrapper"
    wrapper.__annotations__ = {**param_annotations, "return": str}
    wrapper.__signature__ = inspect.Signature(
        parameters,
        return_annotation=str,
    )
    return wrapper
