import asyncio
import json
import logging
import os
import time
from base64 import b64encode
from datetime import datetime, timezone
from functools import partial
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Any
from urllib.parse import unquote
from fastapi import HTTPException, Request, status
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis
from crawl4ai import (
    AsyncUrlSeeder,
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMConfig,
    LLMExtractionStrategy,
    MemoryAdaptiveDispatcher,
    PlaywrightAdapter,
    RateLimiter,
    SeedingConfig,
    UndetectedAdapter,
)

# Import StealthAdapter with fallback for compatibility
try:
    from crawl4ai import StealthAdapter
except ImportError:
    # Fallback: import directly from browser_adapter module
    try:
        import os
        import sys
        # Add the project root to path for development
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        sys.path.insert(0, project_root)
        from crawl4ai.browser_adapter import StealthAdapter
    except ImportError:
        # If all else fails, create a simple fallback
        from crawl4ai.browser_adapter import PlaywrightAdapter

        class StealthAdapter(PlaywrightAdapter):
            """Fallback StealthAdapter that uses PlaywrightAdapter"""
            pass
from crawl4ai.content_filter_strategy import (
    BM25ContentFilter,
    LLMContentFilter,
    PruningContentFilter,
)
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.utils import perform_completion_with_backoff

# Import missing utility functions and types
try:
    from utils import (
        FilterType, TaskStatus, get_base_url, is_task_id,
        get_llm_api_key, get_llm_temperature, get_llm_base_url,
        validate_llm_provider
    )
except ImportError:
    # Fallback definitions for development/testing
    from enum import Enum
    
    class FilterType(str, Enum):
        RAW = "raw"
        FIT = "fit"
        BM25 = "bm25"
        LLM = "llm"
    
    class TaskStatus(str, Enum):
        PROCESSING = "processing"
        FAILED = "failed"
        COMPLETED = "completed"
    
    def get_base_url(request): 
        return f"{request.url.scheme}://{request.url.netloc}"
    
    def is_task_id(value: str): 
        return value.startswith("llm_") and "_" in value
    
    def get_llm_api_key(config, provider=None): 
        return None
    
    def get_llm_temperature(config, provider=None): 
        return 0.7
    
    def get_llm_base_url(config, provider=None): 
        return None
    
    def validate_llm_provider(config, provider): 
        return True, None

logger = logging.getLogger(__name__)


# --- Helper to get memory ---
def _get_memory_mb():
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception as e:
        logger.warning("Could not get memory info: %s", e)
        return None


# --- Helper to get browser adapter based on anti_bot_strategy ---
def _get_browser_adapter(anti_bot_strategy: str, browser_config: BrowserConfig):
    """Get the appropriate browser adapter based on anti_bot_strategy."""
    if anti_bot_strategy == "stealth":
        return StealthAdapter()
    elif anti_bot_strategy == "undetected":
        return UndetectedAdapter()
    elif anti_bot_strategy == "max_evasion":
        # Use undetected for maximum evasion
        return UndetectedAdapter()
    else:  # "default"
        # If stealth is enabled in browser config, use stealth adapter
        if getattr(browser_config, "enable_stealth", False):
            return StealthAdapter()
        return PlaywrightAdapter()


# --- Helper to apply headless setting ---
def _apply_headless_setting(browser_config: BrowserConfig, headless: bool):
    """Apply headless setting to browser config."""
    browser_config.headless = headless
    return browser_config


