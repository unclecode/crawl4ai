# deploy/docker/mcp_bridge.py

from __future__ import annotations
import inspect, json, re
from typing import Any, Callable, Dict, List
from contextlib import asynccontextmanager
import httpx

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastmcp import FastMCP

# Decorator functions for marking FastAPI routes
def mcp_resource(name: str | None = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "resource", name
        return fn
    return deco

def mcp_template(name: str | None = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "template", name
        return fn
    return deco

def mcp_tool(name: str | None = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "tool", name
        return fn
    return deco

def _make_http_proxy(base_url: str, route):
    """Create HTTP proxy function for FastAPI route."""
    method = list(route.methods - {"HEAD", "OPTIONS"})[0]

    async def proxy(**kwargs):
        path = route.path
        json_body = {}

        # Check for unwrapped Pydantic body
        if "_pydantic_body" in kwargs:
            kwargs.pop("_param_name")  # Not needed in proxy
            pydantic_data = kwargs.pop("_pydantic_body")
            # FastAPI expects Pydantic model data as the root JSON body, not wrapped
            json_body = pydantic_data
        else:
            # Process each parameter normally
            for k, v in list(kwargs.items()):
                placeholder = "{" + k + "}"
                if placeholder in path:
                    # Path parameter
                    path = path.replace(placeholder, str(v))
                    kwargs.pop(k)
                elif hasattr(v, "model_dump"):
                    # Pydantic model serialization
                    json_body[k] = v.model_dump()
                    kwargs.pop(k)

            # Remaining kwargs are query/body params
            if kwargs:
                json_body.update(kwargs)

        url = base_url.rstrip("/") + path

        async with httpx.AsyncClient() as client:
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
                raise HTTPException(e.response.status_code, e.response.text)
    return proxy

def _body_model(fn: Callable) -> type[BaseModel] | None:
    """Extract Pydantic model from function signature."""
    for p in inspect.signature(fn).parameters.values():
        a = p.annotation
        if inspect.isclass(a) and issubclass(a, BaseModel):
            return a
    return None

def create_mcp_server(
    *,
    name: str | None = None,
    routes: list,
    base_url: str,
) -> FastMCP:
    """Create FastMCP server instance with registered tools."""
    server_name = name or "FastAPI-MCP"

    # Create FastMCP instance
    mcp = FastMCP(name=server_name)

    # Register tools by scanning decorated FastAPI routes
    for route in routes:
        fn = getattr(route, "endpoint", None)
        kind = getattr(fn, "__mcp_kind__", None)

        if kind != "tool":
            continue

        tool_name = fn.__mcp_name__ or re.sub(r"[/{}}]", "_", route.path).strip("_")
        proxy_fn = _make_http_proxy(base_url, route)
        description = inspect.getdoc(fn) or f"Tool for {route.path}"

        # Get function signature to create properly typed wrapper
        sig = inspect.signature(fn)
        params = []
        for param_name, param in sig.parameters.items():
            # Skip Request, Depends, and other FastAPI-specific params
            if param.annotation in (inspect.Parameter.empty, type(None)):
                continue
            if hasattr(param.annotation, "__origin__"):  # Skip complex types like Depends
                continue
            params.append(param)

        # Create function dynamically with explicit parameters
        param_names = [p.name for p in params]
        param_sig = ", ".join(param_names)

        # Build the async function code
        func_code = f"""
async def {tool_name}_wrapper({param_sig}):
    kwargs = {{{", ".join(f'"{name}": {name}' for name in param_names)}}}
    result = await proxy_fn(**kwargs)
    return json.dumps(result, default=str)
"""

        # Execute in a namespace that has access to proxy_fn and json
        namespace = {"proxy_fn": proxy_fn, "json": json}
        exec(func_code, namespace)
        wrapper_fn = namespace[f"{tool_name}_wrapper"]

        # Register the properly typed function
        mcp.tool(name=tool_name, description=description)(wrapper_fn)

    print(f"Registered {len([r for r in routes if getattr(getattr(r, 'endpoint', None), '__mcp_kind__', None) == 'tool'])} MCP tools")

    return mcp

def combine_lifespans(mcp_lifespan, existing_lifespan):
    """Combine MCP and existing lifespans into a single context manager."""
    @asynccontextmanager
    async def combined(app):
        # Run both lifespans - MCP outer, existing inner
        async with mcp_lifespan(app):
            async with existing_lifespan(app):
                yield
    return combined

def register_tools_from_routes(mcp_server: FastMCP, routes: list, base_url: str):
    """Register tools to an existing FastMCP server from FastAPI routes.

    Preserves Pydantic model schemas by using them directly as parameters.
    FastMCP automatically extracts JSON schemas from Pydantic type annotations.
    """
    tool_count = 0
    for route in routes:
        fn = getattr(route, "endpoint", None)
        kind = getattr(fn, "__mcp_kind__", None)

        if kind != "tool":
            continue

        tool_count += 1
        tool_name = fn.__mcp_name__ or re.sub(r"[/{}}]", "_", route.path).strip("_")
        proxy_fn = _make_http_proxy(base_url, route)
        description = inspect.getdoc(fn) or f"Tool for {route.path}"

        # Extract parameters from function signature
        sig = inspect.signature(fn)
        pydantic_model = None
        pydantic_param_name = None
        all_params = {}

        for param_name, param in sig.parameters.items():
            # Skip Request type
            if hasattr(param.annotation, "__name__") and param.annotation.__name__ == "Request":
                continue
            # Skip Depends - check both annotation string and default value
            if str(param.annotation).startswith("Depends"):
                continue
            if param.default != inspect.Parameter.empty and "Depends" in str(param.default):
                continue
            # Skip empty annotations
            if param.annotation == inspect.Parameter.empty:
                continue

            all_params[param_name] = param.annotation

            # Check if this is a Pydantic model (has model_fields attribute)
            if hasattr(param.annotation, "model_fields") and not pydantic_model:
                pydantic_model = param.annotation
                pydantic_param_name = param_name

        if not all_params:
            print(f"Warning: No parameters found for tool {tool_name}, skipping")
            continue

        # Unwrap Pydantic model if found, otherwise use params directly
        try:
            if pydantic_model:
                # Unwrap Pydantic model - use its fields directly with defaults preserved
                param_annotations = {}
                param_defaults = {}
                param_signature_parts = []

                for field_name, field_info in pydantic_model.model_fields.items():
                    # Convert enum annotations to their base type for better MCP compatibility
                    annotation = field_info.annotation
                    if hasattr(annotation, '__bases__') and len(annotation.__bases__) > 0:
                        # This is likely an enum - use its base type (usually str)
                        for base in annotation.__bases__:
                            if base in (str, int, float, bool):
                                annotation = base
                                break
                    param_annotations[field_name] = annotation

                    # Simplified approach: all optional fields default to None
                    if hasattr(field_info, 'default') and field_info.default is not ...:
                        # Has a default - make it optional with None
                        param_defaults[field_name] = None
                        param_signature_parts.append(f"{field_name}=None")
                    elif hasattr(field_info, 'default_factory') and field_info.default_factory is not None:
                        # Has default factory - make it optional with None
                        param_defaults[field_name] = None
                        param_signature_parts.append(f"{field_name}=None")
                    else:
                        # Required field
                        param_signature_parts.append(field_name)

                param_signature = ", ".join(param_signature_parts)

                # Generate wrapper that reconstructs Pydantic model
                # Pass model dict directly to proxy (FastAPI expects body content, not wrapped)
                func_code = f"""
async def {tool_name}_wrapper({param_signature}):
    import json
    model_data = {{{", ".join(f'"{p}": {p}' for p in param_annotations.keys())}}}
    # Pass the model data dict directly - proxy will handle it
    result = await proxy_fn(_pydantic_body=model_data, _param_name="{pydantic_param_name}")
    return json.dumps(result, default=str)
"""

                namespace = {
                    "proxy_fn": proxy_fn,
                    "json": json,
                    "pydantic_model": pydantic_model,
                    "pydantic_param_name": pydantic_param_name
                }
            else:
                # Use individual parameters directly - preserve defaults from FastAPI signature
                param_annotations = all_params.copy()
                param_signature_parts = []

                # Get original function signature to extract defaults - handle FastAPI types safely
                orig_sig = inspect.signature(fn)
                for param_name in param_annotations.keys():
                    if param_name in orig_sig.parameters:
                        orig_param = orig_sig.parameters[param_name]
                        if orig_param.default is not inspect.Parameter.empty:
                            # All parameters with defaults become None (simplified approach)
                            param_signature_parts.append(f"{param_name}=None")
                        else:
                            param_signature_parts.append(param_name)
                    else:
                        param_signature_parts.append(param_name)

                param_signature = ", ".join(param_signature_parts)

                func_code = f"""
async def {tool_name}_wrapper({param_signature}):
    import json
    kwargs = {{{", ".join(f'"{p}": {p}' for p in param_annotations.keys())}}}
    result = await proxy_fn(**kwargs)
    return json.dumps(result, default=str)
"""

                namespace = {"proxy_fn": proxy_fn, "json": json}

            exec(func_code, namespace)
            wrapper_fn = namespace[f"{tool_name}_wrapper"]

            # Set type annotations
            wrapper_fn.__annotations__ = param_annotations.copy()
            wrapper_fn.__annotations__["return"] = str

            # Register with FastMCP
            mcp_server.tool(name=tool_name, description=description)(wrapper_fn)

        except Exception as e:
            print(f"Error creating wrapper for {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"Registered {tool_count} MCP tools")