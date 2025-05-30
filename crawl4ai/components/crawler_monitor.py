import time
import uuid
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import threading
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich import box
from ..models import CrawlStatus

class TerminalUI:
    """Terminal user interface for CrawlerMonitor using rich library."""
    
    def __init__(self, refresh_rate: float = 1.0, max_width: int = 120):
        """
        Initialize the terminal UI.
        
        Args:
            refresh_rate: How often to refresh the UI (in seconds)
            max_width: Maximum width of the UI in characters
        """
        self.console = Console(width=max_width)
        self.layout = Layout()
        self.refresh_rate = refresh_rate
        self.stop_event = threading.Event()
        self.ui_thread = None
        self.monitor = None  # Will be set by CrawlerMonitor
        self.max_width = max_width
        
        # Setup layout - vertical layout (top to bottom)
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="pipeline_status", size=10),
            Layout(name="task_details", ratio=1),
            Layout(name="footer", size=3)  # Increased footer size to fit all content
        )
        
    def start(self, monitor):
        """Start the UI thread."""
        self.monitor = monitor
        self.stop_event.clear()
        self.ui_thread = threading.Thread(target=self._ui_loop)
        self.ui_thread.daemon = True
        self.ui_thread.start()
        
    def stop(self):
        """Stop the UI thread."""
        if self.ui_thread and self.ui_thread.is_alive():
            self.stop_event.set()
            # Only try to join if we're not in the UI thread
            # This prevents "cannot join current thread" errors
            if threading.current_thread() != self.ui_thread:
                self.ui_thread.join(timeout=5.0)
    
    def _ui_loop(self):
        """Main UI rendering loop."""
        import sys
        import select
        import termios
        import tty
        
        # Setup terminal for non-blocking input
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            
            # Use Live display to render the UI
            with Live(self.layout, refresh_per_second=1/self.refresh_rate, screen=True) as live:
                self.live = live  # Store the live display for updates
                
                # Main UI loop
                while not self.stop_event.is_set():
                    self._update_display()
                    
                    # Check for key press (non-blocking)
                    if select.select([sys.stdin], [], [], 0)[0]:
                        key = sys.stdin.read(1)
                        # Check for 'q' to quit
                        if key == 'q':
                            # Signal stop but don't call monitor.stop() from UI thread
                            # as it would cause the thread to try to join itself
                            self.stop_event.set()
                            self.monitor.is_running = False
                            break
                    
                    time.sleep(self.refresh_rate)
                    
                    # Just check if the monitor was stopped
                    if not self.monitor.is_running:
                        break
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    def _update_display(self):
        """Update the terminal display with current statistics."""
        if not self.monitor:
            return
            
        # Update crawler status panel
        self.layout["header"].update(self._create_status_panel())
        
        # Update pipeline status panel and task details panel
        self.layout["pipeline_status"].update(self._create_pipeline_panel())
        self.layout["task_details"].update(self._create_task_details_panel())
        
        # Update footer
        self.layout["footer"].update(self._create_footer())
    
    def _create_status_panel(self) -> Panel:
        """Create the crawler status panel."""
        summary = self.monitor.get_summary()
        
        # Format memory status with icon
        memory_status = self.monitor.get_memory_status()
        memory_icon = "🟢"  # Default NORMAL
        if memory_status == "PRESSURE":
            memory_icon = "🟠"
        elif memory_status == "CRITICAL":
            memory_icon = "🔴"
        
        # Get current memory usage
        current_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        memory_percent = (current_memory / psutil.virtual_memory().total) * 100
        
        # Format runtime
        runtime = self.monitor._format_time(time.time() - self.monitor.start_time if self.monitor.start_time else 0)
        
        # Create the status text
        status_text = Text()
        status_text.append(f"Web Crawler Dashboard | Runtime: {runtime} | Memory: {memory_percent:.1f}% {memory_icon}\n")
        status_text.append(f"Status: {memory_status} | URLs: {summary['urls_completed']}/{summary['urls_total']} | ")
        status_text.append(f"Peak Mem: {summary['peak_memory_percent']:.1f}% at {self.monitor._format_time(summary['peak_memory_time'])}")
        
        return Panel(status_text, title="Crawler Status", border_style="blue")
    
    def _create_pipeline_panel(self) -> Panel:
        """Create the pipeline status panel."""
        summary = self.monitor.get_summary()
        queue_stats = self.monitor.get_queue_stats()
        
        # Create a table for status counts
        table = Table(show_header=True, box=None)
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        table.add_column("Stat", style="cyan")
        table.add_column("Value", justify="right")
        
        # Calculate overall progress
        progress = f"{summary['urls_completed']}/{summary['urls_total']}"
        progress_percent = f"{summary['completion_percentage']:.1f}%"
        
        # Add rows for each status
        table.add_row(
            "Overall Progress", 
            progress, 
            progress_percent,
            "Est. Completion", 
            summary.get('estimated_completion_time', "N/A")
        )
        
        # Add rows for each status
        status_counts = summary['status_counts']
        total = summary['urls_total'] or 1  # Avoid division by zero
        
        # Status rows
        table.add_row(
            "Completed", 
            str(status_counts.get(CrawlStatus.COMPLETED.name, 0)),
            f"{status_counts.get(CrawlStatus.COMPLETED.name, 0) / total * 100:.1f}%",
            "Avg. Time/URL",
            f"{summary.get('avg_task_duration', 0):.2f}s"
        )
        
        table.add_row(
            "Failed", 
            str(status_counts.get(CrawlStatus.FAILED.name, 0)),
            f"{status_counts.get(CrawlStatus.FAILED.name, 0) / total * 100:.1f}%",
            "Concurrent Tasks",
            str(status_counts.get(CrawlStatus.IN_PROGRESS.name, 0))
        )
        
        table.add_row(
            "In Progress", 
            str(status_counts.get(CrawlStatus.IN_PROGRESS.name, 0)),
            f"{status_counts.get(CrawlStatus.IN_PROGRESS.name, 0) / total * 100:.1f}%",
            "Queue Size",
            str(queue_stats['total_queued'])
        )
        
        table.add_row(
            "Queued", 
            str(status_counts.get(CrawlStatus.QUEUED.name, 0)),
            f"{status_counts.get(CrawlStatus.QUEUED.name, 0) / total * 100:.1f}%",
            "Max Wait Time",
            f"{queue_stats['highest_wait_time']:.1f}s"
        )
        
        # Requeued is a special case as it's not a status
        requeued_count = summary.get('requeued_count', 0)
        table.add_row(
            "Requeued", 
            str(requeued_count),
            f"{summary.get('requeue_rate', 0):.1f}%",
            "Avg Wait Time",
            f"{queue_stats['avg_wait_time']:.1f}s"
        )
        
        # Add empty row for spacing
        table.add_row(
            "", 
            "",
            "",
            "Requeue Rate",
            f"{summary.get('requeue_rate', 0):.1f}%"
        )
        
        return Panel(table, title="Pipeline Status", border_style="green")
    
    def _create_task_details_panel(self) -> Panel:
        """Create the task details panel."""
        # Create a table for task details
        table = Table(show_header=True, expand=True)
        table.add_column("Task ID", style="cyan", no_wrap=True, width=10)
        table.add_column("URL", style="blue", ratio=3)
        table.add_column("Status", style="green", width=15)
        table.add_column("Memory", justify="right", width=8)
        table.add_column("Peak", justify="right", width=8)
        table.add_column("Duration", justify="right", width=10)
        
        # Get all task stats
        task_stats = self.monitor.get_all_task_stats()
        
        # Add summary row
        active_tasks = sum(1 for stats in task_stats.values() 
                          if stats['status'] == CrawlStatus.IN_PROGRESS.name)
        
        total_memory = sum(stats['memory_usage'] for stats in task_stats.values())
        total_peak = sum(stats['peak_memory'] for stats in task_stats.values())
        
        # Summary row with separators
        table.add_row(
            "SUMMARY", 
            f"Total: {len(task_stats)}", 
            f"Active: {active_tasks}",
            f"{total_memory:.1f}",
            f"{total_peak:.1f}",
            "N/A"
        )
        
        # Add a separator
        table.add_row("—" * 10, "—" * 20, "—" * 10, "—" * 8, "—" * 8, "—" * 10)
        
        # Status icons
        status_icons = {
            CrawlStatus.QUEUED.name: "⏳",
            CrawlStatus.IN_PROGRESS.name: "🔄",
            CrawlStatus.COMPLETED.name: "✅",
            CrawlStatus.FAILED.name: "❌"
        }
        
        # Calculate how many rows we can display based on available space
        # We can display more rows now that we have a dedicated panel
        display_count = min(len(task_stats), 20)  # Display up to 20 tasks
        
        # Add rows for each task
        for task_id, stats in sorted(
            list(task_stats.items())[:display_count],
            # Sort: 1. IN_PROGRESS first, 2. QUEUED, 3. COMPLETED/FAILED by recency
            key=lambda x: (
                0 if x[1]['status'] == CrawlStatus.IN_PROGRESS.name else 
                1 if x[1]['status'] == CrawlStatus.QUEUED.name else 
                2,
                -1 * (x[1].get('end_time', 0) or 0)  # Most recent first
            )
        ):
            # Truncate task_id and URL for display
            short_id = task_id[:8]
            url = stats['url']
            if len(url) > 50:  # Allow longer URLs in the dedicated panel
                url = url[:47] + "..."
                
            # Format status with icon
            status = f"{status_icons.get(stats['status'], '?')} {stats['status']}"
            
            # Add row
            table.add_row(
                short_id,
                url,
                status,
                f"{stats['memory_usage']:.1f}",
                f"{stats['peak_memory']:.1f}",
                stats['duration'] if 'duration' in stats else "0:00"
            )
        
        return Panel(table, title="Task Details", border_style="yellow")
    
    def _create_footer(self) -> Panel:
        """Create the footer panel."""
        from rich.columns import Columns
        from rich.align import Align
        
        memory_status = self.monitor.get_memory_status()
        memory_icon = "🟢"  # Default NORMAL
        if memory_status == "PRESSURE":
            memory_icon = "🟠"
        elif memory_status == "CRITICAL":
            memory_icon = "🔴"
        
        # Left section - memory status
        left_text = Text()
        left_text.append("Memory Status: ", style="bold")
        status_style = "green" if memory_status == "NORMAL" else "yellow" if memory_status == "PRESSURE" else "red bold"
        left_text.append(f"{memory_icon} {memory_status}", style=status_style)
        
        # Center section - copyright
        center_text = Text("© Crawl4AI 2025 | Made by UnclecCode", style="cyan italic")
        
        # Right section - quit instruction
        right_text = Text()
        right_text.append("Press ", style="bold")
        right_text.append("q", style="white on blue")
        right_text.append(" to quit", style="bold")
        
        # Create columns with the three sections
        footer_content = Columns(
            [
                Align.left(left_text),
                Align.center(center_text),
                Align.right(right_text)
            ],
            expand=True
        )
        
        # Create a more visible footer panel
        return Panel(
            footer_content,
            border_style="white",
            padding=(0, 1)  # Add padding for better visibility
        )


