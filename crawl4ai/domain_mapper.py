"""
domain_mapper.py
Comprehensive domain URL discovery for Crawl4AI

Discovers all URLs under a domain using 8 sources without deep crawling:
  sitemap   — per-host sitemap.xml / sitemap_index.xml / robots.txt Sitemap: directives
  cc        — Common Crawl CDX API
  wayback   — Wayback Machine CDX API
  crt       — Certificate Transparency (crt.sh) subdomain discovery
  probe     — common-path probing with soft-404 detection
  robots    — robots.txt Disallow:/Allow: path mining
  feed      — RSS/Atom feed parsing
  homepage  — homepage link extraction via quick_extract_links()
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import pathlib
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse, quote

import httpx

try:
    from lxml import etree
    LXML = True
except ImportError:
    LXML = False

try:
    import rank_bm25
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

from .async_logger import AsyncLoggerBase, AsyncLogger
from .async_url_seeder import AsyncUrlSeeder, _parse_head
from .utils import (
    normalize_url,
    get_base_domain,
    is_external_url,
    quick_extract_links,
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .async_configs import DomainMapperConfig

# ──────────────────────────────────────────────────────────────── constants

WAYBACK_CDX_URL = "https://web.archive.org/cdx/search/cdx"
CRT_SH_URL = "https://crt.sh/"

DEFAULT_PROBE_PATHS = [
    "/", "/docs", "/api", "/login", "/dashboard", "/blog",
    "/features", "/pricing", "/about", "/contact", "/auth/login",
    "/openapi.json", "/swagger.json", "/api-docs", "/graphql",
    "/status", "/health", "/changelog", "/terms", "/privacy",
    "/faq", "/help", "/support", "/products", "/services",
]

DEFAULT_COMMON_SUBDOMAINS = [
    "www", "app", "api", "docs", "blog", "admin", "staging", "dev",
    "cloud", "mail", "cdn", "static", "portal", "dashboard", "help",
    "support", "shop", "store",
]

FEED_PATHS = [
    "/feed", "/rss", "/atom.xml", "/feed.xml", "/rss.xml",
    "/index.xml", "/feed/rss", "/blog/feed", "/feed/atom",
]

VALID_SOURCES = {"sitemap", "cc", "wayback", "crt", "probe", "robots", "feed", "homepage"}

# Minimal nonsense filter — DomainMapper WANTS /login, /admin etc.
_NONSENSE_SUFFIXES = (
    "/robots.txt", "/sitemap.xml", "/sitemap_index.xml",
    "/favicon.ico", "/apple-touch-icon.png", "/browserconfig.xml",
    "/manifest.json", "/ads.txt", "/humans.txt",
    "/crossdomain.xml",
)

_NONSENSE_CONTAINS = (
    "/.well-known/", "/.git/", "/.svn/", "/.hg/",
)

# Static asset extensions to filter (JS, CSS, fonts, images, media)
_ASSET_EXTENSIONS = (
    ".js", ".css", ".scss", ".sass", ".less", ".map",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".avif",
    ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".mp3", ".wav", ".ogg", ".m4a", ".flac",
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
)


# ──────────────────────────────────────────────────────────────── dataclass

@dataclass
class Soft404Fingerprint:
    """Fingerprint of a known-bad URL response for soft-404 detection."""
    status_code: int
    title: Optional[str]
    content_length: int
    body_hash: str


# ──────────────────────────────────────────────────────────────── class

class DomainMapper:
    """
    Comprehensive domain URL discovery without deep crawling.

    Discovers all URLs under a domain using 8 sources:
    sitemap, cc, wayback, crt, probe, robots, feed, homepage.

    Usage::

        async with DomainMapper() as mapper:
            results = await mapper.scan("example.com")

        # Or via AsyncWebCrawler:
        async with AsyncWebCrawler() as crawler:
            results = await crawler.amap_domain("example.com")
    """

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        logger: Optional[AsyncLoggerBase] = None,
        base_directory: Optional[Union[str, Path]] = None,
    ):
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            http2=True,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
            },
        )
        self.logger = logger or AsyncLogger(verbose=False)
        self.base_directory = Path(
            base_directory or os.getenv("CRAWL4_AI_BASE_DIRECTORY", Path.home())
        )
        self.cache_dir = self.base_directory / ".crawl4ai" / "domain_mapper_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._seeder: Optional[AsyncUrlSeeder] = None
        self._rate_sem: Optional[asyncio.Semaphore] = None

    # ──────────────────────── lifecycle

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False

    async def close(self):
        if self._seeder:
            await self._seeder.close()
            self._seeder = None
        if self._owns_client and self.client:
            await self.client.aclose()

    # ──────────────────────── logging

    def _log(self, level: str, message: str, tag: str = "MAPPER", **kwargs):
        if self.logger:
            fn = getattr(self.logger, level, None)
            if fn:
                fn(message=message, tag=tag, params=kwargs.get("params", {}))

    # ──────────────────────── seeder composition

    async def _get_seeder(self) -> AsyncUrlSeeder:
        if self._seeder is None:
            self._seeder = AsyncUrlSeeder(
                client=self.client,
                logger=self.logger,
                base_directory=self.base_directory,
            )
        return self._seeder

    # ════════════════════════════════════════════════════════════════════════
    #  MAIN ENTRY POINT
    # ════════════════════════════════════════════════════════════════════════

    async def scan(
        self,
        domain: str,
        config: Optional["DomainMapperConfig"] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Discover all URLs under a domain.

        Args:
            domain: Domain to scan (e.g., "superdesign.dev")
            config: DomainMapperConfig. kwargs override config fields.

        Returns:
            List of dicts with url, host, source, status, head_data, relevance_score.
        """
        from .async_configs import DomainMapperConfig as _Cfg
        if config:
            config = config.clone(**kwargs) if kwargs else config
        else:
            config = _Cfg(**kwargs) if kwargs else _Cfg()

        if config.verbose is not None and self.logger:
            self.logger.verbose = config.verbose

        # Parse + validate sources
        sources = {s.strip().lower() for s in config.source.split("+") if s.strip()}
        invalid = sources - VALID_SOURCES
        if invalid:
            raise ValueError(f"Invalid source(s): {invalid}. Valid: {VALID_SOURCES}")

        # Rate limiter
        if config.hits_per_sec and config.hits_per_sec > 0:
            self._rate_sem = asyncio.Semaphore(config.hits_per_sec)
        else:
            self._rate_sem = None

        # Normalize domain
        base_domain = re.sub(r"^https?://", "", domain).strip("/").lower()

        self._log("info", "Scanning domain: {domain} with sources: {sources}",
                  params={"domain": base_domain, "sources": config.source})

        # ── Phase 1: Host Discovery ──────────────────────────────────────
        hosts = await self._discover_hosts(base_domain, sources, config)
        self._log("info", "Discovered {count} live hosts",
                  params={"count": len(hosts)})

        if not hosts:
            self._log("warning", "No live hosts found for {domain}",
                      params={"domain": base_domain})
            return []

        # ── Phase 2: Per-Host Scanning ───────────────────────────────────
        all_results: List[Dict[str, Any]] = []
        scan_tasks = []
        for host in hosts:
            scan_tasks.append(self._scan_host(host, base_domain, sources, config))

        host_results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        for i, result in enumerate(host_results):
            if isinstance(result, Exception):
                self._log("error", "Error scanning host {host}: {err}",
                          params={"host": list(hosts)[i], "err": str(result)})
            else:
                all_results.extend(result)

        self._log("info", "Collected {count} raw URLs from all hosts",
                  params={"count": len(all_results)})

        # ── Phase 3: Post-Processing ─────────────────────────────────────
        results = self._normalize_and_dedup(all_results, base_domain)
        self._log("info", "{count} URLs after normalization/dedup",
                  params={"count": len(results)})

        if config.filter_nonsense_urls:
            results = [r for r in results if not self._is_nonsense(r["url"])]

        # Head extraction
        if config.extract_head:
            results = await self._extract_heads(results, config)

        # BM25 scoring
        if config.query and config.extract_head:
            results = await self._apply_scoring(results, config)

        # Limit
        if config.max_urls > 0:
            results = results[:config.max_urls]

        self._log("info", "Scan complete: {count} URLs found across {hosts} hosts",
                  params={"count": len(results),
                          "hosts": len({r["host"] for r in results})})
        return results

    # ════════════════════════════════════════════════════════════════════════
    #  PHASE 1: HOST DISCOVERY
    # ════════════════════════════════════════════════════════════════════════

    async def _discover_hosts(
        self, base_domain: str, sources: Set[str], config: "DomainMapperConfig"
    ) -> Set[str]:
        """Discover all subdomains/hosts under base_domain."""
        hosts: Set[str] = {base_domain}

        # When include_subdomains is False, skip all subdomain discovery
        # and only scan the exact domain provided
        if not getattr(config, "include_subdomains", True):
            self._log("info", "Subdomain discovery disabled, scanning only {domain}",
                      params={"domain": base_domain})
            validated = await self._validate_hosts(hosts, config)
            return validated

        discovery_tasks = []

        if "crt" in sources:
            discovery_tasks.append(("crt", self._discover_via_crt(base_domain, config)))
        if "wayback" in sources:
            discovery_tasks.append(("wayback", self._discover_via_wayback(base_domain, config)))
        if "cc" in sources:
            discovery_tasks.append(("cc", self._discover_via_cc(base_domain, config)))

        # Always guess common subdomains when crt is enabled
        if "crt" in sources or "probe" in sources:
            prefixes = list(DEFAULT_COMMON_SUBDOMAINS)
            if config.common_subdomains:
                prefixes.extend(config.common_subdomains)
            discovery_tasks.append(("dns", self._guess_subdomains(base_domain, prefixes, config)))

        # Run all discovery in parallel (per-source timeout)
        if discovery_tasks:
            source_timeout = getattr(config, "source_timeout", 30.0)
            coros = [
                asyncio.wait_for(t[1], timeout=source_timeout)
                for t in discovery_tasks
            ]
            names = [t[0] for t in discovery_tasks]
            results = await asyncio.gather(*coros, return_exceptions=True)
            for name, result in zip(names, results):
                if isinstance(result, asyncio.TimeoutError):
                    self._log("warning", "{source} discovery timed out after {timeout}s, skipping",
                              params={"source": name, "timeout": source_timeout})
                elif isinstance(result, Exception):
                    self._log("warning", "{source} discovery failed: {err}",
                              params={"source": name, "err": str(result)})
                else:
                    self._log("info", "{source} discovered {count} hosts: {hosts}",
                              params={"source": name, "count": len(result),
                                      "hosts": ", ".join(sorted(result)[:10])})
                    hosts.update(result)

        # Validate all hosts are actually alive
        validated = await self._validate_hosts(hosts, config)
        return validated

    async def _discover_via_crt(self, base_domain: str, config: "DomainMapperConfig") -> Set[str]:
        """Discover subdomains via Certificate Transparency logs (crt.sh)."""
        hosts: Set[str] = set()
        url = f"{CRT_SH_URL}?q=%.{base_domain}&output=json"
        try:
            resp = await self.client.get(url, timeout=15, follow_redirects=True)
            if resp.status_code != 200:
                self._log("warning", "crt.sh returned HTTP {code}",
                          params={"code": resp.status_code})
                return hosts

            entries = resp.json()
            for entry in entries:
                for field_name in ("common_name", "name_value"):
                    val = entry.get(field_name, "")
                    # name_value can have newline-separated SANs
                    for name in val.split("\n"):
                        name = name.strip().lower()
                        # Skip wildcards
                        if name.startswith("*."):
                            name = name[2:]
                        if not name:
                            continue
                        # Must be a subdomain of base_domain
                        if name == base_domain or name.endswith(f".{base_domain}"):
                            hosts.add(name)
        except Exception as e:
            self._log("warning", "crt.sh query failed: {err}", params={"err": str(e)})
        return hosts

    async def _discover_via_wayback(self, base_domain: str, config: "DomainMapperConfig") -> Set[str]:
        """Discover hosts from Wayback Machine CDX API."""
        hosts: Set[str] = set()
        # Also store URLs for later use in Phase 2
        self._wayback_urls: List[str] = []
        params = {
            "url": f"*.{base_domain}/*",
            "output": "text",
            "fl": "original",
            "collapse": "urlkey",
            "limit": "10000",
        }
        try:
            resp = await self.client.get(
                WAYBACK_CDX_URL, params=params, timeout=30, follow_redirects=True
            )
            if resp.status_code != 200:
                return hosts
            for line in resp.text.strip().splitlines():
                url = line.strip()
                if not url:
                    continue
                self._wayback_urls.append(url)
                parsed = urlparse(url)
                host = parsed.netloc.lower().split(":")[0]
                if host and (host == base_domain or host.endswith(f".{base_domain}")):
                    hosts.add(host)
        except Exception as e:
            self._log("warning", "Wayback CDX query failed: {err}", params={"err": str(e)})
        return hosts

    async def _discover_via_cc(self, base_domain: str, config: "DomainMapperConfig") -> Set[str]:
        """Extract unique hostnames from Common Crawl results."""
        hosts: Set[str] = set()
        try:
            seeder = await self._get_seeder()
            # We need the CC index
            if seeder.index_id is None:
                seeder.index_id = await seeder._latest_index()

            from .async_configs import SeedingConfig
            cc_cfg = SeedingConfig(
                source="cc", max_urls=-1, filter_nonsense_urls=False,
                extract_head=False, live_check=False, force=config.force,
            )
            results = await seeder.urls(base_domain, cc_cfg)
            for r in results:
                url = r["url"] if isinstance(r, dict) else r
                parsed = urlparse(url)
                host = parsed.netloc.lower().split(":")[0]
                if host and (host == base_domain or host.endswith(f".{base_domain}")):
                    hosts.add(host)
        except Exception as e:
            self._log("warning", "CC host discovery failed: {err}", params={"err": str(e)})
        return hosts

    async def _guess_subdomains(
        self, base_domain: str, prefixes: List[str], config: "DomainMapperConfig"
    ) -> Set[str]:
        """Guess common subdomains via DNS resolution."""
        hosts: Set[str] = set()

        async def check(prefix: str):
            fqdn = f"{prefix}.{base_domain}"
            try:
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.getaddrinfo(fqdn, None),
                    timeout=config.dns_timeout,
                )
                return fqdn
            except Exception:
                return None

        results = await asyncio.gather(*[check(p) for p in prefixes])
        for r in results:
            if r:
                hosts.add(r)
        return hosts

    async def _validate_hosts(self, hosts: Set[str], config: "DomainMapperConfig") -> Set[str]:
        """Validate hosts are reachable via HTTP."""
        validated: Set[str] = set()
        # Track redirects so we can map canonical hosts
        self._host_redirects: Dict[str, str] = {}

        async def check(host: str):
            for scheme in ("https", "http"):
                url = f"{scheme}://{host}/"
                try:
                    resp = await self.client.head(
                        url, timeout=config.http_timeout, follow_redirects=False
                    )
                    # Record redirect target for dedup
                    if resp.status_code in (301, 302, 303, 307, 308):
                        loc = resp.headers.get("location", "")
                        if loc:
                            target_host = urlparse(urljoin(url, loc)).netloc.lower().split(":")[0]
                            if target_host != host:
                                self._host_redirects[host] = target_host
                    return host
                except Exception:
                    continue
            return None

        results = await asyncio.gather(*[check(h) for h in hosts])
        for r in results:
            if r:
                validated.add(r)
        return validated

    # ════════════════════════════════════════════════════════════════════════
    #  PHASE 2: PER-HOST SCANNING
    # ════════════════════════════════════════════════════════════════════════

    async def _scan_host(
        self, host: str, base_domain: str, sources: Set[str], config: "DomainMapperConfig"
    ) -> List[Dict[str, Any]]:
        """Run all enabled sources against a single host."""
        results: List[Dict[str, Any]] = []

        # Soft-404 fingerprint (must run first)
        soft_404_fp = None
        if config.soft_404_detection:
            soft_404_fp = await self._fingerprint_soft_404(host, config)
            if soft_404_fp and soft_404_fp.status_code == 200:
                self._log("info", "Soft-404 fingerprint for {host}: title={title}",
                          params={"host": host, "title": soft_404_fp.title or "(none)"})
            else:
                soft_404_fp = None  # Host returns proper 404s, no soft-404 issue

        # robots.txt (feeds into sitemap + probe)
        sitemap_urls: List[str] = []
        disallow_paths: List[str] = []
        if "robots" in sources or "sitemap" in sources:
            sitemap_urls, disallow_paths = await self._scan_robots_txt(host, config)

        # Gather per-host sources in parallel
        tasks: Dict[str, Any] = {}

        if "sitemap" in sources:
            tasks["sitemap"] = self._scan_sitemaps(host, sitemap_urls, config)

        if "probe" in sources or "robots" in sources:
            # If host has soft-404 fingerprint, add robots paths to probe (which does soft-404 checking)
            # rather than treating them as known-good
            probe_paths = list(DEFAULT_PROBE_PATHS)
            if config.probe_paths:
                probe_paths.extend(config.probe_paths)
            if "robots" in sources and disallow_paths:
                probe_paths.extend(disallow_paths)
            # Deduplicate
            probe_paths = list(dict.fromkeys(probe_paths))
            tasks["probe"] = self._probe_paths(host, probe_paths, soft_404_fp, config)

        if "feed" in sources:
            tasks["feed"] = self._discover_feeds(host, config)

        if "homepage" in sources:
            tasks["homepage"] = self._scan_homepage(host, base_domain, config)

        # Run in parallel (per-source timeout)
        if tasks:
            source_timeout = getattr(config, "source_timeout", 30.0)
            source_names = list(tasks.keys())
            coros = [
                asyncio.wait_for(c, timeout=source_timeout)
                for c in tasks.values()
            ]
            task_results = await asyncio.gather(*coros, return_exceptions=True)

            for name, result in zip(source_names, task_results):
                if isinstance(result, asyncio.TimeoutError):
                    self._log("warning", "{source} scan timed out on {host} after {timeout}s, skipping",
                              params={"source": name, "host": host, "timeout": source_timeout})
                    continue
                if isinstance(result, Exception):
                    self._log("warning", "{source} scan failed on {host}: {err}",
                              params={"source": name, "host": host, "err": str(result)})
                    continue

                # For sitemap URLs on hosts with soft-404: sample-check a few URLs
                # If all samples are soft-404, skip the entire batch
                if name == "sitemap" and soft_404_fp and len(result) > 5:
                    import random
                    sample = random.sample(result, min(5, len(result)))
                    soft_404_count = 0
                    for sample_url in sample:
                        try:
                            resp = await self.client.get(
                                sample_url, timeout=config.http_timeout,
                                follow_redirects=True,
                                headers={"Accept-Encoding": "identity"},
                            )
                            if self._is_soft_404(resp.status_code, resp.content, soft_404_fp):
                                soft_404_count += 1
                        except Exception:
                            pass
                    if soft_404_count == len(sample):
                        self._log("info",
                                  "Skipping {count} sitemap URLs from {host} (all samples are soft-404)",
                                  params={"count": len(result), "host": host})
                        continue

                for url in result:
                    results.append({
                        "url": url,
                        "host": host,
                        "source": name,
                        "status": "valid",
                        "head_data": {},
                    })

        # Add Wayback URLs that belong to this host
        if "wayback" in sources and hasattr(self, "_wayback_urls"):
            for url in self._wayback_urls:
                parsed = urlparse(url)
                url_host = parsed.netloc.lower().split(":")[0]
                if url_host == host:
                    results.append({
                        "url": url,
                        "host": host,
                        "source": "wayback",
                        "status": "valid",
                        "head_data": {},
                    })

        return results

    # ──────────────────────── Soft-404 Detection

    async def _fingerprint_soft_404(
        self, host: str, config: "DomainMapperConfig"
    ) -> Optional[Soft404Fingerprint]:
        """Fetch a known-bad URL to fingerprint soft-404 responses."""
        random_path = f"/c4ai-probe-{uuid.uuid4().hex[:12]}"
        url = f"https://{host}{random_path}"
        try:
            resp = await self.client.get(
                url, timeout=config.http_timeout, follow_redirects=True
            )
            body = resp.content[:2048]
            title = None
            m = re.search(rb"<title[^>]*>(.*?)</title>", body, re.I | re.S)
            if m:
                title = m.group(1).decode("utf-8", "replace").strip()
            return Soft404Fingerprint(
                status_code=resp.status_code,
                title=title,
                content_length=int(resp.headers.get("content-length", -1)),
                body_hash=hashlib.md5(body).hexdigest(),
            )
        except Exception:
            return None

    def _is_soft_404(
        self, status_code: int, body: bytes, fingerprint: Optional[Soft404Fingerprint]
    ) -> bool:
        """Check if a response matches the soft-404 fingerprint."""
        if fingerprint is None:
            return False
        if status_code != 200:
            return False

        # Check body hash
        body_hash = hashlib.md5(body[:2048]).hexdigest()
        if body_hash == fingerprint.body_hash:
            return True

        # Check title
        m = re.search(rb"<title[^>]*>(.*?)</title>", body[:2048], re.I | re.S)
        if m and fingerprint.title:
            title = m.group(1).decode("utf-8", "replace").strip()
            if title == fingerprint.title:
                return True

        return False

    # ──────────────────────── robots.txt

    async def _scan_robots_txt(
        self, host: str, config: "DomainMapperConfig"
    ) -> Tuple[List[str], List[str]]:
        """Parse robots.txt for Sitemap: and Disallow: directives."""
        sitemap_urls: List[str] = []
        disallow_paths: List[str] = []

        for scheme in ("https", "http"):
            url = f"{scheme}://{host}/robots.txt"
            try:
                resp = await self.client.get(url, timeout=config.http_timeout, follow_redirects=True)
                if resp.status_code != 200:
                    continue

                for line in resp.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith("sitemap:"):
                        sm_url = line.split(":", 1)[1].strip()
                        if sm_url:
                            sitemap_urls.append(sm_url)
                    elif line.lower().startswith("disallow:"):
                        path = line.split(":", 1)[1].strip()
                        # Keep only concrete paths (no wildcards, no empty)
                        if path and "*" not in path and len(path) > 1:
                            disallow_paths.append(path)
                    elif line.lower().startswith("allow:"):
                        path = line.split(":", 1)[1].strip()
                        if path and "*" not in path and len(path) > 1:
                            disallow_paths.append(path)

                self._log("info", "robots.txt for {host}: {sm} sitemaps, {dp} paths",
                          params={"host": host, "sm": len(sitemap_urls),
                                  "dp": len(disallow_paths)})
                return sitemap_urls, list(dict.fromkeys(disallow_paths))

            except Exception:
                continue

        return sitemap_urls, disallow_paths

    # ──────────────────────── Sitemaps

    async def _scan_sitemaps(
        self, host: str, sitemap_urls: List[str], config: "DomainMapperConfig"
    ) -> List[str]:
        """Discover URLs from sitemaps on a host."""
        urls: List[str] = []

        # If no sitemaps from robots.txt, try defaults
        if not sitemap_urls:
            for scheme in ("https", "http"):
                for suffix in ("/sitemap.xml", "/sitemap_index.xml"):
                    candidate = f"{scheme}://{host}{suffix}"
                    try:
                        resp = await self.client.head(
                            candidate, timeout=config.http_timeout, follow_redirects=True
                        )
                        if 200 <= resp.status_code < 300:
                            sitemap_urls.append(candidate)
                            break
                    except Exception:
                        continue
                if sitemap_urls:
                    break

        if not sitemap_urls:
            return urls

        # Use AsyncUrlSeeder's sitemap parsing
        seeder = await self._get_seeder()
        for sm_url in sitemap_urls:
            try:
                async for u in seeder._iter_sitemap(sm_url):
                    urls.append(u)
            except Exception as e:
                self._log("warning", "Error parsing sitemap {url}: {err}",
                          params={"url": sm_url, "err": str(e)})

        self._log("info", "Sitemaps for {host}: {count} URLs",
                  params={"host": host, "count": len(urls)})
        return urls

    # ──────────────────────── Path Probing

    async def _probe_paths(
        self,
        host: str,
        paths: List[str],
        soft_404_fp: Optional[Soft404Fingerprint],
        config: "DomainMapperConfig",
    ) -> List[str]:
        """Probe common paths on a host, filtering soft-404s."""
        valid_urls: List[str] = []

        async def probe_one(path: str) -> Optional[str]:
            url = f"https://{host}{path}"
            try:
                if self._rate_sem:
                    async with self._rate_sem:
                        return await self._do_probe(url, soft_404_fp, config)
                else:
                    return await self._do_probe(url, soft_404_fp, config)
            except Exception:
                return None

        results = await asyncio.gather(*[probe_one(p) for p in paths])
        for r in results:
            if r:
                valid_urls.append(r)

        self._log("info", "Probed {total} paths on {host}: {valid} valid",
                  params={"total": len(paths), "host": host, "valid": len(valid_urls)})
        return valid_urls

    async def _do_probe(
        self, url: str, soft_404_fp: Optional[Soft404Fingerprint], config: "DomainMapperConfig"
    ) -> Optional[str]:
        """Probe a single URL: HEAD then GET to check soft-404."""
        try:
            resp = await self.client.head(
                url, timeout=config.http_timeout, follow_redirects=True
            )
        except Exception:
            return None

        if resp.status_code >= 400:
            return None

        # For 2xx responses, verify against soft-404
        if soft_404_fp and resp.status_code == 200:
            try:
                get_resp = await self.client.get(
                    url, timeout=config.http_timeout, follow_redirects=True,
                    headers={"Accept-Encoding": "identity"},
                )
                body = get_resp.content[:2048]
                if self._is_soft_404(get_resp.status_code, body, soft_404_fp):
                    self._log("debug", "Soft-404 detected: {url}", params={"url": url})
                    return None
            except Exception:
                pass

        # Return the final URL after redirects
        return str(resp.url)

    # ──────────────────────── Feed Discovery

    async def _discover_feeds(self, host: str, config: "DomainMapperConfig") -> List[str]:
        """Discover URLs from RSS/Atom feeds."""
        discovered: List[str] = []

        for feed_path in FEED_PATHS:
            url = f"https://{host}{feed_path}"
            try:
                resp = await self.client.get(
                    url, timeout=config.http_timeout, follow_redirects=True
                )
                if resp.status_code != 200:
                    continue

                content_type = resp.headers.get("content-type", "").lower()
                body = resp.text

                # Quick check: is this XML/RSS/Atom?
                if not any(x in content_type for x in ("xml", "rss", "atom")) and \
                   not body.strip().startswith("<?xml") and \
                   "<rss" not in body[:500] and "<feed" not in body[:500]:
                    continue

                feed_urls = self._parse_feed_xml(body, str(resp.url))
                if feed_urls:
                    self._log("info", "Feed {path} on {host}: {count} URLs",
                              params={"path": feed_path, "host": host,
                                      "count": len(feed_urls)})
                    discovered.extend(feed_urls)
                    break  # One good feed is enough per host

            except Exception:
                continue

        return discovered

    def _parse_feed_xml(self, xml_text: str, base_url: str) -> List[str]:
        """Parse RSS or Atom feed XML to extract entry URLs."""
        urls: List[str] = []
        try:
            if LXML:
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(xml_text.encode("utf-8", "replace"), parser=parser)

                # RSS: <item><link>URL</link></item>
                for link in root.xpath("//*[local-name()='item']/*[local-name()='link']"):
                    if link.text and link.text.strip():
                        urls.append(urljoin(base_url, link.text.strip()))

                # Atom: <entry><link href="URL"/></entry>
                for link in root.xpath("//*[local-name()='entry']/*[local-name()='link']"):
                    href = link.get("href")
                    if href:
                        urls.append(urljoin(base_url, href.strip()))

                # RSS: <item><guid isPermaLink="true">URL</guid></item>
                if not urls:
                    for guid in root.xpath("//*[local-name()='item']/*[local-name()='guid']"):
                        is_permalink = guid.get("isPermaLink", "true").lower()
                        if is_permalink == "true" and guid.text and guid.text.strip().startswith("http"):
                            urls.append(guid.text.strip())
            else:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(xml_text)
                for elem in root.iter():
                    if "}" in elem.tag:
                        elem.tag = elem.tag.split("}")[1]

                for item in root.findall(".//item"):
                    link = item.find("link")
                    if link is not None and link.text:
                        urls.append(urljoin(base_url, link.text.strip()))

                for entry in root.findall(".//entry"):
                    link = entry.find("link")
                    if link is not None:
                        href = link.get("href")
                        if href:
                            urls.append(urljoin(base_url, href.strip()))
        except Exception:
            pass
        return urls

    # ──────────────────────── Homepage Link Extraction

    async def _scan_homepage(
        self, host: str, base_domain: str, config: "DomainMapperConfig"
    ) -> List[str]:
        """Extract internal links from a host's homepage."""
        urls: List[str] = []
        base_url = f"https://{host}/"

        try:
            resp = await self.client.get(
                base_url, timeout=config.http_timeout, follow_redirects=True
            )
            if resp.status_code != 200:
                return urls

            html = resp.text

            # Extract <a href> links
            links = quick_extract_links(html, str(resp.url))
            for link in links.get("internal", []):
                href = link.get("href", "")
                if href:
                    urls.append(href)

            # Also mine <link> tags from <head>
            head_data = _parse_head(html)
            for rel, entries in head_data.get("link", {}).items():
                if rel in ("alternate", "preload", "prefetch", "next", "prev"):
                    for entry in entries:
                        href = entry.get("href", "")
                        if href:
                            full_url = urljoin(str(resp.url), href)
                            if not is_external_url(full_url, base_domain):
                                urls.append(full_url)

            self._log("info", "Homepage {host}: {count} internal links",
                      params={"host": host, "count": len(urls)})

        except Exception as e:
            self._log("warning", "Failed to fetch homepage for {host}: {err}",
                      params={"host": host, "err": str(e)})

        return urls

    # ════════════════════════════════════════════════════════════════════════
    #  PHASE 3: POST-PROCESSING
    # ════════════════════════════════════════════════════════════════════════

    def _normalize_and_dedup(
        self, results: List[Dict[str, Any]], base_domain: str
    ) -> List[Dict[str, Any]]:
        """Normalize URLs and deduplicate, merging source attribution."""
        seen: Dict[str, Dict[str, Any]] = {}

        for r in results:
            url = r["url"]
            # Normalize
            try:
                normalized = normalize_url(url, f"https://{base_domain}/")
            except Exception:
                normalized = url

            if not normalized:
                continue

            # Strip trailing slash for dedup (keep in output)
            key = normalized.rstrip("/").lower()

            if key in seen:
                # Merge source
                existing_sources = set(seen[key]["source"].split("+"))
                existing_sources.add(r["source"])
                seen[key]["source"] = "+".join(sorted(existing_sources))
            else:
                r_copy = r.copy()
                r_copy["url"] = normalized
                seen[key] = r_copy

        return list(seen.values())

    def _is_nonsense(self, url: str) -> bool:
        """Reduced nonsense filter for DomainMapper."""
        parsed = urlparse(url)
        path = parsed.path.lower()

        # Nonsense suffixes
        if any(path.endswith(s) for s in _NONSENSE_SUFFIXES):
            return True

        # Nonsense contains
        if any(c in path for c in _NONSENSE_CONTAINS):
            return True

        # Sitemap variations
        if "/sitemap" in path and path.endswith((".xml", ".xml.gz", ".txt")):
            return True

        # Static assets (JS, CSS, fonts, images, media, archives)
        if any(path.endswith(ext) for ext in _ASSET_EXTENSIONS):
            return True

        # Next.js / webpack chunks
        if "/_next/" in path or "/webpack" in path:
            return True

        # Hidden dotfiles
        parts = path.split("/")
        if any(p.startswith(".") and p not in (".", "..") for p in parts if p):
            return True

        # Wayback garbage: URLs with encoded newlines/backslashes
        if any(x in url for x in ("%5C", "%0A", "%0D", "\\n", "\\r")):
            return True

        return False

    async def _extract_heads(
        self, results: List[Dict[str, Any]], config: "DomainMapperConfig"
    ) -> List[Dict[str, Any]]:
        """Extract <head> metadata for all valid URLs."""
        seeder = await self._get_seeder()
        sem = asyncio.Semaphore(config.concurrency)

        async def fetch_one(r: Dict[str, Any]):
            if r.get("head_data"):
                return  # Already has head data
            async with sem:
                if self._rate_sem:
                    async with self._rate_sem:
                        await self._do_fetch_head(r, seeder, config)
                else:
                    await self._do_fetch_head(r, seeder, config)

        await asyncio.gather(*[fetch_one(r) for r in results], return_exceptions=True)
        return results

    async def _do_fetch_head(
        self, r: Dict[str, Any], seeder: AsyncUrlSeeder, config: "DomainMapperConfig"
    ):
        """Fetch and parse <head> for a single result."""
        try:
            ok, html, final_url = await seeder._fetch_head(r["url"], int(config.http_timeout))
            if ok:
                r["head_data"] = await asyncio.to_thread(_parse_head, html)
                if final_url and final_url != r["url"]:
                    r["url"] = final_url
            else:
                r["status"] = "not_valid"
        except Exception:
            r["status"] = "not_valid"

    async def _apply_scoring(
        self, results: List[Dict[str, Any]], config: "DomainMapperConfig"
    ) -> List[Dict[str, Any]]:
        """Apply BM25 scoring to results with head data."""
        if not HAS_BM25 or not config.query:
            return results

        seeder = await self._get_seeder()

        # Build text corpus from head data
        text_contexts = []
        scoreable = []
        for r in results:
            if r.get("head_data"):
                text = seeder._extract_text_context(r["head_data"])
                if text:
                    text_contexts.append(text)
                    scoreable.append(r)

        if text_contexts:
            scores = await asyncio.to_thread(
                seeder._calculate_bm25_score, config.query, text_contexts
            )
            for i, r in enumerate(scoreable):
                if i < len(scores):
                    r["relevance_score"] = float(scores[i])

        # Filter by threshold
        if config.score_threshold is not None:
            results = [r for r in results if r.get("relevance_score", 0) >= config.score_threshold]

        # Sort by relevance
        results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
        return results

    # ════════════════════════════════════════════════════════════════════════
    #  CACHING
    # ════════════════════════════════════════════════════════════════════════

    def _cache_key(self, domain: str, config: "DomainMapperConfig") -> str:
        """Generate cache key from domain + config."""
        config_str = f"{config.source}:{config.filter_nonsense_urls}:{config.soft_404_detection}"
        h = hashlib.md5(config_str.encode()).hexdigest()[:8]
        safe_domain = re.sub(r"[/?#]+", "_", domain)
        return f"scan_{safe_domain}_{h}.json"

    def _read_scan_cache(self, domain: str, config: "DomainMapperConfig") -> Optional[List[Dict]]:
        """Read cached scan results if valid."""
        if config.force:
            return None
        path = self.cache_dir / self._cache_key(domain, config)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            if data.get("version") != 1:
                return None
            created = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
            if age_hours > config.cache_ttl_hours:
                return None
            return data.get("results", [])
        except Exception:
            return None

    def _write_scan_cache(
        self, domain: str, config: "DomainMapperConfig", results: List[Dict]
    ):
        """Write scan results to cache."""
        path = self.cache_dir / self._cache_key(domain, config)
        try:
            data = {
                "version": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "domain": domain,
                "result_count": len(results),
                "results": results,
            }
            path.write_text(json.dumps(data, default=str))
        except Exception:
            pass
