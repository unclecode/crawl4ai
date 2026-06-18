# ───────────────────────── server.py ─────────────────────────
"""
Crawl4AI FastAPI entry‑point
• Browser pool + global page cap
• Rate‑limiting, security, metrics
• /crawl, /crawl/stream, /md, /llm endpoints
"""

# ── stdlib & 3rd‑party imports ───────────────────────────────
from crawler_pool import get_crawler, release_crawler, close_all, janitor
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import Provenance, UntrustedConfigError
from crawl4ai.__version__ import __version__
from auth import (
    create_access_token, get_token_dependency, TokenRequest,
    constant_time_eq, resolve_secret_key,
)
from auth_gate import AuthGateMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from fastapi import Request, Depends
from fastapi.responses import FileResponse
import base64
import re
import logging
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
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
)

from utils import (
    FilterType, load_config, setup_logging, verify_email_domain,
    validate_webhook_url, validate_url_destination,
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

# Version is imported from crawl4ai package to ensure it stays in sync

# ── global page semaphore (hard cap) ─────────────────────────
MAX_PAGES = config["crawler"]["pool"].get("max_pages", 30)
GLOBAL_SEM = asyncio.Semaphore(MAX_PAGES)

# ── security feature flags ───────────────────────────────────
# Hooks are disabled by default for security (RCE risk). Set to "true" to enable.
HOOKS_ENABLED = os.environ.get("CRAWL4AI_HOOKS_ENABLED", "false").lower() == "true"

# /execute_js disabled by default (arbitrary JS + SSRF risk). Set to "true" to enable.
EXECUTE_JS_ENABLED = os.environ.get("CRAWL4AI_EXECUTE_JS_ENABLED", "false").lower() == "true"

# Chromium renderer sandbox. --no-sandbox is kept by default because the
# container runs as non-root without a usable sandbox. On a host that provides
# an unprivileged user namespace (unprivileged_userns_clone=1) or a seccomp
# profile, set CRAWL4AI_CHROMIUM_SANDBOX=true to drop --no-sandbox and run the
# renderer sandboxed. Verify Chromium still starts after flipping it.
CHROMIUM_SANDBOX = os.environ.get("CRAWL4AI_CHROMIUM_SANDBOX", "false").lower() == "true"

# Warn loudly if API token is not set (all endpoints unauthenticated)
_api_token = config.get("security", {}).get("api_token", "") or os.environ.get("CRAWL4AI_API_TOKEN", "")
if not _api_token:
    import logging as _logging
    _logging.getLogger("crawl4ai.security").warning(
        "CRAWL4AI_API_TOKEN is not set. All API endpoints are unauthenticated. "
        "Set CRAWL4AI_API_TOKEN environment variable to enable authentication."
    )

# ── default browser config helper ─────────────────────────────
def _browser_extra_args() -> list:
    """Effective Chromium launch flags. Drops --no-sandbox when the operator
    opts into the renderer sandbox (CRAWL4AI_CHROMIUM_SANDBOX=true)."""
    args = list(config["crawler"]["browser"].get("extra_args", []))
    if CHROMIUM_SANDBOX:
        args = [a for a in args if a != "--no-sandbox"]
    return args


def get_default_browser_config() -> BrowserConfig:
    """Get default BrowserConfig from config.yml.

    Egress hardening (TLS-verify on, pinning proxy so Chromium never resolves
    the target itself) is applied here so every endpoint that fetches through
    the default config (/html, /screenshot, /pdf, /execute_js) gets the same
    DNS-rebinding / redirect-to-internal protection as /crawl, rather than
    relying on each handler to remember it."""
    bc = BrowserConfig(
        extra_args=_browser_extra_args(),
        **config["crawler"]["browser"].get("kwargs", {}),
    )
    from egress_broker import enforce_egress
    enforce_egress(bc)
    return bc

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
    from crawler_pool import init_permanent
    from monitor import MonitorStats
    import monitor as monitor_module

    # Enforce auth posture before serving any traffic.
    _resolve_auth()

    # Initialize the sandboxed artifact store + reaper.
    from artifacts import init_store
    init_store()
    app.state.artifact_janitor = asyncio.create_task(_artifact_janitor())

    # Start the localhost pinning forward-proxy and route the browser through it.
    from egress_proxy import PinningProxy
    from egress_broker import set_egress_proxy
    app.state.egress_proxy = PinningProxy()
    set_egress_proxy(await app.state.egress_proxy.start())

    # Bounded background-job queue (per-principal quotas optional).
    from work_queue import WorkQueue, set_job_queue
    from governor import job_queue_caps
    _caps = job_queue_caps(config)
    app.state.job_queue = WorkQueue(**_caps)
    await app.state.job_queue.start()
    set_job_queue(app.state.job_queue)

    # Initialize monitor
    monitor_module.monitor_stats = MonitorStats(redis)
    await monitor_module.monitor_stats.load_from_redis()
    monitor_module.monitor_stats.start_persistence_worker()

    # Initialize browser pool
    await init_permanent(BrowserConfig(
        extra_args=_browser_extra_args(),
        **config["crawler"]["browser"].get("kwargs", {}),
    ))

    # Start background tasks
    app.state.janitor = asyncio.create_task(janitor())
    app.state.timeline_updater = asyncio.create_task(_timeline_updater())

    yield

    # Cleanup
    app.state.janitor.cancel()
    app.state.timeline_updater.cancel()
    app.state.artifact_janitor.cancel()
    try:
        await app.state.egress_proxy.stop()
    except Exception:
        pass
    try:
        await app.state.job_queue.stop()
    except Exception:
        pass

    # Monitor cleanup (persist stats and stop workers)
    from monitor import get_monitor
    try:
        await get_monitor().cleanup()
    except Exception as e:
        logger.error(f"Monitor cleanup failed: {e}")

    await close_all()

async def _artifact_janitor():
    """Periodically reap expired / over-quota artifacts."""
    from artifacts import janitor as _reap
    while True:
        await asyncio.sleep(300)
        try:
            _reap()
        except Exception as e:
            logger.warning(f"Artifact janitor error: {e}")

async def _timeline_updater():
    """Update timeline data every 5 seconds."""
    from monitor import get_monitor
    while True:
        await asyncio.sleep(5)
        try:
            await asyncio.wait_for(get_monitor().update_timeline(), timeout=4.0)
        except asyncio.TimeoutError:
            logger.warning("Timeline update timeout after 4s")
        except Exception as e:
            logger.warning(f"Timeline update error: {e}")

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

# ── static monitor dashboard ────────────────────────────────
MONITOR_DIR = pathlib.Path(__file__).parent / "static" / "monitor"
if not MONITOR_DIR.exists():
    raise RuntimeError(f"Monitor assets not found at {MONITOR_DIR}")
app.mount(
    "/dashboard",
    StaticFiles(directory=MONITOR_DIR, html=True),
    name="monitor_ui",
)

# ── static assets (logo, etc) ────────────────────────────────
ASSETS_DIR = pathlib.Path(__file__).parent / "static" / "assets"
if ASSETS_DIR.exists():
    app.mount(
        "/static/assets",
        StaticFiles(directory=ASSETS_DIR),
        name="assets",
    )


@app.get("/")
async def root():
    return RedirectResponse("/playground")

# ─────────────────── infra / middleware  ─────────────────────
def _build_redis_url(config: dict) -> str:
    """Build Redis URL from config fields and environment variables."""
    rc = config.get("redis", {})
    host = os.environ.get("REDIS_HOST", rc.get("host", "localhost"))
    port = os.environ.get("REDIS_PORT", rc.get("port", 6379))
    password = os.environ.get("REDIS_PASSWORD", rc.get("password", ""))
    db = rc.get("db", 0)
    scheme = "rediss" if rc.get("ssl", False) else "redis"
    auth = f":{password}@" if password else ""
    return f"{scheme}://{auth}{host}:{port}/{db}"

redis = aioredis.from_url(_build_redis_url(config))

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[config["rate_limiting"]["default_limit"]],
    storage_uri=config["rate_limiting"]["storage_uri"],
)


