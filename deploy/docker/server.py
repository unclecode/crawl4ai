# ───────────────────────── server.py ─────────────────────────
"""
Crawl4AI FastAPI entry‑point
• Browser pool + global page cap
• Rate‑limiting, security, metrics
• /crawl, /crawl/stream, /md, /llm endpoints
"""

# ── stdlib & 3rd‑party imports ───────────────────────────────
from crawler_pool import get_crawler, close_all, janitor
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LinkPreviewConfig
from auth import create_access_token, get_token_dependency, TokenRequest
from pydantic import BaseModel
from typing import Optional, List, Dict
from fastapi import Request, Depends
from fastapi.responses import FileResponse
import ast
import asyncio
import base64
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LinkPreviewConfig
from api import (
    handle_markdown_request, handle_llm_qa,
    handle_stream_crawl_request, handle_crawl_request,
    stream_results
)
from schemas import (
    CrawlRequestWithHooks,
    MarkdownRequest,
    RawCode,
    HTMLRequest,
    ScreenshotRequest,
    PDFRequest,
    JSEndpointRequest,
    LinkAnalysisRequest,
)

from utils import (
    FilterType, load_config, setup_logging, verify_email_domain
)
import os
import pathlib
import re
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from api import (
    handle_crawl_request,
    handle_llm_qa,
    handle_markdown_request,
    handle_seed,
    handle_stream_crawl_request,
    handle_url_discovery,
    stream_results,
)
from auth import TokenRequest, create_access_token, get_token_dependency
from crawler_pool import close_all, get_crawler, janitor
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from job import init_job_router
from mcp_bridge import attach_mcp, mcp_resource, mcp_template, mcp_tool
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi
from redis import asyncio as aioredis
from routers import adaptive, dispatchers, scripts
from schemas import (
    CrawlRequest,
    CrawlRequestWithHooks,
    HTMLRequest,
    JSEndpointRequest,
    MarkdownRequest,
    PDFRequest,
    RawCode,
    ScreenshotRequest,
    SeedRequest,
    URLDiscoveryRequest,
)
from slowapi import Limiter
from slowapi.util import get_remote_address
from utils import (
    FilterType, 
    load_config, 
    setup_logging, 
    verify_email_domain,
    create_dispatcher,
    DEFAULT_DISPATCHER_TYPE,
)

import crawl4ai as _c4
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_dispatcher import BaseDispatcher

# ── internal imports (after sys.path append) ─────────────────
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# ────────────────── configuration / logging ──────────────────
config = load_config()
setup_logging(config)

__version__ = "0.5.1-d1"

# ── global page semaphore (hard cap) ─────────────────────────
MAX_PAGES = config["crawler"]["pool"].get("max_pages", 30)
GLOBAL_SEM = asyncio.Semaphore(MAX_PAGES)

# import logging
# page_log = logging.getLogger("page_cap")
# orig_arun = AsyncWebCrawler.arun
# async def capped_arun(self, *a, **kw):
#     await GLOBAL_SEM.acquire()                        # ← take slot
#     try:
#         in_flight = MAX_PAGES - GLOBAL_SEM._value     # used permits
#         page_log.info("🕸️  pages_in_flight=%s / %s", in_flight, MAX_PAGES)
#         return await orig_arun(self, *a, **kw)
#     finally:
#         GLOBAL_SEM.release()                          # ← free slot

orig_arun = AsyncWebCrawler.arun


async def capped_arun(self, *a, **kw):
    async with GLOBAL_SEM:
        return await orig_arun(self, *a, **kw)


AsyncWebCrawler.arun = capped_arun

# ───────────────────── FastAPI lifespan ──────────────────────


@asynccontextmanager
async def lifespan(_: FastAPI):
    import logging
    logger = logging.getLogger(__name__)
    
    # Initialize crawler pool
    await get_crawler(
        BrowserConfig(
            extra_args=config["crawler"]["browser"].get("extra_args", []),
            **config["crawler"]["browser"].get("kwargs", {}),
        )
    )  # warm‑up
    
    # Initialize dispatchers
    try:
        app.state.dispatchers: Dict[str, BaseDispatcher] = {}
        app.state.default_dispatcher_type = DEFAULT_DISPATCHER_TYPE
        
        # Pre-create both dispatcher types
        app.state.dispatchers["memory_adaptive"] = create_dispatcher("memory_adaptive")
        app.state.dispatchers["semaphore"] = create_dispatcher("semaphore")
        
        logger.info(f"✓ Initialized dispatchers: {list(app.state.dispatchers.keys())}")
        logger.info(f"✓ Default dispatcher: {app.state.default_dispatcher_type}")
    except Exception as e:
        logger.error(f"✗ Failed to initialize dispatchers: {e}")
        raise
    
    # Start background tasks
    app.state.janitor = asyncio.create_task(janitor())  # idle GC
    
    yield
    
    # Cleanup
    app.state.janitor.cancel()
    app.state.dispatchers.clear()
    logger.info("✓ Dispatchers cleaned up")
    await close_all()


# ───────────────────── FastAPI instance ──────────────────────
app = FastAPI(
    title=config["app"]["title"],
    version=config["app"]["version"],
    lifespan=lifespan,
)

# ── static playground ──────────────────────────────────────
STATIC_DIR = pathlib.Path(__file__).parent / "static" / "playground"
if not STATIC_DIR.exists():
    raise RuntimeError(f"Playground assets not found at {STATIC_DIR}")
app.mount(
    "/playground",
    StaticFiles(directory=STATIC_DIR, html=True),
    name="play",
)


@app.get("/")
async def root():
    return RedirectResponse("/playground")


# ─────────────────── infra / middleware  ─────────────────────
redis = aioredis.from_url(config["redis"].get("uri", "redis://localhost"))

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[config["rate_limiting"]["default_limit"]],
    storage_uri=config["rate_limiting"]["storage_uri"],
)


def _setup_security(app_: FastAPI):
    sec = config["security"]
    if not sec["enabled"]:
        return
    if sec.get("https_redirect"):
        app_.add_middleware(HTTPSRedirectMiddleware)
    if sec.get("trusted_hosts", []) != ["*"]:
        app_.add_middleware(TrustedHostMiddleware, allowed_hosts=sec["trusted_hosts"])


_setup_security(app)

if config["observability"]["prometheus"]["enabled"]:
    Instrumentator().instrument(app).expose(app)

token_dep = get_token_dependency(config)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    resp = await call_next(request)
    if config["security"]["enabled"]:
        resp.headers.update(config["security"]["headers"])
    return resp