class CrawlerMonitor:
    """
    Comprehensive monitoring and visualization system for tracking web crawler operations in real-time.
    Provides a terminal-based dashboard that displays task statuses, memory usage, queue statistics,
    and performance metrics.
    """
    
    def __init__(
        self,
        urls_total: int = 0,
        refresh_rate: float = 1.0,
        enable_ui: bool = True,
        max_width: int = 120
    ):
        """
        Initialize the CrawlerMonitor.
        
        Args:
            urls_total: Total number of URLs to be crawled
            refresh_rate: How often to refresh the UI (in seconds)
            enable_ui: Whether to display the terminal UI
            max_width: Maximum width of the UI in characters
        """
        # Core monitoring attributes
        self.stats = {}  # Task ID -> stats dict
        self.memory_status = "NORMAL"
        self.start_time = None
        self.end_time = None
        self.is_running = False
        self.queue_stats = {
            "total_queued": 0,
            "highest_wait_time": 0.0,
            "avg_wait_time": 0.0
        }
        self.urls_total = urls_total
        self.urls_completed = 0
        self.peak_memory_percent = 0.0
        self.peak_memory_time = 0.0
        
        # Status counts
        self.status_counts = {
            CrawlStatus.QUEUED.name: 0,
            CrawlStatus.IN_PROGRESS.name: 0,
            CrawlStatus.COMPLETED.name: 0,
            CrawlStatus.FAILED.name: 0
        }
        
        # Requeue tracking
        self.requeued_count = 0
        
        # Thread-safety
        self._lock = threading.RLock()
        
        # Terminal UI
        self.enable_ui = enable_ui
        self.terminal_ui = TerminalUI(
            refresh_rate=refresh_rate, 
            max_width=max_width
        ) if enable_ui else None
    
    def start(self):
        """
        Start the monitoring session.
        
        - Initializes the start_time
        - Sets is_running to True
        - Starts the terminal UI if enabled
        """
        with self._lock:
            self.start_time = time.time()
            self.is_running = True
            
            # Start the terminal UI
            if self.enable_ui and self.terminal_ui:
                self.terminal_ui.start(self)
    
    def stop(self):
        """
        Stop the monitoring session.
        
        - Records end_time
        - Sets is_running to False
        - Stops the terminal UI
        - Generates final summary statistics
        """
        with self._lock:
            self.end_time = time.time()
            self.is_running = False
            
            # Stop the terminal UI
            if self.enable_ui and self.terminal_ui:
                self.terminal_ui.stop()
    
    def add_task(self, task_id: str, url: str):
        """
        Register a new task with the monitor.
        
        Args:
            task_id: Unique identifier for the task
            url: URL being crawled
            
        The task is initialized with:
            - status: QUEUED
            - url: The URL to crawl
            - enqueue_time: Current time
            - memory_usage: 0
            - peak_memory: 0
            - wait_time: 0
            - retry_count: 0
        """
        with self._lock:
            self.stats[task_id] = {
                "task_id": task_id,
                "url": url,
                "status": CrawlStatus.QUEUED.name,
                "enqueue_time": time.time(),
                "start_time": None,
                "end_time": None,
                "memory_usage": 0.0,
                "peak_memory": 0.0,
                "error_message": "",
                "wait_time": 0.0,
                "retry_count": 0,
                "duration": "0:00",
                "counted_requeue": False
            }
            
            # Update status counts
            self.status_counts[CrawlStatus.QUEUED.name] += 1
    
    def update_task(
        self, 
        task_id: str, 
        status: Optional[CrawlStatus] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        memory_usage: Optional[float] = None,
        peak_memory: Optional[float] = None,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None,
        wait_time: Optional[float] = None
    ):
        """
        Update statistics for a specific task.
        
        Args:
            task_id: Unique identifier for the task
            status: New status (QUEUED, IN_PROGRESS, COMPLETED, FAILED)
            start_time: When task execution started
            end_time: When task execution ended
            memory_usage: Current memory usage in MB
            peak_memory: Maximum memory usage in MB
            error_message: Error description if failed
            retry_count: Number of retry attempts
            wait_time: Time spent in queue
            
        Updates task statistics and updates status counts.
        If status changes, decrements old status count and 
        increments new status count.
        """
        with self._lock:
            # Check if task exists
            if task_id not in self.stats:
                return
            
            task_stats = self.stats[task_id]
            
            # Update status counts if status is changing
            old_status = task_stats["status"]
            if status and status.name != old_status:
                self.status_counts[old_status] -= 1
                self.status_counts[status.name] += 1
                
                # Track completion
                if status == CrawlStatus.COMPLETED:
                    self.urls_completed += 1
                
                # Track requeues
                if old_status in [CrawlStatus.COMPLETED.name, CrawlStatus.FAILED.name] and not task_stats.get("counted_requeue", False):
                    self.requeued_count += 1
                    task_stats["counted_requeue"] = True
            
            # Update task statistics
            if status:
                task_stats["status"] = status.name
            if start_time is not None:
                task_stats["start_time"] = start_time
            if end_time is not None:
                task_stats["end_time"] = end_time
            if memory_usage is not None:
                task_stats["memory_usage"] = memory_usage
                
                # Update peak memory if necessary
                current_percent = (memory_usage / psutil.virtual_memory().total) * 100
                if current_percent > self.peak_memory_percent:
                    self.peak_memory_percent = current_percent
                    self.peak_memory_time = time.time()
                
            if peak_memory is not None:
                task_stats["peak_memory"] = peak_memory
            if error_message is not None:
                task_stats["error_message"] = error_message
            if retry_count is not None:
                task_stats["retry_count"] = retry_count
            if wait_time is not None:
                task_stats["wait_time"] = wait_time
            
            # Calculate duration
            if task_stats["start_time"]:
                end = task_stats["end_time"] or time.time()
                duration = end - task_stats["start_time"]
                task_stats["duration"] = self._format_time(duration)
    
    def update_memory_status(self, status: str):
        """
        Update the current memory status.
        
        Args:
            status: Memory status (NORMAL, PRESSURE, CRITICAL, or custom)
            
        Also updates the UI to reflect the new status.
        """
        with self._lock:
            self.memory_status = status
    
    def update_queue_statistics(
        self,
        total_queued: int,
        highest_wait_time: float,
        avg_wait_time: float
    ):
        """
        Update statistics related to the task queue.
        
        Args:
            total_queued: Number of tasks currently in queue
            highest_wait_time: Longest wait time of any queued task
            avg_wait_time: Average wait time across all queued tasks
        """
        with self._lock:
            self.queue_stats = {
                "total_queued": total_queued,
                "highest_wait_time": highest_wait_time,
                "avg_wait_time": avg_wait_time
            }
    
    def get_task_stats(self, task_id: str) -> Dict:
        """
        Get statistics for a specific task.
        
        Args:
            task_id: Unique identifier for the task
            
        Returns:
            Dictionary containing all task statistics
        """
        with self._lock:
            return self.stats.get(task_id, {}).copy()
    
    def get_all_task_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all tasks.
        
        Returns:
            Dictionary mapping task_ids to their statistics
        """
        with self._lock:
            return self.stats.copy()
    
    def get_memory_status(self) -> str:
        """
        Get the current memory status.
        
        Returns:
            Current memory status string
        """
        with self._lock:
            return self.memory_status
    
    def get_queue_stats(self) -> Dict:
        """
        Get current queue statistics.
        
        Returns:
            Dictionary with queue statistics including:
            - total_queued: Number of tasks in queue
            - highest_wait_time: Longest wait time
            - avg_wait_time: Average wait time
        """
        with self._lock:
            return self.queue_stats.copy()
    
    def get_summary(self) -> Dict:
        """
        Get a summary of all crawler statistics.
        
        Returns:
            Dictionary containing:
            - runtime: Total runtime in seconds
            - urls_total: Total URLs to process
            - urls_completed: Number of completed URLs
            - completion_percentage: Percentage complete
            - status_counts: Count of tasks in each status
            - memory_status: Current memory status
            - peak_memory_percent: Highest memory usage
            - peak_memory_time: When peak memory occurred
            - avg_task_duration: Average task processing time
            - estimated_completion_time: Projected finish time
            - requeue_rate: Percentage of tasks requeued
        """
        with self._lock:
            # Calculate runtime
            current_time = time.time()
            runtime = current_time - (self.start_time or current_time)
            
            # Calculate completion percentage
            completion_percentage = 0
            if self.urls_total > 0:
                completion_percentage = (self.urls_completed / self.urls_total) * 100
            
            # Calculate average task duration for completed tasks
            completed_tasks = [
                task for task in self.stats.values() 
                if task["status"] == CrawlStatus.COMPLETED.name and task.get("start_time") and task.get("end_time")
            ]
            
            avg_task_duration = 0
            if completed_tasks:
                total_duration = sum(task["end_time"] - task["start_time"] for task in completed_tasks)
                avg_task_duration = total_duration / len(completed_tasks)
            
            # Calculate requeue rate
            requeue_rate = 0
            if len(self.stats) > 0:
                requeue_rate = (self.requeued_count / len(self.stats)) * 100
            
            # Calculate estimated completion time
            estimated_completion_time = "N/A"
            if avg_task_duration > 0 and self.urls_total > 0 and self.urls_completed > 0:
                remaining_tasks = self.urls_total - self.urls_completed
                estimated_seconds = remaining_tasks * avg_task_duration
                estimated_completion_time = self._format_time(estimated_seconds)
            
            return {
                "runtime": runtime,
                "urls_total": self.urls_total,
                "urls_completed": self.urls_completed,
                "completion_percentage": completion_percentage,
                "status_counts": self.status_counts.copy(),
                "memory_status": self.memory_status,
                "peak_memory_percent": self.peak_memory_percent,
                "peak_memory_time": self.peak_memory_time,
                "avg_task_duration": avg_task_duration,
                "estimated_completion_time": estimated_completion_time,
                "requeue_rate": requeue_rate,
                "requeued_count": self.requeued_count
            }
    
    def render(self):
        """
        Render the terminal UI.
        
        This is the main UI rendering loop that:
        1. Updates all statistics
        2. Formats the display
        3. Renders the ASCII interface
        4. Handles keyboard input
        
        Note: The actual rendering is handled by the TerminalUI class
        which uses the rich library's Live display.
        """
        if self.enable_ui and self.terminal_ui:
            # Force an update of the UI
            if hasattr(self.terminal_ui, '_update_display'):
                self.terminal_ui._update_display()
    
    def _format_time(self, seconds: float) -> str:
        """
        Format time in hours:minutes:seconds.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string (e.g., "1:23:45")
        """
        delta = timedelta(seconds=int(seconds))
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02}:{seconds:02}"
        else:
            return f"{minutes}:{seconds:02}"
    
    def _calculate_estimated_completion(self) -> str:
        """
        Calculate estimated completion time based on current progress.
        
        Returns:
            Formatted time string
        """
        summary = self.get_summary()
        return summary.get("estimated_completion_time", "N/A")


# Example code for testing
if __name__ == "__main__":
    # Initialize the monitor
    monitor = CrawlerMonitor(urls_total=100)
    
    # Start monitoring
    monitor.start()
    
    try:
        # Simulate some tasks
        for i in range(20):
            task_id = str(uuid.uuid4())
            url = f"https://example.com/page{i}"
            monitor.add_task(task_id, url)
            
            # Simulate 20% of tasks are already running
            if i < 4:
                monitor.update_task(
                    task_id=task_id,
                    status=CrawlStatus.IN_PROGRESS,
                    start_time=time.time() - 30,  # Started 30 seconds ago
                    memory_usage=10.5
                )
                
            # Simulate 10% of tasks are completed
            if i >= 4 and i < 6:
                start_time = time.time() - 60
                end_time = time.time() - 15
                monitor.update_task(
                    task_id=task_id,
                    status=CrawlStatus.IN_PROGRESS,
                    start_time=start_time,
                    memory_usage=8.2
                )
                monitor.update_task(
                    task_id=task_id,
                    status=CrawlStatus.COMPLETED,
                    end_time=end_time,
                    memory_usage=0,
                    peak_memory=15.7
                )
                
            # Simulate 5% of tasks fail
            if i >= 6 and i < 7:
                start_time = time.time() - 45
                end_time = time.time() - 20
                monitor.update_task(
                    task_id=task_id,
                    status=CrawlStatus.IN_PROGRESS,
                    start_time=start_time,
                    memory_usage=12.3
                )
                monitor.update_task(
                    task_id=task_id,
                    status=CrawlStatus.FAILED,
                    end_time=end_time,
                    memory_usage=0,
                    peak_memory=18.2,
                    error_message="Connection timeout"
                )
        
        # Simulate memory pressure
        monitor.update_memory_status("PRESSURE")
        
        # Simulate queue statistics
        monitor.update_queue_statistics(
            total_queued=16,  # 20 - 4 (in progress)
            highest_wait_time=120.5,
            avg_wait_time=60.2
        )
        
        # Keep the monitor running for a demonstration
        print("Crawler Monitor is running. Press 'q' to exit.")
        while monitor.is_running:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nExiting crawler monitor...")
    finally:
        # Stop the monitor
        monitor.stop()
        print("Crawler monitor exited successfully.")