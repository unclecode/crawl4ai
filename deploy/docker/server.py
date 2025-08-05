# ───────────────────────── server.py ─────────────────────────
"""
Crawl4AI FastAPI entry‑point
• Browser pool + global page cap
• Rate‑limiting, security, metrics
• /crawl, /crawl/stream, /md, /llm endpoints
"""

# ── stdlib & 3rd‑party imports ───────────────────────────────
from crawler_pool import get_crawler, close_all, janitor
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from auth import create_access_token, get_token_dependency, TokenRequest
from pydantic import BaseModel
from typing import Optional, List, Dict
from fastapi import Request, Depends
from fastapi.responses import FileResponse
import base64
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from api import (
    handle_markdown_request, handle_llm_qa,
    handle_stream_crawl_request, handle_crawl_request,
    stream_results
)
from schemas import (
    CrawlRequest,
    MarkdownRequest,
    RawCode,
    HTMLRequest,
    ScreenshotRequest,
    PDFRequest,
    JSEndpointRequest,
)

from utils import (
    FilterType, load_config, setup_logging, verify_email_domain
)
import os
import sys
import time
import asyncio
from typing import List
from contextlib import asynccontextmanager
import pathlib

from fastapi import (
    FastAPI, HTTPException, Request, Path, Query, Depends
)
from rank_bm25 import BM25Okapi
from fastapi.responses import (
    StreamingResponse, RedirectResponse, PlainTextResponse, JSONResponse
)
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from job import init_job_router

from mcp_bridge import attach_mcp, mcp_resource, mcp_template, mcp_tool

import ast
import crawl4ai as _c4
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator
from redis import asyncio as aioredis

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
    await get_crawler(BrowserConfig(
        extra_args=config["crawler"]["browser"].get("extra_args", []),
        **config["crawler"]["browser"].get("kwargs", {}),
    ))           # warm‑up
    app.state.janitor = asyncio.create_task(janitor())        # idle GC
    yield
    app.state.janitor.cancel()
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
        app_.add_middleware(
            TrustedHostMiddleware, allowed_hosts=sec["trusted_hosts"]
        )


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
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/md")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("md")
async def get_markdown(
    request: Request,
    body: MarkdownRequest,
    _td: Dict = Depends(token_dep),
):
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(
            400, "URL must be absolute and start with http/https")
    markdown = await handle_markdown_request(
        body.url, body.f, body.q, body.c, config, body.provider
    )
    return JSONResponse({
        "url": body.url,
        "filter": body.f,
        "query": body.q,
        "cache": body.c,
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
    raw_html = results[0].html
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
    Capture a full-page PNG screenshot of the specified URL, waiting an optional delay before capture,
    Use when you need an image snapshot of the rendered page. Its recommened to provide an output path to save the screenshot.
    Then in result instead of the screenshot you will get a path to the saved file.
    """
    cfg = CrawlerRunConfig(
        screenshot=True, screenshot_wait_for=body.screenshot_wait_for)
    async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
        results = await crawler.arun(url=body.url, config=cfg)
    screenshot_data = results[0].screenshot
    if body.output_path:
        abs_path = os.path.abspath(body.output_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(base64.b64decode(screenshot_data))
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
    Generate a PDF document of the specified URL,
    Use when you need a printable or archivable snapshot of the page. It is recommended to provide an output path to save the PDF.
    Then in result instead of the PDF you will get a path to the saved file.
    """
    cfg = CrawlerRunConfig(pdf=True)
    async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
        results = await crawler.arun(url=body.url, config=cfg)
    pdf_data = results[0].pdf
    if body.output_path:
        abs_path = os.path.abspath(body.output_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(pdf_data)
        return {"success": True, "path": abs_path}
    return {"success": True, "pdf": base64.b64encode(pdf_data).decode()}


@app.post("/execute_js")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("execute_js")
async def execute_js(
    request: Request,
    body: JSEndpointRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Execute a sequence of JavaScript snippets on the specified URL.
    Return the full CrawlResult JSON (first result).
    Use this when you need to interact with dynamic pages using JS.
    REMEMBER: Scripts accept a list of separated JS snippets to execute and execute them in order.
    IMPORTANT: Each script should be an expression that returns a value. It can be an IIFE or an async function. You can think of it as such.
        Your script will replace '{script}' and execute in the browser context. So provide either an IIFE or a sync/async function that returns a value.
    Return Format:
        - The return result is an instance of CrawlResult, so you have access to markdown, links, and other stuff. If this is enough, you don't need to call again for other endpoints.

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
    data = results[0].model_dump()
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
    if not url.startswith(("http://", "https://")):
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


@app.get(config["observability"]["prometheus"]["endpoint"])
async def metrics():
    return RedirectResponse(config["observability"]["prometheus"]["endpoint"])


@app.post("/crawl")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("crawl")
async def crawl(
    request: Request,
    crawl_request: CrawlRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Crawl a list of URLs and return the results as JSON.
    """
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")
    res = await handle_crawl_request(
        urls=crawl_request.urls,
        browser_config=crawl_request.browser_config,
        crawler_config=crawl_request.crawler_config,
        config=config,
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
    context_type: str = Query("all", regex="^(code|doc|all)$"),
    query: Optional[str] = Query(
        None, description="search query to filter chunks"),
    score_ratio: float = Query(
        0.5, ge=0.0, le=1.0, description="min score as fraction of max_score"),
    max_results: int = Query(
        20, ge=1, description="absolute cap on returned chunks"),
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
        return JSONResponse({
            "code_context": code_content,
            "doc_context": doc_content,
        })

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
        neighbors = set(i for idx in idxs for i in (idx-1, idx, idx+1))
        valid = [i for i in sorted(neighbors) if 0 <= i < len(sections)]
        valid = valid[:max_results]
        results["doc_results"] = [
            {"text": sections[i], "score": scores_d[i]} for i in valid
        ]

    return JSONResponse(results)


# attach MCP layer (adds /mcp/ws, /mcp/sse, /mcp/schema)
print(f"MCP server running on {config['app']['host']}:{config['app']['port']}")
attach_mcp(
    app,
    base_url=f"http://{config['app']['host']}:{config['app']['port']}"
)

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
