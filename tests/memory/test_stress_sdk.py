#!/usr/bin/env python3
"""
Stress test for Crawl4AI's arun_many and dispatcher system.
This version uses a local HTTP server and focuses on testing
the SDK's ability to handle multiple URLs concurrently, with per-batch logging.
"""

import asyncio
import os
import time
import pathlib
import random
import secrets
import argparse
import json
import sys
import subprocess
import signal
from typing import List, Dict, Optional, Union, AsyncGenerator
import shutil
from rich.console import Console

# Crawl4AI components
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    BrowserConfig,
    MemoryAdaptiveDispatcher,
    CrawlerMonitor,
    DisplayMode,
    CrawlResult,
    RateLimiter,
    CacheMode,
)

# Constants
DEFAULT_SITE_PATH = "test_site"
DEFAULT_PORT = 8000
DEFAULT_MAX_SESSIONS = 16
DEFAULT_URL_COUNT = 1
DEFAULT_CHUNK_SIZE = 1 # Define chunk size for batch logging
DEFAULT_REPORT_PATH = "reports"
DEFAULT_STREAM_MODE = False
DEFAULT_MONITOR_MODE = "DETAILED"

# Initialize Rich console
console = Console()

# --- SiteGenerator Class (Unchanged) ---
class SiteGenerator:
    """Generates a local test site with heavy pages for stress testing."""

    def __init__(self, site_path: str = DEFAULT_SITE_PATH, page_count: int = DEFAULT_URL_COUNT):
        self.site_path = pathlib.Path(site_path)
        self.page_count = page_count
        self.images_dir = self.site_path / "images"
        self.lorem_words = " ".join("lorem ipsum dolor sit amet " * 100).split()

        self.html_template = """<!doctype html>
<html>
<head>
    <title>Test Page {page_num}</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Test Page {page_num}</h1>
    {paragraphs}
    {images}
</body>
</html>
"""

    def generate_site(self) -> None:
        self.site_path.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        console.print(f"Generating {self.page_count} test pages...")
        for i in range(self.page_count):
            paragraphs = "\n".join(f"<p>{' '.join(random.choices(self.lorem_words, k=200))}</p>" for _ in range(5))
            images = "\n".join(f'<img src="https://picsum.photos/seed/{secrets.token_hex(8)}/300/200" loading="lazy" alt="Random image {j}"/>' for j in range(3))
            page_path = self.site_path / f"page_{i}.html"
            page_path.write_text(self.html_template.format(page_num=i, paragraphs=paragraphs, images=images), encoding="utf-8")
            if (i + 1) % (self.page_count // 10 or 1) == 0 or i == self.page_count - 1:
                 console.print(f"Generated {i+1}/{self.page_count} pages")
        self._create_index_page()
        console.print(f"[bold green]Successfully generated {self.page_count} test pages in [cyan]{self.site_path}[/cyan][/bold green]")

    def _create_index_page(self) -> None:
        index_content = """<!doctype html><html><head><title>Test Site Index</title><meta charset="utf-8"></head><body><h1>Test Site Index</h1><p>This is an automatically generated site for testing Crawl4AI.</p><div class="page-links">\n"""
        for i in range(self.page_count):
            index_content += f'        <a href="page_{i}.html">Test Page {i}</a><br>\n'
        index_content += """    </div></body></html>"""
        (self.site_path / "index.html").write_text(index_content, encoding="utf-8")

# --- LocalHttpServer Class (Unchanged) ---
class LocalHttpServer:
    """Manages a local HTTP server for serving test pages."""
    def __init__(self, site_path: str = DEFAULT_SITE_PATH, port: int = DEFAULT_PORT):
        self.site_path = pathlib.Path(site_path)
        self.port = port
        self.process = None

    def start(self) -> None:
        if not self.site_path.exists(): raise FileNotFoundError(f"Site directory {self.site_path} does not exist")
        console.print(f"Attempting to start HTTP server in [cyan]{self.site_path}[/cyan] on port {self.port}...")
        try:
            cmd = ["python", "-m", "http.server", str(self.port)]
            creationflags = 0; preexec_fn = None
            if sys.platform == 'win32': creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            self.process = subprocess.Popen(cmd, cwd=str(self.site_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
            time.sleep(1.5)
            if self.is_running(): console.print(f"[bold green]HTTP server started successfully (PID: {self.process.pid})[/bold green]")
            else:
                console.print("[bold red]Failed to start HTTP server. Checking logs...[/bold red]")
                stdout, stderr = self.process.communicate(); print(stdout.decode(errors='ignore')); print(stderr.decode(errors='ignore'))
                self.stop(); raise RuntimeError("HTTP server failed to start.")
        except Exception as e: console.print(f"[bold red]Error starting HTTP server: {str(e)}[/bold red]"); self.stop(); raise

    def stop(self) -> None:
        if self.process and self.is_running():
            console.print(f"Stopping HTTP server (PID: {self.process.pid})...")
            try:
                if sys.platform == 'win32': self.process.send_signal(signal.CTRL_BREAK_EVENT); time.sleep(0.5)
                self.process.terminate()
                try: stdout, stderr = self.process.communicate(timeout=5); console.print("[bold yellow]HTTP server stopped[/bold yellow]")
                except subprocess.TimeoutExpired: console.print("[bold red]Server did not terminate gracefully, killing...[/bold red]"); self.process.kill(); stdout, stderr = self.process.communicate(); console.print("[bold yellow]HTTP server killed[/bold yellow]")
            except Exception as e: console.print(f"[bold red]Error stopping HTTP server: {str(e)}[/bold red]"); self.process.kill()
            finally: self.process = None
        elif self.process: console.print("[dim]HTTP server process already stopped.[/dim]"); self.process = None

    def is_running(self) -> bool:
        if not self.process: return False
        return self.process.poll() is None

# --- SimpleMemoryTracker Class (Unchanged) ---
class SimpleMemoryTracker:
    """Basic memory tracker that doesn't rely on psutil."""
    def __init__(self, report_path: str = DEFAULT_REPORT_PATH, test_id: Optional[str] = None):
        self.report_path = pathlib.Path(report_path); self.report_path.mkdir(parents=True, exist_ok=True)
        self.test_id = test_id or time.strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time(); self.memory_samples = []; self.pid = os.getpid()
        self.csv_path = self.report_path / f"memory_samples_{self.test_id}.csv"
        with open(self.csv_path, 'w', encoding='utf-8') as f: f.write("timestamp,elapsed_seconds,memory_info_mb\n")

    def sample(self) -> Dict:
        try:
            memory_mb = self._get_memory_info_mb()
            memory_str = f"{memory_mb:.1f} MB" if memory_mb is not None else "Unknown"
            timestamp = time.time(); elapsed = timestamp - self.start_time
            sample = {"timestamp": timestamp, "elapsed_seconds": elapsed, "memory_mb": memory_mb, "memory_str": memory_str}
            self.memory_samples.append(sample)
            with open(self.csv_path, 'a', encoding='utf-8') as f: f.write(f"{timestamp},{elapsed:.2f},{memory_mb if memory_mb is not None else ''}\n")
            return sample
        except Exception as e: return {"memory_mb": None, "memory_str": "Error"}

    def _get_memory_info_mb(self) -> Optional[float]:
        pid_str = str(self.pid)
        try:
            if sys.platform == 'darwin': result = subprocess.run(["ps", "-o", "rss=", "-p", pid_str], capture_output=True, text=True, check=True, encoding='utf-8'); return int(result.stdout.strip()) / 1024.0
            elif sys.platform == 'linux':
                with open(f"/proc/{pid_str}/status", encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("VmRSS:"): return int(line.split()[1]) / 1024.0
                return None
            elif sys.platform == 'win32': result = subprocess.run(["tasklist", "/fi", f"PID eq {pid_str}", "/fo", "csv", "/nh"], capture_output=True, text=True, check=True, encoding='cp850', errors='ignore'); parts = result.stdout.strip().split('","'); return int(parts[4].strip().replace('"', '').replace(' K', '').replace(',', '')) / 1024.0 if len(parts) >= 5 else None
            else: return None
        except: return None # Catch all exceptions for robustness

    def get_report(self) -> Dict:
        if not self.memory_samples: return {"error": "No memory samples collected"}
        total_time = time.time() - self.start_time; valid_samples = [s['memory_mb'] for s in self.memory_samples if s['memory_mb'] is not None]
        start_mem = valid_samples[0] if valid_samples else None; end_mem = valid_samples[-1] if valid_samples else None
        max_mem = max(valid_samples) if valid_samples else None; avg_mem = sum(valid_samples) / len(valid_samples) if valid_samples else None
        growth = (end_mem - start_mem) if start_mem is not None and end_mem is not None else None
        return {"test_id": self.test_id, "total_time_seconds": total_time, "sample_count": len(self.memory_samples), "valid_sample_count": len(valid_samples), "csv_path": str(self.csv_path), "platform": sys.platform, "start_memory_mb": start_mem, "end_memory_mb": end_mem, "max_memory_mb": max_mem, "average_memory_mb": avg_mem, "memory_growth_mb": growth}


# --- CrawlerStressTest Class (Refactored for Per-Batch Logging) ---
class CrawlerStressTest:
    """Orchestrates the stress test using arun_many per chunk and a dispatcher."""

    def __init__(
        self,
        url_count: int = DEFAULT_URL_COUNT,
        port: int = DEFAULT_PORT,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        chunk_size: int = DEFAULT_CHUNK_SIZE, # Added chunk_size
        report_path: str = DEFAULT_REPORT_PATH,
        stream_mode: bool = DEFAULT_STREAM_MODE,
        monitor_mode: str = DEFAULT_MONITOR_MODE,
        use_rate_limiter: bool = False
    ):
        self.url_count = url_count
        self.server_port = port
        self.max_sessions = max_sessions
        self.chunk_size = chunk_size # Store chunk size
        self.report_path = pathlib.Path(report_path)
        self.report_path.mkdir(parents=True, exist_ok=True)
        self.stream_mode = stream_mode
        self.monitor_mode = DisplayMode[monitor_mode.upper()]
        self.use_rate_limiter = use_rate_limiter

        self.test_id = time.strftime("%Y%m%d_%H%M%S")
        self.results_summary = {
            "test_id": self.test_id, "url_count": url_count, "max_sessions": max_sessions,
            "chunk_size": chunk_size, "stream_mode": stream_mode, "monitor_mode": monitor_mode,
            "rate_limiter_used": use_rate_limiter, "start_time": "", "end_time": "",
            "total_time_seconds": 0, "successful_urls": 0, "failed_urls": 0,
            "urls_processed": 0, "chunks_processed": 0
        }

    async def run(self) -> Dict:
        """Run the stress test and return results."""
        memory_tracker = SimpleMemoryTracker(report_path=self.report_path, test_id=self.test_id)
        urls = [f"http://localhost:{self.server_port}/page_{i}.html" for i in range(self.url_count)]
        # Split URLs into chunks based on self.chunk_size
        url_chunks = [urls[i:i+self.chunk_size] for i in range(0, len(urls), self.chunk_size)]

        self.results_summary["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        start_time = time.time()

        config = CrawlerRunConfig(
            wait_for_images=False, verbose=False,
            stream=self.stream_mode, # Still pass stream mode, affects arun_many return type
            cache_mode=CacheMode.BYPASS
        )

        total_successful_urls = 0
        total_failed_urls = 0
        total_urls_processed = 0
        start_memory_sample = memory_tracker.sample()
        start_memory_str = start_memory_sample.get("memory_str", "Unknown")

        # monitor = CrawlerMonitor(display_mode=self.monitor_mode, total_urls=self.url_count)
        monitor = None
        rate_limiter = RateLimiter(base_delay=(0.1, 0.3)) if self.use_rate_limiter else None
        dispatcher = MemoryAdaptiveDispatcher(max_session_permit=self.max_sessions, monitor=monitor, rate_limiter=rate_limiter)

        console.print(f"\n[bold cyan]Crawl4AI Stress Test - {self.url_count} URLs, {self.max_sessions} max sessions[/bold cyan]")
        console.print(f"[bold cyan]Mode:[/bold cyan] {'Streaming' if self.stream_mode else 'Batch'}, [bold cyan]Monitor:[/bold cyan] {self.monitor_mode.name}, [bold cyan]Chunk Size:[/bold cyan] {self.chunk_size}")
        console.print(f"[bold cyan]Initial Memory:[/bold cyan] {start_memory_str}")

        # Print batch log header only if not streaming
        if not self.stream_mode:
            console.print("\n[bold]Batch Progress:[/bold] (Monitor below shows overall progress)")
            console.print("[bold] Batch | Progress | Start Mem | End Mem   | URLs/sec | Success/Fail | Time (s) | Status [/bold]")
            console.print("─" * 90)

        monitor_task = asyncio.create_task(self._periodic_memory_sample(memory_tracker, 2.0))

        try:
            async with AsyncWebCrawler(
                    config=BrowserConfig( verbose = False)
                ) as crawler:
                # Process URLs chunk by chunk
                for chunk_idx, url_chunk in enumerate(url_chunks):
                    batch_start_time = time.time()
                    chunk_success = 0
                    chunk_failed = 0

                    # Sample memory before the chunk
                    start_mem_sample = memory_tracker.sample()
                    start_mem_str = start_mem_sample.get("memory_str", "Unknown")

                    # --- Call arun_many for the current chunk ---
                    try:
                        # Note: dispatcher/monitor persist across calls
                        results_gen_or_list: Union[AsyncGenerator[CrawlResult, None], List[CrawlResult]] = \
                            await crawler.arun_many(
                                urls=url_chunk,
                                config=config,
                                dispatcher=dispatcher # Reuse the same dispatcher
                            )

                        if self.stream_mode:
                            # Process stream results if needed, but batch logging is less relevant
                            async for result in results_gen_or_list:
                                total_urls_processed += 1
                                if result.success: chunk_success += 1
                                else: chunk_failed += 1
                            # In stream mode, batch summary isn't as meaningful here
                            # We could potentially track completion per chunk async, but it's complex

                        else: # Batch mode
                            # Process the list of results for this chunk
                            for result in results_gen_or_list:
                                total_urls_processed += 1
                                if result.success: chunk_success += 1
                                else: chunk_failed += 1

                    except Exception as e:
                        console.print(f"[bold red]Error processing chunk {chunk_idx+1}: {e}[/bold red]")
                        chunk_failed = len(url_chunk) # Assume all failed in the chunk on error
                        total_urls_processed += len(url_chunk) # Count them as processed (failed)

                    # --- Log batch results (only if not streaming) ---
                    if not self.stream_mode:
                        batch_time = time.time() - batch_start_time
                        urls_per_sec = len(url_chunk) / batch_time if batch_time > 0 else 0
                        end_mem_sample = memory_tracker.sample()
                        end_mem_str = end_mem_sample.get("memory_str", "Unknown")

                        progress_pct = (total_urls_processed / self.url_count) * 100

                        if chunk_failed == 0: status_color, status = "green", "Success"
                        elif chunk_success == 0: status_color, status = "red", "Failed"
                        else: status_color, status = "yellow", "Partial"

                        console.print(
                             f" {chunk_idx+1:<5} | {progress_pct:6.1f}% | {start_mem_str:>9} | {end_mem_str:>9} | {urls_per_sec:8.1f} | "
                            f"{chunk_success:^7}/{chunk_failed:<6} | {batch_time:8.2f} | [{status_color}]{status:<7}[/{status_color}]"
                        )

                    # Accumulate totals
                    total_successful_urls += chunk_success
                    total_failed_urls += chunk_failed
                    self.results_summary["chunks_processed"] += 1

                    # Optional small delay between starting chunks if needed
                    # await asyncio.sleep(0.1)

        except Exception as e:
             console.print(f"[bold red]An error occurred during the main crawl loop: {e}[/bold red]")
        finally:
            if 'monitor_task' in locals() and not monitor_task.done():
                 monitor_task.cancel()
                 try: await monitor_task
                 except asyncio.CancelledError: pass

        end_time = time.time()
        self.results_summary.update({
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time_seconds": end_time - start_time,
            "successful_urls": total_successful_urls,
            "failed_urls": total_failed_urls,
            "urls_processed": total_urls_processed,
            "memory": memory_tracker.get_report()
        })
        self._save_results()
        return self.results_summary

    async def _periodic_memory_sample(self, tracker: SimpleMemoryTracker, interval: float):
        """Background task to sample memory periodically."""
        while True:
            tracker.sample()
            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break # Exit loop on cancellation

    def _save_results(self) -> None:
        results_path = self.report_path / f"test_summary_{self.test_id}.json"
        try:
            with open(results_path, 'w', encoding='utf-8') as f: json.dump(self.results_summary, f, indent=2, default=str)
            # console.print(f"\n[bold green]Results summary saved to {results_path}[/bold green]") # Moved summary print to run_full_test
        except Exception as e: console.print(f"[bold red]Failed to save results summary: {e}[/bold red]")


# --- run_full_test Function (Adjusted) ---
async def run_full_test(args):
    """Run the complete test process from site generation to crawling."""
    server = None
    site_generated = False

    # --- Site Generation --- (Same as before)
    if not args.use_existing_site and not args.skip_generation:
        if os.path.exists(args.site_path): console.print(f"[yellow]Removing existing site directory: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)
        site_generator = SiteGenerator(site_path=args.site_path, page_count=args.urls); site_generator.generate_site(); site_generated = True
    elif args.use_existing_site: console.print(f"[cyan]Using existing site assumed to be running on port {args.port}[/cyan]")
    elif args.skip_generation:
         console.print(f"[cyan]Skipping site generation, using existing directory: {args.site_path}[/cyan]")
         if not os.path.exists(args.site_path) or not os.path.isdir(args.site_path): console.print(f"[bold red]Error: Site path '{args.site_path}' does not exist or is not a directory.[/bold red]"); return

    # --- Start Local Server --- (Same as before)
    server_started = False
    if not args.use_existing_site:
        server = LocalHttpServer(site_path=args.site_path, port=args.port)
        try: server.start(); server_started = True
        except Exception as e:
            console.print(f"[bold red]Failed to start local server. Aborting test.[/bold red]")
            if site_generated and not args.keep_site: console.print(f"[yellow]Cleaning up generated site: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)
            return

    try:
        # --- Run the Stress Test ---
        test = CrawlerStressTest(
            url_count=args.urls,
            port=args.port,
            max_sessions=args.max_sessions,
            chunk_size=args.chunk_size, # Pass chunk_size
            report_path=args.report_path,
            stream_mode=args.stream,
            monitor_mode=args.monitor_mode,
            use_rate_limiter=args.use_rate_limiter
        )
        results = await test.run() # Run the test which now handles chunks internally

        # --- Print Summary ---
        console.print("\n" + "=" * 80)
        console.print("[bold green]Test Completed[/bold green]")
        console.print("=" * 80)

        # (Summary printing logic remains largely the same)
        success_rate = results["successful_urls"] / results["url_count"] * 100 if results["url_count"] > 0 else 0
        urls_per_second = results["urls_processed"] / results["total_time_seconds"] if results["total_time_seconds"] > 0 else 0

        console.print(f"[bold cyan]Test ID:[/bold cyan] {results['test_id']}")
        console.print(f"[bold cyan]Configuration:[/bold cyan] {results['url_count']} URLs, {results['max_sessions']} sessions, Chunk: {results['chunk_size']}, Stream: {results['stream_mode']}, Monitor: {results['monitor_mode']}")
        console.print(f"[bold cyan]Results:[/bold cyan] {results['successful_urls']} successful, {results['failed_urls']} failed ({results['urls_processed']} processed, {success_rate:.1f}% success)")
        console.print(f"[bold cyan]Performance:[/bold cyan] {results['total_time_seconds']:.2f} seconds total, {urls_per_second:.2f} URLs/second avg")

        mem_report = results.get("memory", {})
        mem_info_str = "Memory tracking data unavailable."
        if mem_report and not mem_report.get("error"):
            start_mb = mem_report.get('start_memory_mb'); end_mb = mem_report.get('end_memory_mb'); max_mb = mem_report.get('max_memory_mb'); growth_mb = mem_report.get('memory_growth_mb')
            mem_parts = []
            if start_mb is not None: mem_parts.append(f"Start: {start_mb:.1f} MB")
            if end_mb is not None: mem_parts.append(f"End: {end_mb:.1f} MB")
            if max_mb is not None: mem_parts.append(f"Max: {max_mb:.1f} MB")
            if growth_mb is not None: mem_parts.append(f"Growth: {growth_mb:.1f} MB")
            if mem_parts: mem_info_str = ", ".join(mem_parts)
            csv_path = mem_report.get('csv_path')
            if csv_path: console.print(f"[dim]Memory samples saved to: {csv_path}[/dim]")

        console.print(f"[bold cyan]Memory Usage:[/bold cyan] {mem_info_str}")
        console.print(f"[bold green]Results summary saved to {results['memory']['csv_path'].replace('memory_samples', 'test_summary').replace('.csv', '.json')}[/bold green]") # Infer summary path


        if results["failed_urls"] > 0: console.print(f"\n[bold yellow]Warning: {results['failed_urls']} URLs failed to process ({100-success_rate:.1f}% failure rate)[/bold yellow]")
        if results["urls_processed"] < results["url_count"]: console.print(f"\n[bold red]Error: Only {results['urls_processed']} out of {results['url_count']} URLs were processed![/bold red]")


    finally:
        # --- Stop Server / Cleanup --- (Same as before)
        if server_started and server and not args.keep_server_alive: server.stop()
        elif server_started and server and args.keep_server_alive:
            console.print(f"[bold cyan]Server is kept running on port {args.port}. Press Ctrl+C to stop it.[/bold cyan]")
            try: await asyncio.Future() # Keep running indefinitely
            except KeyboardInterrupt: console.print("\n[bold yellow]Stopping server due to user interrupt...[/bold yellow]"); server.stop()

        if site_generated and not args.keep_site: console.print(f"[yellow]Cleaning up generated site: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)
        elif args.clean_site and os.path.exists(args.site_path): console.print(f"[yellow]Cleaning up site directory as requested: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)


# --- main Function (Added chunk_size argument) ---
def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Crawl4AI SDK High Volume Stress Test using arun_many")

    # Test parameters
    parser.add_argument("--urls", type=int, default=DEFAULT_URL_COUNT, help=f"Number of URLs to test (default: {DEFAULT_URL_COUNT})")
    parser.add_argument("--max-sessions", type=int, default=DEFAULT_MAX_SESSIONS, help=f"Maximum concurrent crawling sessions (default: {DEFAULT_MAX_SESSIONS})")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help=f"Number of URLs per batch for logging (default: {DEFAULT_CHUNK_SIZE})") # Added
    parser.add_argument("--stream", action="store_true", default=DEFAULT_STREAM_MODE, help=f"Enable streaming mode (disables batch logging) (default: {DEFAULT_STREAM_MODE})")
    parser.add_argument("--monitor-mode", type=str, default=DEFAULT_MONITOR_MODE, choices=["DETAILED", "AGGREGATED"], help=f"Display mode for the live monitor (default: {DEFAULT_MONITOR_MODE})")
    parser.add_argument("--use-rate-limiter", action="store_true", default=False, help="Enable a basic rate limiter (default: False)")

    # Environment parameters
    parser.add_argument("--site-path", type=str, default=DEFAULT_SITE_PATH, help=f"Path to generate/use the test site (default: {DEFAULT_SITE_PATH})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port for the local HTTP server (default: {DEFAULT_PORT})")
    parser.add_argument("--report-path", type=str, default=DEFAULT_REPORT_PATH, help=f"Path to save reports and logs (default: {DEFAULT_REPORT_PATH})")

    # Site/Server management
    parser.add_argument("--skip-generation", action="store_true", help="Use existing test site folder without regenerating")
    parser.add_argument("--use-existing-site", action="store_true", help="Do not generate site or start local server; assume site exists on --port")
    parser.add_argument("--keep-server-alive", action="store_true", help="Keep the local HTTP server running after test")
    parser.add_argument("--keep-site", action="store_true", help="Keep the generated test site files after test")
    parser.add_argument("--clean-reports", action="store_true", help="Clean up report directory before running")
    parser.add_argument("--clean-site", action="store_true", help="Clean up site directory before running (if generating) or after")

    args = parser.parse_args()

    # Display config
    console.print("[bold underline]Crawl4AI SDK Stress Test Configuration[/bold underline]")
    console.print(f"URLs: {args.urls}, Max Sessions: {args.max_sessions}, Chunk Size: {args.chunk_size}") # Added chunk size
    console.print(f"Mode: {'Streaming' if args.stream else 'Batch'}, Monitor: {args.monitor_mode}, Rate Limit: {args.use_rate_limiter}")
    console.print(f"Site Path: {args.site_path}, Port: {args.port}, Report Path: {args.report_path}")
    console.print("-" * 40)
    # (Rest of config display and cleanup logic is the same)
    if args.use_existing_site: console.print("[cyan]Mode: Using existing external site/server[/cyan]")
    elif args.skip_generation: console.print("[cyan]Mode: Using existing site files, starting local server[/cyan]")
    else: console.print("[cyan]Mode: Generating site files, starting local server[/cyan]")
    if args.keep_server_alive: console.print("[cyan]Option: Keep server alive after test[/cyan]")
    if args.keep_site: console.print("[cyan]Option: Keep site files after test[/cyan]")
    if args.clean_reports: console.print("[cyan]Option: Clean reports before test[/cyan]")
    if args.clean_site: console.print("[cyan]Option: Clean site directory[/cyan]")
    console.print("-" * 40)

    if args.clean_reports:
        if os.path.exists(args.report_path): console.print(f"[yellow]Cleaning up reports directory: {args.report_path}[/yellow]"); shutil.rmtree(args.report_path)
        os.makedirs(args.report_path, exist_ok=True)
    if args.clean_site and not args.use_existing_site:
         if os.path.exists(args.site_path): console.print(f"[yellow]Cleaning up site directory as requested: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)

    # Run
    try: asyncio.run(run_full_test(args))
    except KeyboardInterrupt: console.print("\n[bold yellow]Test interrupted by user.[/bold yellow]")
    except Exception as e: console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {e}"); import traceback; traceback.print_exc()

if __name__ == "__main__":
    main()