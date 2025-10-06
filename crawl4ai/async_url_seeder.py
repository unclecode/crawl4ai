"""
async_url_seeder.py
Fast async URL discovery for Crawl4AI

Features
--------
* Common-Crawl streaming via httpx.AsyncClient (HTTP/2, keep-alive)
* robots.txt → sitemap chain (.gz + nested indexes) via async httpx
* Per-domain CDX result cache on disk (~/.crawl4ai/<index>_<domain>_<hash>.jsonl)
* Optional HEAD-only liveness check
* Optional partial <head> download + meta parsing
* Global hits-per-second rate-limit via asyncio.Semaphore
* Concurrency in the thousands — fine on a single event-loop
"""

from __future__ import annotations
import aiofiles
import asyncio
import gzip
import hashlib
import io
import json
import os
import pathlib
import re
import time
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union
from urllib.parse import quote, urljoin

import httpx
import fnmatch
try:
    from lxml import html as lxml_html
    from lxml import etree
    LXML = True
except ImportError:
    LXML = False
try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False
try:
    import rank_bm25
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

# Import AsyncLoggerBase from crawl4ai's logger module
# Assuming crawl4ai/async_logger.py defines AsyncLoggerBase
# You might need to adjust this import based on your exact file structure
# Import AsyncLogger for default if needed
from .async_logger import AsyncLoggerBase, AsyncLogger

# Import SeedingConfig for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .async_configs import SeedingConfig


# ────────────────────────────────────────────────────────────────────────── consts
COLLINFO_URL = "https://index.commoncrawl.org/collinfo.json"
# CACHE_DIR = pathlib.Path("~/.crawl4ai").expanduser() # REMOVED: now managed by __init__
# CACHE_DIR.mkdir(exist_ok=True) # REMOVED: now managed by __init__
# INDEX_CACHE = CACHE_DIR / "latest_cc_index.txt" # REMOVED: now managed by __init__
TTL = timedelta(days=7)  # Keeping this constant as it's a seeder-specific TTL

_meta_rx = re.compile(
    r'<meta\s+(?:[^>]*?(?:name|property|http-equiv)\s*=\s*["\']?([^"\' >]+)[^>]*?content\s*=\s*["\']?([^"\' >]+)[^>]*?)\/?>',
    re.I)
_charset_rx = re.compile(r'<meta\s+[^>]*charset=["\']?([^"\' >]+)', re.I)
_title_rx = re.compile(r'<title>(.*?)</title>', re.I | re.S)
_link_rx = re.compile(
    r'<link\s+[^>]*rel=["\']?([^"\' >]+)[^>]*href=["\']?([^"\' >]+)', re.I)

# ────────────────────────────────────────────────────────────────────────── helpers


def _match(url: str, pattern: str) -> bool:
    if fnmatch.fnmatch(url, pattern):
        return True
    canon = url.split("://", 1)[-1]
    return (fnmatch.fnmatch(canon, pattern)
            or (canon.startswith("www.") and fnmatch.fnmatch(canon[4:], pattern)))


