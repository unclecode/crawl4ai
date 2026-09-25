import os
import json
import asyncio
from typing import List, Tuple, Dict, NamedTuple
from functools import partial
from uuid import uuid4
from datetime import datetime, timezone
from base64 import b64encode

import logging
from typing import Optional, AsyncGenerator
from urllib.parse import unquote
from fastapi import HTTPException, Request, status
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CrawlResult,
    LLMExtractionStrategy,
    CacheMode,
    BrowserConfig,
    MemoryAdaptiveDispatcher,
    RateLimiter, 
    LLMConfig
)
from crawl4ai.async_configs import Provenance, UntrustedConfigError
from hook_registry import build_declarative_hooks, HookValidationError
from llm_broker import LLMProviderNotAllowed
from crawl4ai.utils import perform_completion_with_backoff


def _enqueue_job(background_tasks, factory, principal=None):
    """Submit a background job to the bounded work queue (per-principal quota).

    Falls back to FastAPI BackgroundTasks when the queue isn't running (tests /
    no lifespan). Maps queue/quota limits to HTTP 503 / 429.
    """
    from work_queue import get_job_queue, QueueFull, QuotaExceeded
    q = get_job_queue()
    if q is None or not q.started:
        background_tasks.add_task(factory)
        return
    try:
        q.submit(factory, principal)
    except QuotaExceeded:
        raise HTTPException(status_code=429, detail="Too many concurrent jobs for this caller")
    except QueueFull:
        raise HTTPException(
            status_code=503, detail="Server busy, retry later",
            headers={"Retry-After": "5"},
        )


def _attach_declarative_hooks(crawler, hooks_config: dict) -> dict:
    """Build and attach server-authored hooks from declarative specs.

    Raises HookValidationError on an unknown action / invalid params, which the
    handlers map to HTTP 400.
    """
    specs = hooks_config.get("hooks", []) or []
    hooks = build_declarative_hooks(specs)
    for hook_point, fn in hooks.items():
        crawler.crawler_strategy.set_hook(hook_point, fn)
    return {"status": "success", "attached": list(hooks.keys())}
from crawl4ai.content_filter_strategy import (
    PruningContentFilter,
    BM25ContentFilter,
    LLMContentFilter
)
from crawl4ai.content_filter_strategy_lxml import PruningContentFilterLXML
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

from utils import (
    TaskStatus,
    FilterType,
    get_base_url,
    is_task_id,
    should_cleanup_task,
    decode_redis_hash,
    get_llm_api_key,
    validate_llm_provider,
    get_llm_temperature,
    get_llm_base_url,
    get_redis_task_ttl,
    validate_url_destination,
    datetime_handler,
)
from webhook import WebhookDeliveryService

import psutil, time

logger = logging.getLogger(__name__)


def _raise_for_crawl_failure(result):
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.error_message,
        )


# --- Helper to get memory ---
def _get_memory_mb():
    try:
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception as e:
        logger.warning(f"Could not get memory info: {e}")
        return None


async def hset_with_ttl(redis, key: str, mapping: dict, config: dict):
    """Set Redis hash with automatic TTL expiry.

    Args:
        redis: Redis client instance
        key: Redis key (e.g., "task:abc123")
        mapping: Hash field-value mapping
        config: Application config containing redis.task_ttl_seconds
    """
    await redis.hset(key, mapping=mapping)
    ttl = get_redis_task_ttl(config)
    if ttl > 0:
        await redis.expire(key, ttl)


async def handle_llm_qa(
    url: str,
    query: str,
    config: dict,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
) -> str:
    """Process QA using LLM with crawled content as context."""
    from crawler_pool import get_crawler, release_crawler
    crawler = None
    try:
        if not url.startswith(('http://', 'https://')) and not url.startswith(("raw:", "raw://")):
            url = 'https://' + url
        validate_url_destination(url)
        # Extract base URL by finding last '?q=' occurrence
        last_q_index = url.rfind('?q=')
        if last_q_index != -1:
            url = url[:last_q_index]

        # Get markdown content (use default config)
        from utils import load_config
        cfg = load_config()
        browser_cfg = BrowserConfig(
            extra_args=cfg["crawler"]["browser"].get("extra_args", []),
            **cfg["crawler"]["browser"].get("kwargs", {}),
        )
        from egress_broker import enforce_egress
        enforce_egress(browser_cfg)
        crawler = await get_crawler(browser_cfg)
        result = await crawler.arun(url)
        _raise_for_crawl_failure(result)
        content = result.markdown.fit_markdown or result.markdown.raw_markdown

        # Create prompt and get LLM response
        prompt = f"""Use the following content as context to answer the question.
    Content:
    {content}

    Question: {query}

    Answer:"""

        # Provider by name only; base_url/api_token are server-derived. A
        # request-supplied base_url is ignored (it was the key-exfil vector).
        from llm_broker import resolve_llm
        llm = resolve_llm(config, provider)
        response = perform_completion_with_backoff(
            provider=llm["provider"],
            prompt_with_variables=prompt,
            api_token=llm["api_token"],
            temperature=temperature or llm["temperature"],
            base_url=llm["base_url"],
            base_delay=config["llm"].get("backoff_base_delay", 2),
            max_attempts=config["llm"].get("backoff_max_attempts", 3),
            exponential_factor=config["llm"].get("backoff_exponential_factor", 2)
        )

        return response.choices[0].message.content
    except HTTPException:
        raise
    except LLMProviderNotAllowed as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"QA processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if crawler:
            await release_crawler(crawler)

