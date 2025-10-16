"""
Interactive Monitoring Dashboard Demo

This demo showcases the monitoring and profiling capabilities of Crawl4AI's Docker server.
It provides:
- Real-time statistics dashboard with auto-refresh
- Profiling session management
- System resource monitoring
- URL-specific statistics
- Interactive terminal UI

Usage:
    python demo_monitoring_dashboard.py [--url BASE_URL]
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import httpx


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class MonitoringDashboard:
    """Interactive monitoring dashboard for Crawl4AI."""

    def __init__(self, base_url: str = "http://localhost:11234"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=60.0)
        self.running = True
        self.current_view = "dashboard"  # dashboard, sessions, urls
        self.profiling_sessions: List[Dict] = []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def clear_screen(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="")

    def print_header(self, title: str):
        """Print a formatted header."""
        width = 80
        print(f"\n{Colors.HEADER}{Colors.BOLD}")
        print("=" * width)
        print(f"{title.center(width)}")
        print("=" * width)
        print(f"{Colors.ENDC}")

    def print_section(self, title: str):
        """Print a section header."""
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}▶ {title}{Colors.ENDC}")
        print("-" * 80)

    async def check_health(self) -> Dict:
        """Check server health."""
        try:
            response = await self.client.get("/monitoring/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_stats(self) -> Dict:
        """Get current statistics."""
        try:
            response = await self.client.get("/monitoring/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def get_url_stats(self) -> List[Dict]:
        """Get URL-specific statistics."""
        try:
            response = await self.client.get("/monitoring/stats/urls")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []

    async def list_profiling_sessions(self) -> List[Dict]:
        """List all profiling sessions."""
        try:
            response = await self.client.get("/monitoring/profile")
            response.raise_for_status()
            data = response.json()
            return data.get("sessions", [])
        except Exception as e:
            return []

    async def start_profiling_session(self, urls: List[str], duration: int = 30) -> Dict:
        """Start a new profiling session."""
        try:
            request_data = {
                "urls": urls,
                "duration_seconds": duration,
                "crawler_config": {
                    "word_count_threshold": 10
                }
            }
            response = await self.client.post("/monitoring/profile/start", json=request_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def get_profiling_session(self, session_id: str) -> Dict:
        """Get profiling session details."""
        try:
            response = await self.client.get(f"/monitoring/profile/{session_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def delete_profiling_session(self, session_id: str) -> Dict:
        """Delete a profiling session."""
        try:
            response = await self.client.delete(f"/monitoring/profile/{session_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def reset_stats(self) -> Dict:
        """Reset all statistics."""
        try:
            response = await self.client.post("/monitoring/stats/reset")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def display_dashboard(self, stats: Dict):
        """Display the main statistics dashboard."""
        self.clear_screen()
        self.print_header("Crawl4AI Monitoring Dashboard")

        # Health Status
        print(f"\n{Colors.OKGREEN}● Server Status: ONLINE{Colors.ENDC}")
        print(f"Base URL: {self.base_url}")
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Crawler Statistics
        self.print_section("Crawler Statistics")
        if "error" in stats:
            print(f"{Colors.FAIL}Error fetching stats: {stats['error']}{Colors.ENDC}")
        else:
            print(f"Active Crawls:      {Colors.BOLD}{stats.get('active_crawls', 0)}{Colors.ENDC}")
            print(f"Total Crawls:       {stats.get('total_crawls', 0)}")
            print(f"Successful:         {Colors.OKGREEN}{stats.get('successful_crawls', 0)}{Colors.ENDC}")
            print(f"Failed:             {Colors.FAIL}{stats.get('failed_crawls', 0)}{Colors.ENDC}")
            print(f"Success Rate:       {stats.get('success_rate', 0):.2f}%")
            print(f"Avg Duration:       {stats.get('avg_duration_ms', 0):.2f} ms")
            
            # Format bytes
            total_bytes = stats.get('total_bytes_processed', 0)
            if total_bytes > 1024 * 1024:
                bytes_str = f"{total_bytes / (1024 * 1024):.2f} MB"
            elif total_bytes > 1024:
                bytes_str = f"{total_bytes / 1024:.2f} KB"
            else:
                bytes_str = f"{total_bytes} bytes"
            print(f"Total Data Processed: {bytes_str}")

        # System Statistics
        if "system_stats" in stats:
            self.print_section("System Resources")
            sys_stats = stats["system_stats"]
            
            cpu = sys_stats.get("cpu_percent", 0)
            cpu_color = Colors.OKGREEN if cpu < 50 else Colors.WARNING if cpu < 80 else Colors.FAIL
            print(f"CPU Usage:          {cpu_color}{cpu:.1f}%{Colors.ENDC}")
            
            mem = sys_stats.get("memory_percent", 0)
            mem_color = Colors.OKGREEN if mem < 50 else Colors.WARNING if mem < 80 else Colors.FAIL
            print(f"Memory Usage:       {mem_color}{mem:.1f}%{Colors.ENDC}")
            
            mem_used = sys_stats.get("memory_used_mb", 0)
            mem_available = sys_stats.get("memory_available_mb", 0)
            print(f"Memory Used:        {mem_used:.0f} MB / {mem_available:.0f} MB")
            
            disk = sys_stats.get("disk_usage_percent", 0)
            disk_color = Colors.OKGREEN if disk < 70 else Colors.WARNING if disk < 90 else Colors.FAIL
            print(f"Disk Usage:         {disk_color}{disk:.1f}%{Colors.ENDC}")
            
            print(f"Active Processes:   {sys_stats.get('active_processes', 0)}")

        # Navigation
        self.print_section("Navigation")
        print(f"[D] Dashboard  [S] Profiling Sessions  [U] URL Stats  [R] Reset Stats  [Q] Quit")

    def display_url_stats(self, url_stats: List[Dict]):
        """Display URL-specific statistics."""
        self.clear_screen()
        self.print_header("URL Statistics")

        if not url_stats:
            print(f"\n{Colors.WARNING}No URL statistics available yet.{Colors.ENDC}")
        else:
            print(f"\nTotal URLs tracked: {len(url_stats)}")
            print()
            
            # Table header
            print(f"{Colors.BOLD}{'URL':<50} {'Requests':<10} {'Success':<10} {'Avg Time':<12} {'Data':<12}{Colors.ENDC}")
            print("-" * 94)
            
            # Sort by total requests
            sorted_stats = sorted(url_stats, key=lambda x: x.get('total_requests', 0), reverse=True)
            
            for stat in sorted_stats[:20]:  # Show top 20
                url = stat.get('url', 'unknown')
                if len(url) > 47:
                    url = url[:44] + "..."
                
                total = stat.get('total_requests', 0)
                success = stat.get('successful_requests', 0)
                success_pct = f"{(success/total*100):.0f}%" if total > 0 else "N/A"
                
                avg_time = stat.get('avg_duration_ms', 0)
                time_str = f"{avg_time:.0f} ms"
                
                bytes_processed = stat.get('total_bytes_processed', 0)
                if bytes_processed > 1024 * 1024:
                    data_str = f"{bytes_processed / (1024 * 1024):.2f} MB"
                elif bytes_processed > 1024:
                    data_str = f"{bytes_processed / 1024:.2f} KB"
                else:
                    data_str = f"{bytes_processed} B"
                
                print(f"{url:<50} {total:<10} {success_pct:<10} {time_str:<12} {data_str:<12}")

        # Navigation
        self.print_section("Navigation")
        print(f"[D] Dashboard  [S] Profiling Sessions  [U] URL Stats  [R] Reset Stats  [Q] Quit")

    def display_profiling_sessions(self, sessions: List[Dict]):
        """Display profiling sessions."""
        self.clear_screen()
        self.print_header("Profiling Sessions")

        if not sessions:
            print(f"\n{Colors.WARNING}No profiling sessions found.{Colors.ENDC}")
        else:
            print(f"\nTotal sessions: {len(sessions)}")
            print()
            
            # Table header
            print(f"{Colors.BOLD}{'ID':<25} {'Status':<12} {'URLs':<6} {'Duration':<12} {'Started':<20}{Colors.ENDC}")
            print("-" * 85)
            
            # Sort by started time (newest first)
            sorted_sessions = sorted(sessions, key=lambda x: x.get('started_at', ''), reverse=True)
            
            for session in sorted_sessions[:15]:  # Show top 15
                session_id = session.get('session_id', 'unknown')
                if len(session_id) > 22:
                    session_id = session_id[:19] + "..."
                
                status = session.get('status', 'unknown')
                status_color = Colors.OKGREEN if status == 'completed' else Colors.WARNING if status == 'running' else Colors.FAIL
                
                url_count = len(session.get('urls', []))
                
                duration = session.get('duration_seconds', 0)
                duration_str = f"{duration}s" if duration else "N/A"
                
                started = session.get('started_at', 'N/A')
                if started != 'N/A':
                    try:
                        dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                        started = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                print(f"{session_id:<25} {status_color}{status:<12}{Colors.ENDC} {url_count:<6} {duration_str:<12} {started:<20}")

        # Navigation
        self.print_section("Navigation & Actions")
        print(f"[D] Dashboard  [S] Profiling Sessions  [U] URL Stats")
        print(f"[N] New Session  [V] View Session  [X] Delete Session")
        print(f"[R] Reset Stats  [Q] Quit")

    async def interactive_session_view(self, session_id: str):
        """Display detailed view of a profiling session."""
        session = await self.get_profiling_session(session_id)
        
        self.clear_screen()
        self.print_header(f"Profiling Session: {session_id}")
        
        if "error" in session:
            print(f"\n{Colors.FAIL}Error: {session['error']}{Colors.ENDC}")
        else:
            print(f"\n{Colors.BOLD}Session ID:{Colors.ENDC} {session.get('session_id', 'N/A')}")
            
            status = session.get('status', 'unknown')
            status_color = Colors.OKGREEN if status == 'completed' else Colors.WARNING
            print(f"{Colors.BOLD}Status:{Colors.ENDC} {status_color}{status}{Colors.ENDC}")
            
            print(f"{Colors.BOLD}URLs:{Colors.ENDC}")
            for url in session.get('urls', []):
                print(f"  - {url}")
            
            started = session.get('started_at', 'N/A')
            print(f"{Colors.BOLD}Started:{Colors.ENDC} {started}")
            
            if 'completed_at' in session:
                print(f"{Colors.BOLD}Completed:{Colors.ENDC} {session['completed_at']}")
            
            if 'results' in session:
                self.print_section("Profiling Results")
                results = session['results']
                
                print(f"Total Requests:     {results.get('total_requests', 0)}")
                print(f"Successful:         {Colors.OKGREEN}{results.get('successful_requests', 0)}{Colors.ENDC}")
                print(f"Failed:             {Colors.FAIL}{results.get('failed_requests', 0)}{Colors.ENDC}")
                print(f"Avg Response Time:  {results.get('avg_response_time_ms', 0):.2f} ms")
                
                if 'system_metrics' in results:
                    self.print_section("System Metrics During Profiling")
                    metrics = results['system_metrics']
                    print(f"Avg CPU:            {metrics.get('avg_cpu_percent', 0):.1f}%")
                    print(f"Peak CPU:           {metrics.get('peak_cpu_percent', 0):.1f}%")
                    print(f"Avg Memory:         {metrics.get('avg_memory_percent', 0):.1f}%")
                    print(f"Peak Memory:        {metrics.get('peak_memory_percent', 0):.1f}%")
        
        print(f"\n{Colors.OKCYAN}Press any key to return...{Colors.ENDC}")
        input()

    async def create_new_session(self):
        """Interactive session creation."""
        self.clear_screen()
        self.print_header("Create New Profiling Session")
        
        print(f"\n{Colors.BOLD}Enter URLs to profile (one per line, empty line to finish):{Colors.ENDC}")
        urls = []
        while True:
            url = input(f"{Colors.OKCYAN}URL {len(urls) + 1}:{Colors.ENDC} ").strip()
            if not url:
                break
            urls.append(url)
        
        if not urls:
            print(f"{Colors.FAIL}No URLs provided. Cancelled.{Colors.ENDC}")
            time.sleep(2)
            return
        
        duration = input(f"{Colors.OKCYAN}Duration (seconds, default 30):{Colors.ENDC} ").strip()
        try:
            duration = int(duration) if duration else 30
        except:
            duration = 30
        
        print(f"\n{Colors.WARNING}Starting profiling session for {len(urls)} URL(s), {duration}s...{Colors.ENDC}")
        result = await self.start_profiling_session(urls, duration)
        
        if "error" in result:
            print(f"{Colors.FAIL}Error: {result['error']}{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}✓ Session started successfully!{Colors.ENDC}")
            print(f"Session ID: {result.get('session_id', 'N/A')}")
        
        time.sleep(3)

    async def run_dashboard(self):
        """Run the interactive dashboard."""
        print(f"{Colors.OKGREEN}Starting Crawl4AI Monitoring Dashboard...{Colors.ENDC}")
        print(f"Connecting to {self.base_url}...")
        
        # Check health
        health = await self.check_health()
        if health.get("status") != "healthy":
            print(f"{Colors.FAIL}Error: Server not responding or unhealthy{Colors.ENDC}")
            print(f"Health check result: {health}")
            return
        
        print(f"{Colors.OKGREEN}✓ Connected successfully!{Colors.ENDC}")
        time.sleep(1)
        
        # Main loop
        while self.running:
            if self.current_view == "dashboard":
                stats = await self.get_stats()
                self.display_dashboard(stats)
            elif self.current_view == "urls":
                url_stats = await self.get_url_stats()
                self.display_url_stats(url_stats)
            elif self.current_view == "sessions":
                sessions = await self.list_profiling_sessions()
                self.display_profiling_sessions(sessions)
            
            # Get user input (non-blocking with timeout)
            print(f"\n{Colors.OKCYAN}Enter command (or wait 5s for auto-refresh):{Colors.ENDC} ", end="", flush=True)
            
            try:
                # Simple input with timeout simulation
                import select
                if sys.platform != 'win32':
                    i, _, _ = select.select([sys.stdin], [], [], 5.0)
                    if i:
                        command = sys.stdin.readline().strip().lower()
                    else:
                        command = ""
                else:
                    # Windows doesn't support select on stdin
                    command = input()
            except:
                command = ""
            
            # Process command
            if command == 'q':
                self.running = False
            elif command == 'd':
                self.current_view = "dashboard"
            elif command == 's':
                self.current_view = "sessions"
            elif command == 'u':
                self.current_view = "urls"
            elif command == 'r':
                print(f"\n{Colors.WARNING}Resetting statistics...{Colors.ENDC}")
                await self.reset_stats()
                time.sleep(1)
            elif command == 'n' and self.current_view == "sessions":
                await self.create_new_session()
            elif command == 'v' and self.current_view == "sessions":
                session_id = input(f"{Colors.OKCYAN}Enter session ID:{Colors.ENDC} ").strip()
                if session_id:
                    await self.interactive_session_view(session_id)
            elif command == 'x' and self.current_view == "sessions":
                session_id = input(f"{Colors.OKCYAN}Enter session ID to delete:{Colors.ENDC} ").strip()
                if session_id:
                    result = await self.delete_profiling_session(session_id)
                    if "error" in result:
                        print(f"{Colors.FAIL}Error: {result['error']}{Colors.ENDC}")
                    else:
                        print(f"{Colors.OKGREEN}✓ Session deleted{Colors.ENDC}")
                    time.sleep(2)
        
        self.clear_screen()
        print(f"\n{Colors.OKGREEN}Dashboard closed. Goodbye!{Colors.ENDC}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Crawl4AI Monitoring Dashboard")
    parser.add_argument(
        "--url",
        default="http://localhost:11234",
        help="Base URL of the Crawl4AI Docker server (default: http://localhost:11234)"
    )
    args = parser.parse_args()
    
    dashboard = MonitoringDashboard(base_url=args.url)
    try:
        await dashboard.run_dashboard()
    finally:
        await dashboard.close()


if __name__ == "__main__":
    asyncio.run(main())