def _setup_security(app_: FastAPI):
    sec = config["security"]
    if sec.get("https_redirect"):
        app_.add_middleware(HTTPSRedirectMiddleware)
    # Apply the Host guard whenever real hostnames are configured, independent
    # of `security.enabled` (the old code silently skipped it when disabled).
    trusted = sec.get("trusted_hosts", ["*"])
    if trusted and trusted != ["*"]:
        app_.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted)
    elif config["app"]["host"] not in ("127.0.0.1", "localhost", "::1"):
        logging.getLogger("crawl4ai.security").warning(
            "trusted_hosts is ['*'] on a non-loopback bind (%s): the Host guard "
            "is disabled. Set security.trusted_hosts to your real hostname(s).",
            config["app"]["host"],
        )

    # Deny-by-default CORS: only explicitly allowlisted origins; never '*' with
    # credentials.
    origins = [o for o in (sec.get("cors_allow_origins") or []) if o and o != "*"]
    if origins:
        from fastapi.middleware.cors import CORSMiddleware
        app_.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


_setup_security(app)

if config["observability"]["prometheus"]["enabled"]:
    Instrumentator().instrument(app).expose(app)

token_dep = get_token_dependency(config)

# ── security response headers (unconditional, strict-by-default) ──────
SECURITY_BASELINE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}
# Strict CSP for the API / error surface (the injection-reflection paths).
STRICT_CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; "
    "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
    "base-uri 'none'; form-action 'none'"
)
# The dashboard/playground still ship inline scripts/styles; until they are
# externalized (CSP-compat refactor) they must not receive the strict CSP or
# they break. They still get the baseline headers (nosniff, frame DENY).
_UI_PREFIXES = ("/dashboard", "/playground", "/static")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    resp = await call_next(request)
    for k, v in SECURITY_BASELINE_HEADERS.items():
        resp.headers.setdefault(k, v)
    path = request.url.path
    if not any(path.startswith(p) for p in _UI_PREFIXES):
        resp.headers.setdefault("Content-Security-Policy", STRICT_CSP)
    if config["security"].get("https_redirect"):
        resp.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
    return resp


