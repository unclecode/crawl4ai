"""Lite Crawl4AI API stress‑tester.

✔ batch or stream mode (single unified path)
✔ global stats + JSON summary
✔ rich table progress
✔ Typer CLI with presets (quick / soak)

Usage examples:
    python api_stress_test.py               # uses quick preset
    python api_stress_test.py soak          # 5 K URLs stress run
    python api_stress_test.py --urls 200 --concurrent 10 --chunk 20
"""

from __future__ import annotations

import asyncio, json, time, uuid, pathlib, statistics
from typing import List, Dict, Optional

import httpx, typer
from rich.console import Console
from rich.table import Table

# ───────────────────────── defaults / presets ──────────────────────────
PRESETS = {
    "quick": dict(urls=1, concurrent=1, chunk=1, stream=False),
    "debug": dict(urls=10, concurrent=2, chunk=5, stream=False),
    "soak": dict(urls=5000, concurrent=20, chunk=50, stream=True),
}

API_HEALTH_ENDPOINT = "/health"
REQUEST_TIMEOUT = 180.0

console = Console()
app = typer.Typer(add_completion=False, rich_markup_mode="rich")

# ───────────────────────── helpers ─────────────────────────────────────
async def _check_health(client: httpx.AsyncClient) -> None:
    resp = await client.get(API_HEALTH_ENDPOINT, timeout=10)
    resp.raise_for_status()
    console.print(f"[green]Server healthy — version {resp.json().get('version','?')}[/]")

async def _iter_results(resp: httpx.Response, stream: bool):
    """Yield result dicts from batch JSON or ND‑JSON stream."""
    if stream:
        async for line in resp.aiter_lines():
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("status") == "completed":
                break
            yield rec
    else:
        data = resp.json()
        for rec in data.get("results", []):
            yield rec, data  # rec + whole payload for memory delta/peak

async def _consume_stream(resp: httpx.Response) -> Dict:
    stats = {"success_urls": 0, "failed_urls": 0, "mem_metric": 0.0}
    async for line in resp.aiter_lines():
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("status") == "completed":
            break
        if rec.get("success"):
            stats["success_urls"] += 1
        else:
            stats["failed_urls"] += 1
        mem = rec.get("server_memory_mb")
        if mem is not None:
            stats["mem_metric"] = max(stats["mem_metric"], float(mem))
    return stats

def _consume_batch(body: Dict) -> Dict:
    stats = {"success_urls": 0, "failed_urls": 0}
    for rec in body.get("results", []):
        if rec.get("success"):
            stats["success_urls"] += 1
        else:
            stats["failed_urls"] += 1
    stats["mem_metric"] = body.get("server_memory_delta_mb")
    stats["peak"] = body.get("server_peak_memory_mb")
    return stats

async def _fetch_chunk(
    client: httpx.AsyncClient,
    urls: List[str],
    stream: bool,
    semaphore: asyncio.Semaphore,
) -> Dict:
    endpoint = "/crawl/stream" if stream else "/crawl"
    payload = {
        "urls": urls,
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {"type": "CrawlerRunConfig",
                           "params": {"cache_mode": "BYPASS", "stream": stream}},
    }

    async with semaphore:
        start = time.perf_counter()

        if stream:
            # ---- streaming request ----
            async with client.stream("POST", endpoint, json=payload) as resp:
                resp.raise_for_status()
                stats = await _consume_stream(resp)
        else:
            # ---- batch request ----
            resp = await client.post(endpoint, json=payload)
            resp.raise_for_status()
            stats = _consume_batch(resp.json())

        stats["elapsed"] = time.perf_counter() - start
        return stats


# ───────────────────────── core runner ─────────────────────────────────
async def _run(api: str, urls: int, concurrent: int, chunk: int, stream: bool, report: pathlib.Path):
    client = httpx.AsyncClient(base_url=api, timeout=REQUEST_TIMEOUT, limits=httpx.Limits(max_connections=concurrent+5))
    await _check_health(client)

    url_list = [f"https://httpbin.org/anything/{uuid.uuid4()}" for _ in range(urls)]
    chunks = [url_list[i:i+chunk] for i in range(0, len(url_list), chunk)]
    sem = asyncio.Semaphore(concurrent)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Batch", style="dim", width=6)
    table.add_column("Success/Fail", width=12)
    table.add_column("Mem", width=14)
    table.add_column("Time (s)")

    agg_success = agg_fail = 0
    deltas, peaks = [], []

    start = time.perf_counter()
    tasks = [asyncio.create_task(_fetch_chunk(client, c, stream, sem)) for c in chunks]
    for idx, coro in enumerate(asyncio.as_completed(tasks), 1):
        res = await coro
        agg_success += res["success_urls"]
        agg_fail += res["failed_urls"]
        if res["mem_metric"] is not None:
            deltas.append(res["mem_metric"])
        if res["peak"] is not None:
            peaks.append(res["peak"])

        mem_txt = f"{res['mem_metric']:.1f}" if res["mem_metric"] is not None else "‑"
        if res["peak"] is not None:
            mem_txt = f"{res['peak']:.1f}/{mem_txt}"

        table.add_row(str(idx), f"{res['success_urls']}/{res['failed_urls']}", mem_txt, f"{res['elapsed']:.2f}")

    console.print(table)
    total_time = time.perf_counter() - start

    summary = {
        "urls": urls,
        "concurrent": concurrent,
        "chunk": chunk,
        "stream": stream,
        "success_urls": agg_success,
        "failed_urls": agg_fail,
        "elapsed_sec": round(total_time, 2),
        "avg_mem": round(statistics.mean(deltas), 2) if deltas else None,
        "max_mem": max(deltas) if deltas else None,
        "avg_peak": round(statistics.mean(peaks), 2) if peaks else None,
        "max_peak": max(peaks) if peaks else None,
    }
    console.print("\n[bold green]Done:[/]" , summary)

    report.mkdir(parents=True, exist_ok=True)
    path = report / f"api_test_{int(time.time())}.json"
    path.write_text(json.dumps(summary, indent=2))
    console.print(f"[green]Summary → {path}")

    await client.aclose()

# ───────────────────────── Typer CLI ──────────────────────────────────
@app.command()
def main(
    preset: str = typer.Argument("quick", help="quick / debug / soak or custom"),
    api_url: str = typer.Option("http://localhost:8020", show_default=True),
    urls: int = typer.Option(None, help="Total URLs to crawl"),
    concurrent: int = typer.Option(None, help="Concurrent API requests"),
    chunk: int = typer.Option(None, help="URLs per request"),
    stream: bool = typer.Option(None, help="Use /crawl/stream"),
    report: pathlib.Path = typer.Option("reports_api", help="Where to save JSON summary"),
):
    """Run a stress test against a running Crawl4AI API server."""
    if preset not in PRESETS and any(v is None for v in (urls, concurrent, chunk, stream)):
        console.print(f"[red]Unknown preset '{preset}' and custom params missing[/]")
        raise typer.Exit(1)

    cfg = PRESETS.get(preset, {})
    urls = urls or cfg.get("urls")
    concurrent = concurrent or cfg.get("concurrent")
    chunk = chunk or cfg.get("chunk")
    stream = stream if stream is not None else cfg.get("stream", False)

    console.print(f"[cyan]API:[/] {api_url} | URLs: {urls} | Concurrency: {concurrent} | Chunk: {chunk} | Stream: {stream}")
    asyncio.run(_run(api_url, urls, concurrent, chunk, stream, report))

if __name__ == "__main__":
    app()
