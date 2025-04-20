# ───────────────────────── server.py ─────────────────────────
"""
Crawl4AI FastAPI entry‑point
• Browser pool + global page cap
• Rate‑limiting, security, metrics
• /crawl, /crawl/stream, /md, /llm endpoints
"""

# ── stdlib & 3rd‑party imports ───────────────────────────────
import os, sys, time, asyncio
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
import pathlib

from fastapi import (
    FastAPI, HTTPException, Request, Path, Query, Depends
)
from fastapi.responses import (
    StreamingResponse, RedirectResponse, PlainTextResponse, JSONResponse
)
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

import ast, crawl4ai as _c4
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator
from redis import asyncio as aioredis

# ── internal imports (after sys.path append) ─────────────────
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from utils import (
    FilterType, load_config, setup_logging, verify_email_domain
)
from api import (
    handle_markdown_request, handle_llm_qa,
    handle_stream_crawl_request, handle_crawl_request,
    stream_results
)
from auth import create_access_token, get_token_dependency, TokenRequest
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawler_pool import get_crawler, close_all, janitor

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

# Optional nice‑to‑have: opening the root shows the playground
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
        raise ValueError("Only CrawlerRunConfig(...) or BrowserConfig(...) are allowed")

    # forbid nested calls to keep the surface tiny
    for node in ast.walk(call):
        if isinstance(node, ast.Call) and node is not call:
            raise ValueError("Nested function calls are not permitted")

    # expose everything that crawl4ai exports, nothing else
    safe_env = {name: getattr(_c4, name) for name in dir(_c4) if not name.startswith("_")}
    obj = eval(compile(tree, "<config>", "eval"), {"__builtins__": {}}, safe_env)
    return obj.dump()


# ───────────────────────── Schemas ───────────────────────────
class CrawlRequest(BaseModel):
    urls: List[str] = Field(min_length=1, max_length=100)
    browser_config: Optional[Dict] = Field(default_factory=dict)
    crawler_config: Optional[Dict] = Field(default_factory=dict)

class RawCode(BaseModel):
    code: str

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


@app.get("/md/{url:path}")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def get_markdown(
    request: Request,
    url: str,
    f: FilterType = FilterType.FIT,
    q: Optional[str] = None,
    c: str = "0",
    _td: Dict = Depends(token_dep),
):
    md = await handle_markdown_request(url, f, q, c, config)
    return PlainTextResponse(md)

@app.get("/llm/{url:path}")
async def llm_endpoint(
    request: Request,
    url: str = Path(...),
    q: Optional[str] = Query(None),
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
async def crawl(
    request: Request,
    crawl_request: CrawlRequest,
    _td: Dict = Depends(token_dep),
):
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
