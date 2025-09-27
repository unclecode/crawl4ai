import os
import json
import asyncio
import pathlib
from typing import List, Tuple, Dict
from functools import partial
from uuid import uuid4
from datetime import datetime, date
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
    LLMExtractionStrategy,
    CacheMode,
    BrowserConfig,
    MemoryAdaptiveDispatcher,
    RateLimiter, 
    LLMConfig
)
from crawl4ai.utils import perform_completion_with_backoff
from crawl4ai.content_filter_strategy import (
    PruningContentFilter,
    BM25ContentFilter,
    LLMContentFilter
)
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
    datetime_handler
)
from utils import _ensure_within_base_dir

import psutil, time

logger = logging.getLogger(__name__)

# --- Helper to get memory ---
def _get_memory_mb():
    try:
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception as e:
        logger.warning(f"Could not get memory info: {e}")
        return None


async def handle_llm_qa(
    url: str,
    query: str,
    config: dict
) -> str:
    """Process QA using LLM with crawled content as context."""
    try:
        if not url.startswith(('http://', 'https://')) and not url.startswith(("raw:", "raw://")):
            url = 'https://' + url
        # Extract base URL by finding last '?q=' occurrence
        last_q_index = url.rfind('?q=')
        if last_q_index != -1:
            url = url[:last_q_index]

        # Get markdown content
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url)
            if not result.success:
                from server import _extract_user_friendly_error
                error_msg = result.error_message or "Failed to fetch content"
                friendly_error = _extract_user_friendly_error(error_msg, "LLM QA")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=friendly_error
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
            api_token=get_llm_api_key(config)
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"QA processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def process_llm_extraction(
    redis: aioredis.Redis,
    config: dict,
    task_id: str,
    url: str,
    instruction: str,
    schema: Optional[str] = None,
    cache: str = "0",
    provider: Optional[str] = None
) -> None:
    """Process LLM extraction in background."""
    try:
        # Validate provider
        is_valid, error_msg = validate_llm_provider(config, provider)
        if not is_valid:
            await redis.hset(f"task:{task_id}", mapping={
                "status": TaskStatus.FAILED,
                "error": error_msg
            })
            return
        api_key = get_llm_api_key(config, provider)
        llm_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider=provider or config["llm"]["provider"],
                api_token=api_key
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
                    cache_mode=cache_mode
                )
            )

        if not result.success:
            await redis.hset(f"task:{task_id}", mapping={
                "status": TaskStatus.FAILED,
                "error": result.error_message
            })
            return

        try:
            content = json.loads(result.extracted_content)
        except json.JSONDecodeError:
            content = result.extracted_content
        await redis.hset(f"task:{task_id}", mapping={
            "status": TaskStatus.COMPLETED,
            "result": json.dumps(content)
        })

    except Exception as e:
        logger.error(f"LLM extraction error: {str(e)}", exc_info=True)
        await redis.hset(f"task:{task_id}", mapping={
            "status": TaskStatus.FAILED,
            "error": str(e)
        })

