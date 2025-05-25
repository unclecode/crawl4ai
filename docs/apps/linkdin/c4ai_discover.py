#!/usr/bin/env python3
"""
c4ai-discover — Stage‑1 Discovery CLI

Scrapes LinkedIn company search + their people pages and dumps two newline‑delimited
JSON files: companies.jsonl and people.jsonl.

Key design rules
----------------
* No BeautifulSoup — Crawl4AI only for network + HTML fetch.
* JsonCssExtractionStrategy for structured scraping; schema auto‑generated once
  from sample HTML provided by user and then cached under ./schemas/.
* Defaults are embedded so the file runs inside VS Code debugger without CLI args.
* If executed as a console script (argv > 1), CLI flags win.
* Lightweight deps: argparse + Crawl4AI stack.

Author: Tom @ Kidocode 2025‑04‑26
"""
from __future__ import annotations

import warnings, re
warnings.filterwarnings(
    "ignore",
    message=r"The pseudo class ':contains' is deprecated, ':-soup-contains' should be used.*",
    category=FutureWarning,
    module=r"soupsieve"
)


# ───────────────────────────────────────────────────────────────────────────────
# Imports
# ───────────────────────────────────────────────────────────────────────────────
import argparse
import random
import asyncio
import json
import logging
import os
import pathlib
import sys
# 3rd-party rich for pretty logging
from rich.console import Console
from rich.logging import RichHandler

from datetime import datetime, UTC
from textwrap import dedent
from types import SimpleNamespace
from typing import Dict, List, Optional
from urllib.parse import quote
from pathlib import Path
from glob import glob

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    JsonCssExtractionStrategy,
    BrowserProfiler,
    LLMConfig,
)

# ───────────────────────────────────────────────────────────────────────────────
# Constants / paths
# ───────────────────────────────────────────────────────────────────────────────
BASE_DIR = pathlib.Path(__file__).resolve().parent
SCHEMA_DIR = BASE_DIR / "schemas"
SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
COMPANY_SCHEMA_PATH = SCHEMA_DIR / "company_card.json"
PEOPLE_SCHEMA_PATH = SCHEMA_DIR / "people_card.json"

# ---------- deterministic target JSON examples ----------
_COMPANY_SCHEMA_EXAMPLE = {
    "handle": "/company/posify/",
    "profile_image": "https://media.licdn.com/dms/image/v2/.../logo.jpg",
    "name": "Management Research Services, Inc. (MRS, Inc)",
    "descriptor": "Insurance • Milwaukee, Wisconsin",
    "about": "Insurance • Milwaukee, Wisconsin",
    "followers": 1000
}

_PEOPLE_SCHEMA_EXAMPLE = {
    "profile_url": "https://www.linkedin.com/in/lily-ng/",
    "name": "Lily Ng",
    "headline": "VP Product @ Posify",
    "followers": 890,
    "connection_degree": "2nd",
    "avatar_url": "https://media.licdn.com/dms/image/v2/.../lily.jpg"
}

# Provided sample HTML snippets (trimmed) — used exactly once to cold‑generate schema.
_SAMPLE_COMPANY_HTML = (Path(__file__).resolve().parent / "snippets/company.html").read_text()
_SAMPLE_PEOPLE_HTML = (Path(__file__).resolve().parent / "snippets/people.html").read_text()

