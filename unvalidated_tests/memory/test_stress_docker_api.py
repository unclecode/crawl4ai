"""
Crawl4AI Docker API stress tester.

Examples
--------
python test_stress_docker_api.py --urls 1000 --concurrency 32
python test_stress_docker_api.py --urls 1000 --concurrency 32 --stream
python test_stress_docker_api.py --base-url http://10.0.0.42:11235 --http2
"""

import argparse, asyncio, json, secrets, statistics, time
from typing import List, Tuple
import httpx
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table

console = Console()


# ───────────────────────── helpers ─────────────────────────
def make_fake_urls(n: int) -> List[str]:
    base = "https://httpbin.org/anything/"
    return [f"{base}{secrets.token_hex(8)}" for _ in range(n)]


async def fire(
    client: httpx.AsyncClient, endpoint: str, payload: dict, sem: asyncio.Semaphore
) -> Tuple[bool, float]:
    async with sem:
        print(f"POST {endpoint} with {len(payload['urls'])} URLs")
        t0 = time.perf_counter()
        try:
            if endpoint.endswith("/stream"):
                async with client.stream("POST", endpoint, json=payload) as r:
                    r.raise_for_status()
                    async for _ in r.aiter_lines():
                        pass
            else:
                r = await client.post(endpoint, json=payload)                
                r.raise_for_status()
            return True, time.perf_counter() - t0
        except Exception:
            return False, time.perf_counter() - t0


def pct(lat: List[float], p: float) -> str:
    """Return percentile string even for tiny samples."""
    if not lat:
        return "-"
    if len(lat) == 1:
        return f"{lat[0]:.2f}s"
    lat_sorted = sorted(lat)
    k = (p / 100) * (len(lat_sorted) - 1)
    lo = int(k)
    hi = min(lo + 1, len(lat_sorted) - 1)
    frac = k - lo
    val = lat_sorted[lo] * (1 - frac) + lat_sorted[hi] * frac
    return f"{val:.2f}s"


# ───────────────────────── main ─────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stress test Crawl4AI Docker API")
    p.add_argument("--urls", type=int, default=100, help="number of URLs")
    p.add_argument("--concurrency", type=int, default=1, help="max POSTs in flight")
    p.add_argument("--chunk-size", type=int, default=50, help="URLs per request")
    p.add_argument("--base-url", default="http://localhost:11235", help="API root")
    # p.add_argument("--base-url", default="http://localhost:8020", help="API root")
    p.add_argument("--stream", action="store_true", help="use /crawl/stream")
    p.add_argument("--http2", action="store_true", help="enable HTTP/2")
    p.add_argument("--headless", action="store_true", default=True)
    return p.parse_args()


async def main() -> None:
    args = parse_args()

    urls = make_fake_urls(args.urls)
    batches = [urls[i : i + args.chunk_size] for i in range(0, len(urls), args.chunk_size)]
    endpoint = "/crawl/stream" if args.stream else "/crawl"
    sem = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient(base_url=args.base_url, http2=args.http2, timeout=None) as client:
        with Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task("[cyan]bombarding…", total=len(batches))
            tasks = []
            for chunk in batches:
                payload = {
                    "urls": chunk,
                    "browser_config": {"type": "BrowserConfig", "params": {"headless": args.headless}},
                    "crawler_config": {"type": "CrawlerRunConfig", "params": {"cache_mode": "BYPASS", "stream": args.stream}},
                }
                tasks.append(asyncio.create_task(fire(client, endpoint, payload, sem)))
                progress.advance(task_id)

            results = await asyncio.gather(*tasks)

    ok_latencies = [dt for ok, dt in results if ok]
    err_count = sum(1 for ok, _ in results if not ok)

    table = Table(title="Docker API Stress‑Test Summary")
    table.add_column("total", justify="right")
    table.add_column("errors", justify="right")
    table.add_column("p50", justify="right")
    table.add_column("p95", justify="right")
    table.add_column("max", justify="right")

    table.add_row(
        str(len(results)),
        str(err_count),
        pct(ok_latencies, 50),
        pct(ok_latencies, 95),
        f"{max(ok_latencies):.2f}s" if ok_latencies else "-",
    )
    console.print(table)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]aborted by user[/]")
