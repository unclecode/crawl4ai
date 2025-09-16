"""
Job endpoints (enqueue + poll) for long-running LL​M extraction and raw crawl.
Relies on the existing Redis task helpers in api.py
"""

from typing import Dict, Optional, Callable
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel, HttpUrl

from api import (
    handle_llm_request,
    handle_crawl_job,
    handle_task_status,
)

# ------------- dependency placeholders -------------
_redis = None        # will be injected from server.py
_config = None
_token_dep: Callable = lambda: None  # dummy until injected

# public router
router = APIRouter()


# === init hook called by server.py =========================================
def init_job_router(redis, config, token_dep) -> APIRouter:
    """Inject shared singletons and return the router for mounting."""
    global _redis, _config, _token_dep
    _redis, _config, _token_dep = redis, config, token_dep
    return router


# ---------- payload models --------------------------------------------------
class LlmJobPayload(BaseModel):
    url:    HttpUrl
    q:      str
    schema: Optional[str] = None
    cache:  bool = False
    provider: Optional[str] = None


class CrawlJobPayload(BaseModel):
    urls:           list[HttpUrl]
    browser_config: Dict = {}
    crawler_config: Dict = {}


# ---------- LL​M job ---------------------------------------------------------
@router.post("/llm/job", status_code=202)
async def llm_job_enqueue(
        payload: LlmJobPayload,
        background_tasks: BackgroundTasks,
        request: Request,
        _td: Dict = Depends(lambda: _token_dep()),   # late-bound dep
):
    return await handle_llm_request(
        _redis,
        background_tasks,
        request,
        str(payload.url),
        query=payload.q,
        schema=payload.schema,
        cache=payload.cache,
        config=_config,
        provider=payload.provider,
    )


@router.get("/llm/job/{task_id}")
async def llm_job_status(
    request: Request,
    task_id: str,
    _td: Dict = Depends(lambda: _token_dep())
):
    return await handle_task_status(_redis, task_id)


# ---------- CRAWL job -------------------------------------------------------
@router.post("/crawl/job", status_code=202)
async def crawl_job_enqueue(
        payload: CrawlJobPayload,
        background_tasks: BackgroundTasks,
        _td: Dict = Depends(lambda: _token_dep()),
):
    return await handle_crawl_job(
        _redis,
        background_tasks,
        [str(u) for u in payload.urls],
        payload.browser_config,
        payload.crawler_config,
        config=_config,
    )


@router.get("/crawl/job/{task_id}")
async def crawl_job_status(
    request: Request,
    task_id: str,
    _td: Dict = Depends(lambda: _token_dep())
):
    return await handle_task_status(_redis, task_id, base_url=str(request.base_url))