# --------- tighter schema prompts ----------
_COMPANY_SCHEMA_QUERY = dedent(
    """
    Using the supplied <li> company-card HTML, build a JsonCssExtractionStrategy schema that,
    for every card, outputs *exactly* the keys shown in the example JSON below.
    JSON spec:
      • handle        – href of the outermost <a> that wraps the logo/title, e.g. "/company/posify/"
      • profile_image – absolute URL of the <img> inside that link
      • name          – text of the <a> inside the <span class*='t-16'>
      • descriptor    – text line with industry • location
      • about         – text of the <div class*='t-normal'> below the name (industry + geo)
      • followers     – integer parsed from the <div> containing 'followers'
      
    IMPORTANT: Do not use the base64 kind of classes to target element. It's not reliable.
    The main div parent contains these li element is "div.search-results-container" you can use this.
    The <ul> parent has "role" equal to "list". Using these two should be enough to target the <li> elements.    

    IMPORTANT: Remember there might be multiple <a> tags that start with https://www.linkedin.com/company/[NAME], 
    so in case you refer to them for different fields, make sure to be more specific. One has the image, and one 
    has the person's name.
    
    IMPORTANT: Be very smart in selecting the correct and unique way to address the element. You should ensure 
    your selector points to a single element and is unique to the place that contains the information.
    """
)

_PEOPLE_SCHEMA_QUERY = dedent(
    """
    Using the supplied <li> people-card HTML, build a JsonCssExtractionStrategy schema that
    outputs exactly the keys in the example JSON below.
    Fields:
      • profile_url        – href of the outermost profile link
      • name               – text inside artdeco-entity-lockup__title
      • headline           – inner text of artdeco-entity-lockup__subtitle
      • followers          – integer parsed from the span inside lt-line-clamp--multi-line
      • connection_degree  – '1st', '2nd', etc. from artdeco-entity-lockup__badge
      • avatar_url         – src of the <img> within artdeco-entity-lockup__image
      
    IMPORTANT: Do not use the base64 kind of classes to target element. It's not reliable.
    The main div parent contains these li element is a "div" has these classes "artdeco-card org-people-profile-card__card-spacing org-people__card-margin-bottom".
    """
)

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _load_or_build_schema(
    path: pathlib.Path, 
    sample_html: str, 
    query: str, 
    example_json: Dict,
    force = False
) -> Dict:
    """Load schema from path, else call generate_schema once and persist."""
    if path.exists() and not force:
        return json.loads(path.read_text())

    logging.info("[SCHEMA] Generating schema %s", path.name)
    schema = JsonCssExtractionStrategy.generate_schema(
        html=sample_html,
        llm_config=LLMConfig(
            provider=os.getenv("C4AI_SCHEMA_PROVIDER", "openai/gpt-4o"),
            api_token=os.getenv("OPENAI_API_KEY", "env:OPENAI_API_KEY"),
        ),
        query=query,
        target_json_example=json.dumps(example_json, indent=2),
    )
    path.write_text(json.dumps(schema, indent=2))
    return schema


def _openai_friendly_number(text: str) -> Optional[int]:
    """Extract first int from text like '1K followers' (returns 1000)."""
    import re

    m = re.search(r"(\d[\d,]*)", text.replace(",", ""))
    if not m:
        return None
    val = int(m.group(1))
    if "k" in text.lower():
        val *= 1000
    if "m" in text.lower():
        val *= 1_000_000
    return val

# ---------------------------------------------------------------------------
# Core async workers
# ---------------------------------------------------------------------------
async def crawl_company_search(crawler: AsyncWebCrawler, url: str, schema: Dict, limit: int) -> List[Dict]:
    """Paginate 10-item company search pages until `limit` reached."""
    extraction = JsonCssExtractionStrategy(schema)
    cfg = CrawlerRunConfig(
        extraction_strategy=extraction,
        cache_mode=CacheMode.BYPASS,
        wait_for = ".search-marvel-srp",
        session_id="company_search",
        delay_before_return_html=1,
        magic = True,
        verbose= False,
    )
    companies, page = [], 1
    while len(companies) < max(limit, 10):
        paged_url = f"{url}&page={page}"
        res = await crawler.arun(paged_url, config=cfg)
        batch = json.loads(res[0].extracted_content)
        if not batch:
            break
        for item in batch:
            name = item.get("name", "").strip()
            handle = item.get("handle", "").strip()
            if not handle or not name:
                continue
            descriptor = item.get("descriptor")
            about = item.get("about")
            followers = _openai_friendly_number(str(item.get("followers", "")))
            companies.append(
                {
                    "handle": handle,
                    "name": name,
                    "descriptor": descriptor,
                    "about": about,
                    "followers": followers,
                    "people_url": f"{handle}people/",
                    "captured_at": datetime.now(UTC).isoformat(timespec="seconds") + "Z",
                }
            )
        page += 1
        logging.info(
            f"[dim]Page {page}[/] — running total: {len(companies)}/{limit} companies"
        )

    return companies[:max(limit, 10)]