async def process_llm_extraction(
    redis: aioredis.Redis,
    config: dict,
    task_id: str,
    url: str,
    instruction: str,
    schema: Optional[str] = None,
    cache: str = "0",
    provider: Optional[str] = None,
    webhook_config: Optional[Dict] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None
) -> None:
    """Process LLM extraction in background."""
    # Initialize webhook service
    webhook_service = WebhookDeliveryService(config)

    try:
        # Validate provider
        is_valid, error_msg = validate_llm_provider(config, provider)
        if not is_valid:
            await hset_with_ttl(redis, f"task:{task_id}", {
                "status": TaskStatus.FAILED,
                "error": error_msg
            }, config)

            # Send webhook notification on failure
            await webhook_service.notify_job_completion(
                task_id=task_id,
                task_type="llm_extraction",
                status="failed",
                urls=[url],
                webhook_config=webhook_config,
                error=error_msg
            )
            return
        # Provider by name only; base_url/api_token server-derived (no exfil).
        from llm_broker import resolve_llm
        _llm = resolve_llm(config, provider)
        llm_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider=_llm["provider"],
                api_token=_llm["api_token"],
                temperature=temperature or _llm["temperature"],
                base_url=_llm["base_url"],
            ),
            instruction=instruction,
            schema=json.loads(schema) if schema else None,
        )

        cache_mode = CacheMode.ENABLED if cache == "1" else CacheMode.WRITE_ONLY

        # Re-validate the destination at fetch time (the enqueue-time check is a
        # TOCTOU seed-only guard) and pin egress so the background fetch cannot
        # be rebound/redirected to an internal target.
        validate_url_destination(url)
        from utils import load_config as _load_config
        _wcfg = _load_config()
        worker_browser_cfg = BrowserConfig(
            extra_args=_wcfg["crawler"]["browser"].get("extra_args", []),
            **_wcfg["crawler"]["browser"].get("kwargs", {}),
        )
        from egress_broker import enforce_egress
        enforce_egress(worker_browser_cfg)
        async with AsyncWebCrawler(config=worker_browser_cfg) as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    extraction_strategy=llm_strategy,
                    scraping_strategy=LXMLWebScrapingStrategy(),
                    cache_mode=cache_mode
                )
            )

        if not result.success:
            await hset_with_ttl(redis, f"task:{task_id}", {
                "status": TaskStatus.FAILED,
                "error": result.error_message
            }, config)

            # Send webhook notification on failure
            await webhook_service.notify_job_completion(
                task_id=task_id,
                task_type="llm_extraction",
                status="failed",
                urls=[url],
                webhook_config=webhook_config,
                error=result.error_message
            )
            return

        try:
            content = json.loads(result.extracted_content)
        except json.JSONDecodeError:
            content = result.extracted_content

        result_data = {"extracted_content": content}

        await hset_with_ttl(redis, f"task:{task_id}", {
            "status": TaskStatus.COMPLETED,
            "result": json.dumps(content)
        }, config)

        # Send webhook notification on successful completion
        await webhook_service.notify_job_completion(
            task_id=task_id,
            task_type="llm_extraction",
            status="completed",
            urls=[url],
            webhook_config=webhook_config,
            result=result_data
        )

    except Exception as e:
        logger.error(f"LLM extraction error: {str(e)}", exc_info=True)
        await hset_with_ttl(redis, f"task:{task_id}", {
            "status": TaskStatus.FAILED,
            "error": str(e)
        }, config)

        # Send webhook notification on failure
        await webhook_service.notify_job_completion(
            task_id=task_id,
            task_type="llm_extraction",
            status="failed",
            urls=[url],
            webhook_config=webhook_config,
            error=str(e)
        )