# ── authentication gate (outermost ASGI layer, fails closed) ──────────
# The single place auth is decided: covers every route, static mount, the MCP
# transports and the metrics endpoint, for HTTP and WebSocket alike. Only the
# health check and the token-issuing endpoint are public.
HEALTH_PATH = config["observability"]["health_check"]["endpoint"]


def _current_api_token() -> str:
    """The effective static operator token (config or environment)."""
    return (
        config.get("security", {}).get("api_token", "")
        or os.environ.get("CRAWL4AI_API_TOKEN", "")
    )


app.add_middleware(
    AuthGateMiddleware,
    token_provider=_current_api_token,
    public_paths={HEALTH_PATH, "/token"},
)

# ── request body-size limit (DoS) ─────────────────────────────────────
from governor import BodySizeLimitMiddleware, max_body_bytes_from_config
app.add_middleware(BodySizeLimitMiddleware, max_bytes=max_body_bytes_from_config(config))


def _resolve_auth():
    """Runtime auth-posture guard. Runs at startup (lifespan), not import, so
    the behavioral test harness can import the app without a hard exit.

    - credential configured  -> enforce (fail fast on jwt_enabled w/o SECRET_KEY)
    - none + non-loopback bind -> refuse to start (would be open to the network)
    - none + loopback bind    -> generate a one-off token and print it
    """
    host = config["app"]["host"]
    loopback = host in ("127.0.0.1", "localhost", "::1")
    api_token = _current_api_token()
    jwt_enabled = config.get("security", {}).get("jwt_enabled", False)

    if api_token or jwt_enabled:
        if jwt_enabled:
            resolve_secret_key(required=True)  # fail fast: no ephemeral secret
        logger.info("Auth gate active (credential configured).")
        return

    if not loopback:
        logger.critical(
            "Refusing to start: binding %s with no CRAWL4AI_API_TOKEN and "
            "jwt_enabled=false would expose an unauthenticated API. Set "
            "CRAWL4AI_API_TOKEN=$(openssl rand -hex 32), enable jwt, or bind loopback.",
            host,
        )
        sys.exit(1)

    import secrets as _secrets
    gen = _secrets.token_hex(32)
    os.environ["CRAWL4AI_API_TOKEN"] = gen
    logger.warning(
        "No CRAWL4AI_API_TOKEN set; generated an ephemeral token for this "
        "loopback session:\n    CRAWL4AI_API_TOKEN=%s",
        gen,
    )