async def handle_markdown_request(
    url: str,
    filter_type: FilterType,
    query: Optional[str] = None,
    cache: str = "0",
    config: Optional[dict] = None,
    provider: Optional[str] = None
) -> str:
    """Handle markdown generation requests."""
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

        if filter_type == FilterType.RAW:
            md_generator = DefaultMarkdownGenerator()
        else:
            content_filter = {
                FilterType.FIT: PruningContentFilter(),
                FilterType.BM25: BM25ContentFilter(user_query=query or ""),
                FilterType.LLM: LLMContentFilter(
                    llm_config=LLMConfig(
                        provider=provider or config["llm"]["provider"],
                        api_token=get_llm_api_key(config, provider),
                    ),
                    instruction=query or "Extract main content"
                )
            }[filter_type]
            md_generator = DefaultMarkdownGenerator(content_filter=content_filter)

        cache_mode = CacheMode.ENABLED if cache == "1" else CacheMode.WRITE_ONLY

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=decoded_url,
                config=CrawlerRunConfig(
                    markdown_generator=md_generator,
                    scraping_strategy=LXMLWebScrapingStrategy(),
                    cache_mode=cache_mode
                )
            )

            if not result.success:
                from server import _extract_user_friendly_error
                error_msg = result.error_message or "Failed to fetch content"
                friendly_error = _extract_user_friendly_error(error_msg, "Markdown generation")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=friendly_error
                )

            return (result.markdown.raw_markdown 
                   if filter_type == FilterType.RAW 
                   else result.markdown.fit_markdown)

    except Exception as e:
        logger.error(f"Markdown error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
    provider: Optional[str] = None
) -> JSONResponse:
    """Handle LLM extraction requests."""
    base_url = get_base_url(request)
    
    try:
        if is_task_id(input_path):
            return await handle_task_status(
                redis, input_path, base_url
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
            provider
        )

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
    keep: bool = False
) -> JSONResponse:
    """Handle task status check requests."""
    task = await redis.hgetall(f"task:{task_id}")
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
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
    provider: Optional[str] = None
) -> JSONResponse:
    """Create and initialize a new task."""
    decoded_url = unquote(input_path)
    if not decoded_url.startswith(('http://', 'https://')) and not decoded_url.startswith(("raw:", "raw://")):
        decoded_url = 'https://' + decoded_url

    from datetime import datetime
    task_id = f"llm_{int(datetime.now().timestamp())}_{id(background_tasks)}"
    
    await redis.hset(f"task:{task_id}", mapping={
        "status": TaskStatus.PROCESSING,
        "created_at": datetime.now().isoformat(),
        "url": decoded_url
    })

    background_tasks.add_task(
        process_llm_extraction,
        redis,
        config,
        task_id,
        decoded_url,
        query,
        schema,
        cache,
        provider
    )

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
    output_path: str = None
) -> dict:
    """Handle non-streaming crawl requests."""
    start_mem_mb = _get_memory_mb() # <--- Get memory before
    start_time = time.time()
    mem_delta_mb = None
    peak_mem_mb = start_mem_mb
    
    try:
        urls = [('https://' + url) if not url.startswith(('http://', 'https://')) and not url.startswith(("raw:", "raw://")) else url for url in urls]
        browser_config = BrowserConfig.load(browser_config)
        if getattr(browser_config, "headless", True) is False:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Non-headless browser sessions are not supported inside the Docker image. "
                "Set browser_config.headless=true or omit the flag."
            )
        crawler_config = CrawlerRunConfig.load(crawler_config)

        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=config["crawler"]["memory_threshold_percent"],
            rate_limiter=RateLimiter(
                base_delay=tuple(config["crawler"]["rate_limiter"]["base_delay"])
            ) if config["crawler"]["rate_limiter"]["enabled"] else None
        )
        
        from crawler_pool import get_crawler
        crawler = await get_crawler(browser_config)

        # crawler: AsyncWebCrawler = AsyncWebCrawler(config=browser_config)
        # await crawler.start()
        
        base_config = config["crawler"]["base_config"]
        # Iterate on key-value pairs in global_config then use haseattr to set them 
        for key, value in base_config.items():
            if hasattr(crawler_config, key):
                setattr(crawler_config, key, value)

        results = []
        func = getattr(crawler, "arun" if len(urls) == 1 else "arun_many")
        payload = urls[0] if len(urls) == 1 else urls
        partial_func = partial(
            func,
            payload,
            config=crawler_config,
            dispatcher=dispatcher,
        )
        try:
            results_gen = await partial_func()
            # Handle both list and async generator results
            if hasattr(results_gen, '__aiter__'):
                # It's an async generator, collect all results
                results = []
                async for result in results_gen:
                    results.append(result)
            else:
                # Normalize non-async-generator results
                if results_gen is None:
                    results = []
                elif isinstance(results_gen, (list, tuple)):
                    # It's already a sequence
                    results = list(results_gen)
                else:
                    # Single model/object, wrap it in a list
                    results = [results_gen]
        except Exception as bulk_error:
            logger.warning("Bulk crawl failed, retrying per-URL: %s", bulk_error)
            fallback_results = []
            for url in urls:
                try:
                    single_result = await crawler.arun(
                        url=url,
                        config=crawler_config,
                        dispatcher=dispatcher,
                    )
                    fallback_results.append(single_result)
                except Exception as url_error:
                    logger.warning("Crawl failed for %s: %s", url, url_error)
                    fallback_results.append(
                        {
                            "url": url,
                            "success": False,
                            "error_message": str(url_error),
                        }
                    )
            results = fallback_results

        # await crawler.close()
        
        end_mem_mb = _get_memory_mb() # <--- Get memory after
        end_time = time.time()
        
        if start_mem_mb is not None and end_mem_mb is not None:
            mem_delta_mb = end_mem_mb - start_mem_mb # <--- Calculate delta
            peak_mem_mb = max(peak_mem_mb if peak_mem_mb else 0, end_mem_mb) # <--- Get peak memory
        logger.info(f"Memory usage: Start: {start_mem_mb} MB, End: {end_mem_mb} MB, Delta: {mem_delta_mb} MB, Peak: {peak_mem_mb} MB")

        # Process results to handle PDF bytes
        processed_results = []
        for result in results:
            if hasattr(result, "model_dump"):
                result_dict = result.model_dump()
            elif isinstance(result, dict):
                result_dict = result.copy()
                result_dict.setdefault("success", False)
            else:
                result_dict = {
                    "url": getattr(result, "url", ""),
                    "success": getattr(result, "success", False),
                    "error_message": getattr(result, "error_message", "Unknown error"),
                }

            # Clean up non-serializable properties with recursive normalization
            def _normalize_value(val):
                if isinstance(val, (datetime, date)):
                    return datetime_handler(val)
                if isinstance(val, (os.PathLike, pathlib.Path)):
                    return os.fspath(val)
                if isinstance(val, bytes):
                    return b64encode(val).decode('utf-8')
                if isinstance(val, dict):
                    return {k: _normalize_value(v) for k, v in val.items()}
                if isinstance(val, (list, tuple, set)):
                    return [_normalize_value(v) for v in val]
                return val

            cleaned_dict = {}
            for key, value in result_dict.items():
                # Special handling for PDF binary data (preserve existing logic)
                if key == 'pdf' and value is not None and isinstance(value, bytes):
                    cleaned_dict[key] = b64encode(value).decode('utf-8')
                    continue

                # Recursively normalize the value
                normalized = _normalize_value(value)
                try:
                    json.dumps(normalized)
                    cleaned_dict[key] = normalized
                except (TypeError, ValueError):
                    logger.warning(
                        "Skipping non-serializable field '%s' of type %s: %s",
                        key,
                        type(value),
                        value,
                    )

            processed_results.append(cleaned_dict)

        response_data = {
            "success": True,
            "results": processed_results,
            "server_processing_time_s": end_time - start_time,
            "server_memory_delta_mb": mem_delta_mb,
            "server_peak_memory_mb": peak_mem_mb
        }

        # Handle output_path if provided
        if output_path:
            binary_base_dir = config.get("binary", {}).get("default_dir", "/tmp/crawl4ai-exports")
            abs_path = os.path.abspath(output_path)

            # Validate path is within allowed directory
            _ensure_within_base_dir(abs_path, binary_base_dir)

            # Ensure directory exists
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            # Write JSON to file
            try:
                from utils import datetime_handler
                with open(abs_path, 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, ensure_ascii=False, indent=2, default=datetime_handler)
                return {
                    "success": True,
                    "path": abs_path,
                    "results_count": len(processed_results),
                    "server_processing_time_s": end_time - start_time,
                    "server_memory_delta_mb": mem_delta_mb,
                    "server_peak_memory_mb": peak_mem_mb
                }
            except (OSError, TypeError) as write_error:
                logger.warning("crawl file write failed: %s", write_error, exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to write to {abs_path}: {str(write_error)}"
                )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crawl error: {str(e)}", exc_info=True)
        if 'crawler' in locals() and crawler.ready: # Check if crawler was initialized and started
            #  try:
            #      await crawler.close()
            #  except Exception as close_e:
            #       logger.error(f"Error closing crawler during exception handling: {close_e}")
            logger.error(f"Error closing crawler during exception handling: {str(e)}")

        # Measure memory even on error if possible
        end_mem_mb_error = _get_memory_mb()
        if start_mem_mb is not None and end_mem_mb_error is not None:
            mem_delta_mb = end_mem_mb_error - start_mem_mb

        import json as json_module  # Import locally to avoid any scoping issues
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=json_module.dumps({ # Send structured error
                "error": str(e),
                "server_memory_delta_mb": mem_delta_mb,
                "server_peak_memory_mb": max(peak_mem_mb if peak_mem_mb else 0, end_mem_mb_error or 0)
            })
        )