async def handle_markdown_request(
    url: str,
    filter_type: FilterType,
    query: Optional[str] = None,
    cache: str = "0",
    config: Optional[dict] = None,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None
) -> str:
    """Handle markdown generation requests."""
    crawler = None
    try:
        # Validate provider if using LLM filter
        if filter_type == FilterType.LLM:
            is_valid, error_msg = validate_llm_provider(config, provider)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
        decoded_url = unquote(url)
        if not decoded_url.startswith(('http://', 'https://')) and not decoded_url.startswith(("raw:", "raw://")):
            decoded_url = 'https://' + decoded_url
        validate_url_destination(decoded_url)

        if filter_type == FilterType.RAW:
            md_generator = DefaultMarkdownGenerator()
        else:
            # Provider by name only; base_url/api_token are server-derived.
            from llm_broker import resolve_llm
            _llm = resolve_llm(config, provider)
            content_filter = {
                FilterType.FIT: PruningContentFilterLXML(),
                FilterType.BM25: BM25ContentFilter(user_query=query or ""),
                FilterType.LLM: LLMContentFilter(
                    llm_config=LLMConfig(
                        provider=_llm["provider"],
                        api_token=_llm["api_token"],
                        temperature=temperature or _llm["temperature"],
                        base_url=_llm["base_url"],
                    ),
                    instruction=query or "Extract main content"
                )
            }[filter_type]
            md_generator = DefaultMarkdownGenerator(content_filter=content_filter)

        cache_mode = CacheMode.ENABLED if cache == "1" else CacheMode.WRITE_ONLY

        from crawler_pool import get_crawler, release_crawler
        from utils import load_config as _load_config
        _cfg = _load_config()
        browser_cfg = BrowserConfig(
            extra_args=_cfg["crawler"]["browser"].get("extra_args", []),
            **_cfg["crawler"]["browser"].get("kwargs", {}),
        )
        from egress_broker import enforce_egress
        enforce_egress(browser_cfg)
        crawler = await get_crawler(browser_cfg)
        result = await crawler.arun(
            url=decoded_url,
            config=CrawlerRunConfig(
                markdown_generator=md_generator,
                scraping_strategy=LXMLWebScrapingStrategy(),
                cache_mode=cache_mode
            )
        )

        _raise_for_crawl_failure(result)

        return (result.markdown.raw_markdown
               if filter_type == FilterType.RAW
               else result.markdown.fit_markdown)

    except HTTPException:
        raise
    except LLMProviderNotAllowed as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Markdown error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if crawler:
            await release_crawler(crawler)