def _parse_head(src: str) -> Dict[str, Any]:
    if LXML:
        try:
            if isinstance(src, str):
                # strip Unicode, let lxml decode
                src = src.encode("utf-8", "replace")
            doc = lxml_html.fromstring(src)
        except (ValueError, etree.ParserError):
            return {}        # malformed, bail gracefully
        info: Dict[str, Any] = {
            "title": (doc.find(".//title").text or "").strip()
            if doc.find(".//title") is not None else None,
            "charset": None,
            "meta": {}, "link": {}, "jsonld": []
        }
        for el in doc.xpath(".//meta"):
            k = el.attrib.get("name") or el.attrib.get(
                "property") or el.attrib.get("http-equiv")
            if k:
                info["meta"][k.lower()] = el.attrib.get("content", "")
            elif "charset" in el.attrib:
                info["charset"] = el.attrib["charset"].lower()
        for el in doc.xpath(".//link"):
            rel_attr = el.attrib.get("rel", "")
            if not rel_attr:
                continue
            # Handle multiple space-separated rel values
            rel_values = rel_attr.lower().split()
            entry = {a: el.attrib[a] for a in (
                "href", "as", "type", "hreflang") if a in el.attrib}
            # Add entry for each rel value
            for rel in rel_values:
                info["link"].setdefault(rel, []).append(entry)
        # Extract JSON-LD structured data
        for script in doc.xpath('.//script[@type="application/ld+json"]'):
            if script.text:
                try:
                    jsonld_data = json.loads(script.text.strip())
                    info["jsonld"].append(jsonld_data)
                except json.JSONDecodeError:
                    pass
        # Extract html lang attribute
        html_elem = doc.find(".//html")
        if html_elem is not None:
            info["lang"] = html_elem.attrib.get("lang", "")
        return info
    # regex fallback
    info: Dict[str, Any] = {"title": None, "charset": None,
                            "meta": {}, "link": {}, "jsonld": [], "lang": ""}
    m = _title_rx.search(src)
    info["title"] = m.group(1).strip() if m else None
    for k, v in _meta_rx.findall(src):
        info["meta"][k.lower()] = v
    m = _charset_rx.search(src)
    info["charset"] = m.group(1).lower() if m else None
    for rel, href in _link_rx.findall(src):
        info["link"].setdefault(rel.lower(), []).append({"href": href})
    # Try to extract JSON-LD with regex
    jsonld_pattern = re.compile(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
    for match in jsonld_pattern.findall(src):
        try:
            jsonld_data = json.loads(match.strip())
            info["jsonld"].append(jsonld_data)
        except json.JSONDecodeError:
            pass
    # Try to extract lang attribute
    lang_match = re.search(r'<html[^>]*lang=["\']?([^"\' >]+)', src, re.I)
    if lang_match:
        info["lang"] = lang_match.group(1)
    return info

# ────────────────────────────────────────────────────────────────────────── class


class AsyncUrlSeeder:
    """
    Async version of UrlSeeder.
    Call pattern is await/async for / async with.

    Public coroutines
    -----------------
    await seed.urls(...)
        returns List[Dict[str,Any]]  (url, status, head_data)
    await seed.many_urls(...)
        returns Dict[str, List[Dict[str,Any]]]
    await seed.close()
        closes the HTTP client if owned by seeder
    
    Usage examples
    --------------
    # Manual cleanup:
    seeder = AsyncUrlSeeder()
    try:
        urls = await seeder.urls("example.com", config)
    finally:
        await seeder.close()
    
    # Using async context manager (recommended):
    async with AsyncUrlSeeder() as seeder:
        urls = await seeder.urls("example.com", config)
    
    # Reusing existing client:
    client = httpx.AsyncClient()
    seeder = AsyncUrlSeeder(client=client)
    urls = await seeder.urls("example.com", config)
    # No need to close seeder, as it doesn't own the client
    """

    def __init__(
        self,
        ttl: timedelta = TTL,
        client: Optional[httpx.AsyncClient] = None,
        logger: Optional[AsyncLoggerBase] = None,  # NEW: Add logger parameter
        # NEW: Add base_directory
        base_directory: Optional[Union[str, pathlib.Path]] = None,
        cache_root: Optional[Union[str, Path]] = None,
    ):
        self.ttl = ttl
        self._owns_client = client is None  # Track if we created the client
        self.client = client or httpx.AsyncClient(http2=True, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) +AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        })
        self.logger = logger  # Store the logger instance
        self.base_directory = pathlib.Path(base_directory or os.getenv(
            "CRAWL4_AI_BASE_DIRECTORY", Path.home()))  # Resolve base_directory
        self.cache_dir = self.base_directory / ".crawl4ai" / \
            "seeder_cache"  # NEW: Specific cache dir for seeder
        self.cache_dir.mkdir(parents=True, exist_ok=True)  # Ensure it exists
        self.index_cache_path = self.cache_dir / \
            "latest_cc_index.txt"  # NEW: Index cache path

        # defer – grabbing the index inside an active loop blows up
        self.index_id: Optional[str] = None
        self._rate_sem: Optional[asyncio.Semaphore] = None

        # ───────── cache dirs ─────────
        self.cache_root = Path(os.path.expanduser(
            cache_root or "~/.cache/url_seeder"))
        (self.cache_root / "live").mkdir(parents=True, exist_ok=True)
        (self.cache_root / "head").mkdir(exist_ok=True)

    def _log(self, level: str, message: str, tag: str = "URL_SEED", **kwargs: Any):
        """Helper to log messages using the provided logger, if available."""
        if self.logger:
            log_method = getattr(self.logger, level, None)
            if log_method:
                log_method(message=message, tag=tag,
                           params=kwargs.get('params', {}))
            # else: # Fallback for unknown level, should not happen with AsyncLoggerBase
            #     print(f"[{tag}] {level.upper()}: {message.format(**kwargs)}")

    # ───────── cache helpers ─────────
    def _cache_path(self, kind: str, url: str) -> Path:
        h = hashlib.sha1(url.encode()).hexdigest()
        return self.cache_root / kind / f"{h}.json"

    async def _cache_get(self, kind: str, url: str) -> Optional[Dict[str, Any]]:
        p = self._cache_path(kind, url)
        if not p.exists():
            return None
        if time.time()-p.stat().st_mtime > self.ttl.total_seconds():
            return None
        try:
            async with aiofiles.open(p, "r") as f:
                return json.loads(await f.read())
        except Exception:
            return None

    async def _cache_set(self, kind: str, url: str, data: Dict[str, Any]) -> None:
        try:
            async with aiofiles.open(self._cache_path(kind, url), "w") as f:
                await f.write(json.dumps(data, separators=(",", ":")))
        except Exception:
            pass

    # ─────────────────────────────── discovery entry

    async def urls(self,
                   domain: str,
                   config: "SeedingConfig",
                   ) -> List[Dict[str, Any]]:
        """
        Fetch URLs for a domain using configuration from SeedingConfig.

        Parameters
        ----------
        domain : str
            The domain to fetch URLs for (e.g., "example.com")
        config : SeedingConfig
            Configuration object containing all seeding parameters
        """
        # Extract parameters from config
        pattern = config.pattern or "*"
        source = config.source
        live_check = config.live_check
        extract_head = config.extract_head
        concurrency = config.concurrency
        head_timeout = 5  # Default timeout for HEAD requests
        hits_per_sec = config.hits_per_sec
        self.force = config.force  # Store force flag as instance attribute
        force = config.force
        verbose = config.verbose if config.verbose is not None else (
            self.logger.verbose if self.logger else False)
        max_urls = config.max_urls if config.max_urls is not None else -1
        query = config.query
        score_threshold = config.score_threshold
        scoring_method = config.scoring_method

        # Ensure seeder's logger verbose matches the config's verbose if it's set
        if self.logger and hasattr(self.logger, 'verbose') and config.verbose is not None:
            self.logger.verbose = config.verbose

        # ensure we have the latest CC collection id
        if self.index_id is None:
            self.index_id = await self._latest_index()

        # Parse source parameter - split by '+' to get list of sources
        sources = source.split('+')
        valid_sources = {"cc", "sitemap"}
        for s in sources:
            if s not in valid_sources:
                raise ValueError(
                    f"Invalid source '{s}'. Valid sources are: {', '.join(valid_sources)}")

        if hits_per_sec:
            if hits_per_sec <= 0:
                self._log(
                    "warning", "hits_per_sec must be positive. Disabling rate limiting.", tag="URL_SEED")
                self._rate_sem = None
            else:
                self._rate_sem = asyncio.Semaphore(hits_per_sec)
        else:
            self._rate_sem = None  # Ensure it's None if no rate limiting

        self._log("info", "Starting URL seeding for {domain} with source={source}",
                  params={"domain": domain, "source": source}, tag="URL_SEED")

        # choose stream
        async def gen():
            if "sitemap" in sources:
                self._log("debug", "Fetching from sitemaps...", tag="URL_SEED")
                async for u in self._from_sitemaps(domain, pattern, force):
                    yield u
            if "cc" in sources:
                self._log("debug", "Fetching from Common Crawl...",
                          tag="URL_SEED")
                async for u in self._from_cc(domain, pattern, force):
                    yield u

        # Use bounded queue to prevent RAM spikes with large domains
        queue_size = min(10000, max(1000, concurrency * 100))  # Dynamic size based on concurrency
        queue = asyncio.Queue(maxsize=queue_size)
        producer_done = asyncio.Event()
        stop_event = asyncio.Event()
        seen: set[str] = set()
        filter_nonsense = config.filter_nonsense_urls  # Extract this for passing to workers

        async def producer():
            try:
                async for u in gen():
                    if u in seen:
                        self._log("debug", "Skipping duplicate URL: {url}",
                                  params={"url": u}, tag="URL_SEED")
                        continue
                    if stop_event.is_set():
                        self._log(
                            "info", "Producer stopping due to max_urls limit.", tag="URL_SEED")
                        break
                    seen.add(u)
                    await queue.put(u)  # Will block if queue is full, providing backpressure
            except Exception as e:
                self._log("error", "Producer encountered an error: {error}", params={
                          "error": str(e)}, tag="URL_SEED")
            finally:
                producer_done.set()
                self._log("debug", "Producer finished.", tag="URL_SEED")

        async def worker(res_list: List[Dict[str, Any]]):
            while True:
                if queue.empty() and producer_done.is_set():
                    # self._log("debug", "Worker exiting: queue empty and producer done.", tag="URL_SEED")
                    break
                try:
                    # Increased timeout slightly
                    url = await asyncio.wait_for(queue.get(), 5)
                except asyncio.TimeoutError:
                    continue  # Keep checking queue and producer_done status
                except Exception as e:
                    self._log("error", "Worker failed to get URL from queue: {error}", params={
                              "error": str(e)}, tag="URL_SEED")
                    continue

                if max_urls > 0 and len(res_list) >= max_urls:
                    self._log(
                        "info",
                        "Worker stopping due to max_urls limit.",
                        tag="URL_SEED",
                    )
                    stop_event.set()

                    # mark the current item done
                    queue.task_done()

                    # flush whatever is still sitting in the queue so
                    # queue.join() can finish cleanly
                    while not queue.empty():
                        try:
                            queue.get_nowait()
                            queue.task_done()
                        except asyncio.QueueEmpty:
                            break
                    break

                if self._rate_sem:  # global QPS control
                    async with self._rate_sem:
                        await self._validate(url, res_list, live_check, extract_head,
                                             head_timeout, verbose, query, score_threshold, scoring_method,
                                             filter_nonsense)
                else:
                    await self._validate(url, res_list, live_check, extract_head,
                                         head_timeout, verbose, query, score_threshold, scoring_method,
                                         filter_nonsense)
                queue.task_done()  # Mark task as done for queue.join() if ever used

        # launch
        results: List[Dict[str, Any]] = []
        prod_task = asyncio.create_task(producer())
        workers = [asyncio.create_task(worker(results))
                   for _ in range(concurrency)]

        # Wait for all workers to finish
        await asyncio.gather(prod_task, *workers)
        await queue.join()  # Ensure all queued items are processed

        self._log("info", "Finished URL seeding for {domain}. Total URLs: {count}",
                  params={"domain": domain, "count": len(results)}, tag="URL_SEED")

        # Apply BM25 scoring if query was provided
        if query and extract_head and scoring_method == "bm25":
            # Apply collective BM25 scoring across all documents
            results = await self._apply_bm25_scoring(results, config)
            
            # Filter by score threshold if specified
            if score_threshold is not None:
                original_count = len(results)
                results = [r for r in results if r.get("relevance_score", 0) >= score_threshold]
                if original_count > len(results):
                    self._log("info", "Filtered {filtered} URLs below score threshold {threshold}",
                              params={"filtered": original_count - len(results), "threshold": score_threshold}, tag="URL_SEED")
            
            # Sort by relevance score
            results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
            self._log("info", "Sorted {count} URLs by relevance score for query: '{query}'",
                      params={"count": len(results), "query": query}, tag="URL_SEED")
        elif query and not extract_head:
            self._log(
                "warning", "Query provided but extract_head is False. Enable extract_head for relevance scoring.", tag="URL_SEED")

        return results[:max_urls] if max_urls > 0 else results

    async def many_urls(
        self,
        domains: Sequence[str],
        config: "SeedingConfig",
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch URLs for many domains in parallel.

        Parameters
        ----------
        domains : Sequence[str]
            List of domains to fetch URLs for
        config : SeedingConfig
            Configuration object containing all seeding parameters

        Returns a {domain: urls-list} dict.
        """
        self._log("info", "Starting URL seeding for {count} domains...",
                  params={"count": len(domains)}, tag="URL_SEED")

        # Ensure seeder's logger verbose matches the config's verbose if it's set
        if self.logger and hasattr(self.logger, 'verbose') and config.verbose is not None:
            self.logger.verbose = config.verbose

        tasks = [
            self.urls(domain, config)
            for domain in domains
        ]
        results = await asyncio.gather(*tasks)

        final_results = dict(zip(domains, results))
        self._log(
            "info", "Finished URL seeding for multiple domains.", tag="URL_SEED")
        return final_results

    async def extract_head_for_urls(
        self,
        urls: List[str],
        config: Optional["SeedingConfig"] = None,
        concurrency: int = 10,
        timeout: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract head content for a custom list of URLs using URLSeeder's parallel processing.
        
        This method reuses URLSeeder's efficient parallel processing, caching, and head extraction
        logic to process a custom list of URLs rather than discovering URLs from sources.
        
        Parameters
        ----------
        urls : List[str]
            List of URLs to extract head content from
        config : SeedingConfig, optional
            Configuration object. If None, uses default settings for head extraction
        concurrency : int, default=10
            Number of concurrent requests
        timeout : int, default=5
            Timeout for each request in seconds
            
        Returns
        -------
        List[Dict[str, Any]]
            List of dictionaries containing url, status, head_data, and optional relevance_score
        """
        # Create default config if none provided
        if config is None:
            # Import here to avoid circular imports
            from .async_configs import SeedingConfig
            config = SeedingConfig(
                extract_head=True,
                concurrency=concurrency,
                verbose=False
            )
        
        # Override concurrency and ensure head extraction is enabled
        config.concurrency = concurrency
        config.extract_head = True
        
        self._log("info", "Starting head extraction for {count} custom URLs",
                  params={"count": len(urls)}, tag="URL_SEED")
        
        # Setup rate limiting if specified in config
        if config.hits_per_sec:
            if config.hits_per_sec <= 0:
                self._log("warning", "hits_per_sec must be positive. Disabling rate limiting.", tag="URL_SEED")
                self._rate_sem = None
            else:
                self._rate_sem = asyncio.Semaphore(config.hits_per_sec)
        else:
            self._rate_sem = None
        
        # Use bounded queue to prevent memory issues with large URL lists
        queue_size = min(10000, max(1000, concurrency * 100))
        queue = asyncio.Queue(maxsize=queue_size)
        producer_done = asyncio.Event()
        stop_event = asyncio.Event()
        seen: set[str] = set()
        
        # Results collection
        results: List[Dict[str, Any]] = []
        
        async def producer():
            """Producer to feed URLs into the queue."""
            try:
                for url in urls:
                    if url in seen:
                        self._log("debug", "Skipping duplicate URL: {url}",
                                  params={"url": url}, tag="URL_SEED")
                        continue
                    if stop_event.is_set():
                        break
                    seen.add(url)
                    await queue.put(url)
            finally:
                producer_done.set()
        
        async def worker(res_list: List[Dict[str, Any]]):
            """Worker to process URLs from the queue."""
            while True:
                try:
                    # Wait for URL or producer completion
                    url = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    if producer_done.is_set() and queue.empty():
                        break
                    continue
                
                try:
                    # Use existing _validate method which handles head extraction, caching, etc.
                    await self._validate(
                        url, res_list, 
                        live=False,  # We're not doing live checks, just head extraction
                        extract=True,  # Always extract head content
                        timeout=timeout,
                        verbose=config.verbose or False,
                        query=config.query,
                        score_threshold=config.score_threshold,
                        scoring_method=config.scoring_method or "bm25",
                        filter_nonsense=config.filter_nonsense_urls
                    )
                except Exception as e:
                    self._log("error", "Failed to process URL {url}: {error}",
                              params={"url": url, "error": str(e)}, tag="URL_SEED")
                    # Add failed entry to results
                    res_list.append({
                        "url": url,
                        "status": "failed",
                        "head_data": {},
                        "error": str(e)
                    })
                finally:
                    queue.task_done()
        
        # Start producer
        producer_task = asyncio.create_task(producer())
        
        # Start workers
        worker_tasks = []
        for _ in range(concurrency):
            worker_task = asyncio.create_task(worker(results))
            worker_tasks.append(worker_task)
        
        # Wait for producer to finish
        await producer_task
        
        # Wait for all items to be processed
        await queue.join()
        
        # Cancel workers
        for task in worker_tasks:
            task.cancel()
        
        # Wait for workers to finish canceling
        await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # Apply BM25 scoring if query is provided
        if config.query and config.scoring_method == "bm25":
            results = await self._apply_bm25_scoring(results, config)
        
        # Apply score threshold filtering
        if config.score_threshold is not None:
            results = [r for r in results if r.get("relevance_score", 0) >= config.score_threshold]
        
        # Sort by relevance score if available
        if any("relevance_score" in r for r in results):
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        self._log("info", "Completed head extraction for {count} URLs, {success} successful",
                  params={
                      "count": len(urls),
                      "success": len([r for r in results if r.get("status") == "valid"])
                  }, tag="URL_SEED")
        
        return results

    async def _apply_bm25_scoring(self, results: List[Dict[str, Any]], config: "SeedingConfig") -> List[Dict[str, Any]]:
        """Apply BM25 scoring to results that have head_data."""
        if not HAS_BM25:
            self._log("warning", "BM25 scoring requested but rank_bm25 not available", tag="URL_SEED")
            return results
        
        # Extract text contexts from head data
        text_contexts = []
        valid_results = []
        
        for result in results:
            if result.get("status") == "valid" and result.get("head_data"):
                text_context = self._extract_text_context(result["head_data"])
                if text_context:
                    text_contexts.append(text_context)
                    valid_results.append(result)
                else:
                    # Use URL-based scoring as fallback
                    score = self._calculate_url_relevance_score(config.query, result["url"])
                    result["relevance_score"] = float(score)
            elif result.get("status") == "valid":
                # No head data but valid URL - use URL-based scoring
                score = self._calculate_url_relevance_score(config.query, result["url"])
                result["relevance_score"] = float(score)
        
        # Calculate BM25 scores for results with text context
        if text_contexts and valid_results:
            scores = await asyncio.to_thread(self._calculate_bm25_score, config.query, text_contexts)
            for i, result in enumerate(valid_results):
                if i < len(scores):
                    result["relevance_score"] = float(scores[i])
        
        return results

    async def _resolve_head(self, url: str) -> Optional[str]:
        """
        HEAD-probe a URL.

        Returns:
            * the same URL if it answers 2xx,
            * the absolute redirect target if it answers 3xx,
            * None on any other status or network error.
        """
        try:
            r = await self.client.head(url, timeout=10, follow_redirects=False)

            # direct hit
            if 200 <= r.status_code < 300:
                return str(r.url)

            # single level redirect
            if r.status_code in (301, 302, 303, 307, 308):
                loc = r.headers.get("location")
                if loc:
                    return urljoin(url, loc)

            return None

        except Exception as e:
            self._log("debug", "HEAD {url} failed: {err}",
                      params={"url": url, "err": str(e)}, tag="URL_SEED")
            return None

    # ─────────────────────────────── CC
    async def _from_cc(self, domain: str, pattern: str, force: bool):
        import re
        digest = hashlib.md5(pattern.encode()).hexdigest()[:8]

        # ── normalise for CC   (strip scheme, query, fragment)
        raw = re.sub(r'^https?://', '', domain).split('#',
                                                      1)[0].split('?', 1)[0].lstrip('.')

        # ── sanitize only for cache-file name
        safe = re.sub('[/?#]+', '_', raw)
        path = self.cache_dir / f"{self.index_id}_{safe}_{digest}.jsonl"

        if path.exists() and not force:
            self._log("info", "Loading CC URLs for {domain} from cache: {path}",
                      params={"domain": domain, "path": path}, tag="URL_SEED")
            async with aiofiles.open(path, "r") as fp:
                async for line in fp:
                    url = line.strip()
                    if _match(url, pattern):
                        yield url
            return

        # build CC glob – if a path is present keep it, else add trailing /*
        glob = f"*.{raw}*" if '/' in raw else f"*.{raw}/*"
        url = f"https://index.commoncrawl.org/{self.index_id}-index?url={quote(glob, safe='*')}&output=json"

        retries = (1, 3, 7)
        self._log("info", "Fetching CC URLs for {domain} from Common Crawl index: {url}",
                  params={"domain": domain, "url": url}, tag="URL_SEED")
        for i, d in enumerate(retries+(-1,)):  # last -1 means don't retry
            try:
                async with self.client.stream("GET", url) as r:
                    r.raise_for_status()
                    async with aiofiles.open(path, "w") as fp:
                        async for line in r.aiter_lines():
                            rec = json.loads(line)
                            u = rec["url"]
                            await fp.write(u+"\n")
                            if _match(u, pattern):
                                yield u
                return
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503 and i < len(retries):
                    self._log("warning", "Common Crawl API returned 503 for {domain}. Retrying in {delay}s.",
                              params={"domain": domain, "delay": retries[i]}, tag="URL_SEED")
                    await asyncio.sleep(retries[i])
                    continue
                self._log("error", "HTTP error fetching CC index for {domain}: {error}",
                          params={"domain": domain, "error": str(e)}, tag="URL_SEED")
                raise
            except Exception as e:
                self._log("error", "Error fetching CC index for {domain}: {error}",
                          params={"domain": domain, "error": str(e)}, tag="URL_SEED")
                raise

    # ─────────────────────────────── Sitemaps
    async def _from_sitemaps(self, domain: str, pattern: str, force: bool = False):
        """
        1. Probe default sitemap locations.
        2. If none exist, parse robots.txt for alternative sitemap URLs.
        3. Yield only URLs that match `pattern`.
        """

       # ── cache file (same logic as _from_cc)
        host = re.sub(r'^https?://', '', domain).rstrip('/')
        host = re.sub('[/?#]+', '_', domain)
        digest = hashlib.md5(pattern.encode()).hexdigest()[:8]
        path = self.cache_dir / f"sitemap_{host}_{digest}.jsonl"

        if path.exists() and not force:
            self._log("info", "Loading sitemap URLs for {d} from cache: {p}",
                      params={"d": host, "p": str(path)}, tag="URL_SEED")
            async with aiofiles.open(path, "r") as fp:
                async for line in fp:
                    url = line.strip()
                    if _match(url, pattern):
                        yield url
            return

        # 1️⃣ direct sitemap probe
        # strip any scheme so we can handle https → http fallback
        host = re.sub(r'^https?://', '', domain).rstrip('/')

        schemes = ('https', 'http')  # prefer TLS, downgrade if needed
        for scheme in schemes:
            for suffix in ("/sitemap.xml", "/sitemap_index.xml"):
                sm = f"{scheme}://{host}{suffix}"
                sm = await self._resolve_head(sm)
                if sm:
                    self._log("info", "Found sitemap at {url}", params={
                              "url": sm}, tag="URL_SEED")
                    async with aiofiles.open(path, "w") as fp:
                        async for u in self._iter_sitemap(sm):
                            await fp.write(u + "\n")
                            if _match(u, pattern):
                                yield u
                    return

        # 2️⃣ robots.txt fallback
        robots = f"https://{domain.rstrip('/')}/robots.txt"
        try:
            r = await self.client.get(robots, timeout=10, follow_redirects=True)
            if not 200 <= r.status_code < 300:
                self._log("warning", "robots.txt unavailable for {d} HTTP{c}", params={
                          "d": domain, "c": r.status_code}, tag="URL_SEED")
                return
            sitemap_lines = [l.split(":", 1)[1].strip(
            ) for l in r.text.splitlines() if l.lower().startswith("sitemap:")]
        except Exception as e:
            self._log("warning", "Failed to fetch robots.txt for {d}: {e}", params={
                      "d": domain, "e": str(e)}, tag="URL_SEED")
            return

        if sitemap_lines:
            async with aiofiles.open(path, "w") as fp:
                for sm in sitemap_lines:
                    async for u in self._iter_sitemap(sm):
                        await fp.write(u + "\n")
                        if _match(u, pattern):
                            yield u

    async def _iter_sitemap(self, url: str):
        try:
            r = await self.client.get(url, timeout=15, follow_redirects=True)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._log("warning", "Failed to fetch sitemap {url}: HTTP {status_code}",
                      params={"url": url, "status_code": e.response.status_code}, tag="URL_SEED")
            return
        except httpx.RequestError as e:
            self._log("warning", "Network error fetching sitemap {url}: {error}",
                      params={"url": url, "error": str(e)}, tag="URL_SEED")
            return
        except Exception as e:
            self._log("error", "Unexpected error fetching sitemap {url}: {error}",
                      params={"url": url, "error": str(e)}, tag="URL_SEED")
            return

        data = gzip.decompress(r.content) if url.endswith(".gz") else r.content

        # Detect if this is a sitemap index by checking for <sitemapindex> or presence of <sitemap> elements
        is_sitemap_index = False
        sub_sitemaps = []
        regular_urls = []

        # Use lxml for XML parsing if available, as it's generally more robust
        if LXML:
            try:
                # Use XML parser for sitemaps, not HTML parser
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(data, parser=parser)

                # Define namespace for sitemap
                ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

                # Check for sitemap index entries
                sitemap_locs = root.xpath('//s:sitemap/s:loc', namespaces=ns)
                if sitemap_locs:
                    is_sitemap_index = True
                    for sitemap_elem in sitemap_locs:
                        loc = sitemap_elem.text.strip() if sitemap_elem.text else ""
                        if loc:
                            sub_sitemaps.append(loc)

                # If not a sitemap index, get regular URLs
                if not is_sitemap_index:
                    for loc_elem in root.xpath('//s:url/s:loc', namespaces=ns):
                        loc = loc_elem.text.strip() if loc_elem.text else ""
                        if loc:
                            regular_urls.append(loc)
            except Exception as e:
                self._log("error", "LXML parsing error for sitemap {url}: {error}",
                          params={"url": url, "error": str(e)}, tag="URL_SEED")
                return
        else:  # Fallback to xml.etree.ElementTree
            import xml.etree.ElementTree as ET
            try:
                # Parse the XML
                root = ET.fromstring(data)
                # Remove namespace from tags for easier processing
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}')[1]

                # Check for sitemap index entries
                sitemaps = root.findall('.//sitemap')
                if sitemaps:
                    is_sitemap_index = True
                    for sitemap in sitemaps:
                        loc_elem = sitemap.find('loc')
                        if loc_elem is not None and loc_elem.text:
                            sub_sitemaps.append(loc_elem.text.strip())

                # If not a sitemap index, get regular URLs
                if not is_sitemap_index:
                    for url_elem in root.findall('.//url'):
                        loc_elem = url_elem.find('loc')
                        if loc_elem is not None and loc_elem.text:
                            regular_urls.append(loc_elem.text.strip())
            except Exception as e:
                self._log("error", "ElementTree parsing error for sitemap {url}: {error}",
                          params={"url": url, "error": str(e)}, tag="URL_SEED")
                return

        # Process based on type
        if is_sitemap_index and sub_sitemaps:
            self._log("info", "Processing sitemap index with {count} sub-sitemaps in parallel",
                      params={"count": len(sub_sitemaps)}, tag="URL_SEED")

            # Create a bounded queue for results to prevent RAM issues
            # For sitemap indexes, use a larger queue as we expect many URLs
            queue_size = min(50000, len(sub_sitemaps) * 1000)  # Estimate 1000 URLs per sitemap
            result_queue = asyncio.Queue(maxsize=queue_size)
            completed_count = 0
            total_sitemaps = len(sub_sitemaps)

            async def process_subsitemap(sitemap_url: str):
                try:
                    self._log(
                        "debug", "Processing sub-sitemap: {url}", params={"url": sitemap_url}, tag="URL_SEED")
                    # Recursively process sub-sitemap
                    async for u in self._iter_sitemap(sitemap_url):
                        await result_queue.put(u)  # Will block if queue is full
                except Exception as e:
                    self._log("error", "Error processing sub-sitemap {url}: {error}",
                              params={"url": sitemap_url, "error": str(e)}, tag="URL_SEED")
                finally:
                    # Put sentinel to signal completion
                    await result_queue.put(None)

            # Start all tasks
            tasks = [asyncio.create_task(process_subsitemap(sm))
                     for sm in sub_sitemaps]

            # Yield results as they come in
            while completed_count < total_sitemaps:
                item = await result_queue.get()
                if item is None:
                    completed_count += 1
                else:
                    yield item

            # Ensure all tasks are done
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Regular sitemap - yield URLs directly
            for u in regular_urls:
                yield u

    # ─────────────────────────────── validate helpers
    async def _validate(self, url: str, res_list: List[Dict[str, Any]], live: bool,
                        extract: bool, timeout: int, verbose: bool, query: Optional[str] = None,
                        score_threshold: Optional[float] = None, scoring_method: str = "bm25",
                        filter_nonsense: bool = True):
        # Local verbose parameter for this function is used to decide if intermediate logs should be printed
        # The main logger's verbose status should be controlled by the caller.
        
        # First check if this is a nonsense URL (if filtering is enabled)
        if filter_nonsense and self._is_nonsense_url(url):
            self._log("debug", "Filtered out nonsense URL: {url}", 
                      params={"url": url}, tag="URL_SEED")
            return

        cache_kind = "head" if extract else "live"

        # ---------- try cache ----------
        if not (hasattr(self, 'force') and self.force):
            cached = await self._cache_get(cache_kind, url)
            if cached:
                res_list.append(cached)
                return

        if extract:
            self._log("debug", "Fetching head for {url}", params={
                      "url": url}, tag="URL_SEED")
            ok, html, final = await self._fetch_head(url, timeout)
            status = "valid" if ok else "not_valid"
            self._log("info" if ok else "warning", "HEAD {status} for {final_url}",
                      params={"status": status.upper(), "final_url": final or url}, tag="URL_SEED")
            # head_data = _parse_head(html) if ok else {}
            head_data = await asyncio.to_thread(_parse_head, html) if ok else {}
            entry = {
                "url": final or url,
                "status": status,
                "head_data": head_data,
            }

        elif live:
            self._log("debug", "Performing live check for {url}", params={
                      "url": url}, tag="URL_SEED")
            ok = await self._resolve_head(url)
            status = "valid" if ok else "not_valid"
            self._log("info" if ok else "warning", "LIVE CHECK {status} for {url}",
                      params={"status": status.upper(), "url": url}, tag="URL_SEED")
            entry = {"url": url, "status": status, "head_data": {}}

        else:
            entry = {"url": url, "status": "unknown", "head_data": {}}

        # Add entry to results (scoring will be done later)
        if live or extract:
            await self._cache_set(cache_kind, url, entry)
        res_list.append(entry)

    async def _head_ok(self, url: str, timeout: int) -> bool:
        try:
            r = await self.client.head(url, timeout=timeout,
                                       headers={"Range": "bytes=0-0", "Accept-Encoding": "identity"})
            r.raise_for_status()  # Raise for bad status codes (4xx, 5xx)
            return True
        except httpx.RequestError as e:
            self._log("debug", "HEAD check network error for {url}: {error}",
                      params={"url": url, "error": str(e)}, tag="URL_SEED")
            return False
        except httpx.HTTPStatusError as e:
            self._log("debug", "HEAD check HTTP status error for {url}: {status_code}",
                      params={"url": url, "status_code": e.response.status_code}, tag="URL_SEED")
            return False
        except Exception as e:
            self._log("error", "Unexpected error during HEAD check for {url}: {error}",
                      params={"url": url, "error": str(e)}, tag="URL_SEED")
            return False

    async def _fetch_head(
        self,
        url: str,
        timeout: int,
        max_redirects: int = 5,
        max_bytes: int = 65_536,  # stop after 64 kB even if </head> never comes
        chunk_size: int = 4096,       # how much we read per await
    ):
        for _ in range(max_redirects+1):
            try:
                # ask the first `max_bytes` and force plain text to avoid
                # partial-gzip decode headaches
                async with self.client.stream(
                    "GET",
                    url,
                    timeout=timeout,
                    headers={
                        # "Range": f"bytes=0-{max_bytes-1}", # Dropped the Range header – no need now, and some servers ignore it. We still keep an upper‐bound max_bytes as a fail-safe.
                        "Accept-Encoding": "identity",
                    },
                    follow_redirects=False,
                ) as r:

                    if r.status_code in (301, 302, 303, 307, 308):
                        location = r.headers.get("Location")
                        if location:
                            url = urljoin(url, location)
                            self._log("debug", "Redirecting from {original_url} to {new_url}",
                                      params={"original_url": r.url, "new_url": url}, tag="URL_SEED")
                            continue
                        else:
                            self._log("warning", "Redirect status {status_code} but no Location header for {url}",
                                      params={"status_code": r.status_code, "url": r.url}, tag="URL_SEED")
                            # Return original URL if no new location
                            return False, "", str(r.url)

                    # For 2xx or other non-redirect codes, proceed to read content
                    # Only allow successful codes, or continue
                    if not (200 <= r.status_code < 400):
                        self._log("warning", "Non-success status {status_code} when fetching head for {url}",
                                  params={"status_code": r.status_code, "url": r.url}, tag="URL_SEED")
                        return False, "", str(r.url)

                    buf = bytearray()
                    async for chunk in r.aiter_bytes(chunk_size):
                        buf.extend(chunk)
                        low = buf.lower()
                        if b"</head>" in low or len(buf) >= max_bytes:
                            await r.aclose()
                            break

                    enc = r.headers.get("Content-Encoding", "").lower()
                    try:
                        if enc == "gzip" and buf[:2] == b"\x1f\x8b":
                            buf = gzip.decompress(buf)
                        elif enc == "br" and HAS_BROTLI and buf[:4] == b"\x8b\x6c\x0a\x1a":
                            buf = brotli.decompress(buf)
                        elif enc in {"gzip", "br"}:
                            # Header says “gzip” or “br” but payload is plain – ignore
                            self._log(
                                "debug",
                                "Skipping bogus {encoding} for {url}",
                                params={"encoding": enc, "url": r.url},
                                tag="URL_SEED",
                            )
                    except Exception as e:
                        self._log(
                            "warning",
                            "Decompression error for {url} ({encoding}): {error}",
                            params={"url": r.url,
                                    "encoding": enc, "error": str(e)},
                            tag="URL_SEED",
                        )
                        # fall through with raw buf

                    # Find the </head> tag case-insensitively and decode
                    idx = buf.lower().find(b"</head>")
                    if idx == -1:
                        self._log("debug", "No </head> tag found in initial bytes of {url}",
                                  params={"url": r.url}, tag="URL_SEED")
                        # If no </head> is found, take a reasonable chunk or all if small
                        # Take max 10KB if no head tag
                        html_bytes = buf if len(buf) < 10240 else buf[:10240]
                    else:
                        html_bytes = buf[:idx+7]  # Include </head> tag

                    try:
                        html = html_bytes.decode("utf-8", "replace")
                    except Exception as e:
                        self._log(
                            "warning",
                            "Failed to decode head content for {url}: {error}",
                            params={"url": r.url, "error": str(e)},
                            tag="URL_SEED",
                        )
                        html = html_bytes.decode("latin-1", "replace")

                    # Return the actual URL after redirects
                    return True, html, str(r.url)

            except httpx.RequestError as e:
                self._log("debug", "Fetch head network error for {url}: {error}",
                          params={"url": url, "error": str(e)}, tag="URL_SEED")
                return False, "", url

        # If loop finishes without returning (e.g. too many redirects)
        self._log("warning", "Exceeded max redirects ({max_redirects}) for {url}",
                  params={"max_redirects": max_redirects, "url": url}, tag="URL_SEED")
        return False, "", url

    # ─────────────────────────────── BM25 scoring helpers
    def _extract_text_context(self, head_data: Dict[str, Any]) -> str:
        """Extract all relevant text from head metadata for scoring."""
        # Priority fields with their weights (for future enhancement)
        text_parts = []

        # Title
        if head_data.get("title"):
            text_parts.append(head_data["title"])

        # Standard meta tags
        meta = head_data.get("meta", {})
        for key in ["description", "keywords", "author", "subject", "summary", "abstract"]:
            if meta.get(key):
                text_parts.append(meta[key])

        # Open Graph tags
        for key in ["og:title", "og:description", "og:site_name", "article:tag"]:
            if meta.get(key):
                text_parts.append(meta[key])

        # Twitter Card tags
        for key in ["twitter:title", "twitter:description", "twitter:image:alt"]:
            if meta.get(key):
                text_parts.append(meta[key])

        # Dublin Core tags
        for key in ["dc.title", "dc.description", "dc.subject", "dc.creator"]:
            if meta.get(key):
                text_parts.append(meta[key])

        # JSON-LD structured data
        for jsonld in head_data.get("jsonld", []):
            if isinstance(jsonld, dict):
                # Extract common fields from JSON-LD
                for field in ["name", "headline", "description", "abstract", "keywords"]:
                    if field in jsonld:
                        if isinstance(jsonld[field], str):
                            text_parts.append(jsonld[field])
                        elif isinstance(jsonld[field], list):
                            text_parts.extend(str(item)
                                              for item in jsonld[field] if item)

                # Handle @graph structures
                if "@graph" in jsonld and isinstance(jsonld["@graph"], list):
                    for item in jsonld["@graph"]:
                        if isinstance(item, dict):
                            for field in ["name", "headline", "description"]:
                                if field in item and isinstance(item[field], str):
                                    text_parts.append(item[field])

        # Combine all text parts
        return " ".join(filter(None, text_parts))

    def _calculate_url_relevance_score(self, query: str, url: str) -> float:
        """Calculate relevance score between query and URL using string matching."""
        # Normalize inputs
        query_lower = query.lower()
        url_lower = url.lower()

        # Extract URL components
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/')

        # Create searchable text from URL
        # Split domain by dots and path by slashes
        domain_parts = domain.split('.')
        path_parts = [p for p in path.split('/') if p]

        # Include query parameters if any
        query_params = parsed.query
        param_parts = []
        if query_params:
            for param in query_params.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    param_parts.extend([key, value])

        # Combine all parts
        all_parts = domain_parts + path_parts + param_parts

        # Calculate scores
        scores = []
        query_tokens = query_lower.split()

        # 1. Exact match in any part (highest score)
        for part in all_parts:
            part_lower = part.lower()
            if query_lower in part_lower:
                scores.append(1.0)
            elif part_lower in query_lower:
                scores.append(0.9)

        # 2. Token matching
        for token in query_tokens:
            token_scores = []
            for part in all_parts:
                part_lower = part.lower()
                if token in part_lower:
                    # Score based on how much of the part the token covers
                    coverage = len(token) / len(part_lower)
                    token_scores.append(0.7 * coverage)
                elif part_lower in token:
                    coverage = len(part_lower) / len(token)
                    token_scores.append(0.6 * coverage)

            if token_scores:
                scores.append(max(token_scores))

        # 3. Character n-gram similarity (for fuzzy matching)
        def get_ngrams(text, n=3):
            return set(text[i:i+n] for i in range(len(text)-n+1))

        # Combine all URL parts into one string for n-gram comparison
        url_text = ' '.join(all_parts).lower()
        if len(query_lower) >= 3 and len(url_text) >= 3:
            query_ngrams = get_ngrams(query_lower)
            url_ngrams = get_ngrams(url_text)
            if query_ngrams and url_ngrams:
                intersection = len(query_ngrams & url_ngrams)
                union = len(query_ngrams | url_ngrams)
                jaccard = intersection / union if union > 0 else 0
                scores.append(0.5 * jaccard)

        # Calculate final score
        if not scores:
            return 0.0

        # Weighted average with bias towards higher scores
        scores.sort(reverse=True)
        weighted_score = 0
        total_weight = 0
        for i, score in enumerate(scores):
            weight = 1 / (i + 1)  # Higher weight for better matches
            weighted_score += score * weight
            total_weight += weight

        final_score = weighted_score / total_weight if total_weight > 0 else 0
        return min(final_score, 1.0)  # Cap at 1.0

    def _is_nonsense_url(self, url: str) -> bool:
        """
        Check if URL is a utility/nonsense URL that shouldn't be crawled.
        Returns True if the URL should be filtered out.
        """
        url_lower = url.lower()
        
        # Extract path and filename
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # 1. Robot and sitemap files
        if path.endswith(('/robots.txt', '/sitemap.xml', '/sitemap_index.xml')):
            return True
        
        # 2. Sitemap variations
        if '/sitemap' in path and path.endswith(('.xml', '.xml.gz', '.txt')):
            return True
        
        # 3. Common utility files
        utility_files = [
            'ads.txt', 'humans.txt', 'security.txt', '.well-known/security.txt',
            'crossdomain.xml', 'browserconfig.xml', 'manifest.json',
            'apple-app-site-association', '.well-known/apple-app-site-association',
            'favicon.ico', 'apple-touch-icon.png', 'android-chrome-192x192.png'
        ]
        if any(path.endswith(f'/{file}') for file in utility_files):
            return True
        
        # # 4. Feed files
        # if path.endswith(('.rss', '.atom', '/feed', '/rss', '/atom', '/feed.xml', '/rss.xml')):
        #     return True
        
        # # 5. API endpoints and data files
        # api_patterns = ['/api/', '/v1/', '/v2/', '/v3/', '/graphql', '/.json', '/.xml']
        # if any(pattern in path for pattern in api_patterns):
        #     return True
        
        # # 6. Archive and download files
        # download_extensions = [
        #     '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2',
        #     '.exe', '.dmg', '.pkg', '.deb', '.rpm',
        #     '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        #     '.csv', '.tsv', '.sql', '.db', '.sqlite'
        # ]
        # if any(path.endswith(ext) for ext in download_extensions):
        #     return True
        
        # # 7. Media files (often not useful for text content)
        # media_extensions = [
        #     '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico',
        #     '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
        #     '.mp3', '.wav', '.ogg', '.m4a', '.flac',
        #     '.woff', '.woff2', '.ttf', '.eot', '.otf'
        # ]
        # if any(path.endswith(ext) for ext in media_extensions):
        #     return True
        
        # # 8. Source code and config files
        # code_extensions = [
        #     '.js', '.css', '.scss', '.sass', '.less',
        #     '.map', '.min.js', '.min.css',
        #     '.py', '.rb', '.php', '.java', '.cpp', '.h',
        #     '.yaml', '.yml', '.toml', '.ini', '.conf', '.config'
        # ]
        # if any(path.endswith(ext) for ext in code_extensions):
        #     return True
        
        # 9. Hidden files and directories
        path_parts = path.split('/')
        if any(part.startswith('.') for part in path_parts if part):
            return True
        
        # 10. Common non-content paths
        non_content_paths = [
            '/wp-admin', '/wp-includes', '/wp-content/uploads',
            '/admin', '/login', '/signin', '/signup', '/register',
            '/checkout', '/cart', '/account', '/profile',
            '/search', '/404', '/error',
            '/.git', '/.svn', '/.hg',
            '/cgi-bin', '/scripts', '/includes'
        ]
        if any(ncp in path for ncp in non_content_paths):
            return True
        
        # 11. URL patterns that indicate non-content
        if any(pattern in url_lower for pattern in ['?print=', '&print=', '/print/', '_print.']):
            return True
        
        # 12. Very short paths (likely homepage redirects or errors)
        if len(path.strip('/')) < 3 and path not in ['/', '/en', '/de', '/fr', '/es', '/it']:
            return True
        
        return False
    
    def _calculate_bm25_score(self, query: str, documents: List[str]) -> List[float]:
        """Calculate BM25 scores for documents against a query."""
        if not HAS_BM25:
            self._log(
                "warning", "rank_bm25 not installed. Returning zero scores.", tag="URL_SEED")
            return [0.0] * len(documents)

        if not query or not documents:
            return [0.0] * len(documents)

        # Tokenize query and documents (simple whitespace tokenization)
        # For production, consider using a proper tokenizer
        query_tokens = query.lower().split()
        tokenized_docs = [doc.lower().split() for doc in documents]

        # Handle edge case where all documents are empty
        if all(len(doc) == 0 for doc in tokenized_docs):
            return [0.0] * len(documents)

        # Create BM25 instance and calculate scores
        try:
            from rank_bm25 import BM25Okapi
            bm25 = BM25Okapi(tokenized_docs)
            scores = bm25.get_scores(query_tokens)

            # Normalize scores to 0-1 range
            # BM25 can return negative scores, so we need to handle the full range
            if len(scores) == 0:
                return []
            
            min_score = min(scores)
            max_score = max(scores)
            
            # If all scores are the same, return 0.5 for all
            if max_score == min_score:
                return [0.5] * len(scores)
            
            # Normalize to 0-1 range using min-max normalization
            normalized_scores = [(score - min_score) / (max_score - min_score) for score in scores]

            return normalized_scores
        except Exception as e:
            self._log("error", "Error calculating BM25 scores: {error}",
                      params={"error": str(e)}, tag="URL_SEED")
            return [0.0] * len(documents)

    # ─────────────────────────────── cleanup methods
    async def close(self):
        """Close the HTTP client if we own it."""
        if self._owns_client and self.client:
            await self.client.aclose()
            self._log("debug", "Closed HTTP client", tag="URL_SEED")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False

    # ─────────────────────────────── index helper
    async def _latest_index(self) -> str:
        if self.index_cache_path.exists() and (time.time()-self.index_cache_path.stat().st_mtime) < self.ttl.total_seconds():
            self._log("info", "Loading latest CC index from cache: {path}",
                      params={"path": self.index_cache_path}, tag="URL_SEED")
            return self.index_cache_path.read_text().strip()

        self._log("info", "Fetching latest Common Crawl index from {url}",
                  params={"url": COLLINFO_URL}, tag="URL_SEED")
        try:
            async with httpx.AsyncClient() as c:
                j = await c.get(COLLINFO_URL, timeout=10)
                j.raise_for_status()  # Raise an exception for bad status codes
                idx = j.json()[0]["id"]
                self.index_cache_path.write_text(idx)
                self._log("success", "Successfully fetched and cached CC index: {index_id}",
                          params={"index_id": idx}, tag="URL_SEED")
                return idx
        except httpx.RequestError as e:
            self._log("error", "Network error fetching CC index info: {error}",
                      params={"error": str(e)}, tag="URL_SEED")
            raise
        except httpx.HTTPStatusError as e:
            self._log("error", "HTTP error fetching CC index info: {status_code}",
                      params={"status_code": e.response.status_code}, tag="URL_SEED")
            raise
        except Exception as e:
            self._log("error", "Unexpected error fetching CC index info: {error}",
                      params={"error": str(e)}, tag="URL_SEED")
            raise
