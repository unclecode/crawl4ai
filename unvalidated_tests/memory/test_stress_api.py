#!/usr/bin/env python3
"""
Stress test for Crawl4AI's Docker API server (/crawl and /crawl/stream endpoints).

This version targets a running Crawl4AI API server, sending concurrent requests
to test its ability to handle multiple crawl jobs simultaneously.
It uses httpx for async HTTP requests and logs results per batch of requests,
including server-side memory usage reported by the API.
"""

import asyncio
import time
import uuid
import argparse
import json
import sys
import os
import shutil
from typing import List, Dict, Optional, Union, AsyncGenerator, Tuple
import httpx
import pathlib # Import pathlib explicitly
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# --- Constants ---
DEFAULT_API_URL = "http://localhost:11235" # Default port
DEFAULT_API_URL = "http://localhost:8020" # Default port
DEFAULT_URL_COUNT = 100
DEFAULT_MAX_CONCURRENT_REQUESTS = 1
DEFAULT_CHUNK_SIZE = 10
DEFAULT_REPORT_PATH = "reports_api"
DEFAULT_STREAM_MODE = True
REQUEST_TIMEOUT = 180.0

# Initialize Rich console
console = Console()

# --- API Health Check (Unchanged) ---
async def check_server_health(client: httpx.AsyncClient, health_endpoint: str = "/health"):
    """Check if the API server is healthy."""
    console.print(f"[bold cyan]Checking API server health at {client.base_url}{health_endpoint}...[/]", end="")
    try:
        response = await client.get(health_endpoint, timeout=10.0)
        response.raise_for_status()
        health_data = response.json()
        version = health_data.get('version', 'N/A')
        console.print(f"[bold green] Server OK! Version: {version}[/]")
        return True
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        console.print(f"\n[bold red]Server health check FAILED:[/]")
        console.print(f"Error: {e}")
        console.print(f"Is the server running and accessible at {client.base_url}?")
        return False
    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred during health check:[/]")
        console.print(e)
        return False