async def handle_stream_crawl_request(
    urls: List[str],
    browser_config: dict,
    crawler_config: dict,
    config: dict
) -> Tuple[AsyncWebCrawler, AsyncGenerator]:
    """Handle streaming crawl requests."""
    try:
        browser_config = BrowserConfig.load(browser_config)
        # browser_config.verbose = True # Set to False or remove for production stress testing
        browser_config.verbose = False
        crawler_config = CrawlerRunConfig.load(crawler_config)
        crawler_config.scraping_strategy = LXMLWebScrapingStrategy()
        crawler_config.stream = True

        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=config["crawler"]["memory_threshold_percent"],
            rate_limiter=RateLimiter(
                base_delay=tuple(config["crawler"]["rate_limiter"]["base_delay"])
            )
        )

        from crawler_pool import get_crawler
        crawler = await get_crawler(browser_config)

        # crawler = AsyncWebCrawler(config=browser_config)
        # await crawler.start()

        results_gen = await crawler.arun_many(
            urls=urls,
            config=crawler_config,
            dispatcher=dispatcher
        )

        return crawler, results_gen

    except Exception as e:
        # Make sure to close crawler if started during an error here
        if 'crawler' in locals() and crawler.ready:
            #  try:
            #       await crawler.close()
            #  except Exception as close_e:
            #       logger.error(f"Error closing crawler during stream setup exception: {close_e}")
            logger.error(f"Error closing crawler during stream setup exception: {str(e)}")
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
) -> Dict:
    """
    Fire-and-forget version of handle_crawl_request.
    Creates a task in Redis, runs the heavy work in a background task,
    lets /crawl/job/{task_id} polling fetch the result.
    """
    task_id = f"crawl_{uuid4().hex[:8]}"
    await redis.hset(f"task:{task_id}", mapping={
        "status": TaskStatus.PROCESSING,         # <-- keep enum values consistent
        "created_at": datetime.utcnow().isoformat(),
        "url": json.dumps(urls),                 # store list as JSON string
        "result": "",
        "error": "",
    })

    async def _runner():
        try:
            result = await handle_crawl_request(
                urls=urls,
                browser_config=browser_config,
                crawler_config=crawler_config,
                config=config,
            )
            await redis.hset(f"task:{task_id}", mapping={
                "status": TaskStatus.COMPLETED,
                "result": json.dumps(result),
            })
            await asyncio.sleep(5)  # Give Redis time to process the update
        except Exception as exc:
            await redis.hset(f"task:{task_id}", mapping={
                "status": TaskStatus.FAILED,
                "error": str(exc),
            })

    background_tasks.add_task(_runner)
    return {"task_id": task_id}