async def crawl_people_page(
    crawler: AsyncWebCrawler,
    people_url: str,
    schema: Dict,
    limit: int,
    title_kw: str,
) -> List[Dict]:
    people_u = f"{people_url}?keywords={quote(title_kw)}"
    extraction = JsonCssExtractionStrategy(schema)
    cfg = CrawlerRunConfig(
        extraction_strategy=extraction,
        # scan_full_page=True,
        cache_mode=CacheMode.BYPASS,
        magic=True,
        wait_for=".org-people-profile-card__card-spacing",
        wait_for_images=5000,
        delay_before_return_html=1,
        session_id="people_search",
    )
    res = await crawler.arun(people_u, config=cfg)
    if not res[0].success:
        return []
    raw = json.loads(res[0].extracted_content)
    people = []
    for p in raw[:limit]:
        followers = _openai_friendly_number(str(p.get("followers", "")))
        people.append(
            {
                "profile_url": p.get("profile_url"),
                "name": p.get("name"),
                "headline": p.get("headline"),
                "followers": followers,
                "connection_degree": p.get("connection_degree"),
                "avatar_url": p.get("avatar_url"),
            }
        )
    return people

# ---------------------------------------------------------------------------
# CLI + main
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser("c4ai-discover — Crawl4AI LinkedIn discovery")
    sub = ap.add_subparsers(dest="cmd", required=False, help="run scope")

    def add_flags(parser: argparse.ArgumentParser):
        parser.add_argument("--query", required=False, help="query keyword(s)")
        parser.add_argument("--geo", required=False, type=int, help="LinkedIn geoUrn")
        parser.add_argument("--title-filters", default="Product,Engineering", help="comma list of job keywords")
        parser.add_argument("--max-companies", type=int, default=1000)
        parser.add_argument("--max-people", type=int, default=500)
        parser.add_argument("--profile-name", default=str(pathlib.Path.home() / ".crawl4ai/profiles/profile_linkedin_uc"))
        parser.add_argument("--outdir", default="./output")
        parser.add_argument("--concurrency", type=int, default=4)
        parser.add_argument("--log-level", default="info", choices=["debug", "info", "warn", "error"])

    add_flags(sub.add_parser("full"))
    add_flags(sub.add_parser("companies"))
    add_flags(sub.add_parser("people"))

    # global flags
    ap.add_argument(
        "--debug",
        action="store_true",
        help="Use built-in demo defaults (same as C4AI_DEMO_DEBUG=1)",
    )
    return ap


def detect_debug_defaults(force = False) -> SimpleNamespace:
    if not force and sys.gettrace() is None and not os.getenv("C4AI_DEMO_DEBUG"):
        return SimpleNamespace()
    # ----- debug‑friendly defaults -----
    return SimpleNamespace(
        cmd="full",
        query="health insurance management",
        geo=102713980,
        # title_filters="Product,Engineering",
        title_filters="",
        max_companies=10,
        max_people=5,
        profile_name="profile_linkedin_uc",
        outdir="./debug_out",
        concurrency=2,
        log_level="debug",
    )