# --- Helper to create proxy rotation strategy ---
def _create_proxy_rotation_strategy(
    strategy_name: Optional[str],
    proxies: Optional[List[Dict[str, Any]]],
    failure_threshold: int = 3,
    recovery_time: int = 300
):
    """Create proxy rotation strategy from request parameters."""
    if not strategy_name or not proxies:
        return None
    
    # Import proxy strategies
    from crawl4ai.proxy_strategy import (
        RoundRobinProxyStrategy, RandomProxyStrategy, 
        LeastUsedProxyStrategy, FailureAwareProxyStrategy
    )
    from crawl4ai.async_configs import ProxyConfig
    
    # Convert proxy inputs to ProxyConfig objects
    proxy_configs = []
    try:
        for proxy in proxies:
            if isinstance(proxy, dict):
                # Validate required fields
                if "server" not in proxy:
                    raise ValueError(f"Proxy configuration missing 'server' field: {proxy}")
                proxy_configs.append(ProxyConfig.from_dict(proxy))
            else:
                raise ValueError(f"Invalid proxy format: {type(proxy)}")
    except Exception as e:
        raise ValueError(f"Invalid proxy configuration: {str(e)}")
    
    if not proxy_configs:
        return None
    
    # Strategy factory with optimized implementations
    strategy_name = strategy_name.lower()
    
    if strategy_name == "round_robin":
        return RoundRobinProxyStrategy(proxy_configs)
    elif strategy_name == "random":
        return RandomProxyStrategy(proxy_configs)
    elif strategy_name == "least_used":
        return LeastUsedProxyStrategy(proxy_configs)
    elif strategy_name == "failure_aware":
        return FailureAwareProxyStrategy(
            proxy_configs, 
            failure_threshold=failure_threshold,
            recovery_time=recovery_time
        )
    else:
        raise ValueError(
            f"Unsupported proxy rotation strategy: {strategy_name}. "
            f"Available: round_robin, random, least_used, failure_aware"
        )


async def handle_llm_qa(url: str, query: str, config: dict) -> str:
    """Process QA using LLM with crawled content as context."""
    try:
        if not url.startswith(("http://", "https://")) and not url.startswith(
            ("raw:", "raw://")
        ):
            url = "https://" + url
        # Extract base URL by finding last '?q=' occurrence
        last_q_index = url.rfind("?q=")
        if last_q_index != -1:
            url = url[:last_q_index]

        # Get markdown content
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url)
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error_message,
                )
            content = result.markdown.fit_markdown or result.markdown.raw_markdown

        # Create prompt and get LLM response
        prompt = f"""Use the following content as context to answer the question.
    Content:
    {content}

    Question: {query}

    Answer:"""

        # api_token=os.environ.get(config["llm"].get("api_key_env", ""))

        response = perform_completion_with_backoff(
            provider=config["llm"]["provider"],
            prompt_with_variables=prompt,
            api_token=get_llm_api_key(config),  # Returns None to let litellm handle it
            temperature=get_llm_temperature(config),
            base_url=get_llm_base_url(config),
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"QA processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def process_llm_extraction(
    redis: aioredis.Redis,
    config: dict,
    task_id: str,
    url: str,
    instruction: str,
    schema: Optional[str] = None,
    cache: str = "0",
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
) -> None:
    """Process LLM extraction in background."""
    try:
        # Validate provider
        is_valid, error_msg = validate_llm_provider(config, provider)
        if not is_valid:
            await redis.hset(
                f"task:{task_id}",
                mapping={"status": TaskStatus.FAILED, "error": error_msg},
            )
            return
        api_key = get_llm_api_key(
            config, provider
        )  # Returns None to let litellm handle it
        llm_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider=provider or config["llm"]["provider"],
                api_token=api_key,
                temperature=temperature or get_llm_temperature(config, provider),
                base_url=base_url or get_llm_base_url(config, provider),
            ),
            instruction=instruction,
            schema=json.loads(schema) if schema else None,
        )

        cache_mode = CacheMode.ENABLED if cache == "1" else CacheMode.WRITE_ONLY

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    extraction_strategy=llm_strategy,
                    scraping_strategy=LXMLWebScrapingStrategy(),
                    cache_mode=cache_mode,
                ),
            )

        if not result.success:
            await redis.hset(
                f"task:{task_id}",
                mapping={"status": TaskStatus.FAILED, "error": result.error_message},
            )
            return

        try:
            content = json.loads(result.extracted_content)
        except json.JSONDecodeError:
            content = result.extracted_content
        await redis.hset(
            f"task:{task_id}",
            mapping={"status": TaskStatus.COMPLETED, "result": json.dumps(content)},
        )

    except Exception as e:
        logger.error(f"LLM extraction error: {str(e)}", exc_info=True)
        await redis.hset(
            f"task:{task_id}", mapping={"status": TaskStatus.FAILED, "error": str(e)}
        )