# ───────────────── URL validation helper ─────────────────
ALLOWED_URL_SCHEMES = ("http://", "https://")
ALLOWED_URL_SCHEMES_WITH_RAW = ("http://", "https://", "raw:", "raw://")


def validate_url_scheme(url: str, allow_raw: bool = False) -> None:
    """Validate URL scheme (LFI) and destination (SSRF)."""
    allowed = ALLOWED_URL_SCHEMES_WITH_RAW if allow_raw else ALLOWED_URL_SCHEMES
    if not url.startswith(allowed):
        schemes = ", ".join(allowed)
        raise HTTPException(400, f"URL must start with {schemes}")
    validate_url_destination(url)


# ───────────────── safe config‑dump helper ─────────────────
ALLOWED_TYPES = {
    "CrawlerRunConfig": CrawlerRunConfig,
    "BrowserConfig": BrowserConfig,
}


def _config_from_json(data: dict) -> dict:
    """Validate a {type, params} config under the untrusted trust boundary and
    echo the normalized result.

    This endpoint is no longer a gadget-construction oracle: only the gated,
    side-effect-free CrawlerRunConfig/BrowserConfig types may be validated, the
    untrusted gate raises on forbidden power-fields and disallowed nested types
    (LLM*, proxy, deep-crawl - which is what would read env/secrets), drops
    unknown fields, and clamps quantities."""
    config_type = data.get("type")
    if config_type == "CrawlerRunConfig":
        obj = CrawlerRunConfig.load(data, provenance=Provenance.UNTRUSTED)
    elif config_type == "BrowserConfig":
        obj = BrowserConfig.load(data, provenance=Provenance.UNTRUSTED)
    else:
        raise ValueError("type must be 'CrawlerRunConfig' or 'BrowserConfig'")
    return obj.dump()


# ── job router ──────────────────────────────────────────────
app.include_router(init_job_router(redis, config, token_dep))

# ── monitor router ──────────────────────────────────────────
from monitor_routes import router as monitor_router
app.include_router(monitor_router, dependencies=[Depends(token_dep)])

logger = logging.getLogger(__name__)


# ── central exception handling (no internal detail leaks) ─────────────
# 16 sites used to return raw str(e) to clients, leaking paths, dependency
# versions, resolved internal IPs and sometimes secrets. Centralize: 5xx
# responses are generic + carry a correlation id; the full detail is logged
# server-side. 4xx developer messages are preserved.
import uuid as _uuid
from starlette.exceptions import HTTPException as _StarletteHTTPException


