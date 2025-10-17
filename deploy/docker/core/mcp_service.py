# deploy/docker/mcp_service.py

from __future__ import annotations

import inspect
import json
import logging
import re
import urllib.parse
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, get_args, get_origin

import httpx
from fastapi import HTTPException
from fastapi.params import Param
from fastapi.routing import APIRoute
from fastmcp import FastMCP
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class MCPToolDefinition:
    """
    Represents an MCP tool definition extracted from OpenAPI/FastAPI routes.

    This replaces runtime route introspection with a more structured approach.
    """

    def __init__(
        self,
        name: str,
        description: str,
        endpoint_path: str,
        http_method: str,
        parameters: List[inspect.Parameter],
        pydantic_model: Optional[type[BaseModel]] = None,
        pydantic_param_name: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.endpoint_path = endpoint_path
        self.http_method = http_method
        self.parameters = parameters
        self.pydantic_model = pydantic_model
        self.pydantic_param_name = pydantic_param_name


class MCPService:
    """
    Dedicated service layer for MCP integration.

    Decouples MCP logic from FastAPI route introspection and provides:
    - Clean separation of concerns
    - Dependency injection for route discovery
    - OpenAPI-based tool registration
    - Centralized proxy creation
    """
    def get_mcp_schema(self, openapi_schema: dict, routes: list) -> dict:
        """
        Generate the MCP tool schema from the FastAPI app's OpenAPI schema and routes.
        """
        mcp_schema = {
            "tools": [],
            "resources": [],
            "prompts": []
        }

        # Helper to resolve $ref links in the OpenAPI schema
        def resolve_ref(ref):
            parts = ref.strip("#/").split("/")
            d = openapi_schema
            for part in parts:
                d = d[part]
            return d

        # Iterate through the app's routes to find functions marked as tools
        for route in routes:
            if not isinstance(route, APIRoute) or not hasattr(route.endpoint, "__mcp_kind__") or getattr(route.endpoint, "__mcp_kind__") != "tool":
                continue

            path = route.path
            if not route.methods:
                continue
            method = next(iter(route.methods)).lower()

            if path not in openapi_schema.get("paths", {}) or method not in openapi_schema["paths"].get(path, {}):
                continue
            
            operation = openapi_schema["paths"][path][method]

            tool_name = getattr(route.endpoint, "__mcp_name__", None) or operation.get("summary") or route.name

            input_schema = {"type": "object", "properties": {}}

            if "requestBody" in operation:
                request_body = operation.get("requestBody", {})
                if "content" in request_body and "$ref" in request_body.get("content", {}).get("application/json", {}).get("schema", {}):
                    schema_ref = request_body["content"]["application/json"]["schema"]["$ref"]
                    input_schema = resolve_ref(schema_ref)
                elif "content" in request_body:
                    input_schema = request_body["content"].get("application/json", {}).get("schema", {})

            if "parameters" in operation:
                if "properties" not in input_schema:
                    input_schema["properties"] = {}
                
                properties = input_schema["properties"]
                for param in operation["parameters"]:
                    if "$ref" in param:
                        param = resolve_ref(param["$ref"])
                    
                    if param.get("in") not in ["query", "path"]:
                        continue

                    param_name = param["name"]
                    param_schema = param.get("schema", {})
                    
                    if "description" in param:
                        param_schema["description"] = param["description"]
                        
                    properties[param_name] = param_schema

            tool_schema = {
                "name": tool_name,
                "description": operation.get("description", "") or inspect.getdoc(route.endpoint) or "",
                "inputSchema": input_schema
            }

            mcp_schema["tools"].append(tool_schema)

        return mcp_schema

    def __init__(self, base_url: str, server_name: str = "FastAPI-MCP"):
        self.base_url = base_url
        self.server_name = server_name
        self.mcp_server = FastMCP(name=server_name)
        self._registered_tools: Dict[str, MCPToolDefinition] = {}

    def extract_tools_from_routes(self, routes: List[APIRoute]) -> List[MCPToolDefinition]:
        """
        Extract MCP tool definitions from FastAPI routes.

        Uses route metadata rather than deep introspection.
        """
        tools = []

        for route in routes:
            fn = getattr(route, "endpoint", None)
            if not fn:
                continue

            kind = getattr(fn, "__mcp_kind__", None)
            if kind != "tool":
                continue

            try:
                tool_def = self._create_tool_definition(route, fn)
                tools.append(tool_def)
            except ValueError as e:
                logger.warning("Skipping tool %s: %s", route.path, e)
            except Exception:
                logger.exception("Error extracting tool from %s", route.path)

        return tools

    def _create_tool_definition(self, route: APIRoute, fn: Callable) -> MCPToolDefinition:
        """Create tool definition from route and endpoint function."""
        raw_name = getattr(fn, "__mcp_name__", None) or route.path
        tool_name = self._sanitize_tool_name(raw_name)
        description = inspect.getdoc(fn) or f"Tool for {route.path}"

        methods = route.methods - {"HEAD", "OPTIONS"}
        http_method = next(iter(methods)) if methods else "GET"

        sig = inspect.signature(fn)
        usable_params: Dict[str, inspect.Parameter] = {}
        pydantic_model: Optional[type[BaseModel]] = None
        pydantic_param_name: Optional[str] = None

        for name, param in sig.parameters.items():
            if param.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
                continue

            annotation = param.annotation
            if annotation is inspect.Parameter.empty or annotation is type(None):
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

        parameters = list(usable_params.values())

        return MCPToolDefinition(
            name=tool_name,
            description=description,
            endpoint_path=route.path,
            http_method=http_method,
            parameters=parameters,
            pydantic_model=pydantic_model,
            pydantic_param_name=pydantic_param_name,
        )

    def register_tools(self, tools: List[MCPToolDefinition]) -> None:
        """Register extracted tools with the MCP server."""
        for tool_def in tools:
            try:
                self._register_single_tool(tool_def)
                self._registered_tools[tool_def.name] = tool_def
            except Exception:
                logger.exception("Failed to register tool %s", tool_def.name)

        logger.info("Registered %d MCP tools", len(self._registered_tools))

    def _register_single_tool(self, tool_def: MCPToolDefinition) -> None:
        """Register a single tool with the MCP server."""
        proxy_fn = self._create_http_proxy(tool_def)

        if tool_def.pydantic_model and tool_def.pydantic_param_name:
            wrapper_fn = self._build_pydantic_wrapper(tool_def, proxy_fn)
        else:
            wrapper_fn = self._build_parameter_wrapper(tool_def, proxy_fn)

        self.mcp_server.tool(name=tool_def.name, description=tool_def.description)(wrapper_fn)

    def _create_http_proxy(self, tool_def: MCPToolDefinition) -> Callable:
        """
        Create HTTP proxy function for a tool.

        Uses tool definition instead of inspecting route directly.
        """
        async def proxy(**kwargs):
            path = tool_def.endpoint_path
            json_body = {}

            if "_pydantic_body" in kwargs:
                kwargs.pop("_param_name", None)
                pydantic_data = kwargs.pop("_pydantic_body")
                json_body = pydantic_data
            else:
                for k, v in list(kwargs.items()):
                    typed_match = re.search(r"\{" + re.escape(k) + r":([^}]*)\}", path)
                    safe_chars = "/" if typed_match and typed_match.group(1) == "path" else ""
                    encoded_value = urllib.parse.quote(str(v), safe=safe_chars)
                    pattern = re.compile(r"\{" + re.escape(k) + r"(?:\:[^}]*)?\}")

                    if pattern.search(path):
                        path = pattern.sub(encoded_value, path)
                        kwargs.pop(k)
                    elif hasattr(v, "model_dump"):
                        json_body[k] = v.model_dump()
                        kwargs.pop(k)

                if kwargs:
                    json_body.update(kwargs)

            url = self.base_url.rstrip("/") + path

            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    r = (
                        await client.get(url, params=json_body)
                        if tool_def.http_method == "GET"
                        else await client.request(tool_def.http_method, url, json=json_body)
                    )
                    r.raise_for_status()

                    try:
                        return r.json()
                    except (ValueError, TypeError):
                        return r.text

                except httpx.HTTPStatusError as e:
                    raise HTTPException(e.response.status_code, e.response.text) from e

        return proxy

    def _build_pydantic_wrapper(
        self, tool_def: MCPToolDefinition, proxy_fn: Callable
    ) -> Callable:
        """Build wrapper for Pydantic model parameters."""
        model = tool_def.pydantic_model
        param_name = tool_def.pydantic_param_name

        field_annotations: Dict[str, object] = {}
        parameters: List[inspect.Parameter] = []
        list_fields: set[str] = set()
        numeric_int_fields: set[str] = set()
        numeric_float_fields: set[str] = set()

        for field_name, field_info in model.model_fields.items():
            annotation = self._normalize_annotation(field_info.annotation)

            if self._annotation_is_list(field_info.annotation):
                list_fields.add(field_name)
            if self._annotation_has_numeric(field_info.annotation, int):
                numeric_int_fields.add(field_name)
            if self._annotation_has_numeric(field_info.annotation, float):
                numeric_float_fields.add(field_name)

            field_annotations[field_name] = annotation

            # Check if field is required (is_required is a method in Pydantic v2)
            is_required = field_info.is_required() if callable(field_info.is_required) else field_info.is_required

            if is_required:
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

        wrapper.__name__ = f"{tool_def.name}_wrapper"
        wrapper.__annotations__ = {**field_annotations, "return": str}
        wrapper.__signature__ = inspect.Signature(parameters, return_annotation=str)

        return wrapper

    def _build_parameter_wrapper(
        self, tool_def: MCPToolDefinition, proxy_fn: Callable
    ) -> Callable:
        """Build wrapper for regular parameters."""
        param_annotations: Dict[str, object] = {}
        numeric_int_fields: set[str] = set()
        numeric_float_fields: set[str] = set()
        list_fields: set[str] = set()
        parameters: List[inspect.Parameter] = []

        params = {p.name: p for p in tool_def.parameters}

        for name, param in params.items():
            annotation = self._normalize_annotation(param.annotation)
            param_annotations[name] = annotation

            if self._annotation_has_numeric(param.annotation, int):
                numeric_int_fields.add(name)
            if self._annotation_has_numeric(param.annotation, float):
                numeric_float_fields.add(name)
            if self._annotation_is_list(param.annotation):
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

        wrapper.__name__ = f"{tool_def.name}_wrapper"
        wrapper.__annotations__ = {**param_annotations, "return": str}
        wrapper.__signature__ = inspect.Signature(parameters, return_annotation=str)

        return wrapper

    @staticmethod
    def _sanitize_tool_name(raw_name: str) -> str:
        """Sanitize tool name for MCP compatibility."""
        sanitized = re.sub(r"[^0-9a-zA-Z_]", "_", raw_name).strip("_")
        if not sanitized or not re.match(r"[A-Za-z_]", sanitized):
            sanitized = f"tool_{sanitized}" if sanitized else "tool"
        return sanitized

    @staticmethod
    def _normalize_annotation(annotation: object) -> object:
        """Normalize annotation but preserve typing information."""
        if inspect.isclass(annotation) and issubclass(annotation, Enum):
            for base in annotation.__mro__[1:]:
                if base in {str, int, float, bool}:
                    return base
        return annotation

    @staticmethod
    def _annotation_is_list(annotation: object) -> bool:
        """Check if annotation is a list type."""
        origin = get_origin(annotation)
        return origin in (list, List)

    @staticmethod
    def _annotation_has_numeric(annotation: object, target: type) -> bool:
        """Check if annotation contains numeric type."""
        if annotation is target:
            return True
        origin = get_origin(annotation)
        if not origin:
            return False
        return any(
            MCPService._annotation_has_numeric(arg, target)
            for arg in get_args(annotation)
        )


def mcp_resource(name: str | None = None):
    """Decorator to mark FastAPI route as MCP resource."""
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "resource", name
        return fn
    return deco


def mcp_template(name: str | None = None):
    """Decorator to mark FastAPI route as MCP template."""
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "template", name
        return fn
    return deco


def mcp_tool(name: str | None = None):
    """Decorator to mark FastAPI route as MCP tool."""
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "tool", name
        return fn
    return deco