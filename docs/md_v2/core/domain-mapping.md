# Domain Mapping: Discover Every URL Under a Domain

## What Is Domain Mapping?

Domain mapping goes beyond URL seeding. Instead of checking a single sitemap or index, `DomainMapper` combines **8 discovery sources** to find every URL under a domain — including subdomains you didn't know existed.

### DomainMapper vs AsyncUrlSeeder

| Aspect | AsyncUrlSeeder | DomainMapper |
|--------|---------------|--------------|
| **Scope** | Single host, listed URLs only | Entire domain + all subdomains |
| **Sources** | Sitemap + Common Crawl | 8 sources (sitemap, CC, Wayback, crt.sh, probe, robots.txt, feeds, homepage) |
| **Subdomain discovery** | No | Yes (Certificate Transparency, DNS, Wayback) |
| **Soft-404 detection** | No | Yes (fingerprints SPA sites) |
| **Best for** | Known domains with good sitemaps | Full domain reconnaissance |

**Real-world example**: For `superdesign.dev`, AsyncUrlSeeder found 4 URLs. DomainMapper found **171 URLs across 11 hosts** — including docs, API servers, staging environments, and analytics dashboards that no sitemap listed.

## Quick Start

```python
import asyncio
from crawl4ai import DomainMapper, DomainMapperConfig

async def main():
    async with DomainMapper() as mapper:
        results = await mapper.scan("example.com")

    print(f"Found {len(results)} URLs")
    for r in results[:10]:
        print(f"  [{r['source']}] {r['url']}")
        if r.get("head_data", {}).get("title"):
            print(f"    Title: {r['head_data']['title']}")

asyncio.run(main())
```

Or via `AsyncWebCrawler`:

```python
from crawl4ai import AsyncWebCrawler, DomainMapperConfig

async with AsyncWebCrawler() as crawler:
    results = await crawler.amap_domain("example.com")
```

## The 8 Discovery Sources

DomainMapper combines these sources, each catching URLs the others miss:

### 1. `sitemap` — Sitemap Discovery

Checks `/sitemap.xml`, `/sitemap_index.xml`, and `robots.txt` `Sitemap:` directives **on every discovered host** — not just the root domain.

```python
config = DomainMapperConfig(source="sitemap")
```

### 2. `cc` — Common Crawl

Queries the Common Crawl CDX API for `*.domain.tld/*`, catching URLs and subdomains the web's largest public crawl has indexed.

```python
config = DomainMapperConfig(source="cc")
```

### 3. `wayback` — Wayback Machine

Queries the Internet Archive's CDX API. Often has different coverage than Common Crawl — including historical pages that have since been removed.

```python
config = DomainMapperConfig(source="wayback")
```

### 4. `crt` — Certificate Transparency

