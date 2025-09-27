# ───────────────────────── server.py ─────────────────────────
"""
Crawl4AI FastAPI entry‑point
• Browser pool + global page cap
• Rate‑limiting, security, metrics
• /crawl, /crawl/stream, /md, /llm endpoints
"""

# ── stdlib & 3rd‑party imports ───────────────────────────────
import asyncio
import ast
import base64
import inspect
import logging
import os
import pathlib
import re
import sys
import time
import urllib.parse
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

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
from prometheus_fastapi_instrumentator import Instrumentator
from rank_bm25 import BM25Okapi
from redis import asyncio as aioredis
from slowapi import Limiter
from slowapi.util import get_remote_address

from api import (
    handle_crawl_request,
    handle_llm_qa,
    handle_markdown_request,
    handle_stream_crawl_request,
    stream_results,
)
from auth import TokenRequest, create_access_token, get_token_dependency
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
import crawl4ai as _c4
from crawler_pool import close_all, get_crawler, janitor
from job import init_job_router
from mcp_bridge import combine_lifespans, create_mcp_server, mcp_resource, mcp_template, mcp_tool
from schemas import (
    CrawlRequest,
    HTMLRequest,
    JSEndpointRequest,
    MarkdownRequest,
    PDFRequest,
    RawCode,
    ScreenshotRequest,
)
from utils import FilterType, load_config, setup_logging, verify_email_domain, _ensure_within_base_dir
from pydantic import BaseModel, Field

# ── internal imports (after sys.path append) ─────────────────
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# ────────────────── configuration / logging ──────────────────
config = load_config()
setup_logging(config)

__version__ = "0.7.4"

# ── global page semaphore (hard cap) ─────────────────────────
MAX_PAGES = config["crawler"]["pool"].get("max_pages", 30)
GLOBAL_SEM = asyncio.Semaphore(MAX_PAGES)
INLINE_BINARY_MAX_BYTES = 16 * 1024  # ~16KB (~21k base64 chars ≈ <25k tokens)
INLINE_BINARY_MAX_BASE64_CHARS = INLINE_BINARY_MAX_BYTES * 4 // 3

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

# ───────────────────── MCP & FastAPI setup ──────────────────────

# Create empty MCP server first (tools will be registered after routes exist)
from fastmcp import FastMCP
mcp_server = FastMCP(name=config["app"]["title"])
mcp_app = mcp_server.http_app(path="/mcp")

# Define existing crawler lifespan
@asynccontextmanager
async def crawler_lifespan(app: FastAPI):
    await get_crawler(BrowserConfig(
        extra_args=config["crawler"]["browser"].get("extra_args", []),
        **config["crawler"]["browser"].get("kwargs", {}),
    ))           # warm‑up
    app.state.janitor = asyncio.create_task(janitor())        # idle GC
    yield
    app.state.janitor.cancel()
    await close_all()

# Combine MCP and crawler lifespans
combined_lifespan = combine_lifespans(mcp_app.lifespan, crawler_lifespan)