async def handle_markdown_request(
    url: str,
    filter_type: FilterType,
    query: Optional[str] = None,
    cache: str = "0",
    config: Optional[dict] = None,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
) -> str:
    """Handle markdown generation requests."""
    try:
        # Validate provider if using LLM filter
        if filter_type == FilterType.LLM:
            is_valid, error_msg = validate_llm_provider(config, provider)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
                )
        decoded_url = unquote(url)
        if not decoded_url.startswith(
            ("http://", "https://")
        ) and not decoded_url.startswith(("raw:", "raw://")):
            decoded_url = "https://" + decoded_url

        if filter_type == FilterType.RAW:
            md_generator = DefaultMarkdownGenerator()
        else:
            content_filter = {
                FilterType.FIT: PruningContentFilter(),
                FilterType.BM25: BM25ContentFilter(user_query=query or ""),
                FilterType.LLM: LLMContentFilter(
                    llm_config=LLMConfig(
                        provider=provider or config["llm"]["provider"],
                        api_token=get_llm_api_key(
                            config, provider
                        ),  # Returns None to let litellm handle it
                        temperature=temperature
                        or get_llm_temperature(config, provider),
                        base_url=base_url or get_llm_base_url(config, provider),
                    ),
                    instruction=query or "Extract main content",
                ),
            }[filter_type]
            md_generator = DefaultMarkdownGenerator(content_filter=content_filter)

        cache_mode = CacheMode.ENABLED if cache == "1" else CacheMode.WRITE_ONLY

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=decoded_url,
                config=CrawlerRunConfig(
                    markdown_generator=md_generator,
                    scraping_strategy=LXMLWebScrapingStrategy(),
                    cache_mode=cache_mode,
                ),
            )

            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error_message,
                )

            return (
                result.markdown.raw_markdown
                if filter_type == FilterType.RAW
                else result.markdown.fit_markdown
            )

    except Exception as e:
        logger.error(f"Markdown error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


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
    temperature: Optional[float] = None,
    api_base_url: Optional[str] = None,
) -> JSONResponse:
    """Handle LLM extraction requests."""
    base_url = get_base_url(request)

    try:
        if is_task_id(input_path):
            return await handle_task_status(redis, input_path, base_url)

        if not query:
            return JSONResponse(
                {
                    "message": "Please provide an instruction",
                    "_links": {
                        "example": {
                            "href": f"{base_url}/llm/{input_path}?q=Extract+main+content",
                            "title": "Try this example",
                        }
                    },
                }
            )

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
            temperature,
            api_base_url,
        )

    except Exception as e:
        logger.error(f"LLM endpoint error: {str(e)}", exc_info=True)
        return JSONResponse(
            {"error": str(e), "_links": {"retry": {"href": str(request.url)}}},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def handle_task_status(
    redis: aioredis.Redis, task_id: str, base_url: str, *, keep: bool = False
) -> JSONResponse:
    """Handle task status check requests."""
    task = await redis.hgetall(f"task:{task_id}")
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    task = decode_redis_hash(task)
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
    temperature: Optional[float] = None,
    api_base_url: Optional[str] = None,
) -> JSONResponse:
    """Create and initialize a new task."""
    decoded_url = unquote(input_path)
    if not decoded_url.startswith(
        ("http://", "https://")
    ) and not decoded_url.startswith(("raw:", "raw://")):
        decoded_url = "https://" + decoded_url

    from datetime import datetime

    task_id = f"llm_{int(datetime.now().timestamp())}_{id(background_tasks)}"

    await redis.hset(
        f"task:{task_id}",
        mapping={
            "status": TaskStatus.PROCESSING,
            "created_at": datetime.now().isoformat(),
            "url": decoded_url,
        },
    )

    background_tasks.add_task(
        process_llm_extraction,
        redis,
        config,
        task_id,
        decoded_url,
        query,
        schema,
        cache,
        provider,
        temperature,
        api_base_url,
    )

    return JSONResponse(
        {
            "task_id": task_id,
            "status": TaskStatus.PROCESSING,
            "url": decoded_url,
            "_links": {
                "self": {"href": f"{base_url}/llm/{task_id}"},
                "status": {"href": f"{base_url}/llm/{task_id}"},
            },
        }
    )