# ───────────────── safe config‑dump helper ─────────────────
ALLOWED_TYPES = {
    "CrawlerRunConfig": CrawlerRunConfig,
    "BrowserConfig": BrowserConfig,
}


def _safe_eval_config(expr: str) -> dict:
    """
    Accept exactly one top‑level call to CrawlerRunConfig(...) or BrowserConfig(...).
    Whatever is inside the parentheses is fine *except* further function calls
    (so no  __import__('os') stuff).  All public names from crawl4ai are available
    when we eval.
    """
    tree = ast.parse(expr, mode="eval")

    # must be a single call
    if not isinstance(tree.body, ast.Call):
        raise ValueError("Expression must be a single constructor call")

    call = tree.body
    if not (
        isinstance(call.func, ast.Name)
        and call.func.id in {"CrawlerRunConfig", "BrowserConfig"}
    ):
        raise ValueError("Only CrawlerRunConfig(...) or BrowserConfig(...) are allowed")

    # forbid nested calls to keep the surface tiny
    for node in ast.walk(call):
        if isinstance(node, ast.Call) and node is not call:
            raise ValueError("Nested function calls are not permitted")

    # expose everything that crawl4ai exports, nothing else
    safe_env = {
        name: getattr(_c4, name) for name in dir(_c4) if not name.startswith("_")
    }
    obj = eval(compile(tree, "<config>", "eval"), {"__builtins__": {}}, safe_env)
    return obj.dump()


# ── job router ──────────────────────────────────────────────
app.include_router(init_job_router(redis, config, token_dep))
app.include_router(adaptive.router)
app.include_router(dispatchers.router)
app.include_router(scripts.router)


# ──────────────────────── Endpoints ──────────────────────────
@app.post("/token", 
    summary="Get Authentication Token",
    description="Generate a JWT authentication token for API access using your email address.",
    response_description="JWT token with expiration time",
    tags=["Authentication"]
)
async def get_token(req: TokenRequest):
    """
    Generate an authentication token for API access.
    
    This endpoint creates a JWT token that must be included in the Authorization 
    header of subsequent requests. Tokens are valid for the duration specified 
    in server configuration (default: 60 minutes).
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "email": "user@example.com",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer"
    }
    ```
    
    **Usage:**
    ```python
    import requests
    
    response = requests.post(
        "http://localhost:11235/token",
        json={"email": "user@example.com"}
    )
    token = response.json()["access_token"]
    
    # Use token in subsequent requests
    headers = {"Authorization": f"Bearer {token}"}
    ```
    
    **Notes:**
    - Email domain must be in the allowed list (configurable via config.yml)
    - Tokens expire after configured duration
    - Store tokens securely and refresh before expiration
    """
    if not verify_email_domain(req.email):
        raise HTTPException(400, "Invalid email domain")
    token = create_access_token({"sub": req.email})
    return {"email": req.email, "access_token": token, "token_type": "bearer"}