Queries [crt.sh](https://crt.sh) for SSL certificates issued to `*.domain.tld`. This is the single most effective subdomain discovery technique — it found 14 subdomains for `superdesign.dev` that no other source knew about.

```python
config = DomainMapperConfig(source="crt")
```

### 5. `probe` — Common Path Probing

Tries ~25 well-known paths on each discovered host (`/docs`, `/api`, `/login`, `/dashboard`, `/openapi.json`, etc.). Combined with soft-404 detection to avoid false positives.

```python
config = DomainMapperConfig(source="probe")

# Add custom paths to probe
config = DomainMapperConfig(
    source="probe",
    probe_paths=["/custom-api", "/internal/status"]
)
```

### 6. `robots` — robots.txt Path Mining

Parses `Disallow:` and `Allow:` lines from `robots.txt`. These are confirmed real paths the site acknowledges exist — often revealing admin panels, APIs, and internal tools that aren't linked anywhere.

```python
config = DomainMapperConfig(source="robots")
```

### 7. `feed` — RSS/Atom Feed Parsing

Discovers and parses RSS/Atom feeds at common paths (`/feed`, `/rss`, `/atom.xml`, etc.). Feeds are curated lists of content URLs maintained by the site.

```python
config = DomainMapperConfig(source="feed")
```

### 8. `homepage` — Homepage Link Extraction

Fetches each host's homepage via HTTP and extracts all internal links using `quick_extract_links()`. Also mines `<link rel="alternate|preload|prefetch">` tags from the `<head>` for additional URLs. No browser needed.

```python
config = DomainMapperConfig(source="homepage")
```

### Combining Sources

Sources are combined with `+`:

```python
# Default: most useful combination
config = DomainMapperConfig(source="sitemap+cc+crt+probe")

# Maximum coverage: all 8 sources
config = DomainMapperConfig(
    source="sitemap+cc+wayback+crt+probe+robots+feed+homepage"
)

# Lightweight: just sitemap + probing
config = DomainMapperConfig(source="sitemap+probe")
```

## How It Works: The Three Phases

### Phase 1: Host Discovery

DomainMapper first discovers all subdomains under your domain:

```
superdesign.dev
├── crt.sh           → docs, app, cloud, insights, staging-api, ui2web, ...
├── Wayback CDX      → api, app, docs, www, ...
├── Common Crawl     → app, www, ...
└── DNS guessing     → www, app, api, docs, blog, admin, cloud, ...

Result: 13 validated hosts
```

Each discovered host is validated with an HTTP HEAD request. Hosts that don't respond are dropped.

### Phase 2: Per-Host Scanning

For each validated host, DomainMapper runs all enabled sources in parallel:

```
docs.superdesign.dev
├── Soft-404 fingerprint  → (404 returns proper error — no SPA issue)
├── robots.txt            → 1 sitemap URL, 1 disallow path
├── Sitemap parsing       → 19 URLs
├── Path probing          → 2 valid (/docs, /)
├── Feed discovery        → (no feeds found)
└── Homepage extraction   → 26 internal links
```

### Phase 3: Post-Processing

All discovered URLs go through:

1. **URL normalization** — using `normalize_url()` to canonicalize
2. **Deduplication** — by normalized URL, merging source attribution
3. **Nonsense filtering** — removes static assets (JS, CSS, images, fonts), webpack chunks, Wayback garbage
4. **Head extraction** — parallel `<head>` fetching for metadata (optional)
5. **BM25 scoring** — relevance scoring against a query (optional)

## Soft-404 Detection

Many modern SPAs return HTTP 200 for every URL — even pages that don't exist. DomainMapper detects this:

1. **Fingerprinting**: Fetches a guaranteed-nonexistent URL (e.g., `/c4ai-probe-a1b2c3d4`) on each host
2. **Recording**: Captures the response title and body hash
3. **Filtering**: When probing real paths, compares against the fingerprint. If they match → soft-404, filtered out

For `superdesign.dev`, this correctly:
- Blocked **all 25+ probe paths** on `app.superdesign.dev` (SPA that returns 200 for everything)
- Blocked **476 sitemap URLs** from `app.superdesign.dev` (all rendering the same shell)
- Kept all 19 legitimate URLs from `docs.superdesign.dev`

```python
# Soft-404 detection is on by default
config = DomainMapperConfig(soft_404_detection=True)

# Disable if you want raw results
config = DomainMapperConfig(soft_404_detection=False)
```

## Configuration Reference

### DomainMapperConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | str | `"sitemap+cc+crt+probe"` | Discovery sources joined by `+` |
| `max_urls` | int | `-1` | Maximum URLs to return (-1 = unlimited) |
| `concurrency` | int | `50` | Max concurrent requests across all hosts |
| `hits_per_sec` | int | `10` | Rate limit in requests/second |
| `force` | bool | `False` | Bypass all caches |
| `extract_head` | bool | `True` | Fetch and parse `<head>` metadata |
| `filter_nonsense_urls` | bool | `True` | Filter static assets and utility URLs |
| `soft_404_detection` | bool | `True` | Fingerprint and filter soft-404 pages |
| `query` | str | `None` | BM25 relevance query (requires `extract_head=True`) |
| `score_threshold` | float | `None` | Minimum relevance score (0.0-1.0) |
| `scoring_method` | str | `"bm25"` | Scoring algorithm |
| `probe_paths` | List[str] | `None` | Extra paths to probe on each host |
| `common_subdomains` | List[str] | `None` | Extra subdomain prefixes to guess |
| `use_browser_for_homepage` | bool | `False` | Use Playwright for JS-rendered homepages |
| `verbose` | bool | `None` | Override logger verbose setting |
| `cache_ttl_hours` | int | `24` | Hours before cached results expire |
| `dns_timeout` | float | `3.0` | Timeout for DNS resolution (seconds) |
| `http_timeout` | float | `10.0` | Timeout for HTTP requests (seconds) |

### Output Format

Each result is a dict:

```python
{
    "url": "https://docs.superdesign.dev/quickstart",
    "host": "docs.superdesign.dev",
    "source": "homepage+sitemap",     # which source(s) found it
    "status": "valid",                # valid | not_valid | soft_404
    "head_data": {                    # if extract_head=True
        "title": "Quickstart",
        "meta": {"description": "..."},
        "link": {...},
        "jsonld": [...]
    },
    "relevance_score": 0.85,          # if query provided
}
```

## Practical Examples

### Discover and Crawl Documentation

```python
import asyncio
from crawl4ai import AsyncWebCrawler, DomainMapperConfig, CrawlerRunConfig

async def crawl_all_docs():
    async with AsyncWebCrawler() as crawler:
        # Step 1: Discover all URLs
        pages = await crawler.amap_domain("example.com", DomainMapperConfig(
            source="sitemap+crt+probe+homepage",
            extract_head=True,
            query="documentation tutorial guide",
        ))

        # Step 2: Filter for docs
        doc_urls = [
            p["url"] for p in pages
            if p.get("relevance_score", 0) > 0.3
        ]
        print(f"Found {len(doc_urls)} documentation pages")

        # Step 3: Crawl them
        results = await crawler.arun_many(
            doc_urls[:50],
            config=CrawlerRunConfig(only_text=True)
        )
        for r in results:
            if r.success:
                print(f"  Crawled: {r.url}")

asyncio.run(crawl_all_docs())
```

### Security Audit: Find Exposed Services

```python
async def audit_domain():
    async with DomainMapper() as mapper:
        results = await mapper.scan("company.com", DomainMapperConfig(
            source="crt+probe+robots",
            extract_head=True,
            probe_paths=[
                "/openapi.json", "/swagger.json", "/api-docs",
                "/graphql", "/.env", "/debug", "/admin",
                "/phpinfo.php", "/server-status",
            ],
        ))

        # Flag exposed services
        for r in results:
            title = r.get("head_data", {}).get("title", "")
            if any(x in title.lower() for x in ["swagger", "api", "admin", "debug"]):
                print(f"  EXPOSED: {r['url']} — {title}")
```

### Compare Subdomains Across a Domain

```python
async def map_infrastructure():
    async with DomainMapper() as mapper:
        results = await mapper.scan("company.com", DomainMapperConfig(
            source="crt+probe",
            extract_head=False,
        ))

        # Group by host
        from collections import defaultdict
        by_host = defaultdict(list)
        for r in results:
            by_host[r["host"]].append(r)

        print(f"Discovered {len(by_host)} hosts:")
        for host, urls in sorted(by_host.items()):
            print(f"  {host}: {len(urls)} URLs")
```

## Tips and Best Practices

1. **Start with the default sources** (`sitemap+cc+crt+probe`). Add `wayback`, `robots`, `feed`, and `homepage` if you need maximum coverage.

2. **Use `extract_head=False` for speed** when you just need URL lists. Head extraction makes ~1 HTTP request per URL.

3. **The `query` parameter is powerful** for finding specific content across a large domain without crawling anything.

4. **`probe_paths` is your extensibility hook** — add domain-specific paths you suspect exist.

5. **Rate limiting matters** — `hits_per_sec=10` is respectful. Lower it for smaller sites, raise it for your own infrastructure.

6. **Soft-404 detection is critical for SPAs** — without it, single-page apps flood your results with hundreds of identical shell pages.

## See Also

- [URL Seeding](url-seeding.md) — simpler, single-host URL discovery from sitemaps and Common Crawl
- [Deep Crawling](deep-crawling.md) — follow links dynamically within pages
- [Multi-URL Crawling](../advanced/multi-url-crawling.md) — crawl discovered URLs in bulk