def create_task_response(task: dict, task_id: str, base_url: str) -> dict:
    """Create response for task status check."""
    response = {
        "task_id": task_id,
        "status": task["status"],
        "created_at": task["created_at"],
        "url": task["url"],
        "_links": {
            "self": {"href": f"{base_url}/llm/{task_id}"},
            "refresh": {"href": f"{base_url}/llm/{task_id}"},
        },
    }

    if task["status"] == TaskStatus.COMPLETED:
        response["result"] = json.loads(task["result"])
    elif task["status"] == TaskStatus.FAILED:
        response["error"] = task["error"]

    return response


async def stream_results(
    crawler: AsyncWebCrawler, results_gen: AsyncGenerator
) -> AsyncGenerator[bytes, None]:
    """Stream results with heartbeats and completion markers."""
    import json

    from utils import datetime_handler

    try:
        async for result in results_gen:
            try:
                server_memory_mb = _get_memory_mb()
                result_dict = result.model_dump()
                result_dict["server_memory_mb"] = server_memory_mb
                # Ensure fit_html is JSON-serializable
                if "fit_html" in result_dict and not (
                    result_dict["fit_html"] is None
                    or isinstance(result_dict["fit_html"], str)
                ):
                    result_dict["fit_html"] = None
                # If PDF exists, encode it to base64
                if result_dict.get("pdf") is not None:
                    result_dict["pdf"] = b64encode(result_dict["pdf"]).decode("utf-8")
                logger.info(f"Streaming result for {result_dict.get('url', 'unknown')}")
                data = json.dumps(result_dict, default=datetime_handler) + "\n"
                yield data.encode("utf-8")
            except Exception as e:
                logger.error(f"Serialization error: {e}")
                error_response = {
                    "error": str(e),
                    "url": getattr(result, "url", "unknown"),
                }
                yield (json.dumps(error_response) + "\n").encode("utf-8")

        yield json.dumps({"status": "completed"}).encode("utf-8")

    except asyncio.CancelledError:
        logger.warning("Client disconnected during streaming")
    finally:
        # try:
        #     await crawler.close()
        # except Exception as e:
        #     logger.error(f"Crawler cleanup error: {e}")
        pass