@app.exception_handler(_StarletteHTTPException)
async def _http_exception_handler(request: Request, exc: _StarletteHTTPException):
    # 500 is the raw-str(e) leak vector -> genericize with a correlation id.
    # Deliberate operational statuses (502/503/504, with their own short
    # messages + headers like Retry-After) pass through, as do 4xx.
    if exc.status_code == 500:
        cid = _uuid.uuid4().hex[:12]
        logger.error("server error 500 [cid=%s]: %s", cid, exc.detail)
        return JSONResponse(
            {"error": "Internal server error", "correlation_id": cid},
            status_code=500,
        )
    return JSONResponse(
        {"detail": exc.detail},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    cid = _uuid.uuid4().hex[:12]
    logger.exception("unhandled exception [cid=%s]", cid)
    return JSONResponse(
        {"error": "Internal server error", "correlation_id": cid},
        status_code=500,
    )


# ──────────────────────── Endpoints ──────────────────────────
@app.post("/token")
async def get_token(req: TokenRequest):
    expected_token = config.get("security", {}).get("api_token", "")
    if not expected_token:
        # Fail closed: without a configured api_token the old behavior minted a
        # JWT to anyone whose email merely had an MX record. Refuse instead.
        raise HTTPException(
            403,
            "Token issuance is disabled: no api_token is configured on the server.",
        )
    if not req.api_token or not constant_time_eq(req.api_token, expected_token):
        raise HTTPException(401, "Invalid or missing api_token")
    if not verify_email_domain(req.email):
        raise HTTPException(400, "Invalid email domain")
    token = create_access_token({"sub": req.email})
    return {"email": req.email, "access_token": token, "token_type": "bearer"}


@app.post("/config/dump")
async def config_dump(
    data: dict,
    _td: Dict = Depends(token_dep),
):
    try:
        return JSONResponse(_config_from_json(data))
    except (TypeError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.post("/md")
@limiter.limit(config["rate_limiting"]["default_limit"])
@mcp_tool("md")
async def get_markdown(
    request: Request,
    body: MarkdownRequest,
    _td: Dict = Depends(token_dep),
):
    """
    Convert a web page into Markdown format.

    Supports multiple extraction modes:
    - fit (default): Readability-based extraction for clean content
    - raw: Direct DOM to Markdown conversion
    - bm25: BM25 relevance ranking with optional query
    - llm: LLM-based summarization with optional query

    Use this tool when you need clean, readable text from web pages.
    """
    if not body.url.startswith(("http://", "https://")) and not body.url.startswith(("raw:", "raw://")):
        raise HTTPException(
            400, "Invalid URL format. Must start with http://, https://, or for raw HTML (raw:, raw://)")
    # base_url is intentionally not accepted from the request (key-exfil vector);
    # the LLM endpoint is server-derived from the provider name only.
    markdown = await handle_markdown_request(
        body.url, body.f, body.q, body.c, config, body.provider,
        body.temperature
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
    validate_url_scheme(body.url, allow_raw=True)
    cfg = CrawlerRunConfig()
    crawler = None
    try:
        crawler = await get_crawler(get_default_browser_config())
        results = await crawler.arun(url=body.url, config=cfg)
        if not results[0].success:
            raise HTTPException(500, detail=results[0].error_message or "Crawl failed")

        raw_html = results[0].html
        from crawl4ai.utils import preprocess_html_for_schema
        processed_html = preprocess_html_for_schema(raw_html)
        return JSONResponse({"html": processed_html, "url": body.url, "success": True})
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    finally:
        if crawler:
            await release_crawler(crawler)

# ── artifact store helpers ───────────────────────────────────
def _store_artifact(kind: str, data: bytes) -> dict:
    """Write to the sandboxed store; map quota/size errors to HTTP codes."""
    from artifacts import write_artifact, ArtifactTooLarge, QuotaExceeded
    try:
        meta = write_artifact(kind, data)
    except ArtifactTooLarge:
        raise HTTPException(413, "Artifact too large")
    except QuotaExceeded:
        raise HTTPException(507, "Artifact storage quota exceeded")
    return {
        "artifact_id": meta["artifact_id"],
        "url": f"/artifacts/{meta['artifact_id']}",
        "mime": meta["mime"],
        "size": meta["size"],
    }


@app.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str, _td: Dict = Depends(token_dep)):
    """Fetch a previously generated artifact by its opaque id (authed)."""
    from artifacts import resolve_artifact, ArtifactNotFound
    try:
        path, mime = resolve_artifact(artifact_id)
    except ArtifactNotFound:
        raise HTTPException(404, "Artifact not found")
    return FileResponse(path, media_type=mime, headers={"X-Content-Type-Options": "nosniff"})


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
    Capture a full-page PNG screenshot of the specified URL, waiting an optional delay before capture.
    Use when you need an image snapshot of the rendered page. The image is also written to the
    sandboxed artifact store; the response includes an `artifact_id` and a `url` to fetch it.
    """
    validate_url_scheme(body.url)
    crawler = None
    try:
        cfg = CrawlerRunConfig(screenshot=True, screenshot_wait_for=body.screenshot_wait_for, wait_for_images=body.wait_for_images)
        crawler = await get_crawler(get_default_browser_config())
        results = await crawler.arun(url=body.url, config=cfg)
        if not results[0].success:
            raise HTTPException(500, detail=results[0].error_message or "Crawl failed")
        screenshot_data = results[0].screenshot
        art = _store_artifact("png", base64.b64decode(screenshot_data))
        return {"success": True, "screenshot": screenshot_data, **art}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    finally:
        if crawler:
            await release_crawler(crawler)

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
    Generate a PDF document of the specified URL.
    Use when you need a printable or archivable snapshot of the page. The PDF is also written to the
    sandboxed artifact store; the response includes an `artifact_id` and a `url` to fetch it.
    """
    validate_url_scheme(body.url)
    crawler = None
    try:
        cfg = CrawlerRunConfig(pdf=True)
        crawler = await get_crawler(get_default_browser_config())
        results = await crawler.arun(url=body.url, config=cfg)
        if not results[0].success:
            raise HTTPException(500, detail=results[0].error_message or "Crawl failed")
        pdf_data = results[0].pdf
        art = _store_artifact("pdf", pdf_data)
        return {"success": True, "pdf": base64.b64encode(pdf_data).decode(), **art}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    finally:
        if crawler:
            await release_crawler(crawler)


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
    if not EXECUTE_JS_ENABLED:
        raise HTTPException(403, "execute_js endpoint is disabled. Set CRAWL4AI_EXECUTE_JS_ENABLED=true to enable.")
    validate_url_scheme(body.url)
    # Block SSRF: reject internal/private IPs
    try:
        validate_webhook_url(body.url)  # reuse SSRF blocklist
    except ValueError as e:
        raise HTTPException(400, str(e))
    crawler = None
    try:
        cfg = CrawlerRunConfig(js_code=body.scripts)
        crawler = await get_crawler(get_default_browser_config())
        results = await crawler.arun(url=body.url, config=cfg)
        if not results[0].success:
            raise HTTPException(500, detail=results[0].error_message or "Crawl failed")
        data = results[0].model_dump()
        return JSONResponse(data)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    finally:
        if crawler:
            await release_crawler(crawler)


@app.get("/llm/{url:path}")
async def llm_endpoint(
    request: Request,
    url: str = Path(...),
    q: str = Query(...),
    provider: Optional[str] = Query(None, description="LLM provider override, e.g. 'openai/gpt-4o-mini'"),
    temperature: Optional[float] = Query(None, description="LLM temperature override"),
    _td: Dict = Depends(token_dep),
):
    # base_url is intentionally not accepted (key-exfil vector); the endpoint is
    # derived server-side from the provider name only.
    if not q:
        raise HTTPException(400, "Query parameter 'q' is required")
    if not url.startswith(("http://", "https://")) and not url.startswith(("raw:", "raw://")):
        url = "https://" + url
    answer = await handle_llm_qa(url, q, config, provider=provider, temperature=temperature)
    return JSONResponse({"answer": answer})


@app.get("/schema")
async def get_schema():
    from crawl4ai import BrowserConfig, CrawlerRunConfig
    return {"browser": BrowserConfig().dump(),
            "crawler": CrawlerRunConfig().dump()}


@app.get("/hooks/info")
async def get_hooks_info():
    """Enumerate the available declarative hook actions and their parameter schemas.

    Arbitrary hook code is no longer accepted (it was an exec()-based RCE
    surface). Each action maps to a server-authored, single-purpose Playwright
    operation; clients select an action and supply schema-validated params.
    """
    from hook_registry import describe_registry

    return JSONResponse({
        "available_actions": describe_registry(),
        "usage": {
            "field": "hooks",
            "shape": [{"action": "<action>", "params": {"...": "..."}}],
            "max_hooks": 10,
        },
        "timeout_limits": {"min": 1, "max": 120, "default": 30},
    })


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
    crawl_request: CrawlRequestWithHooks,
    _td: Dict = Depends(token_dep),
):
    """
    Crawl a list of URLs and return the results as JSON.
    For streaming responses, use /crawl/stream endpoint.
    Supports optional user-provided hook functions for customization.
    """
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")
    if crawl_request.hooks and not HOOKS_ENABLED:
        raise HTTPException(403, "Hooks are disabled. Set CRAWL4AI_HOOKS_ENABLED=true to enable.")
    # Check whether it is a redirection for a streaming request
    try:
        crawler_config = CrawlerRunConfig.load(
            crawl_request.crawler_config, provenance=Provenance.UNTRUSTED
        )
    except UntrustedConfigError as e:
        raise HTTPException(400, f"Rejected config: {e}")
    if crawler_config.stream:
        return await stream_process(crawl_request=crawl_request)
    
    # Prepare hooks config if provided
    hooks_config = None
    if crawl_request.hooks:
        hooks_config = {
            'hooks': crawl_request.hooks.hooks,
            'timeout': crawl_request.hooks.timeout
        }
    
    results = await handle_crawl_request(
        urls=crawl_request.urls,
        browser_config=crawl_request.browser_config,
        crawler_config=crawl_request.crawler_config,
        config=config,
        hooks_config=hooks_config,
        crawler_configs=crawl_request.crawler_configs,
    )
    # check if all of the results are not successful
    if all(not result["success"] for result in results["results"]):
        raise HTTPException(500, f"Crawl request failed: {results['results'][0]['error_message']}")
    return JSONResponse(results)


@app.post("/crawl/stream")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def crawl_stream(
    request: Request,
    crawl_request: CrawlRequestWithHooks,
    _td: Dict = Depends(token_dep),
):
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")
    if crawl_request.hooks and not HOOKS_ENABLED:
        raise HTTPException(403, "Hooks are disabled. Set CRAWL4AI_HOOKS_ENABLED=true to enable.")

    return await stream_process(crawl_request=crawl_request)

async def stream_process(crawl_request: CrawlRequestWithHooks):
    
    # Prepare hooks config if provided# Prepare hooks config if provided
    hooks_config = None
    if crawl_request.hooks:
        hooks_config = {
            'hooks': crawl_request.hooks.hooks,
            'timeout': crawl_request.hooks.timeout
        }
    
    crawler, gen, hooks_info = await handle_stream_crawl_request(
        urls=crawl_request.urls,
        browser_config=crawl_request.browser_config,
        crawler_config=crawl_request.crawler_config,
        config=config,
        hooks_config=hooks_config
    )
    
    # Add hooks info to response headers if available
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Stream-Status": "active",
    }
    if hooks_info:
        import json
        headers["X-Hooks-Status"] = json.dumps(hooks_info['status']['status'])
    
    return StreamingResponse(
        stream_results(crawler, gen),
        media_type="application/x-ndjson",
        headers=headers,
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
    # Internal MCP tool calls go over loopback to our own gated endpoints,
    # carrying a service token. Pin to 127.0.0.1 (config host may be 0.0.0.0,
    # which is a bind address, not a valid connect target).
    base_url=f"http://127.0.0.1:{config['app']['port']}"
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