@app.post("/config/dump",
    summary="Validate and Dump Configuration",
    description="Validate CrawlerRunConfig or BrowserConfig and return serialized version.",
    response_description="Serialized configuration dictionary",
    tags=["Utility"]
)
async def config_dump(raw: RawCode):
    """
    Validate and serialize crawler or browser configuration.
    
    This endpoint accepts Python code containing a CrawlerRunConfig or BrowserConfig
    constructor and returns the serialized configuration dict. Useful for validating
    configurations before use.
    
    **Example Request:**
    ```json
    {
        "code": "CrawlerRunConfig(word_count_threshold=10, screenshot=True)"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "word_count_threshold": 10,
        "screenshot": true,
        "wait_until": "networkidle",
        ...
    }
    ```
    
    **Security:**
    - Only CrawlerRunConfig() and BrowserConfig() constructors allowed
    - No nested function calls permitted
    - Prevents code injection attempts
    """
    try:
        return JSONResponse(_safe_eval_config(raw.code.strip()))
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/seed",
    summary="URL Discovery and Seeding",
    description="Discover and extract crawlable URLs from a website for subsequent crawling.",
    response_description="List of discovered URLs with count",
    tags=["Core Crawling"]
)
async def seed_url(request: SeedRequest):
    """
    Discover and seed URLs from a website.
    
    This endpoint crawls a starting URL and discovers all available links based on
    specified filters. Useful for finding URLs to crawl before running a full crawl.
    
    **Parameters:**
    - **url**: Starting URL to discover links from
    - **config**: Seeding configuration
      - **max_urls**: Maximum number of URLs to return (default: 100)
      - **filter_type**: Filter strategy for URLs
        - `all`: Include all discovered URLs
        - `domain`: Only URLs from same domain
        - `subdomain`: Only URLs from same subdomain
      - **exclude_external**: Exclude external links (default: false)
    
    **Example Request:**
    ```json
    {
        "url": "https://www.nbcnews.com",
        "config": {
            "max_urls": 20,
            "filter_type": "domain",
            "exclude_external": true
        }
    }
    ```
    
    **Example Response:**
    ```json
    {
        "seed_url": [
            "https://www.nbcnews.com/news/page1",
            "https://www.nbcnews.com/news/page2",
            "https://www.nbcnews.com/about"
        ],
        "count": 3
    }
    ```
    
    **Usage:**
    ```python
    response = requests.post(
        "http://localhost:11235/seed",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "url": "https://www.nbcnews.com",
            "config": {"max_urls": 20, "filter_type": "domain"}
        }
    )
    urls = response.json()["seed_url"]
    ```
    
    **Notes:**
    - Returns direct list of URLs in `seed_url` field (not nested dict)
    - Empty list returned if no URLs found
    - Respects robots.txt if configured
    """
    try:
        # Extract the domain (e.g., "docs.crawl4ai.com") from the full URL
        domain = urlparse(request.url).netloc
        if not domain:
            raise HTTPException(
                status_code=400,
                detail="Invalid URL provided. Could not extract domain.",
            )
        res = await handle_seed(request.url, request.config)
        return JSONResponse({"seed_url": res, "count": len(res)})

    except Exception as e:
        print(f"❌ Error in seed_url: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/urls/discover",
    summary="URL Discovery and Seeding",
    description="Discover and extract crawlable URLs from a domain using AsyncUrlSeeder functionality.",
    response_description="List of discovered URL objects with metadata",
    tags=["Core Crawling"]
)
async def discover_urls(request: URLDiscoveryRequest):
    """
    Discover URLs from a domain using AsyncUrlSeeder functionality.
    
    This endpoint allows users to find relevant URLs from a domain before 
    committing to a full crawl. It supports various discovery sources like 
    sitemaps and Common Crawl, with filtering and scoring capabilities.
    
    **Parameters:**
    - **domain**: Domain to discover URLs from (e.g., "example.com")
    - **seeding_config**: Configuration object mirroring SeedingConfig parameters
      - **source**: Discovery source(s) - "sitemap", "cc", or "sitemap+cc" (default: "sitemap+cc")
      - **pattern**: URL pattern filter using glob-style wildcards (default: "*")
      - **live_check**: Whether to verify URL liveness with HEAD requests (default: false)
      - **extract_head**: Whether to fetch and parse <head> metadata (default: false)
      - **max_urls**: Maximum URLs to discover, -1 for no limit (default: -1)
      - **concurrency**: Maximum concurrent requests (default: 1000)
      - **hits_per_sec**: Rate limit in requests per second (default: 5)
      - **force**: Bypass internal cache and re-fetch URLs (default: false)
      - **query**: Search query for BM25 relevance scoring (optional)
      - **scoring_method**: Scoring method when query provided (default: "bm25")
      - **score_threshold**: Minimum score threshold for filtering (optional)
      - **filter_nonsense_urls**: Filter out nonsense URLs (default: true)
    
    **Example Request:**
    ```json
    {
        "domain": "docs.crawl4ai.com",
        "seeding_config": {
            "source": "sitemap",
            "pattern": "*/docs/*",
            "extract_head": true,
            "max_urls": 50,
            "query": "API documentation"
        }
    }
    ```
    
    **Example Response:**
    ```json
    [
        {
            "url": "https://docs.crawl4ai.com/api/getting-started",
            "status": "valid",
            "head_data": {
                "title": "Getting Started - Crawl4AI API",
                "description": "Learn how to get started with Crawl4AI API"
            },
            "score": 0.85
        }
    ]
    ```
    
    **Usage:**
    ```python
    response = requests.post(
        "http://localhost:11235/urls/discover",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "domain": "docs.crawl4ai.com",
            "seeding_config": {
                "source": "sitemap+cc",
                "extract_head": true,
                "max_urls": 100
            }
        }
    )
    urls = response.json()
    ```
    
    **Notes:**
    - Returns direct list of URL objects with metadata if requested
    - Empty list returned if no URLs found
    - Supports BM25 relevance scoring when query is provided
    - Can combine multiple sources for maximum coverage
    """
    try:
        res = await handle_url_discovery(request.domain, request.seeding_config)
        return JSONResponse(res)

    except Exception as e:
        print(f"❌ Error in discover_urls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/md",
    summary="Extract Markdown",
    description="Extract clean markdown content from a URL or raw HTML.",
    response_description="Markdown content with metadata",
    tags=["Content Extraction"]
)
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("md")
async def get_markdown(
    request: Request,
    body: MarkdownRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Extract clean markdown content from a URL.
    
    This endpoint fetches a page and converts it to clean, readable markdown format.
    Useful for LLM processing, content analysis, or markdown export.
    
    **Request Body:**
    ```json
    {
        "url": "https://example.com",
        "f": "markdown",
        "q": "",
        "c": true,
        "provider": "openai",
        "temperature": 0.0
    }
    ```
    
    **Parameters:**
    - `url`: Target URL (or raw:// for raw HTML)
    - `f`: Output format ("markdown", "fit_markdown")
    - `q`: Query for filtered extraction
    - `c`: Enable caching (default: true)
    - `provider`: LLM provider for enhanced extraction
    - `temperature`: LLM temperature setting
    - `base_url`: Custom LLM API base URL
    
    **Response:**
    ```json
    {
        "url": "https://example.com",
        "markdown": "# Example Domain\\n\\nThis domain is for use...",
        "success": true,
        "filter": "markdown",
        "query": "",
        "cache": true
    }
    ```
    
    **Usage:**
    ```python
    response = requests.post(
        "http://localhost:11235/md",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "https://example.com"}
    )
    markdown = response.json()["markdown"]
    print(markdown)
    ```
    
    **Notes:**
    - Supports raw HTML input with `raw://` prefix
    - Returns clean, structured markdown
    - LLM-friendly format for AI processing
    - Caching improves performance for repeated requests
    """
    if not body.url.startswith(("http://", "https://")) and not body.url.startswith(
        ("raw:", "raw://")
    ):
        raise HTTPException(
            400,
            "Invalid URL format. Must start with http://, https://, or for raw HTML (raw:, raw://)",
        )
    markdown = await handle_markdown_request(
        body.url,
        body.f,
        body.q,
        body.c,
        config,
        body.provider,
        body.temperature,
        body.base_url,
    )
    return JSONResponse(
        {
            "url": body.url,
            "filter": body.f,
            "query": body.q,
            "cache": body.c,
            "markdown": markdown,
            "success": True,
        }
    )


@app.post("/html",
    summary="Extract Processed HTML",
    description="Crawl a URL and return preprocessed HTML suitable for schema extraction.",
    response_description="Processed HTML content",
    tags=["Content Extraction"]
)
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("html")
async def generate_html(
    request: Request,
    body: HTMLRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Crawl a URL and return sanitized, preprocessed HTML.
    
    This endpoint crawls a page and returns processed HTML that's been cleaned
    and prepared for schema extraction or further processing. The HTML is
    sanitized to remove scripts, styles, and other non-content elements.
    
    **Request Body:**
    ```json
    {
        "url": "https://example.com"
    }
    ```
    
    **Response:**
    ```json
    {
        "url": "https://example.com",
        "html": "<html><body><h1>Example Domain</h1>...</body></html>",
        "success": true
    }
    ```
    
    **Usage:**
    ```python
    response = requests.post(
        "http://localhost:11235/html",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "https://example.com"}
    )
    html = response.json()["html"]
    ```
    
    **Notes:**
    - HTML is preprocessed for schema extraction
    - Scripts, styles, and non-content elements removed
    - Preserves semantic structure
    - Useful for building data extraction schemas
    """
    cfg = CrawlerRunConfig()
    try:
        async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        # Check if the crawl was successful
        if not results[0].success:
            raise HTTPException(
                status_code=500, detail=results[0].error_message or "Crawl failed"
            )

        raw_html = results[0].html
        from crawl4ai.utils import preprocess_html_for_schema

        processed_html = preprocess_html_for_schema(raw_html)
        return JSONResponse({"html": processed_html, "url": body.url, "success": True})
    except Exception as e:
        # Log and raise as HTTP 500 for other exceptions
        raise HTTPException(status_code=500, detail=str(e))


# Screenshot endpoint


@app.post("/screenshot",
    summary="Capture Screenshot",
    description="Capture a full-page PNG screenshot of a URL.",
    response_description="Screenshot data (base64 or file path)",
    tags=["Content Extraction"]
)
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("screenshot")
async def generate_screenshot(
    request: Request,
    body: ScreenshotRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Capture a full-page PNG screenshot of a URL.
    
    This endpoint navigates to a URL and captures a full-page screenshot.
    Optionally wait for page content to load before capturing.
    
    **Request Body:**
    ```json
    {
        "url": "https://example.com",
        "screenshot_wait_for": 2.0,
        "output_path": "/path/to/screenshot.png"
    }
    ```
    
    **Parameters:**
    - `url`: Target URL to screenshot
    - `screenshot_wait_for`: Seconds to wait before capture (default: 0)
    - `output_path`: Optional path to save screenshot file
    
    **Response (with output_path):**
    ```json
    {
        "url": "https://example.com",
        "screenshot": "/absolute/path/to/screenshot.png",
        "success": true
    }
    ```
    
    **Response (without output_path):**
    ```json
    {
        "url": "https://example.com",
        "screenshot": "iVBORw0KGgoAAAANS...",
        "success": true
    }
    ```
    
    **Usage:**
    ```python
    # Save to file
    response = requests.post(
        "http://localhost:11235/screenshot",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "url": "https://example.com",
            "output_path": "./screenshot.png"
        }
    )
    print(response.json()["screenshot"])  # File path
    
    # Get base64 data
    response = requests.post(
        "http://localhost:11235/screenshot",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "https://example.com"}
    )
    import base64
    screenshot_data = base64.b64decode(response.json()["screenshot"])
    with open("screenshot.png", "wb") as f:
        f.write(screenshot_data)
    ```
    
    **Notes:**
    - Captures full page (scrolls to bottom)
    - Returns base64 PNG data if no output_path specified
    - Saves to file and returns path if output_path provided
    - Wait time helps ensure dynamic content is loaded
    """
    try:
        cfg = CrawlerRunConfig(
            screenshot=True, screenshot_wait_for=body.screenshot_wait_for
        )
        async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        if not results[0].success:
            raise HTTPException(
                status_code=500, detail=results[0].error_message or "Crawl failed"
            )
        screenshot_data = results[0].screenshot
        if body.output_path:
            abs_path = os.path.abspath(body.output_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "wb") as f:
                f.write(base64.b64decode(screenshot_data))
            return {"success": True, "path": abs_path}
        return {"success": True, "screenshot": screenshot_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PDF endpoint


@app.post("/pdf",
    summary="Generate PDF",
    description="Generate a PDF document from a URL.",
    response_description="PDF data (base64 or file path)",
    tags=["Content Extraction"]
)
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("pdf")
async def generate_pdf(
    request: Request,
    body: PDFRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Generate a PDF document from a URL.
    
    This endpoint navigates to a URL and generates a PDF document of the page.
    Useful for archiving, printing, or offline viewing.
    
    **Request Body:**
    ```json
    {
        "url": "https://example.com",
        "output_path": "/path/to/document.pdf"
    }
    ```
    
    **Parameters:**
    - `url`: Target URL to convert to PDF
    - `output_path`: Optional path to save PDF file
    
    **Response (with output_path):**
    ```json
    {
        "success": true,
        "path": "/absolute/path/to/document.pdf"
    }
    ```
    
    **Response (without output_path):**
    ```json
    {
        "success": true,
        "pdf": "JVBERi0xLjQKJeLjz9MKMy..."
    }
    ```
    
    **Usage:**
    ```python
    # Save to file
    response = requests.post(
        "http://localhost:11235/pdf",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "url": "https://example.com",
            "output_path": "./document.pdf"
        }
    )
    print(response.json()["path"])
    
    # Get base64 data
    response = requests.post(
        "http://localhost:11235/pdf",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "https://example.com"}
    )
    import base64
    pdf_data = base64.b64decode(response.json()["pdf"])
    with open("document.pdf", "wb") as f:
        f.write(pdf_data)
    ```
    
    **Notes:**
    - Generates printable PDF format
    - Returns base64 PDF data if no output_path specified
    - Saves to file and returns path if output_path provided
    - Preserves page layout and styling
    """
    try:
        cfg = CrawlerRunConfig(pdf=True)
        async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        if not results[0].success:
            raise HTTPException(
                status_code=500, detail=results[0].error_message or "Crawl failed"
            )
        pdf_data = results[0].pdf
        if body.output_path:
            abs_path = os.path.abspath(body.output_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "wb") as f:
                f.write(pdf_data)
            return {"success": True, "path": abs_path}
        return {"success": True, "pdf": base64.b64encode(pdf_data).decode()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute_js",
    summary="Execute JavaScript",
    description="Execute JavaScript code on a page and return the full crawl result.",
    response_description="Complete CrawlResult with JS execution results",
    tags=["Advanced"]
)
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("execute_js")
async def execute_js(
    request: Request,
    body: JSEndpointRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Execute JavaScript code on a page and return the complete crawl result.
    
    This endpoint navigates to a URL and executes custom JavaScript code in the
    browser context. Each script must be an expression that returns a value.
    
    **Request Body:**
    ```json
    {
        "url": "https://example.com",
        "scripts": [
            "document.title",
            "(async () => { await new Promise(r => setTimeout(r, 1000)); return document.body.innerText; })()"
        ],
        "wait_for": "css:.content"
    }
    ```
    
    **Parameters:**
    - `url`: Target URL to execute scripts on
    - `scripts`: List of JavaScript expressions to execute in order
    - `wait_for`: Optional selector or condition to wait for
    
    **Script Format:**
    Each script should be an expression that returns a value:
    - Simple expression: `"document.title"`
    - IIFE: `"(() => { return window.location.href; })()"`
    - Async IIFE: `"(async () => { await fetch('/api'); return 'done'; })()"`
    
    **Response:**
    Returns complete CrawlResult with:
    ```json
    {
        "url": "https://example.com",
        "html": "<html>...",
        "markdown": "# Page Content...",
        "js_execution_result": {
            "0": "Example Domain",
            "1": "This domain is for use in..."
        },
        "links": {...},
        "media": {...},
        "success": true
    }
    ```
    
    **Usage:**
    ```python
    response = requests.post(
        "http://localhost:11235/execute_js",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "url": "https://example.com",
            "scripts": [
                "document.title",
                "document.querySelectorAll('p').length"
            ]
        }
    )
    result = response.json()
    print(result["js_execution_result"])  # {"0": "Example Domain", "1": 2}
    print(result["markdown"])  # Full markdown content
    ```
    
    **Notes:**
    - Scripts execute in order
    - Each script must return a value
    - Returns full CrawlResult (no need to call other endpoints)
    - Use for dynamic content, button clicks, form submissions
    - Access results via js_execution_result dictionary (indexed by position)
    
    **Return Format:**
    The return result is an instance of CrawlResult, so you have access to markdown, links, and other stuff. If this is enough, you don't need to call again for other endpoints.

        ```python
        class CrawlResult(BaseModel):
            url: str
            html: str
            success: bool
            cleaned_html: Optional[str] = None
            media: Dict[str, List[Dict]] = {}
            links: Dict[str, List[Dict]] = {}
            downloaded_files: Optional[List[str]] = None
            js_execution_result: Optional[Dict[str, Any]] = None
            screenshot: Optional[str] = None
            pdf: Optional[bytes] = None
            mhtml: Optional[str] = None
            _markdown: Optional[MarkdownGenerationResult] = PrivateAttr(default=None)
            extracted_content: Optional[str] = None
            metadata: Optional[dict] = None
            error_message: Optional[str] = None
            session_id: Optional[str] = None
            response_headers: Optional[dict] = None
            status_code: Optional[int] = None
            ssl_certificate: Optional[SSLCertificate] = None
            dispatch_result: Optional[DispatchResult] = None
            redirected_url: Optional[str] = None
            network_requests: Optional[List[Dict[str, Any]]] = None
            console_messages: Optional[List[Dict[str, Any]]] = None

        class MarkdownGenerationResult(BaseModel):
            raw_markdown: str
            markdown_with_citations: str
            references_markdown: str
            fit_markdown: Optional[str] = None
            fit_html: Optional[str] = None
        ```

    """
    try:
        cfg = CrawlerRunConfig(js_code=body.scripts)
        async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        if not results[0].success:
            raise HTTPException(
                status_code=500, detail=results[0].error_message or "Crawl failed"
            )
        # Return JSON-serializable dict of the first CrawlResult
        data = results[0].model_dump()
        return JSONResponse(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/links/analyze")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("links_analyze")
async def analyze_links(
    request: Request,
    body: LinkAnalysisRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Analyze and score links on a webpage.
    Returns a dictionary of links with their scores and metadata.
    """
    try:
        # Create AsyncWebCrawler instance
        async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
            # Deserialize config dict to LinkPreviewConfig, use default if not provided
            link_preview_config = LinkPreviewConfig.from_dict(body.config) if body.config else LinkPreviewConfig()

            # Create CrawlerRunConfig with link analysis settings
            run_config = CrawlerRunConfig(
                link_preview_config=link_preview_config,
                score_links=True,
                screenshot=False,
                pdf=False,
                extraction_strategy=None
            )

            # Execute the crawl
            result = await crawler.arun(url=body.url, config=run_config)

            # Check if crawl was successful
            if not result.success:
                raise HTTPException(
                    status_code=500,
                    detail=result.error_message or "Crawl failed"
                )

            # Extract and return the links dictionary
            return JSONResponse(result.links)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/llm/{url:path}",
    summary="LLM Q&A",
    description="Ask questions about a webpage using LLM.",
    response_description="Answer from LLM based on page content",
    tags=["Advanced"]
)
async def llm_endpoint(
    request: Request,
    url: str = Path(..., description="URL to analyze (can omit https://)"),
    q: str = Query(..., description="Question to ask about the page"),
    _td: Dict = Depends(token_dep),
):
    """
    Ask questions about a webpage using an LLM.
    
    This endpoint crawls a page and uses an LLM to answer questions about
    the content. Useful for extracting specific information or insights.
    
    **Request:**
    ```
    GET /llm/example.com?q=What is this page about?
    ```
    
    **Parameters:**
    - `url`: Target URL (path parameter, https:// is optional)
    - `q`: Question to ask (query parameter)
    
    **Response:**
    ```json
    {
        "answer": "This page is the official documentation for Example Domain..."
    }
    ```
    
    **Usage:**
    ```python
    import requests
    from urllib.parse import quote
    
    url = "example.com"
    question = "What is this page about?"
    
    response = requests.get(
        f"http://localhost:11235/llm/{url}?q={quote(question)}",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(response.json()["answer"])
    ```
    
    ```bash
    curl "http://localhost:11235/llm/example.com?q=What%20is%20this%20page%20about?" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    
    **Notes:**
    - Automatically crawls the page and extracts content
    - Uses configured LLM to generate answers
    - URL can omit https:// prefix
    - URL-encode the query parameter
    - Supports raw:// prefix for raw HTML
    """
    if not q:
        raise HTTPException(400, "Query parameter 'q' is required")
    if not url.startswith(("http://", "https://")) and not url.startswith(
        ("raw:", "raw://")
    ):
        url = "https://" + url
    answer = await handle_llm_qa(url, q, config)
    return JSONResponse({"answer": answer})


@app.get("/schema",
    summary="Get Configuration Schemas",
    description="Get JSON schemas for BrowserConfig and CrawlerRunConfig.",
    response_description="Configuration schemas",
    tags=["Utility"]
)
async def get_schema():
    """
    Get JSON schemas for configuration objects.
    
    Returns the complete schemas for BrowserConfig and CrawlerRunConfig,
    showing all available configuration options and their types.
    
    **Response:**
    ```json
    {
        "browser": {
            "type": "object",
            "properties": {
                "headless": {"type": "boolean", "default": true},
                "verbose": {"type": "boolean", "default": false},
                ...
            }
        },
        "crawler": {
            "type": "object",
            "properties": {
                "word_count_threshold": {"type": "integer", "default": 10},
                "wait_for": {"type": "string"},
                ...
            }
        }
    }
    ```
    
    **Usage:**
    ```python
    response = requests.get(
        "http://localhost:11235/schema",
        headers={"Authorization": f"Bearer {token}"}
    )
    schemas = response.json()
    print(schemas["browser"])  # BrowserConfig schema
    print(schemas["crawler"])  # CrawlerRunConfig schema
    ```
    
    **Notes:**
    - No authentication required
    - Shows all available configuration options
    - Includes default values and types
    - Useful for building configuration UIs
    """
    from crawl4ai import BrowserConfig, CrawlerRunConfig

    return {"browser": BrowserConfig().dump(), "crawler": CrawlerRunConfig().dump()}


@app.get("/hooks/info")
async def get_hooks_info():
    """Get information about available hook points and their signatures"""
    from hook_manager import UserHookManager

    hook_info = {}
    for hook_point, params in UserHookManager.HOOK_SIGNATURES.items():
        hook_info[hook_point] = {
            "parameters": params,
            "description": get_hook_description(hook_point),
            "example": get_hook_example(hook_point),
        }

    return JSONResponse(
        {
            "available_hooks": hook_info,
            "timeout_limits": {"min": 1, "max": 120, "default": 30},
        }
    )


def get_hook_description(hook_point: str) -> str:
    """Get description for each hook point"""
    descriptions = {
        "on_browser_created": "Called after browser instance is created",
        "on_page_context_created": "Called after page and context are created - ideal for authentication",
        "before_goto": "Called before navigating to the target URL",
        "after_goto": "Called after navigation is complete",
        "on_user_agent_updated": "Called when user agent is updated",
        "on_execution_started": "Called when custom JavaScript execution begins",
        "before_retrieve_html": "Called before retrieving the final HTML - ideal for scrolling",
        "before_return_html": "Called just before returning the HTML content",
    }
    return descriptions.get(hook_point, "")


def get_hook_example(hook_point: str) -> str:
    """Get example code for each hook point"""
    examples = {
        "on_page_context_created": """async def hook(page, context, **kwargs):
    # Add authentication cookie
    await context.add_cookies([{
        'name': 'session',
        'value': 'my-session-id',
        'domain': '.example.com'
    }])
    return page""",
        "before_retrieve_html": """async def hook(page, context, **kwargs):
    # Scroll to load lazy content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(2000)
    return page""",
        "before_goto": """async def hook(page, context, url, **kwargs):
    # Set custom headers
    await page.set_extra_http_headers({
        'X-Custom-Header': 'value'
    })
    return page""",
    }
    return examples.get(hook_point, "# Implement your hook logic here\nreturn page")


@app.get(config["observability"]["health_check"]["endpoint"],
    summary="Health Check",
    description="Check if the API server is running and healthy.",
    response_description="Health status with timestamp and version",
    tags=["Utility"]
)
async def health():
    """
    Health check endpoint.
    
    Returns the current health status of the API server, including
    timestamp and version information.
    
    **Response:**
    ```json
    {
        "status": "ok",
        "timestamp": 1704067200.0,
        "version": "0.4.0"
    }
    ```
    
    **Usage:**
    ```python
    response = requests.get("http://localhost:11235/health")
    print(response.json())
    ```
    
    ```bash
    curl http://localhost:11235/health
    ```
    
    **Notes:**
    - No authentication required
    - Returns 200 OK if server is healthy
    - Use for monitoring and load balancer checks
    """
    return {"status": "ok", "timestamp": time.time(), "version": __version__}


@app.get(config["observability"]["prometheus"]["endpoint"],
    summary="Prometheus Metrics",
    description="Get Prometheus-formatted metrics for monitoring.",
    response_description="Prometheus metrics",
    tags=["Utility"]
)
async def metrics():
    """
    Get Prometheus metrics.
    
    Returns Prometheus-formatted metrics for monitoring API performance,
    including request counts, latencies, and error rates.
    
    **Response:**
    ```
    # HELP http_requests_total Total HTTP requests
    # TYPE http_requests_total counter
    http_requests_total{method="POST",path="/crawl",status="200"} 42
    
    # HELP http_request_duration_seconds HTTP request latency
    # TYPE http_request_duration_seconds histogram
    http_request_duration_seconds_bucket{le="0.5"} 38
    ...
    ```
    
    **Usage:**
    ```python
    response = requests.get("http://localhost:11235/metrics")
    print(response.text)
    ```
    
    ```bash
    curl http://localhost:11235/metrics
    ```
    
    **Notes:**
    - No authentication required
    - Returns metrics in Prometheus exposition format
    - Configure Prometheus to scrape this endpoint
    - Includes request counts, latencies, and errors
    """
    return RedirectResponse(config["observability"]["prometheus"]["endpoint"])


@app.post("/crawl",
    summary="Crawl URLs",
    description="Main endpoint for crawling one or more URLs and extracting content.",
    response_description="Crawl results with extracted content, metadata, and media",
    tags=["Core Crawling"]
)
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("crawl")
async def crawl(
    request: Request,
    crawl_request: CrawlRequest | CrawlRequestWithHooks,
    _td: Dict = Depends(token_dep),
):
    """
    Crawl one or more URLs and extract content.
    
    This is the main crawling endpoint that fetches pages, extracts content, and returns
    structured data including HTML, markdown, links, media, and metadata.
    
    **Request Body:**
    ```json
    {
        "urls": ["https://example.com"],
        "browser_config": {
            "headless": true,
            "viewport_width": 1920,
            "viewport_height": 1080
        },
        "crawler_config": {
            "word_count_threshold": 10,
            "wait_until": "networkidle",
            "screenshot": true,
            "pdf": false
        },
        "dispatcher": "memory_adaptive",
        "anti_bot_strategy": "stealth",
        "proxy_rotation_strategy": "round_robin",
        "proxies": ["http://proxy1:8080"]
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "results": [
            {
                "url": "https://example.com",
                "html": "<html>...</html>",
                "markdown": "# Example Domain\\n\\nThis domain is...",
                "cleaned_html": "<div>...</div>",
                "screenshot": "base64_encoded_image",
                "success": true,
                "status_code": 200,
                "metadata": {
                    "title": "Example Domain",
                    "description": "Example description"
                },
                "links": {
                    "internal": ["https://example.com/about"],
                    "external": ["https://other.com"]
                },
                "media": {
                    "images": [{"src": "image.jpg", "alt": "Image"}]
                }
            }
        ]
    }
    ```
    
    **Configuration Options:**
    
    *Browser Config:*
    - `headless`: Run browser in headless mode (default: true)
    - `viewport_width`: Browser width in pixels (default: 1920)
    - `viewport_height`: Browser height in pixels (default: 1080)
    - `user_agent`: Custom user agent string
    - `java_script_enabled`: Enable JavaScript (default: true)
    
    *Crawler Config:*
    - `word_count_threshold`: Minimum words per content block (default: 10)
    - `wait_until`: Page load strategy ("networkidle", "domcontentloaded", "load")
    - `wait_for`: CSS selector to wait for before extraction
    - `screenshot`: Capture page screenshot (base64 encoded)
    - `pdf`: Generate PDF export
    - `remove_overlay_elements`: Remove popups/modals automatically
    - `css_selector`: Extract only specific elements
    - `js_code`: Execute custom JavaScript before extraction
    
    *Dispatcher Options:*
    - `memory_adaptive`: Dynamic concurrency based on memory usage (recommended)
    - `semaphore`: Fixed concurrency limit
    
    *Anti-Bot Strategies:*
    - `stealth`: Basic stealth mode
    - `undetected`: Maximum evasion techniques
    
    *Proxy Rotation:*
    - `round_robin`: Sequential proxy rotation
    - `random`: Random proxy selection
    
    **Usage Examples:**
    
    ```python
    import requests
    
    response = requests.post(
        "http://localhost:11235/crawl",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "urls": ["https://example.com"],
            "browser_config": {"headless": True},
            "crawler_config": {"screenshot": True},
            "dispatcher": "memory_adaptive"
        }
    )
    
    data = response.json()
    if data["success"]:
        result = data["results"][0]
        print(f"Title: {result['metadata']['title']}")
        print(f"Content: {result['markdown'][:200]}...")
    ```
    
    **Notes:**
    - For streaming responses with real-time progress, use `/crawl/stream`
    - Set `stream: true` in crawler_config to auto-redirect to streaming endpoint
    - All URLs must start with http:// or https://
    - Rate limiting applies (default: 100 requests/minute)
    - Supports custom hooks for advanced processing
    """
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")
    # Check whether it is a redirection for a streaming request
    crawler_config = CrawlerRunConfig.load(crawl_request.crawler_config)
    if crawler_config.stream:
        return await stream_process(crawl_request=crawl_request)

    # Prepare hooks config if provided
    hooks_config = None
    if hasattr(crawl_request, 'hooks') and crawl_request.hooks:
        hooks_config = {
            "code": crawl_request.hooks.code,
            "timeout": crawl_request.hooks.timeout,
        }

    # Get dispatcher from app state
    dispatcher_type = crawl_request.dispatcher.value if crawl_request.dispatcher else app.state.default_dispatcher_type
    dispatcher = app.state.dispatchers.get(dispatcher_type)
    
    if not dispatcher:
        raise HTTPException(
            500, 
            f"Dispatcher '{dispatcher_type}' not available. Available dispatchers: {list(app.state.dispatchers.keys())}"
        )
    
    results = await handle_crawl_request(
        urls=crawl_request.urls,
        browser_config=crawl_request.browser_config,
        crawler_config=crawl_request.crawler_config,
        config=config,
        hooks_config=hooks_config,
        anti_bot_strategy=crawl_request.anti_bot_strategy,
        headless=crawl_request.headless,
        proxy_rotation_strategy=crawl_request.proxy_rotation_strategy,
        proxies=crawl_request.proxies,
        proxy_failure_threshold=crawl_request.proxy_failure_threshold,
        proxy_recovery_time=crawl_request.proxy_recovery_time,
        dispatcher=dispatcher,
    )
    # check if all of the results are not successful
    if all(not result["success"] for result in results["results"]):
        raise HTTPException(
            500, f"Crawl request failed: {results['results'][0]['error_message']}"
        )
    return JSONResponse(results)


@app.post("/crawl/stream",
    summary="Crawl URLs with Streaming",
    description="Stream crawl progress in real-time using Server-Sent Events (SSE).",
    response_description="Server-Sent Events stream with progress updates and results",
    tags=["Core Crawling"]
)
@limiter.limit(config["rate_limiting"]["default_limit"])
async def crawl_stream(
    request: Request,
    crawl_request: CrawlRequestWithHooks,
    _td: Dict = Depends(token_dep),
):
    """
    Crawl URLs with real-time streaming progress updates.
    
    This endpoint returns Server-Sent Events (SSE) stream with real-time updates
    about crawl progress, allowing you to monitor long-running crawl operations.
    
    **Request Body:**
    Same as `/crawl` endpoint.
    
    **Response Stream:**
    Server-Sent Events with the following event types:
    
    ```
    data: {"type": "progress", "url": "https://example.com", "status": "started"}
    
    data: {"type": "progress", "url": "https://example.com", "status": "fetching"}
    
    data: {"type": "result", "url": "https://example.com", "data": {...}}
    
    data: {"type": "complete", "success": true, "total_urls": 1}
    ```
    
    **Event Types:**
    - `progress`: Crawl progress updates
    - `result`: Individual URL result
    - `complete`: All URLs processed
    - `error`: Error occurred
    
    **Usage Examples:**
    
    *Python with requests:*
    ```python
    import requests
    import json
    
    response = requests.post(
        "http://localhost:11235/crawl/stream",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"urls": ["https://example.com"]},
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print(f"Event: {data.get('type')} - {data}")
                
                if data['type'] == 'complete':
                    break
    ```
    
    *JavaScript with EventSource:*
    ```javascript
    const eventSource = new EventSource('http://localhost:11235/crawl/stream');
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress:', data);
        
        if (data.type === 'result') {
            console.log('Got result for:', data.url);
        }
        
        if (data.type === 'complete') {
            eventSource.close();
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('Stream error:', error);
        eventSource.close();
    };
    ```
    
    **Benefits:**
    - Real-time progress monitoring
    - Immediate feedback on each URL
    - Better for long-running operations
    - Can process results as they arrive
    
    **Notes:**
    - Response uses `text/event-stream` content type
    - Keep connection alive to receive all events
    - Connection automatically closes after completion
    - Use `/crawl` for simple batch operations without streaming
    """
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")

    return await stream_process(crawl_request=crawl_request)


async def stream_process(crawl_request: CrawlRequestWithHooks):
    # Prepare hooks config if provided
    hooks_config = None
    if hasattr(crawl_request, 'hooks') and crawl_request.hooks:
        hooks_config = {
            "code": crawl_request.hooks.code,
            "timeout": crawl_request.hooks.timeout,
        }

    # Get dispatcher from app state
    dispatcher_type = crawl_request.dispatcher.value if crawl_request.dispatcher else app.state.default_dispatcher_type
    dispatcher = app.state.dispatchers.get(dispatcher_type)
    
    if not dispatcher:
        raise HTTPException(
            500, 
            f"Dispatcher '{dispatcher_type}' not available. Available dispatchers: {list(app.state.dispatchers.keys())}"
        )

    crawler, gen, hooks_info = await handle_stream_crawl_request(
        urls=crawl_request.urls,
        browser_config=crawl_request.browser_config,
        crawler_config=crawl_request.crawler_config,
        config=config,
        hooks_config=hooks_config,
        anti_bot_strategy=crawl_request.anti_bot_strategy,
        headless=crawl_request.headless,
        proxy_rotation_strategy=crawl_request.proxy_rotation_strategy,
        proxies=crawl_request.proxies,
        proxy_failure_threshold=crawl_request.proxy_failure_threshold,
        proxy_recovery_time=crawl_request.proxy_recovery_time,
        dispatcher=dispatcher,
    )

    # Add hooks info to response headers if available
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Stream-Status": "active",
    }
    if hooks_info:
        import json

        headers["X-Hooks-Status"] = json.dumps(hooks_info["status"]["status"])

    return StreamingResponse(
        stream_results(crawler, gen),
        media_type="application/x-ndjson",
        headers=headers,
    )


def chunk_code_functions(code_md: str) -> List[str]:
    """Extract each function/class from markdown code blocks per file."""
    pattern = re.compile(
        # match "## File: <path>" then a ```py fence, then capture until the closing ```
        r"##\s*File:\s*(?P<path>.+?)\s*?\r?\n"  # file header
        r"```py\s*?\r?\n"  # opening fence
        r"(?P<code>.*?)(?=\r?\n```)",  # code block
        re.DOTALL,
    )
    chunks: List[str] = []
    for m in pattern.finditer(code_md):
        file_path = m.group("path").strip()
        code_blk = m.group("code")
        tree = ast.parse(code_blk)
        lines = code_blk.splitlines()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = node.lineno - 1
                end = getattr(node, "end_lineno", start + 1)
                snippet = "\n".join(lines[start:end])
                chunks.append(f"# File: {file_path}\n{snippet}")
    return chunks


def chunk_doc_sections(doc: str) -> List[str]:
    lines = doc.splitlines(keepends=True)
    sections = []
    current: List[str] = []
    for line in lines:
        if re.match(r"^#{1,6}\s", line):
            if current:
                sections.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("".join(current))
    return sections


@app.get("/ask")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("ask")
async def get_context(
    request: Request,
    _td: Dict = Depends(token_dep),
    context_type: str = Query("all", regex="^(code|doc|all)$"),
    query: Optional[str] = Query(None, description="search query to filter chunks"),
    score_ratio: float = Query(
        0.5, ge=0.0, le=1.0, description="min score as fraction of max_score"
    ),
    max_results: int = Query(20, ge=1, description="absolute cap on returned chunks"),
):
    """
    This end point is design for any questions about Crawl4ai library. It returns a plain text markdown with extensive information about Crawl4ai.
    You can use this as a context for any AI assistant. Use this endpoint for AI assistants to retrieve library context for decision making or code generation tasks.
    Alway is BEST practice you provide a query to filter the context. Otherwise the lenght of the response will be very long.

    Parameters:
    - context_type: Specify "code" for code context, "doc" for documentation context, or "all" for both.
    - query: RECOMMENDED search query to filter paragraphs using BM25. You can leave this empty to get all the context.
    - score_ratio: Minimum score as a fraction of the maximum score for filtering results.
    - max_results: Maximum number of results to return. Default is 20.

    Returns:
    - JSON response with the requested context.
    - If "code" is specified, returns the code context.
    - If "doc" is specified, returns the documentation context.
    - If "all" is specified, returns both code and documentation contexts.
    """
    # load contexts
    base = os.path.dirname(__file__)
    code_path = os.path.join(base, "c4ai-code-context.md")
    doc_path = os.path.join(base, "c4ai-doc-context.md")
    if not os.path.exists(code_path) or not os.path.exists(doc_path):
        raise HTTPException(404, "Context files not found")

    with open(code_path, "r") as f:
        code_content = f.read()
    with open(doc_path, "r") as f:
        doc_content = f.read()

    # if no query, just return raw contexts
    if not query:
        if context_type == "code":
            return JSONResponse({"code_context": code_content})
        if context_type == "doc":
            return JSONResponse({"doc_context": doc_content})
        return JSONResponse(
            {
                "code_context": code_content,
                "doc_context": doc_content,
            }
        )

    tokens = query.split()
    results: Dict[str, List[Dict[str, float]]] = {}

    # code BM25 over functions/classes
    if context_type in ("code", "all"):
        code_chunks = chunk_code_functions(code_content)
        bm25 = BM25Okapi([c.split() for c in code_chunks])
        scores = bm25.get_scores(tokens)
        max_sc = float(scores.max()) if scores.size > 0 else 0.0
        cutoff = max_sc * score_ratio
        picked = [(c, s) for c, s in zip(code_chunks, scores) if s >= cutoff]
        picked = sorted(picked, key=lambda x: x[1], reverse=True)[:max_results]
        results["code_results"] = [{"text": c, "score": s} for c, s in picked]

    # doc BM25 over markdown sections
    if context_type in ("doc", "all"):
        sections = chunk_doc_sections(doc_content)
        bm25d = BM25Okapi([sec.split() for sec in sections])
        scores_d = bm25d.get_scores(tokens)
        max_sd = float(scores_d.max()) if scores_d.size > 0 else 0.0
        cutoff_d = max_sd * score_ratio
        idxs = [i for i, s in enumerate(scores_d) if s >= cutoff_d]
        neighbors = set(i for idx in idxs for i in (idx - 1, idx, idx + 1))
        valid = [i for i in sorted(neighbors) if 0 <= i < len(sections)]
        valid = valid[:max_results]
        results["doc_results"] = [
            {"text": sections[i], "score": scores_d[i]} for i in valid
        ]

    return JSONResponse(results)


# attach MCP layer (adds /mcp/ws, /mcp/sse, /mcp/schema)
print(f"MCP server running on {config['app']['host']}:{config['app']['port']}")
attach_mcp(app, base_url=f"http://{config['app']['host']}:{config['app']['port']}")

# ────────────────────────── cli ──────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host=config["app"]["host"],
        port=config["app"]["port"],
        reload=config["app"]["reload"],
        timeout_keep_alive=config["app"]["timeout_keep_alive"],
    )
# ─────────────────────────────────────────────────────────────