async def handle_crawl_request(
    urls: List[str],
    browser_config: dict,
    crawler_config: dict,
    config: dict,
    hooks_config: Optional[dict] = None,
    anti_bot_strategy: str = "default",
    headless: bool = True,
    proxy_rotation_strategy: Optional[str] = None,
    proxies: Optional[List[Dict[str, Any]]] = None,
    proxy_failure_threshold: int = 3,
    proxy_recovery_time: int = 300,
) -> dict:
    """Handle non-streaming crawl requests with optional hooks."""
    start_mem_mb = _get_memory_mb()  # <--- Get memory before
    start_time = time.time()
    mem_delta_mb = None
    peak_mem_mb = start_mem_mb
    hook_manager = None

    try:
        urls = [
            ("https://" + url)
            if not url.startswith(("http://", "https://"))
            and not url.startswith(("raw:", "raw://"))
            else url
            for url in urls
        ]
        browser_config = BrowserConfig.load(browser_config)
        _apply_headless_setting(browser_config, headless)
        crawler_config = CrawlerRunConfig.load(crawler_config)

        # Configure proxy rotation strategy if specified
        if proxy_rotation_strategy and proxies:
            try:
                proxy_strategy = _create_proxy_rotation_strategy(
                    proxy_rotation_strategy,
                    proxies,
                    proxy_failure_threshold,
                    proxy_recovery_time
                )
                crawler_config.proxy_rotation_strategy = proxy_strategy
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Configure browser adapter based on anti_bot_strategy
        browser_adapter = _get_browser_adapter(anti_bot_strategy, browser_config)

        # TODO: add support for other dispatchers

        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=config["crawler"]["memory_threshold_percent"],
            rate_limiter=RateLimiter(
                base_delay=tuple(config["crawler"]["rate_limiter"]["base_delay"])
            )
            if config["crawler"]["rate_limiter"]["enabled"]
            else None,
        )

        from crawler_pool import get_crawler

        crawler = await get_crawler(browser_config, browser_adapter)

        # crawler: AsyncWebCrawler = AsyncWebCrawler(config=browser_config)
        # await crawler.start()

        # Attach hooks if provided
        hooks_status = {}
        if hooks_config:
            from hook_manager import UserHookManager, attach_user_hooks_to_crawler

            hook_manager = UserHookManager(timeout=hooks_config.get("timeout", 30))
            hooks_status, hook_manager = await attach_user_hooks_to_crawler(
                crawler,
                hooks_config.get("code", {}),
                timeout=hooks_config.get("timeout", 30),
                hook_manager=hook_manager,
            )
            logger.info(f"Hooks attachment status: {hooks_status['status']}")

        base_config = config["crawler"]["base_config"]
        # Iterate on key-value pairs in global_config then use hasattr to set them
        for key, value in base_config.items():
            if hasattr(crawler_config, key):
                current_value = getattr(crawler_config, key)
                # Only set base config if user didn't provide a value
                if current_value is None or current_value == "":
                    setattr(crawler_config, key, value)

        results = []
        func = getattr(crawler, "arun" if len(urls) == 1 else "arun_many")
        partial_func = partial(
            func,
            urls[0] if len(urls) == 1 else urls,
            config=crawler_config,
            dispatcher=dispatcher,
        )
        results = await partial_func()

        # Ensure results is always a list
        if not isinstance(results, list):
            results = [results]

        # await crawler.close()

        end_mem_mb = _get_memory_mb()  # <--- Get memory after
        end_time = time.time()

        if start_mem_mb is not None and end_mem_mb is not None:
            mem_delta_mb = end_mem_mb - start_mem_mb  # <--- Calculate delta
            peak_mem_mb = max(
                peak_mem_mb if peak_mem_mb else 0, end_mem_mb
            )  # <--- Get peak memory
        logger.info(
            f"Memory usage: Start: {start_mem_mb} MB, End: {end_mem_mb} MB, Delta: {mem_delta_mb} MB, Peak: {peak_mem_mb} MB"
        )

        # Process results to handle PDF bytes
        processed_results = []
        for result in results:
            try:
                # Check if result has model_dump method (is a proper CrawlResult)
                if hasattr(result, "model_dump"):
                    result_dict = result.model_dump()
                elif isinstance(result, dict):
                    result_dict = result
                else:
                    # Handle unexpected result type
                    logger.warning(f"Unexpected result type: {type(result)}")
                    result_dict = {
                        "url": str(result) if hasattr(result, "__str__") else "unknown",
                        "success": False,
                        "error_message": f"Unexpected result type: {type(result).__name__}",
                    }

                # if fit_html is not a string, set it to None to avoid serialization errors
                if "fit_html" in result_dict and not (
                    result_dict["fit_html"] is None
                    or isinstance(result_dict["fit_html"], str)
                ):
                    result_dict["fit_html"] = None

                # If PDF exists, encode it to base64
                if result_dict.get("pdf") is not None and isinstance(
                    result_dict.get("pdf"), bytes
                ):
                    result_dict["pdf"] = b64encode(result_dict["pdf"]).decode("utf-8")

                processed_results.append(result_dict)
            except Exception as e:
                logger.error(f"Error processing result: {e}")
                processed_results.append(
                    {"url": "unknown", "success": False, "error_message": str(e)}
                )

        response = {
            "success": True,
            "results": processed_results,
            "server_processing_time_s": end_time - start_time,
            "server_memory_delta_mb": mem_delta_mb,
            "server_peak_memory_mb": peak_mem_mb,
        }

        # Add hooks information if hooks were used
        if hooks_config and hook_manager:
            from hook_manager import UserHookManager

            if isinstance(hook_manager, UserHookManager):
                try:
                    # Ensure all hook data is JSON serializable
                    hook_data = {
                        "status": hooks_status,
                        "execution_log": hook_manager.execution_log,
                        "errors": hook_manager.errors,
                        "summary": hook_manager.get_summary(),
                    }
                    # Test that it's serializable
                    json.dumps(hook_data)
                    response["hooks"] = hook_data
                except (TypeError, ValueError) as e:
                    logger.error(f"Hook data not JSON serializable: {e}")
                    response["hooks"] = {
                        "status": {
                            "status": "error",
                            "message": "Hook data serialization failed",
                        },
                        "execution_log": [],
                        "errors": [{"error": str(e)}],
                        "summary": {},
                    }

        return response

    except Exception as e:
        logger.error(f"Crawl error: {str(e)}", exc_info=True)
        if (
            "crawler" in locals() and crawler.ready
        ):  # Check if crawler was initialized and started
            #  try:
            #      await crawler.close()
            #  except Exception as close_e:
            #       logger.error(f"Error closing crawler during exception handling: {close_e}")
            logger.error(f"Error closing crawler during exception handling: {str(e)}")

        # Measure memory even on error if possible
        end_mem_mb_error = _get_memory_mb()
        if start_mem_mb is not None and end_mem_mb_error is not None:
            mem_delta_mb = end_mem_mb_error - start_mem_mb

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=json.dumps(
                {  # Send structured error
                    "error": str(e),
                    "server_memory_delta_mb": mem_delta_mb,
                    "server_peak_memory_mb": max(
                        peak_mem_mb if peak_mem_mb else 0, end_mem_mb_error or 0
                    ),
                }
            ),
        )


