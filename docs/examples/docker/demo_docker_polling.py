
#!/usr/bin/env python3
"""
demo_docker_polling.py
Quick sanity-check for the asynchronous crawl job endpoints:

  • POST  /crawl/job          – enqueue work, get task_id
  • GET   /crawl/job/{id}     – poll status / fetch result

The style matches demo_docker_api.py (console.rule banners, helper
functions, coloured status lines).  Adjust BASE_URL as needed.

Run:  python demo_docker_polling.py
"""

import asyncio, json, os, time, urllib.parse
from typing import Dict, List

import httpx
from rich.console import Console
from rich.panel   import Panel
from rich.syntax  import Syntax

console   = Console()
BASE_URL  = os.getenv("BASE_URL", "http://localhost:11234")
SIMPLE_URL = "https://example.org"
LINKS_URL  = "https://httpbin.org/links/10/1"

# --- helpers --------------------------------------------------------------


def print_payload(payload: Dict):
    console.print(Panel(Syntax(json.dumps(payload, indent=2),
                               "json", theme="monokai", line_numbers=False),
                        title="Payload", border_style="cyan", expand=False))


async def check_server_health(client: httpx.AsyncClient) -> bool:
    try:
        resp = await client.get("/health")
        if resp.is_success:
            console.print("[green]Server healthy[/]")
            return True
    except Exception:
        pass
    console.print("[bold red]Server is not responding on /health[/]")
    return False


async def poll_for_result(client: httpx.AsyncClient, task_id: str,
                          poll_interval: float = 1.5, timeout: float = 90.0):
    """Hit /crawl/job/{id} until COMPLETED/FAILED or timeout."""
    start = time.time()
    while True:
        resp = await client.get(f"/crawl/job/{task_id}")
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        if status.upper() in ("COMPLETED", "FAILED"):
            return data
        if time.time() - start > timeout:
            raise TimeoutError(f"Task {task_id} did not finish in {timeout}s")
        await asyncio.sleep(poll_interval)


# --- demo functions -------------------------------------------------------


async def demo_poll_single_url(client: httpx.AsyncClient):
    payload = {
        "urls": [SIMPLE_URL],
        "browser_config": {"type": "BrowserConfig",
                           "params": {"headless": True}},
        "crawler_config": {"type": "CrawlerRunConfig",
                           "params": {"cache_mode": "BYPASS"}}
    }

    console.rule("[bold blue]Demo A: /crawl/job Single URL[/]", style="blue")
    print_payload(payload)

    # enqueue
    resp = await client.post("/crawl/job", json=payload)
    console.print(f"Enqueue status: [bold]{resp.status_code}[/]")
    resp.raise_for_status()
    task_id = resp.json()["task_id"]
    console.print(f"Task ID: [yellow]{task_id}[/]")

    # poll
    console.print("Polling…")
    result = await poll_for_result(client, task_id)
    console.print(Panel(Syntax(json.dumps(result, indent=2),
                               "json", theme="fruity"),
                        title="Final result", border_style="green"))
    if result["status"] == "COMPLETED":
        console.print("[green]✅ Crawl succeeded[/]")
    else:
        console.print("[red]❌ Crawl failed[/]")


async def demo_poll_multi_url(client: httpx.AsyncClient):
    payload = {
        "urls": [SIMPLE_URL, LINKS_URL],
        "browser_config": {"type": "BrowserConfig",
                           "params": {"headless": True}},
        "crawler_config": {"type": "CrawlerRunConfig",
                           "params": {"cache_mode": "BYPASS"}}
    }

    console.rule("[bold magenta]Demo B: /crawl/job Multi-URL[/]",
                 style="magenta")
    print_payload(payload)

    resp = await client.post("/crawl/job", json=payload)
    console.print(f"Enqueue status: [bold]{resp.status_code}[/]")
    resp.raise_for_status()
    task_id = resp.json()["task_id"]
    console.print(f"Task ID: [yellow]{task_id}[/]")

    console.print("Polling…")
    result = await poll_for_result(client, task_id)
    console.print(Panel(Syntax(json.dumps(result, indent=2),
                               "json", theme="fruity"),
                        title="Final result", border_style="green"))
    if result["status"] == "COMPLETED":
        console.print(
            f"[green]✅ {len(json.loads(result['result'])['results'])} URLs crawled[/]")
    else:
        console.print("[red]❌ Crawl failed[/]")


# --- main runner ----------------------------------------------------------


async def main_demo():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=300.0) as client:
        if not await check_server_health(client):
            return
        await demo_poll_single_url(client)
        await demo_poll_multi_url(client)
        console.rule("[bold green]Polling demos complete[/]", style="green")


if __name__ == "__main__":
    try:
        asyncio.run(main_demo())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/]")
    except Exception:
        console.print_exception(show_locals=False)