async def async_main(opts):
    # ─────────── logging setup ───────────
    console = Console()
    logging.basicConfig(
        level=opts.log_level.upper(),
        format="%(message)s",
        handlers=[RichHandler(console=console, markup=True, rich_tracebacks=True)],
    )

    # -------------------------------------------------------------------
    # Load or build schemas (one‑time LLM call each)
    # -------------------------------------------------------------------
    company_schema = _load_or_build_schema(
        COMPANY_SCHEMA_PATH,
        _SAMPLE_COMPANY_HTML,
        _COMPANY_SCHEMA_QUERY,
        _COMPANY_SCHEMA_EXAMPLE,
        # True
    )
    people_schema = _load_or_build_schema(
        PEOPLE_SCHEMA_PATH,
        _SAMPLE_PEOPLE_HTML,
        _PEOPLE_SCHEMA_QUERY,
        _PEOPLE_SCHEMA_EXAMPLE,
        # True
    )

    outdir = BASE_DIR / pathlib.Path(opts.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    f_companies = (BASE_DIR / outdir / "companies.jsonl").open("a", encoding="utf-8")
    f_people = (BASE_DIR / outdir / "people.jsonl").open("a", encoding="utf-8")

    # -------------------------------------------------------------------
    # Prepare crawler with cookie pool rotation
    # -------------------------------------------------------------------
    profiler = BrowserProfiler()
    path = profiler.get_profile_path(opts.profile_name)
    bc = BrowserConfig(
        headless=False,        
        verbose=False,
        user_data_dir=path,
        use_managed_browser=True,
        user_agent_mode = "random",
        user_agent_generator_config= {
            "platforms": "mobile",
            "os": "Android"
        }
    )
    crawler = AsyncWebCrawler(config=bc)
    
    await crawler.start()

    # Single worker for simplicity; concurrency can be scaled by arun_many if needed.
    # crawler = await next_crawler().start()
    try:
        # Build LinkedIn search URL
        search_url = f'https://www.linkedin.com/search/results/companies/?keywords={quote(opts.query)}&companyHqGeo="{opts.geo}"'
        logging.info("Seed URL => %s", search_url)

        companies: List[Dict] = []
        if opts.cmd in ("companies", "full"):
            companies = await crawl_company_search(
                crawler, search_url, company_schema, opts.max_companies
            )
            for c in companies:
                f_companies.write(json.dumps(c, ensure_ascii=False) + "\n")
            logging.info(f"[bold green]✓[/] Companies scraped so far: {len(companies)}")

        if opts.cmd in ("people", "full"):
            if not companies:
                # load from previous run
                src = outdir / "companies.jsonl"
                if not src.exists():
                    logging.error("companies.jsonl missing — run companies/full first")
                    return 10
                companies = [json.loads(l) for l in src.read_text().splitlines()]
            total_people = 0
            title_kw = " ".join([t.strip() for t in opts.title_filters.split(",") if t.strip()]) if opts.title_filters else ""
            for comp in companies:
                people = await crawl_people_page(
                    crawler,
                    comp["people_url"],
                    people_schema,
                    opts.max_people,
                    title_kw,
                )
                for p in people:
                    rec = p | {
                        "company_handle": comp["handle"],
                        # "captured_at": datetime.now(UTC).isoformat(timespec="seconds") + "Z",
                        "captured_at": datetime.now(UTC).isoformat(timespec="seconds") + "Z",
                    }
                    f_people.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total_people += len(people)
                logging.info(
                    f"{comp['name']} — [cyan]{len(people)}[/] people extracted"
                )
                await asyncio.sleep(random.uniform(0.5, 1))
            logging.info("Total people scraped: %d", total_people)
    finally:
        await crawler.close()
        f_companies.close()
        f_people.close()

    return 0


def main():
    parser = build_arg_parser()
    cli_opts = parser.parse_args()

    # decide on debug defaults
    if cli_opts.debug:
        opts = detect_debug_defaults(force=True)
        cli_opts = opts
    else:
        env_defaults = detect_debug_defaults()
        opts = env_defaults if env_defaults else cli_opts

    if not getattr(opts, "cmd", None):
        opts.cmd = "full"

    exit_code = asyncio.run(async_main(cli_opts))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