# --- API Stress Test Class ---
class ApiStressTest:
    """Orchestrates the stress test by sending concurrent requests to the API."""

    def __init__(
        self,
        api_url: str,
        url_count: int,
        max_concurrent_requests: int,
        chunk_size: int,
        report_path: str,
        stream_mode: bool,
    ):
        self.api_base_url = api_url.rstrip('/')
        self.url_count = url_count
        self.max_concurrent_requests = max_concurrent_requests
        self.chunk_size = chunk_size
        self.report_path = pathlib.Path(report_path)
        self.report_path.mkdir(parents=True, exist_ok=True)
        self.stream_mode = stream_mode
        
        # Ignore repo path and set it to current file path
        self.repo_path = pathlib.Path(__file__).parent.resolve()


        self.test_id = time.strftime("%Y%m%d_%H%M%S")
        self.results_summary = {
            "test_id": self.test_id, "api_url": api_url, "url_count": url_count,
            "max_concurrent_requests": max_concurrent_requests, "chunk_size": chunk_size,
            "stream_mode": stream_mode, "start_time": "", "end_time": "",
            "total_time_seconds": 0, "successful_requests": 0, "failed_requests": 0,
            "successful_urls": 0, "failed_urls": 0, "total_urls_processed": 0,
            "total_api_calls": 0,
            "server_memory_metrics": { # To store aggregated server memory info
                 "batch_mode_avg_delta_mb": None,
                 "batch_mode_max_delta_mb": None,
                 "stream_mode_avg_max_snapshot_mb": None,
                 "stream_mode_max_max_snapshot_mb": None,
                 "samples": [] # Store individual request memory results
             }
        }
        self.http_client = httpx.AsyncClient(base_url=self.api_base_url, timeout=REQUEST_TIMEOUT, limits=httpx.Limits(max_connections=max_concurrent_requests + 5, max_keepalive_connections=max_concurrent_requests))

    async def close_client(self):
        """Close the httpx client."""
        await self.http_client.aclose()

    async def run(self) -> Dict:
        """Run the API stress test."""
        # No client memory tracker needed
        urls_to_process = [f"https://httpbin.org/anything/{uuid.uuid4()}" for _ in range(self.url_count)]
        url_chunks = [urls_to_process[i:i+self.chunk_size] for i in range(0, len(urls_to_process), self.chunk_size)]

        self.results_summary["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        start_time = time.time()

        console.print(f"\n[bold cyan]Crawl4AI API Stress Test - {self.url_count} URLs, {self.max_concurrent_requests} concurrent requests[/bold cyan]")
        console.print(f"[bold cyan]Target API:[/bold cyan] {self.api_base_url}, [bold cyan]Mode:[/bold cyan] {'Streaming' if self.stream_mode else 'Batch'}, [bold cyan]URLs per Request:[/bold cyan] {self.chunk_size}")
        # Removed client memory log

        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        # Updated Batch logging header
        console.print("\n[bold]API Request Batch Progress:[/bold]")
        # Adjusted spacing and added Peak
        console.print("[bold] Batch | Progress | SrvMem Peak / Δ|Max (MB) | Reqs/sec | S/F URLs | Time (s) | Status  [/bold]")
        # Adjust separator length if needed, looks okay for now
        console.print("─" * 95) 

        # No client memory monitor task needed

        tasks = []
        total_api_calls = len(url_chunks)
        self.results_summary["total_api_calls"] = total_api_calls

        try:
            for i, chunk in enumerate(url_chunks):
                task = asyncio.create_task(self._make_api_request(
                    chunk=chunk,
                    batch_idx=i + 1,
                    total_batches=total_api_calls,
                    semaphore=semaphore
                    # No memory tracker passed
                ))
                tasks.append(task)

            api_results = await asyncio.gather(*tasks)

            # Process aggregated results including server memory
            total_successful_requests = sum(1 for r in api_results if r['request_success'])
            total_failed_requests = total_api_calls - total_successful_requests
            total_successful_urls = sum(r['success_urls'] for r in api_results)
            total_failed_urls = sum(r['failed_urls'] for r in api_results)
            total_urls_processed = total_successful_urls + total_failed_urls

            # Aggregate server memory metrics
            valid_samples = [r for r in api_results if r.get('server_delta_or_max_mb') is not None] # Filter results with valid mem data
            self.results_summary["server_memory_metrics"]["samples"] = valid_samples # Store raw samples with both peak and delta/max

            if valid_samples:
                 delta_or_max_values = [r['server_delta_or_max_mb'] for r in valid_samples]
                 if self.stream_mode:
                     # Stream mode: delta_or_max holds max snapshot
                     self.results_summary["server_memory_metrics"]["stream_mode_avg_max_snapshot_mb"] = sum(delta_or_max_values) / len(delta_or_max_values)
                     self.results_summary["server_memory_metrics"]["stream_mode_max_max_snapshot_mb"] = max(delta_or_max_values)
                 else: # Batch mode
                     # delta_or_max holds delta
                     self.results_summary["server_memory_metrics"]["batch_mode_avg_delta_mb"] = sum(delta_or_max_values) / len(delta_or_max_values)
                     self.results_summary["server_memory_metrics"]["batch_mode_max_delta_mb"] = max(delta_or_max_values)

                     # Aggregate peak values for batch mode
                     peak_values = [r['server_peak_memory_mb'] for r in valid_samples if r.get('server_peak_memory_mb') is not None]
                     if peak_values:
                          self.results_summary["server_memory_metrics"]["batch_mode_avg_peak_mb"] = sum(peak_values) / len(peak_values)
                          self.results_summary["server_memory_metrics"]["batch_mode_max_peak_mb"] = max(peak_values)


            self.results_summary.update({
                "successful_requests": total_successful_requests,
                "failed_requests": total_failed_requests,
                "successful_urls": total_successful_urls,
                "failed_urls": total_failed_urls,
                "total_urls_processed": total_urls_processed,
            })

        except Exception as e:
             console.print(f"[bold red]An error occurred during task execution: {e}[/bold red]")
             import traceback
             traceback.print_exc()
        # No finally block needed for monitor task

        end_time = time.time()
        self.results_summary.update({
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time_seconds": end_time - start_time,
            # No client memory report
        })
        self._save_results()
        return self.results_summary

    async def _make_api_request(
        self,
        chunk: List[str],
        batch_idx: int,
        total_batches: int,
        semaphore: asyncio.Semaphore
        # No memory tracker
    ) -> Dict:
        """Makes a single API request for a chunk of URLs, handling concurrency and logging server memory."""
        request_success = False
        success_urls = 0
        failed_urls = 0
        status = "Pending"
        status_color = "grey"
        server_memory_metric = None # Store delta (batch) or max snapshot (stream)
        api_call_start_time = time.time()

        async with semaphore:
            try:
                # No client memory sampling

                endpoint = "/crawl/stream" if self.stream_mode else "/crawl"
                payload = {
                    "urls": chunk,
                    "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
                    "crawler_config": {
                        "type": "CrawlerRunConfig",
                        "params": {"cache_mode": "BYPASS", "stream": self.stream_mode}
                    }
                }

                if self.stream_mode:
                    max_server_mem_snapshot = 0.0 # Track max memory seen in this stream
                    async with self.http_client.stream("POST", endpoint, json=payload) as response:
                        initial_status_code = response.status_code
                        response.raise_for_status()

                        completed_marker_received = False
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    if data.get("status") == "completed":
                                        completed_marker_received = True
                                        break
                                    elif data.get("url"):
                                        if data.get("success"): success_urls += 1
                                        else: failed_urls += 1
                                        # Extract server memory snapshot per result
                                        mem_snapshot = data.get('server_memory_mb')
                                        if mem_snapshot is not None:
                                            max_server_mem_snapshot = max(max_server_mem_snapshot, float(mem_snapshot))
                                except json.JSONDecodeError:
                                    console.print(f"[Batch {batch_idx}] [red]Stream decode error for line:[/red] {line}")
                                    failed_urls = len(chunk)
                                    break
                        request_success = completed_marker_received
                        if not request_success:
                             failed_urls = len(chunk) - success_urls
                        server_memory_metric = max_server_mem_snapshot # Use max snapshot for stream logging

                else: # Batch mode
                    response = await self.http_client.post(endpoint, json=payload)
                    response.raise_for_status()
                    data = response.json()

                    # Extract server memory delta from the response
                    server_memory_metric = data.get('server_memory_delta_mb')
                    server_peak_mem_mb = data.get('server_peak_memory_mb') 

                    if data.get("success") and "results" in data:
                        request_success = True
                        results_list = data.get("results", [])
                        for result_item in results_list:
                            if result_item.get("success"): success_urls += 1
                            else: failed_urls += 1
                        if len(results_list) != len(chunk):
                             console.print(f"[Batch {batch_idx}] [yellow]Warning: Result count ({len(results_list)}) doesn't match URL count ({len(chunk)})[/yellow]")
                             failed_urls = len(chunk) - success_urls
                    else:
                        request_success = False
                        failed_urls = len(chunk)
                        # Try to get memory from error detail if available
                        detail = data.get('detail')
                        if isinstance(detail, str):
                            try: detail_json = json.loads(detail)
                            except: detail_json = {}
                        elif isinstance(detail, dict):
                            detail_json = detail
                        else: detail_json = {}
                        server_peak_mem_mb = detail_json.get('server_peak_memory_mb', None)
                        server_memory_metric = detail_json.get('server_memory_delta_mb', None)
                        console.print(f"[Batch {batch_idx}] [red]API request failed:[/red] {detail_json.get('error', 'No details')}")


            except httpx.HTTPStatusError as e:
                request_success = False
                failed_urls = len(chunk)
                console.print(f"[Batch {batch_idx}] [bold red]HTTP Error {e.response.status_code}:[/] {e.request.url}")
                try:
                    error_detail = e.response.json()
                    # Attempt to extract memory info even from error responses
                    detail_content = error_detail.get('detail', {})
                    if isinstance(detail_content, str): # Handle if detail is stringified JSON
                         try: detail_content = json.loads(detail_content)
                         except: detail_content = {}
                    server_memory_metric = detail_content.get('server_memory_delta_mb', None)
                    server_peak_mem_mb = detail_content.get('server_peak_memory_mb', None)
                    console.print(f"Response: {error_detail}")
                except Exception:
                     console.print(f"Response Text: {e.response.text[:200]}...")
            except httpx.RequestError as e:
                request_success = False
                failed_urls = len(chunk)
                console.print(f"[Batch {batch_idx}] [bold red]Request Error:[/bold] {e.request.url} - {e}")
            except Exception as e:
                request_success = False
                failed_urls = len(chunk)
                console.print(f"[Batch {batch_idx}] [bold red]Unexpected Error:[/bold] {e}")
                import traceback
                traceback.print_exc()

            finally:
                api_call_time = time.time() - api_call_start_time
                total_processed_urls = success_urls + failed_urls

                if request_success and failed_urls == 0: status_color, status = "green", "Success"
                elif request_success and success_urls > 0: status_color, status = "yellow", "Partial"
                else: status_color, status = "red", "Failed"

                current_total_urls = batch_idx * self.chunk_size
                progress_pct = min(100.0, (current_total_urls / self.url_count) * 100)
                reqs_per_sec = 1.0 / api_call_time if api_call_time > 0 else float('inf')

                # --- New Memory Formatting ---
                mem_display = " N/A " # Default
                peak_mem_value = None
                delta_or_max_value = None

                if self.stream_mode:
                    # server_memory_metric holds max snapshot for stream
                    if server_memory_metric is not None:
                        mem_display = f"{server_memory_metric:.1f} (Max)"
                        delta_or_max_value = server_memory_metric # Store for aggregation
                else: # Batch mode - expect peak and delta
                    # We need to get peak and delta from the API response
                    peak_mem_value = locals().get('server_peak_mem_mb', None) # Get from response data if available
                    delta_value = server_memory_metric # server_memory_metric holds delta for batch

                    if peak_mem_value is not None and delta_value is not None:
                        mem_display = f"{peak_mem_value:.1f} / {delta_value:+.1f}"
                        delta_or_max_value = delta_value # Store delta for aggregation
                    elif peak_mem_value is not None:
                         mem_display = f"{peak_mem_value:.1f} / N/A"
                    elif delta_value is not None:
                         mem_display = f"N/A / {delta_value:+.1f}"
                         delta_or_max_value = delta_value # Store delta for aggregation

                # --- Updated Print Statement with Adjusted Padding ---
                console.print(
                    f" {batch_idx:<5} | {progress_pct:6.1f}% | {mem_display:>24} | {reqs_per_sec:8.1f} | " # Increased width for memory column
                    f"{success_urls:^7}/{failed_urls:<6} | {api_call_time:8.2f} | [{status_color}]{status:<7}[/{status_color}] " # Added trailing space
                )

                # --- Updated Return Dictionary ---
                return_data = {
                    "batch_idx": batch_idx,
                    "request_success": request_success,
                    "success_urls": success_urls,
                    "failed_urls": failed_urls,
                    "time": api_call_time,
                    # Return both peak (if available) and delta/max
                    "server_peak_memory_mb": peak_mem_value, # Will be None for stream mode
                    "server_delta_or_max_mb": delta_or_max_value # Delta for batch, Max for stream
                }
                # Add back the specific batch mode delta if needed elsewhere, but delta_or_max covers it
                # if not self.stream_mode:
                #    return_data["server_memory_delta_mb"] = delta_value
                return return_data

    # No _periodic_memory_sample needed

    def _save_results(self) -> None:
        """Saves the results summary to a JSON file."""
        results_path = self.report_path / f"api_test_summary_{self.test_id}.json"
        try:
            # No client memory path to convert
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(self.results_summary, f, indent=2, default=str)
        except Exception as e:
            console.print(f"[bold red]Failed to save results summary: {e}[/bold red]")


# --- run_full_test Function ---
async def run_full_test(args):
    """Runs the full API stress test process."""
    client = httpx.AsyncClient(base_url=args.api_url, timeout=REQUEST_TIMEOUT)

    if not await check_server_health(client):
        console.print("[bold red]Aborting test due to server health check failure.[/]")
        await client.aclose()
        return
    await client.aclose()

    test = ApiStressTest(
        api_url=args.api_url,
        url_count=args.urls,
        max_concurrent_requests=args.max_concurrent_requests,
        chunk_size=args.chunk_size,
        report_path=args.report_path,
        stream_mode=args.stream,
    )
    results = {}
    try:
        results = await test.run()
    finally:
        await test.close_client()

    if not results:
        console.print("[bold red]Test did not produce results.[/bold red]")
        return

    console.print("\n" + "=" * 80)
    console.print("[bold green]API Stress Test Completed[/bold green]")
    console.print("=" * 80)

    success_rate_reqs = results["successful_requests"] / results["total_api_calls"] * 100 if results["total_api_calls"] > 0 else 0
    success_rate_urls = results["successful_urls"] / results["url_count"] * 100 if results["url_count"] > 0 else 0
    urls_per_second = results["total_urls_processed"] / results["total_time_seconds"] if results["total_time_seconds"] > 0 else 0
    reqs_per_second = results["total_api_calls"] / results["total_time_seconds"] if results["total_time_seconds"] > 0 else 0


    console.print(f"[bold cyan]Test ID:[/bold cyan] {results['test_id']}")
    console.print(f"[bold cyan]Target API:[/bold cyan] {results['api_url']}")
    console.print(f"[bold cyan]Configuration:[/bold cyan] {results['url_count']} URLs, {results['max_concurrent_requests']} concurrent client requests, URLs/Req: {results['chunk_size']}, Stream: {results['stream_mode']}")
    console.print(f"[bold cyan]API Requests:[/bold cyan] {results['successful_requests']} successful, {results['failed_requests']} failed ({results['total_api_calls']} total, {success_rate_reqs:.1f}% success)")
    console.print(f"[bold cyan]URL Processing:[/bold cyan] {results['successful_urls']} successful, {results['failed_urls']} failed ({results['total_urls_processed']} processed, {success_rate_urls:.1f}% success)")
    console.print(f"[bold cyan]Performance:[/bold cyan] {results['total_time_seconds']:.2f}s total | Avg Reqs/sec: {reqs_per_second:.2f} | Avg URLs/sec: {urls_per_second:.2f}")

    # Report Server Memory
    mem_metrics = results.get("server_memory_metrics", {})
    mem_samples = mem_metrics.get("samples", [])
    if mem_samples:
         num_samples = len(mem_samples)
         if results['stream_mode']:
             avg_mem = mem_metrics.get("stream_mode_avg_max_snapshot_mb")
             max_mem = mem_metrics.get("stream_mode_max_max_snapshot_mb")
             avg_str = f"{avg_mem:.1f}" if avg_mem is not None else "N/A"
             max_str = f"{max_mem:.1f}" if max_mem is not None else "N/A"
             console.print(f"[bold cyan]Server Memory (Stream):[/bold cyan] Avg Max Snapshot: {avg_str} MB | Max Max Snapshot: {max_str} MB (across {num_samples} requests)")
         else: # Batch mode
             avg_delta = mem_metrics.get("batch_mode_avg_delta_mb")
             max_delta = mem_metrics.get("batch_mode_max_delta_mb")
             avg_peak = mem_metrics.get("batch_mode_avg_peak_mb")
             max_peak = mem_metrics.get("batch_mode_max_peak_mb")

             avg_delta_str = f"{avg_delta:.1f}" if avg_delta is not None else "N/A"
             max_delta_str = f"{max_delta:.1f}" if max_delta is not None else "N/A"
             avg_peak_str = f"{avg_peak:.1f}" if avg_peak is not None else "N/A"
             max_peak_str = f"{max_peak:.1f}" if max_peak is not None else "N/A"

             console.print(f"[bold cyan]Server Memory (Batch):[/bold cyan] Avg Peak: {avg_peak_str} MB | Max Peak: {max_peak_str} MB | Avg Delta: {avg_delta_str} MB | Max Delta: {max_delta_str} MB (across {num_samples} requests)")
    else:
        console.print("[bold cyan]Server Memory:[/bold cyan] No memory data reported by server.")


    # No client memory report
    summary_path = pathlib.Path(args.report_path) / f"api_test_summary_{results['test_id']}.json"
    console.print(f"[bold green]Results summary saved to {summary_path}[/bold green]")

    if results["failed_requests"] > 0:
        console.print(f"\n[bold yellow]Warning: {results['failed_requests']} API requests failed ({100-success_rate_reqs:.1f}% failure rate)[/bold yellow]")
    if results["failed_urls"] > 0:
         console.print(f"[bold yellow]Warning: {results['failed_urls']} URLs failed to process ({100-success_rate_urls:.1f}% URL failure rate)[/bold yellow]")
    if results["total_urls_processed"] < results["url_count"]:
        console.print(f"\n[bold red]Error: Only {results['total_urls_processed']} out of {results['url_count']} target URLs were processed![/bold red]")


# --- main Function (Argument parsing mostly unchanged) ---
def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Crawl4AI API Server Stress Test")

    parser.add_argument("--api-url", type=str, default=DEFAULT_API_URL, help=f"Base URL of the Crawl4AI API server (default: {DEFAULT_API_URL})")
    parser.add_argument("--urls", type=int, default=DEFAULT_URL_COUNT, help=f"Total number of unique URLs to process via API calls (default: {DEFAULT_URL_COUNT})")
    parser.add_argument("--max-concurrent-requests", type=int, default=DEFAULT_MAX_CONCURRENT_REQUESTS, help=f"Maximum concurrent API requests from this client (default: {DEFAULT_MAX_CONCURRENT_REQUESTS})")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help=f"Number of URLs per API request payload (default: {DEFAULT_CHUNK_SIZE})")
    parser.add_argument("--stream", action="store_true", default=DEFAULT_STREAM_MODE, help=f"Use the /crawl/stream endpoint instead of /crawl (default: {DEFAULT_STREAM_MODE})")
    parser.add_argument("--report-path", type=str, default=DEFAULT_REPORT_PATH, help=f"Path to save reports and logs (default: {DEFAULT_REPORT_PATH})")
    parser.add_argument("--clean-reports", action="store_true", help="Clean up report directory before running")

    args = parser.parse_args()

    console.print("[bold underline]Crawl4AI API Stress Test Configuration[/bold underline]")
    console.print(f"API URL: {args.api_url}")
    console.print(f"Total URLs: {args.urls}, Concurrent Client Requests: {args.max_concurrent_requests}, URLs per Request: {args.chunk_size}")
    console.print(f"Mode: {'Streaming' if args.stream else 'Batch'}")
    console.print(f"Report Path: {args.report_path}")
    console.print("-" * 40)
    if args.clean_reports: console.print("[cyan]Option: Clean reports before test[/cyan]")
    console.print("-" * 40)

    if args.clean_reports:
        report_dir = pathlib.Path(args.report_path)
        if report_dir.exists():
            console.print(f"[yellow]Cleaning up reports directory: {args.report_path}[/yellow]")
            shutil.rmtree(args.report_path)
        report_dir.mkdir(parents=True, exist_ok=True)

    try:
        asyncio.run(run_full_test(args))
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Test interrupted by user.[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # No need to modify sys.path for SimpleMemoryTracker as it's removed
    main()