async def handle_stream_crawl_request(
    urls: List[str],
    browser_config: dict,
    crawler_config: dict,
    config: dict,
    hooks_config: Optional[dict] = None,
    anti_bot_strategy: str = "default",
    headless: bool = True,
    proxy_rotation_strategy: Optional[str] = None,
    proxies: Optional[List[Dict[str, Any]]] = None,
    proxy_failure_threshold: int = 3,
    proxy_recovery_time: int = 300,
) -> Tuple[AsyncWebCrawler, AsyncGenerator, Optional[Dict]]:
    """Handle streaming crawl requests with optional hooks."""
    hooks_info = None
    try:
        browser_config = BrowserConfig.load(browser_config)
        # browser_config.verbose = True # Set to False or remove for production stress testing
        browser_config.verbose = False
        _apply_headless_setting(browser_config, headless)
        crawler_config = CrawlerRunConfig.load(crawler_config)
        crawler_config.scraping_strategy = LXMLWebScrapingStrategy()
        crawler_config.stream = True

        # Configure proxy rotation strategy if specified
        if proxy_rotation_strategy and proxies:
            try:
                proxy_strategy = _create_proxy_rotation_strategy(
                    proxy_rotation_strategy,
                    proxies,
                    proxy_failure_threshold,
                    proxy_recovery_time
                )
                crawler_config.proxy_rotation_strategy = proxy_strategy
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Configure browser adapter based on anti_bot_strategy
        browser_adapter = _get_browser_adapter(anti_bot_strategy, browser_config)

        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=config["crawler"]["memory_threshold_percent"],
            rate_limiter=RateLimiter(
                base_delay=tuple(config["crawler"]["rate_limiter"]["base_delay"])
            ),
        )

        from crawler_pool import get_crawler

        crawler = await get_crawler(browser_config, browser_adapter)

        # crawler = AsyncWebCrawler(config=browser_config)
        # await crawler.start()

        # Attach hooks if provided
        if hooks_config:
            from hook_manager import UserHookManager, attach_user_hooks_to_crawler

            hook_manager = UserHookManager(timeout=hooks_config.get("timeout", 30))
            hooks_status, hook_manager = await attach_user_hooks_to_crawler(
                crawler,
                hooks_config.get("code", {}),
                timeout=hooks_config.get("timeout", 30),
                hook_manager=hook_manager,
            )
            logger.info(
                f"Hooks attachment status for streaming: {hooks_status['status']}"
            )
            # Include hook manager in hooks_info for proper tracking
            hooks_info = {"status": hooks_status, "manager": hook_manager}

        results_gen = await crawler.arun_many(
            urls=urls, config=crawler_config, dispatcher=dispatcher
        )

        return crawler, results_gen, hooks_info

    except Exception as e:
        # Make sure to close crawler if started during an error here
        if "crawler" in locals() and crawler.ready:
            #  try:
            #       await crawler.close()
            #  except Exception as close_e:
            #       logger.error(f"Error closing crawler during stream setup exception: {close_e}")
            logger.error(
                f"Error closing crawler during stream setup exception: {str(e)}"
            )
        logger.error(f"Stream crawl error: {str(e)}", exc_info=True)
        # Raising HTTPException here will prevent streaming response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def handle_crawl_job(
    redis,
    background_tasks: BackgroundTasks,
    urls: List[str],
    browser_config: Dict,
    crawler_config: Dict,
    config: Dict,
) -> Dict:
    """
    Fire-and-forget version of handle_crawl_request.
    Creates a task in Redis, runs the heavy work in a background task,
    lets /crawl/job/{task_id} polling fetch the result.
    """
    task_id = f"crawl_{uuid4().hex[:8]}"
    await redis.hset(
        f"task:{task_id}",
        mapping={
            "status": TaskStatus.PROCESSING,  # <-- keep enum values consistent
            "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            "url": json.dumps(urls),  # store list as JSON string
            "result": "",
            "error": "",
        },
    )

    async def _runner():
        try:
            result = await handle_crawl_request(
                urls=urls,
                browser_config=browser_config,
                crawler_config=crawler_config,
                config=config,
            )
            await redis.hset(
                f"task:{task_id}",
                mapping={
                    "status": TaskStatus.COMPLETED,
                    "result": json.dumps(result),
                },
            )
            await asyncio.sleep(5)  # Give Redis time to process the update
        except Exception as exc:
            await redis.hset(
                f"task:{task_id}",
                mapping={
                    "status": TaskStatus.FAILED,
                    "error": str(exc),
                },
            )

    background_tasks.add_task(_runner)
    return {"task_id": task_id}


async def handle_seed(url, cfg):
    # Create the configuration from the request body
    try:
        seeding_config = cfg
        config = SeedingConfig(**seeding_config)

        # Use an async context manager for the seeder
        async with AsyncUrlSeeder() as seeder:
            # The seeder's 'urls' method expects a domain, not a full URL
            urls = await seeder.urls(url, config)
        return urls
    except Exception as e:
        return {
            "seeded_urls": [],
            "count": 0,
            "message": "No URLs found for the given domain and configuration.",
        }