async def handle_llm_request(
    redis: aioredis.Redis,
    background_tasks: BackgroundTasks,
    request: Request,
    input_path: str,
    query: Optional[str] = None,
    schema: Optional[str] = None,
    cache: str = "0",
    config: Optional[dict] = None,
    provider: Optional[str] = None,
    webhook_config: Optional[Dict] = None,
    temperature: Optional[float] = None,
    api_base_url: Optional[str] = None,
    requester: Optional[str] = None,
    is_admin: bool = False,
) -> JSONResponse:
    """Handle LLM extraction requests."""
    base_url = get_base_url(request)

    try:
        if is_task_id(input_path):
            return await handle_task_status(
                redis, input_path, base_url,
                requester=requester, is_admin=is_admin,
            )

        if not query:
            return JSONResponse({
                "message": "Please provide an instruction",
                "_links": {
                    "example": {
                        "href": f"{base_url}/llm/{input_path}?q=Extract+main+content",
                        "title": "Try this example"
                    }
                }
            })

        return await create_new_task(
            redis,
            background_tasks,
            input_path,
            query,
            schema,
            cache,
            base_url,
            config,
            provider,
            webhook_config,
            temperature,
            api_base_url,
            owner=requester,
        )

    except HTTPException:
        raise  # 429/503 (queue/quota), 400, etc. - don't mask as 500
    except Exception as e:
        logger.error(f"LLM endpoint error: {str(e)}", exc_info=True)
        return JSONResponse({
            "error": str(e),
            "_links": {
                "retry": {"href": str(request.url)}
            }
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

async def handle_task_status(
    redis: aioredis.Redis,
    task_id: str,
    base_url: str,
    *,
    keep: bool = False,
    requester: Optional[str] = None,
    is_admin: bool = False,
) -> JSONResponse:
    """Handle task status check requests.

    Enforces ownership: a task records the `owner` (principal sub) that created
    it; a different requester gets 404 (not 403, so task existence is not
    revealed). Admin-scope principals may read any task.
    """
    task = await redis.hgetall(f"task:{task_id}")
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    task = decode_redis_hash(task)

    owner = task.get("owner")
    if owner and not is_admin and owner != requester:
        # Do not leak existence of someone else's task.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    response = create_task_response(task, task_id, base_url)

    if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        if not keep and should_cleanup_task(task["created_at"]):
            await redis.delete(f"task:{task_id}")

    return JSONResponse(response)

async def create_new_task(
    redis: aioredis.Redis,
    background_tasks: BackgroundTasks,
    input_path: str,
    query: str,
    schema: Optional[str],
    cache: str,
    base_url: str,
    config: dict,
    provider: Optional[str] = None,
    webhook_config: Optional[Dict] = None,
    temperature: Optional[float] = None,
    api_base_url: Optional[str] = None,
    owner: Optional[str] = None,
) -> JSONResponse:
    """Create and initialize a new task."""
    decoded_url = unquote(input_path)
    if not decoded_url.startswith(('http://', 'https://')) and not decoded_url.startswith(("raw:", "raw://")):
        decoded_url = 'https://' + decoded_url
    validate_url_destination(decoded_url)

    from datetime import datetime
    task_id = f"llm_{int(datetime.now().timestamp())}_{id(background_tasks)}"

    task_data = {
        "status": TaskStatus.PROCESSING,
        "created_at": datetime.now().isoformat(),
        "url": decoded_url
    }
    if owner:
        task_data["owner"] = owner

    # Store webhook config if provided
    if webhook_config:
        task_data["webhook_config"] = json.dumps(webhook_config)

    await hset_with_ttl(redis, f"task:{task_id}", task_data, config)

    try:
        _enqueue_job(
            background_tasks,
            lambda: process_llm_extraction(
                redis, config, task_id, decoded_url, query, schema, cache,
                provider, webhook_config, temperature, api_base_url,
            ),
            principal=owner,
        )
    except HTTPException:
        # Don't leave an orphan PROCESSING task if we refused to enqueue.
        await redis.delete(f"task:{task_id}")
        raise

    return JSONResponse({
        "task_id": task_id,
        "status": TaskStatus.PROCESSING,
        "url": decoded_url,
        "_links": {
            "self": {"href": f"{base_url}/llm/{task_id}"},
            "status": {"href": f"{base_url}/llm/{task_id}"}
        }
    })

def create_task_response(task: dict, task_id: str, base_url: str) -> dict:
    """Create response for task status check."""
    response = {
        "task_id": task_id,
        "status": task["status"],
        "created_at": task["created_at"],
        "url": task["url"],
        "_links": {
            "self": {"href": f"{base_url}/llm/{task_id}"},
            "refresh": {"href": f"{base_url}/llm/{task_id}"}
        }
    }

    if task["status"] == TaskStatus.COMPLETED:
        response["result"] = json.loads(task["result"])
    elif task["status"] == TaskStatus.FAILED:
        response["error"] = task["error"]

    return response

async def _dispose_crawler(crawler):
    """Close a dedicated PDF crawler (not pooled) or release a pooled one."""
    from crawl4ai.processors.pdf import PDFCrawlerStrategy
    from crawler_pool import release_crawler
    if isinstance(crawler.crawler_strategy, PDFCrawlerStrategy):
        await crawler.close()
    else:
        await release_crawler(crawler)

async def stream_results(crawler: AsyncWebCrawler, results_gen: AsyncGenerator) -> AsyncGenerator[bytes, None]:
    """Stream results with heartbeats and completion markers."""
    import json
    from utils import datetime_handler

    try:
        async for result in results_gen:
            try:
                server_memory_mb = _get_memory_mb()
                result_dict = result.model_dump()
                result_dict['server_memory_mb'] = server_memory_mb
                # Ensure fit_html is JSON-serializable
                if "fit_html" in result_dict and not (result_dict["fit_html"] is None or isinstance(result_dict["fit_html"], str)):
                    result_dict["fit_html"] = None
                # If PDF exists, encode it to base64
                if result_dict.get('pdf') is not None:
                    result_dict['pdf'] = b64encode(result_dict['pdf']).decode('utf-8')
                logger.info(f"Streaming result for {result_dict.get('url', 'unknown')}")
                data = json.dumps(result_dict, default=datetime_handler) + "\n"
                yield data.encode('utf-8')
            except Exception as e:
                logger.error(f"Serialization error: {e}")
                error_response = {"error": str(e), "url": getattr(result, 'url', 'unknown')}
                yield (json.dumps(error_response) + "\n").encode('utf-8')

        yield json.dumps({"status": "completed"}).encode('utf-8')
        
    except asyncio.CancelledError:
        logger.warning("Client disconnected during streaming")
    finally:
        if crawler:
            await _dispose_crawler(crawler)


class _SeedBatch(NamedTuple):
    """The outcome of normalizing and destination-checking one batch of seeds.

    `crawlable` are the seeds to fetch, in the caller's order. `refused` holds
    `(url, detail)` for each seed the destination check turned away, in the
    caller's order, where `detail` is the message the 400 used to carry.
    """
    crawlable: List[str]
    refused: List[Tuple[str, str]]


def _normalize_and_validate_seeds(urls: List[str]) -> _SeedBatch:
    """Prefix bare hosts with https:// and SSRF-validate every seed URL's
    destination. Shared by the streaming and non-streaming crawl handlers so a
    new entry point cannot silently skip the destination check.

    A refused seed does not fail the whole request. It is reported back as one
    failed result among the batch, the way a robots.txt refusal already is, so
    one bad URL in a sitemap-derived list cannot take a batch down (#2288). The
    detail is carried through verbatim, which is what keeps this from becoming
    a resolution oracle: an internal address and a name that does not resolve
    both still produce the same opaque "URL blocked", and the caller already
    knows the hostname it sent. A request with nothing left to crawl is still a
    rejected request, and keeps the 400 (see _require_crawlable_seeds)."""
    crawlable: List[str] = []
    refused: List[Tuple[str, str]] = []
    for url in urls:
        url = ('https://' + url) if not url.startswith(('http://', 'https://')) and not url.startswith(("raw:", "raw://")) else url
        try:
            validate_url_destination(url)
        except HTTPException as e:
            refused.append((url, e.detail))
            continue
        crawlable.append(url)
    if refused:
        # One line an operator can grep, so a refused seed is visible server-side
        # and not just inferable from the response. The URLs are the caller's own
        # and come straight back to it in the failed results. Each is truncated
        # because a seed can be arbitrarily long, and a scanner probing blocked
        # URLs should not be able to write megabytes into the log.
        shown = ", ".join(url[:200] for url, _detail in refused[:5])
        if len(refused) > 5:
            shown += f", +{len(refused) - 5} more"
        logger.warning(
            "[seeds] %d of %d seed(s) refused by the destination check, "
            "reported as failed results: %s",
            len(refused), len(urls), shown,
        )
    return _SeedBatch(crawlable, refused)


def _require_crawlable_seeds(batch: _SeedBatch) -> None:
    """Refuse a request that has no crawlable seed left.

    With every seed refused there is no batch to report per-URL failures in, so
    this stays the 400 it has always been. That also keeps a single blocked URL
    a 400, which is the contract the /md, /llm and /crawl/stream callers (and
    the existing SSRF tests) rely on.
    """
    if batch.refused and not batch.crawlable:
        raise HTTPException(status_code=400, detail=batch.refused[0][1])


def _refused_seed_result(url: str, detail: str):
    """A refused seed as a failed CrawlResult.

    Shaped like the robots.txt refusal in async_webcrawler.arun() (success
    False, 403, a marker header) so a caller handles one refused seed and one
    robots-refused seed the same way. Built as a real CrawlResult so the key
    set matches every other entry in `results` -- the SDK client rebuilds each
    one with `CrawlResult(**result)`, so a partial dict would break it.
    """
    return CrawlResult(
        url=url,
        html="",
        success=False,
        status_code=403,
        error_message=detail,
        response_headers={"X-Egress-Status": "Blocked by egress policy"},
    )


def _append_refused_results(results: List, batch: _SeedBatch) -> List:
    """Add one failed result per refused seed to `results`.

    Appended, not spliced into place: MemoryAdaptiveDispatcher.run_urls returns
    in completion order, so `results` never lined up with the caller's `urls` to
    begin with. Callers therefore already have to match a result to its seed by
    `result.url` -- which is exactly the field that makes a refused seed
    identifiable, and the thing the 400 gave them no way to recover.
    """
    if not batch.refused:
        return results
    return list(results) + [
        _refused_seed_result(url, detail) for url, detail in batch.refused
    ]


async def _prepend_refused_results(results_gen, batch: _SeedBatch):
    """Yield one failed result per refused seed, then the crawled results.

    A refusal is known before the first byte is fetched, so it goes first. A
    stream is completion-ordered like the batch path, so a caller matches
    results to seeds by `result.url` here too.

    The results are built before the first yield on purpose: this generator is
    consumed inside the response, where an exception would truncate a 200 the
    client had already been given, with no error frame and no completion marker.
    """
    for result in [_refused_seed_result(url, detail) for url, detail in batch.refused]:
        yield result
    async for result in results_gen:
        yield result


async def handle_crawl_request(
    urls: List[str],
    browser_config: dict,
    crawler_config: dict,
    config: dict,
    hooks_config: Optional[dict] = None,
    crawler_configs: Optional[List[dict]] = None,
) -> dict:
    """Handle non-streaming crawl requests with optional hooks."""
    # Track request start
    request_id = f"req_{uuid4().hex[:8]}"
    crawler = None
    is_pdf_crawl = False
    try:
        from monitor import get_monitor
        await get_monitor().track_request_start(
            request_id, "/crawl", urls[0] if urls else "batch", browser_config
        )
    except:
        pass  # Monitor not critical

    start_mem_mb = _get_memory_mb() # <--- Get memory before
    start_time = time.time()
    mem_delta_mb = None
    peak_mem_mb = start_mem_mb

    try:
        seeds = _normalize_and_validate_seeds(urls)
        _require_crawlable_seeds(seeds)
        # A refused seed comes back as a failed result rather than a 400, so the
        # rest of this handler only ever sees the seeds it may actually fetch.
        seed_count = len(urls)
        urls = seeds.crawlable
        browser_config = BrowserConfig.load(browser_config, provenance=Provenance.UNTRUSTED)
        crawler_config = CrawlerRunConfig.load(crawler_config, provenance=Provenance.UNTRUSTED)
        from egress_broker import enforce_egress
        enforce_egress(browser_config)
        from governor import clamp_deep_crawl
        clamp_deep_crawl(crawler_config)

        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=config["crawler"]["memory_threshold_percent"],
            rate_limiter=RateLimiter(
                base_delay=tuple(config["crawler"]["rate_limiter"]["base_delay"])
            ) if config["crawler"]["rate_limiter"]["enabled"] else None
        )
        
        from crawler_pool import get_crawler, release_crawler
        from crawl4ai.processors.pdf import PDFContentScrapingStrategy, PDFCrawlerStrategy
        is_pdf_crawl = isinstance(crawler_config.scraping_strategy, PDFContentScrapingStrategy)
        if is_pdf_crawl:
            if hooks_config:
                # PDFCrawlerStrategy has no browser page, so hooks can't attach to it
                raise HTTPException(status_code=400, detail="Hooks are not supported with PDFContentScrapingStrategy")
            # SSRF protection: vet the PDF download URL and every redirect hop
            crawler_config.scraping_strategy.url_validator = validate_url_destination
            # Use PDFCrawlerStrategy when scraping PDFs, as headless Chromium can't render PDFs inline
            crawler = AsyncWebCrawler(crawler_strategy=PDFCrawlerStrategy())
            await crawler.start()
        else:
            crawler = await get_crawler(browser_config)
        
        # Attach declarative hooks if provided
        hooks_status = {}
        if hooks_config:
            hooks_status = _attach_declarative_hooks(crawler, hooks_config)
            logger.info(f"Hooks attachment status: {hooks_status['status']}")
        
        base_config = config["crawler"]["base_config"]

        # Build the config(s) to pass to arun/arun_many.
        # A caller that sent per-URL crawler_configs still means them when a
        # seed is refused, so the branch keys off the ORIGINAL url count, not
        # the number that survived. The list itself is not filtered or
        # reordered: the dispatcher pairs a config to a URL by url_matcher
        # (see BaseDispatcher.select_config), not by position.
        per_url_configs = bool(crawler_configs) and seed_count > 1
        if per_url_configs:
            # Per-URL config list: deserialize each and apply base_config
            config_list = [CrawlerRunConfig.load(cc, provenance=Provenance.UNTRUSTED) for cc in crawler_configs]
            for cfg in config_list:
                for key, value in base_config.items():
                    if hasattr(cfg, key):
                        current_value = getattr(cfg, key)
                        if current_value is None or current_value == "":
                            setattr(cfg, key, value)
                # SSRF: per-URL PDF strategies need the validator wired too
                if isinstance(cfg.scraping_strategy, PDFContentScrapingStrategy):
                    cfg.scraping_strategy.url_validator = validate_url_destination
            effective_config = config_list
        else:
            # Single config (original behavior)
            for key, value in base_config.items():
                if hasattr(crawler_config, key):
                    current_value = getattr(crawler_config, key)
                    if current_value is None or current_value == "":
                        setattr(crawler_config, key, value)
            effective_config = crawler_config

        results = []
        # arun_many unless exactly one seed is left, or the caller sent per-URL
        # configs (arun_many is what pairs them to their URLs). The `!= 1` shape
        # is deliberate: /crawl and /crawl/stream reject an empty urls list, but
        # CrawlJobPayload.urls has no min_length, so arun_many([]) is still
        # reachable here and must not become an arun(urls[0]) IndexError.
        use_many = len(urls) != 1 or per_url_configs
        func = getattr(crawler, "arun_many" if use_many else "arun")
        partial_func = partial(func,
                                urls if use_many else urls[0],
                                config=effective_config,
                                dispatcher=dispatcher)
        # Optional per-crawl wall-clock deadline (config limits.wall_clock_s; 0 = none).
        from governor import wall_clock_seconds
        _deadline = wall_clock_seconds(config)
        if _deadline and _deadline > 0:
            results = await asyncio.wait_for(partial_func(), timeout=_deadline)
        else:
            results = await partial_func()
        
        # Ensure results is always a list
        if not isinstance(results, list):
            results = [results]

        # Report one failed result for each seed the destination check refused.
        results = _append_refused_results(results, seeds)

        end_mem_mb = _get_memory_mb() # <--- Get memory after
        end_time = time.time()
        
        if start_mem_mb is not None and end_mem_mb is not None:
            mem_delta_mb = end_mem_mb - start_mem_mb # <--- Calculate delta
            peak_mem_mb = max(peak_mem_mb if peak_mem_mb else 0, end_mem_mb) # <--- Get peak memory
        logger.info(f"Memory usage: Start: {start_mem_mb} MB, End: {end_mem_mb} MB, Delta: {mem_delta_mb} MB, Peak: {peak_mem_mb} MB")

        # Process results to handle PDF bytes
        processed_results = []
        for result in results:
            try:
                # Check if result has model_dump method (is a proper CrawlResult)
                if hasattr(result, 'model_dump'):
                    result_dict = result.model_dump()
                elif isinstance(result, dict):
                    result_dict = result
                else:
                    # Handle unexpected result type
                    logger.warning(f"Unexpected result type: {type(result)}")
                    result_dict = {
                        "url": str(result) if hasattr(result, '__str__') else "unknown",
                        "success": False,
                        "error_message": f"Unexpected result type: {type(result).__name__}"
                    }
                
                # if fit_html is not a string, set it to None to avoid serialization errors
                if "fit_html" in result_dict and not (result_dict["fit_html"] is None or isinstance(result_dict["fit_html"], str)):
                    result_dict["fit_html"] = None
                    
                # If PDF exists, encode it to base64
                if result_dict.get('pdf') is not None and isinstance(result_dict.get('pdf'), bytes):
                    result_dict['pdf'] = b64encode(result_dict['pdf']).decode('utf-8')
                    
                if is_pdf_crawl:
                    # PDF metadata contains datetimes that JSONResponse can't serialize
                    result_dict = json.loads(json.dumps(result_dict, default=datetime_handler))

                processed_results.append(result_dict)
            except Exception as e:
                logger.error(f"Error processing result: {e}")
                processed_results.append({
                    "url": "unknown",
                    "success": False,
                    "error_message": str(e)
                })
            
        response = {
            "success": True,
            "results": processed_results,
            "server_processing_time_s": end_time - start_time,
            "server_memory_delta_mb": mem_delta_mb,
            "server_peak_memory_mb": peak_mem_mb
        }

        # Track request completion
        try:
            from monitor import get_monitor
            await get_monitor().track_request_end(
                request_id, success=True, pool_hit=True, status_code=200
            )
        except:
            pass

        # Add hooks information if hooks were used
        if hooks_config:
            response["hooks"] = hooks_status

        return response

    except (UntrustedConfigError, HookValidationError) as e:
        # An untrusted request body tried to set a forbidden power-field,
        # construct a disallowed type, or specify an invalid hook. Client error.
        try:
            from monitor import get_monitor
            await get_monitor().track_request_end(
                request_id, success=False, error=str(e), status_code=400
            )
        except:
            pass
        raise HTTPException(status_code=400, detail=f"Rejected request: {e}")

    except asyncio.TimeoutError:
        # Per-crawl wall-clock deadline exceeded.
        raise HTTPException(status_code=504, detail="Crawl exceeded the time limit")

    except HTTPException:
        # Deliberate status (e.g. 400 SSRF "URL blocked") must pass through
        # rather than be genericized to 500 by the handler below.
        raise

    except Exception as e:
        logger.error(f"Crawl error: {str(e)}", exc_info=True)

        # Track request error
        try:
            from monitor import get_monitor
            await get_monitor().track_request_end(
                request_id, success=False, error=str(e), status_code=500
            )
        except:
            pass

        # Measure memory even on error if possible
        end_mem_mb_error = _get_memory_mb()
        if start_mem_mb is not None and end_mem_mb_error is not None:
            mem_delta_mb = end_mem_mb_error - start_mem_mb

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=json.dumps({ # Send structured error
                "error": str(e),
                "server_memory_delta_mb": mem_delta_mb,
                "server_peak_memory_mb": max(peak_mem_mb if peak_mem_mb else 0, end_mem_mb_error or 0)
            })
        )
    finally:
        if crawler:
            if is_pdf_crawl:
                await crawler.close()  # not pooled; release_crawler would be a no-op
            else:
                await release_crawler(crawler)