# ───────────────────── FastAPI instance ──────────────────────
app = FastAPI(
    title=config["app"]["title"],
    version=config["app"]["version"],
    lifespan=combined_lifespan,
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
        app_.add_middleware(
            TrustedHostMiddleware, allowed_hosts=sec["trusted_hosts"]
        )


_setup_security(app)

if config["observability"]["prometheus"]["enabled"]:
    Instrumentator().instrument(app).expose(app)
else:

    @app.get(config["observability"]["prometheus"]["endpoint"])
    async def metrics_disabled():
        return PlainTextResponse("Prometheus metrics disabled", status_code=404)

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


logger = logging.getLogger(__name__)


def _resolve_binary_base_dir() -> str:
    base_dir = config.get("binary", {}).get("default_dir", "/tmp/crawl4ai-exports")
    return os.path.abspath(base_dir)





def _ensure_directory(path: str) -> None:
    os.makedirs(path, mode=0o750, exist_ok=True)


def _extract_user_friendly_error(error_msg: str, operation: str = "operation") -> str:
    """Extract user-friendly error message from crawler error."""
    if "ERR_NAME_NOT_RESOLVED" in error_msg:
        return f"{operation} failed: Unable to resolve hostname. Please check the URL is valid and accessible."
    elif "ERR_CONNECTION_REFUSED" in error_msg:
        return f"{operation} failed: Connection refused. The server may be down or unreachable."
    elif "ERR_CONNECTION_TIMED_OUT" in error_msg or "Timeout" in error_msg:
        return f"{operation} failed: Connection timed out. The server took too long to respond."
    elif "ERR_CONNECTION_CLOSED" in error_msg:
        return f"{operation} failed: Connection closed unexpectedly. The server may have terminated the connection."
    elif "ERR_SSL_PROTOCOL_ERROR" in error_msg or "SSL" in error_msg:
        return f"{operation} failed: SSL/TLS error. The server's certificate may be invalid or expired."
    elif "ERR_CERT" in error_msg:
        return f"{operation} failed: Certificate error. The server's SSL certificate is invalid."
    elif "ERR_TOO_MANY_REDIRECTS" in error_msg:
        return f"{operation} failed: Too many redirects. The URL may be misconfigured."
    elif "net::" in error_msg:
        import re
        match = re.search(r'net::(ERR_[A-Z_]+)', error_msg)
        if match:
            return f"{operation} failed: Network error ({match.group(1)}). Please check the URL and network connectivity."

    # Return original message if no specific pattern matched
    return f"{operation} failed: {error_msg}"


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
    if not (isinstance(call.func, ast.Name) and call.func.id in {"CrawlerRunConfig", "BrowserConfig"}):
        raise ValueError(
            "Only CrawlerRunConfig(...) or BrowserConfig(...) are allowed")

    # forbid nested calls to keep the surface tiny
    for node in ast.walk(call):
        if isinstance(node, ast.Call) and node is not call:
            raise ValueError("Nested function calls are not permitted")

    # expose everything that crawl4ai exports, nothing else
    safe_env = {name: getattr(_c4, name)
                for name in dir(_c4) if not name.startswith("_")}
    obj = eval(compile(tree, "<config>", "eval"),
               {"__builtins__": {}}, safe_env)
    return obj.dump()


# ── job router ──────────────────────────────────────────────
app.include_router(init_job_router(redis, config, token_dep))

# ──────────────────────── Endpoints ──────────────────────────
@app.post("/token")
async def get_token(req: TokenRequest):
    if not verify_email_domain(req.email):
        raise HTTPException(400, "Invalid email domain")
    token = create_access_token({"sub": req.email})
    return {"email": req.email, "access_token": token, "token_type": "bearer"}


@app.post("/config/dump")
async def config_dump(raw: RawCode):
    try:
        return JSONResponse(_safe_eval_config(raw.code.strip()))
    except ValueError as e:
        raise HTTPException(400, f"Configuration validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(400, f"Failed to parse configuration: {str(e)}. Ensure you're using valid CrawlerRunConfig() or BrowserConfig() syntax.")


@app.post("/md")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("md")
async def get_markdown(
    request: Request,
    body: MarkdownRequest,
    _td: Dict = Depends(token_dep),
    # Backward compatibility query parameters
    f: Optional[str] = Query(None, description="Deprecated: use 'filter' in request body"),
    q: Optional[str] = Query(None, description="Deprecated: use 'query' in request body"),
    c: Optional[str] = Query(None, description="Deprecated: use 'cache' in request body"),
):
    """
    Tool for /md

    Generate Markdown from a URL or raw HTML.

    - Filter `filter` allowed values: 'raw', 'fit', 'bm25', 'llm'.
    - Query `query` is used only by 'bm25' and 'llm' filters (recommended/required for meaningful results).
    - For `filter="llm"`, ensure an LLM API key is configured (via environment or server config).
    - URLs must start with http(s) or use the raw scheme: `raw:` or `raw://` for inline HTML.

    Note: Query parameters f/q/c are deprecated but supported for backward compatibility.
    Use request body parameters filter/query/cache instead.
    """
    # Parameter precedence: body params > query params (backward compatibility)
    # Use query params as fallback for default values
    filter_param = body.filter
    if body.filter == FilterType.FIT and f is not None:
        try:
            filter_param = FilterType(f)
        except ValueError:
            raise HTTPException(400, f"Invalid filter value: {f}. Must be one of: raw, fit, bm25, llm")

    query_param = q if body.query is None and q is not None else body.query
    cache_param = c if body.cache == "0" and c is not None else body.cache
    provider_param = body.provider

    if not body.url.startswith(("http://", "https://")) and not body.url.startswith(("raw:", "raw://")):
        raise HTTPException(
            400, "Invalid URL format. Must start with http://, https://, or for raw HTML (raw:, raw://)")
    markdown = await handle_markdown_request(
        body.url, filter_param, query_param, cache_param, config, provider_param
    )
    return JSONResponse({
        "url": body.url,
        "filter": filter_param,
        "query": query_param,
        "cache": cache_param,
        "markdown": markdown,
        "success": True
    })


@app.post("/html")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("html")
async def generate_html(
    request: Request,
    body: HTMLRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Crawls the URL, preprocesses the raw HTML for schema extraction, and returns the processed HTML.
    Use when you need sanitized HTML structures for building schemas or further processing.
    """
    cfg = CrawlerRunConfig()
    async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
        results = await crawler.arun(url=body.url, config=cfg)
    first_result = results[0]
    if not getattr(first_result, "success", False) or not getattr(first_result, "html", ""):
        error_msg = getattr(first_result, "error_message", "Unable to retrieve HTML")
        friendly_error = _extract_user_friendly_error(error_msg, "Fetch HTML")
        raise HTTPException(502, friendly_error)

    raw_html = first_result.html
    from crawl4ai.utils import preprocess_html_for_schema
    processed_html = preprocess_html_for_schema(raw_html)
    return JSONResponse({"html": processed_html, "url": body.url, "success": True})

# Screenshot endpoint


@app.post("/screenshot")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("screenshot")
async def generate_screenshot(
    request: Request,
    body: ScreenshotRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Capture a full-page PNG screenshot of the specified URL, waiting an optional delay before capture, returning base64 data if output_path is omitted.
    Use when you need an image snapshot of the rendered page. It is strongly recommended to provide `output_path` to save the screenshot to disk.
    This avoids returning large base64 payloads that can exceed token/context limits. When `output_path` is provided, the response returns the saved file path instead of inline data.

    Note on screenshot_wait_for:
    - Positive values: Wait the specified number of seconds before capturing
    - Zero or negative values: Accepted but treated as no wait (immediate capture)
    - Default: 0.0 seconds (immediate capture after page load)
    """
    cfg = CrawlerRunConfig(
        screenshot=True, screenshot_wait_for=body.screenshot_wait_for)
    async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
        results = await crawler.arun(url=body.url, config=cfg)

    first_result = results[0]
    if not first_result.success:
        error_msg = first_result.error_message or "Screenshot capture failed"
        friendly_error = _extract_user_friendly_error(error_msg, "Screenshot capture")
        raise HTTPException(502, friendly_error)

    screenshot_data = first_result.screenshot
    if screenshot_data is None:
        raise HTTPException(502, "Screenshot capture failed: No screenshot data returned")

    binary_base_dir = _resolve_binary_base_dir()
    decoded_bytes: Optional[bytes] = None

    def ensure_decoded() -> bytes:
        nonlocal decoded_bytes
        if decoded_bytes is None:
            decoded_bytes = base64.b64decode(screenshot_data)
        return decoded_bytes

    if body.output_path:
        abs_path = os.path.abspath(body.output_path)
        _ensure_within_base_dir(abs_path, binary_base_dir)
        _ensure_directory(os.path.dirname(abs_path))
        try:
            with open(abs_path, "wb") as file_handle:
                file_handle.write(ensure_decoded())
        except OSError as write_error:
            logger.warning("screenshot file write failed: %s", write_error)
        else:
            return {"success": True, "path": abs_path}

    bin_cfg = config.get("binary", {})
    if bin_cfg.get("default_mode") == "file":
        _ensure_directory(binary_base_dir)
        parsed = urllib.parse.urlparse(body.url)
        host = parsed.netloc or "page"
        unique_id = uuid.uuid4().hex
        filename = f"screenshot_{host}_{unique_id}.png"
        abs_path = os.path.join(binary_base_dir, filename)
        try:
            with open(abs_path, "wb") as file_handle:
                file_handle.write(ensure_decoded())
        except OSError as write_error:
            logger.warning("screenshot file write failed: %s", write_error)
        else:
            return {"success": True, "path": abs_path}

    return {"success": True, "screenshot": screenshot_data}

# PDF endpoint


@app.post("/pdf")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("pdf")
async def generate_pdf(
    request: Request,
    body: PDFRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Generate a PDF document of the specified URL, returning base64 data if output_path is omitted.
    Use when you need a printable or archivable snapshot of the page. It is strongly recommended to provide `output_path` to save the PDF to disk.
    This avoids returning large binary/base64 payloads that can exceed token/context limits. When `output_path` is provided, the response returns the saved file path instead of inline data.
    """
    cfg = CrawlerRunConfig(pdf=True)
    async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
        results = await crawler.arun(url=body.url, config=cfg)

    first_result = results[0]
    if not first_result.success:
        error_msg = first_result.error_message or "PDF generation failed - page navigation failed"
        friendly_error = _extract_user_friendly_error(error_msg, "PDF generation")
        raise HTTPException(502, friendly_error)

    pdf_data = first_result.pdf
    binary_base_dir = _resolve_binary_base_dir()

    if body.output_path:
        abs_path = os.path.abspath(body.output_path)
        _ensure_within_base_dir(abs_path, binary_base_dir)
        _ensure_directory(os.path.dirname(abs_path))
        try:
            with open(abs_path, "wb") as file_handle:
                file_handle.write(pdf_data)
        except OSError as write_error:
            logger.warning("pdf file write failed: %s", write_error)
        else:
            return {"success": True, "path": abs_path}

    bin_cfg = config.get("binary", {})
    default_mode = bin_cfg.get("default_mode") == "file"
    if default_mode and pdf_data is not None:
        _ensure_directory(binary_base_dir)
        parsed = urllib.parse.urlparse(body.url)
        host = parsed.netloc or "page"
        unique_id = uuid.uuid4().hex
        filename = f"document_{host}_{unique_id}.pdf"
        abs_path = os.path.join(binary_base_dir, filename)
        try:
            with open(abs_path, "wb") as file_handle:
                file_handle.write(pdf_data)
        except OSError as write_error:
            logger.warning("pdf file write failed: %s", write_error)
        else:
            return {"success": True, "path": abs_path}

    if pdf_data is None:
        raise HTTPException(502, "PDF generation failed")

    encoded_pdf = base64.b64encode(pdf_data).decode()

    return {"success": True, "pdf": encoded_pdf}


@app.post("/execute_js")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("execute_js")
async def execute_js(
    request: Request,
    body: JSEndpointRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Execute JavaScript snippets against a fresh instance of the requested page.

    Each call loads ``body.url`` in a new browser context, runs the supplied
    ``scripts`` sequentially (as if passed to ``page.evaluate``), captures the
    resulting page content, and then tears the context down.  There is no
    persistent session between requests.

    Usage notes:

    - Snippets execute in the page scope.  Do **not** reference a ``page``
      object; use DOM APIs such as ``document`` or ``window``.
    - Provide each snippet as an expression (a self-invoking sync/async
      function is the safest pattern).  A snippet may ``return`` a value which
      will be captured and made available in the response.
    - All snippets run even if one fails; inspect
      ``js_execution_result['results']`` for per-snippet status and error
      stacks, and ``js_execution_result['return_values']`` for actual returned values.

    The endpoint returns the first ``CrawlResult`` produced by the crawl so you
    can inspect the mutated HTML, links, markdown, etc., after the scripts have
    executed.  Use this when you need to poke a page with a bit of JavaScript
    but don't require a long-lived automated session.

    Return Format:
        - The return result is an instance of CrawlResult, so you have access to
          markdown, links, and other fields.  If that contains what you need,
          there is no need to call other endpoints.

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
    cfg = CrawlerRunConfig(js_code=body.scripts)
    async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
        results = await crawler.arun(url=body.url, config=cfg)

    # Return JSON-serializable dict of the first CrawlResult
    result = results[0]
    data = result.model_dump()

    # Ensure js_execution_result is properly structured and extract return values
    if data.get('js_execution_result'):
        logger.info(f"JS execution results: {data['js_execution_result']}")

        # Post-process to extract actual return values for backward compatibility
        js_result = data['js_execution_result']

        if js_result.get('success') and js_result.get('results'):
            processed_results = []
            for result_item in js_result['results']:
                # Handle different result structures
                if isinstance(result_item, dict):
                    if result_item.get('success') is False:
                        # Keep error results as-is for debugging
                        processed_results.append(result_item)
                    elif result_item.get('success') is True and 'result' in result_item:
                        # Extract the actual return value from {success: true, result: value}
                        processed_results.append(result_item['result'])
                    elif result_item.get('success') is True:
                        # Handle {success: true} without result field - means undefined/null return
                        processed_results.append(None)
                    else:
                        # Direct value object - this IS the return value
                        processed_results.append(result_item)
                else:
                    # Direct primitive value - this IS the return value
                    processed_results.append(result_item)

            # Update the js_execution_result to include both raw results and processed return values
            data['js_execution_result']['return_values'] = processed_results
    else:
        logger.warning(f"No JS execution results found. Result fields: {list(data.keys())}")

    return JSONResponse(data)


@app.get("/llm/{url:path}")
async def llm_endpoint(
    request: Request,
    url: str = Path(...),
    q: str = Query(...),
    _td: Dict = Depends(token_dep),
):
    if not q:
        raise HTTPException(400, "Query parameter 'q' is required")
    if not url.startswith(("http://", "https://")) and not url.startswith(("raw:", "raw://")):
        url = "https://" + url
    answer = await handle_llm_qa(url, q, config)
    return JSONResponse({"answer": answer})


@app.get("/schema")
async def get_schema():
    from crawl4ai import BrowserConfig, CrawlerRunConfig
    return {"browser": BrowserConfig().dump(),
            "crawler": CrawlerRunConfig().dump()}


@app.get(config["observability"]["health_check"]["endpoint"])
async def health():
    return {"status": "ok", "timestamp": time.time(), "version": __version__}


@app.post("/crawl")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("crawl")
async def crawl(
    request: Request,
    crawl_request: CrawlRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Crawl a list of URLs and return the results as JSON. Accepts a single string or a list of strings.

    If your MCP client encounters token/size limit errors with large responses, use the `output_path` parameter
    to export results to a file instead.
    """
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")
    res = await handle_crawl_request(
        urls=crawl_request.urls,
        browser_config=crawl_request.browser_config,
        crawler_config=crawl_request.crawler_config,
        config=config,
        output_path=crawl_request.output_path,
    )
    return JSONResponse(res)


@app.post("/crawl/stream")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def crawl_stream(
    request: Request,
    crawl_request: CrawlRequest,
    _td: Dict = Depends(token_dep),
):
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")
    crawler, gen = await handle_stream_crawl_request(
        urls=crawl_request.urls,
        browser_config=crawl_request.browser_config,
        crawler_config=crawl_request.crawler_config,
        config=config,
    )
    return StreamingResponse(
        stream_results(crawler, gen),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Status": "active",
        },
    )


def chunk_code_functions(code_md: str) -> List[str]:
    """Extract each function/class from markdown code blocks per file."""
    pattern = re.compile(
        # match "## File: <path>" then a ```py fence, then capture until the closing ```
        r'##\s*File:\s*(?P<path>.+?)\s*?\r?\n'      # file header
        r'```py\s*?\r?\n'                         # opening fence
        r'(?P<code>.*?)(?=\r?\n```)',             # code block
        re.DOTALL
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
    context_type: str = Query("all", pattern="^(code|doc|all)$"),
    query: Optional[str] = Query(
        None, description="search query to filter chunks"),
    score_ratio: float = Query(
        0.5, ge=0.0, le=1.0, description="min score as fraction of max_score"),
    max_results: int = Query(
        20, ge=1, description="absolute cap on returned chunks"),
):
    """
    This endpoint is designed for any questions about the Crawl4AI library. It returns plain text markdown with extensive information about Crawl4AI.
    You can use this as context for any AI assistant. Use this endpoint for AI assistants to retrieve library context for decision making or code generation tasks.
    It is BEST practice to provide a query to filter the context. Otherwise the length of the response will be very long.

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

    with open(code_path, "r", encoding="utf-8") as f:
        code_content = f.read()
    with open(doc_path, "r", encoding="utf-8") as f:
        doc_content = f.read()

    def _truncate(text: str, limit: int = 800) -> str:
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + "…"

    results: Dict[str, List[Dict[str, object]]] = {}

    if query:
        tokens = query.split()
        if context_type in ("code", "all"):
            code_chunks = chunk_code_functions(code_content)
            bm25 = BM25Okapi([c.split() for c in code_chunks])
            scores = bm25.get_scores(tokens)
            max_sc = float(scores.max()) if scores.size > 0 else 0.0
            cutoff = max_sc * score_ratio
            picked = [(c, s) for c, s in zip(code_chunks, scores) if s >= cutoff]
            picked = sorted(picked, key=lambda x: x[1], reverse=True)[:max_results]
            results["code_results"] = [{"text": c, "score": s} for c, s in picked]

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
    else:
        default_cap = min(max_results, 5)
        if context_type in ("code", "all"):
            code_chunks = chunk_code_functions(code_content)[:default_cap]
            results["code_results"] = [
                {"text": _truncate(chunk), "score": None} for chunk in code_chunks
            ]
        if context_type in ("doc", "all"):
            doc_sections = chunk_doc_sections(doc_content)[:default_cap]
            results["doc_results"] = [
                {"text": _truncate(section), "score": None} for section in doc_sections
            ]

    return JSONResponse(results)


# Register tools to the existing MCP server and mount it
print(f"MCP server running on {config['app']['host']}:{config['app']['port']}")
from mcp_bridge import register_tools_from_routes
# Fix: Map 0.0.0.0 to 127.0.0.1 for internal proxy - HTTP clients can't connect to 0.0.0.0
proxy_host = "127.0.0.1" if config['app']['host'] == "0.0.0.0" else config['app']['host']
register_tools_from_routes(
    mcp_server=mcp_server,
    routes=app.routes,
    base_url=f"http://{proxy_host}:{config['app']['port']}"
)

# Add MCP schema endpoint for documentation and introspection
@app.get("/mcp/schema")
@mcp_resource("mcp_schema")
async def get_mcp_schema():
    """
    Get MCP tool schemas for documentation and introspection.
    
    Returns detailed information about available MCP tools, their parameters,
    and capabilities in a structured format.
    """
    try:
        # Get tools directly from FastMCP server
        tools_dict = await mcp_server.get_tools()
        
        schema_data = {
            "tools": [],
            "resources": [],
            "prompts": []
        }
        
        # Process FastMCP tools (they come as a dict, not an object with .tools)
        for tool_name, function_tool in tools_dict.items():
            try:
                # Extract schema from the FastMCP FunctionTool
                tool_info = {
                    "name": tool_name,
                    "description": function_tool.description or "No description available",
                    "inputSchema": {"type": "object", "properties": {}}
                }
                
                # Get the function and its signature
                if hasattr(function_tool, 'fn'):
                    fn = function_tool.fn
                    sig = inspect.signature(fn)
                    
                    # Process each parameter
                    for param_name, param in sig.parameters.items():
                        if param.annotation == inspect.Parameter.empty:
                            continue
                            
                        # Create proper schema for each parameter type
                        param_schema = _create_param_schema(param.annotation, param.default)
                        tool_info["inputSchema"]["properties"][param_name] = param_schema
                
                schema_data["tools"].append(tool_info)
                
            except Exception as e:
                # Log but don't fail for individual tools
                import logging
                logging.getLogger(__name__).warning(f"Failed to extract schema for tool {tool_name}: {e}")
                continue
        
        return JSONResponse(schema_data)
        
    except Exception as e:
        return JSONResponse({
            "error": f"Failed to generate MCP schema: {str(e)}",
            "tools": [],
            "resources": [],
            "prompts": []
        }, status_code=500)


def _create_param_schema(annotation, default_value):
    """Create JSON schema for a parameter based on its type annotation."""
    import json
    from typing import get_origin, get_args
    
    schema = {"type": "string"}  # Default fallback
    
    try:
        # Handle basic types
        if annotation is str:
            schema = {"type": "string"}
        elif annotation is int:
            schema = {"type": "integer"}
        elif annotation is float:
            schema = {"type": "number"}
        elif annotation is bool:
            schema = {"type": "boolean"}
        else:
            # Handle typing constructs
            origin = get_origin(annotation)
            args = get_args(annotation)
            
            if origin is list:
                schema = {"type": "array"}
                if args and len(args) > 0:
                    # Recursive call for array items
                    item_schema = _create_param_schema(args[0], None)
                    schema["items"] = item_schema
            elif origin is dict:
                schema = {"type": "object"}
                if args and len(args) >= 2:
                    # Could add additionalProperties for typed dicts
                    schema["additionalProperties"] = True
            elif origin is type(None) or str(origin) == "typing.Union":
                # Handle Optional[T] (Union[T, None])
                if args:
                    non_none_types = [arg for arg in args if arg is not type(None)]
                    if non_none_types:
                        schema = _create_param_schema(non_none_types[0], default_value)
            else:
                # For unknown types, try to get a string representation
                schema = {"type": "string", "description": f"Type: {annotation}"}
        
        # Add default value if present and JSON serializable
        if default_value != inspect.Parameter.empty and default_value is not None:
            try:
                json.dumps(default_value)  # Test if serializable
                schema["default"] = default_value
            except (TypeError, ValueError):
                # If not serializable, convert to string representation
                if isinstance(default_value, (str, int, float, bool)):
                    schema["default"] = default_value
                else:
                    schema["default"] = str(default_value)
                    
    except Exception:
        # Fallback for any errors in schema generation
        schema = {"type": "string", "description": f"Type: {annotation}"}
    
    return schema


# Mount MCP app at root level but preserve our FastAPI routes
# Known limitation: MCP tools don't forward JWT Authorization headers when security.jwt_enabled=true
# Internal proxy calls will fail authentication. Disable JWT or implement header forwarding for MCP usage.
app.mount("/", app=mcp_app, name="mcp")
print("Mounted MCP app at / (MCP endpoint at /mcp)")
print(f"MCP schema available at http://{config['app']['host']}:{config['app']['port']}/mcp/schema")

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