async def handle_stream_crawl_request(
    urls: List[str],
    browser_config: dict,
    crawler_config: dict,
    config: dict,
    hooks_config: Optional[dict] = None
) -> Tuple[AsyncWebCrawler, AsyncGenerator, Optional[Dict]]:
    """Handle streaming crawl requests with optional hooks."""
    hooks_info = None
    crawler = None
    try:
        # SSRF guard: validate every seed URL's destination before fetching,
        # mirroring handle_crawl_request. The streaming path previously skipped
        # this, leaving /crawl/stream (and /crawl with stream=true) unguarded.
        seeds = _normalize_and_validate_seeds(urls)
        _require_crawlable_seeds(seeds)
        seed_count = len(urls)
        urls = seeds.crawlable
        browser_config = BrowserConfig.load(
            browser_config, provenance=Provenance.UNTRUSTED
        )
        # browser_config.verbose = True # Set to False or remove for production stress testing
        browser_config.verbose = False
        from egress_broker import enforce_egress

        enforce_egress(browser_config)
        crawler_config = CrawlerRunConfig.load(
            crawler_config, provenance=Provenance.UNTRUSTED
        )
        from governor import clamp_deep_crawl

        clamp_deep_crawl(crawler_config)
        crawler_config.stream = True

        # Deep crawl streaming supports exactly one start URL. Keyed off the
        # caller's own count: a request for several seeds is refused for that
        # reason whether or not one of them was also refused by egress, and the
        # deep-crawl limit is not this handler's business to relax.
        if crawler_config.deep_crawl_strategy is not None and seed_count != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Deep crawling with stream currently supports exactly one URL per request. "
                    f"Received {seed_count} URLs."
                ),
            )

        from crawler_pool import get_crawler
        from crawl4ai.processors.pdf import PDFContentScrapingStrategy, PDFCrawlerStrategy
        if isinstance(crawler_config.scraping_strategy, PDFContentScrapingStrategy):
            if hooks_config:
                # PDFCrawlerStrategy has no browser page, so hooks can't attach to it
                raise HTTPException(status_code=400, detail="Hooks are not supported with PDFContentScrapingStrategy")
            # SSRF protection: vet the PDF download URL and every redirect hop
            crawler_config.scraping_strategy.url_validator = validate_url_destination
            # Use PDFCrawlerStrategy when scraping PDFs, as headless Chromium can't render PDFs inline
            crawler = AsyncWebCrawler(crawler_strategy=PDFCrawlerStrategy())
            await crawler.start()
        else:
            crawler = await get_crawler(browser_config)

        # Attach declarative hooks if provided
        if hooks_config:
            hooks_status = _attach_declarative_hooks(crawler, hooks_config)
            logger.info(f"Hooks attachment status for streaming: {hooks_status['status']}")
            hooks_info = {'status': hooks_status}

        # Deep crawl with single URL: use arun() which returns an async generator
        # mirroring the Python library's streaming behavior.
        # The guard above rejects any request that did not send exactly one seed,
        # so reaching here means seed_count == 1 and therefore len(urls) == 1.
        if crawler_config.deep_crawl_strategy is not None and len(urls) == 1:
            results_gen = await crawler.arun(
                urls[0],
                config=crawler_config,
            )
        else:
            # Default multi-URL streaming via arun_many
            dispatcher = MemoryAdaptiveDispatcher(
                memory_threshold_percent=config["crawler"]["memory_threshold_percent"],
                rate_limiter=RateLimiter(
                    base_delay=tuple(config["crawler"]["rate_limiter"]["base_delay"])
                )
            )
            results_gen = await crawler.arun_many(
                urls=urls,
                config=crawler_config,
                dispatcher=dispatcher
            )

        # Yield the refused seeds first, so a streamed batch reports a refusal
        # exactly like the non-streaming one does instead of dropping it. Their
        # position in the stream is not the caller's `urls` position, because a
        # stream's order is completion order, not request order.
        if seeds.refused:
            results_gen = _prepend_refused_results(results_gen, seeds)

        return crawler, results_gen, hooks_info

    except (UntrustedConfigError, HookValidationError) as e:
        if crawler:
            await _dispose_crawler(crawler)
        raise HTTPException(status_code=400, detail=f"Rejected request: {e}")

    except HTTPException:
        # Deliberate status (e.g. 400 SSRF "URL blocked") must pass through
        # rather than be genericized to 500 by the handler below.
        if crawler:
            await _dispose_crawler(crawler)
        raise

    except Exception as e:
        # Dispose crawler on setup error (for successful streams,
        # disposal happens in stream_results finally block)
        if crawler:
            await _dispose_crawler(crawler)
        logger.error(f"Stream crawl error: {str(e)}", exc_info=True)
        # Raising HTTPException here will prevent streaming response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def handle_crawl_job(
    redis,
    background_tasks: BackgroundTasks,
    urls: List[str],
    browser_config: Dict,
    crawler_config: Dict,
    config: Dict,
    webhook_config: Optional[Dict] = None,
    owner: Optional[str] = None,
) -> Dict:
    """
    Fire-and-forget version of handle_crawl_request.
    Creates a task in Redis, runs the heavy work in a background task,
    lets /crawl/job/{task_id} polling fetch the result.
    """
    task_id = f"crawl_{uuid4().hex[:8]}"

    # Store task data in Redis
    task_data = {
        "status": TaskStatus.PROCESSING,         # <-- keep enum values consistent
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "url": json.dumps(urls),                 # store list as JSON string
        "result": "",
        "error": "",
    }
    if owner:
        task_data["owner"] = owner

    # Store webhook config if provided
    if webhook_config:
        task_data["webhook_config"] = json.dumps(webhook_config)

    await hset_with_ttl(redis, f"task:{task_id}", task_data, config)

    # Initialize webhook service
    webhook_service = WebhookDeliveryService(config)

    async def _runner():
        try:
            result = await handle_crawl_request(
                urls=urls,
                browser_config=browser_config,
                crawler_config=crawler_config,
                config=config,
            )
            await hset_with_ttl(redis, f"task:{task_id}", {
                "status": TaskStatus.COMPLETED,
                "result": json.dumps(result),
            }, config)

            # Send webhook notification on successful completion
            await webhook_service.notify_job_completion(
                task_id=task_id,
                task_type="crawl",
                status="completed",
                urls=urls,
                webhook_config=webhook_config,
                result=result
            )

        except Exception as exc:
            await hset_with_ttl(redis, f"task:{task_id}", {
                "status": TaskStatus.FAILED,
                "error": str(exc),
            }, config)

            # Send webhook notification on failure
            await webhook_service.notify_job_completion(
                task_id=task_id,
                task_type="crawl",
                status="failed",
                urls=urls,
                webhook_config=webhook_config,
                error=str(exc)
            )

    try:
        _enqueue_job(background_tasks, _runner, principal=owner)
    except HTTPException:
        await redis.delete(f"task:{task_id}")
        raise
    return {"task_id": task_id}
