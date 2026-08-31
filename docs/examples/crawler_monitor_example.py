"""
CrawlerMonitor Example

This example demonstrates how to use the CrawlerMonitor component 
to visualize and track web crawler operations in real-time.
"""

import time
import uuid
import random
import threading
from crawl4ai.components.crawler_monitor import CrawlerMonitor
from crawl4ai.models import CrawlStatus

def simulate_webcrawler_operations(monitor, num_tasks=20):
    """
    Simulates a web crawler's operations with multiple tasks and different states.
    
    Args:
        monitor: The CrawlerMonitor instance
        num_tasks: Number of tasks to simulate
    """
    print(f"Starting simulation with {num_tasks} tasks...")
    
    # Create and register all tasks first
    task_ids = []
    for i in range(num_tasks):
        task_id = str(uuid.uuid4())
        url = f"https://example.com/page{i}"
        monitor.add_task(task_id, url)
        task_ids.append((task_id, url))
        
        # Small delay between task creation
        time.sleep(0.2)
    
    # Process tasks with a variety of different behaviors
    threads = []
    for i, (task_id, url) in enumerate(task_ids):
        # Create a thread for each task
        thread = threading.Thread(
            target=process_task,
            args=(monitor, task_id, url, i)
        )
        thread.daemon = True
        threads.append(thread)
    
    # Start threads in batches to simulate concurrent processing
    batch_size = 4  # Process 4 tasks at a time
    for i in range(0, len(threads), batch_size):
        batch = threads[i:i+batch_size]
        for thread in batch:
            thread.start()
            time.sleep(0.5)  # Stagger thread start times
        
        # Wait a bit before starting next batch
        time.sleep(random.uniform(1.0, 3.0))
        
        # Update queue statistics
        update_queue_stats(monitor)
        
        # Simulate memory pressure changes
        active_threads = [t for t in threads if t.is_alive()]
        if len(active_threads) > 8:
            monitor.update_memory_status("CRITICAL")
        elif len(active_threads) > 4:
            monitor.update_memory_status("PRESSURE")
        else:
            monitor.update_memory_status("NORMAL")
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Final updates
    update_queue_stats(monitor)
    monitor.update_memory_status("NORMAL")
    
    print("Simulation completed!")
    
def process_task(monitor, task_id, url, index):
    """Simulate processing of a single task."""
    # Tasks start in queued state (already added)
    
    # Simulate waiting in queue
    wait_time = random.uniform(0.5, 3.0)
    time.sleep(wait_time)
    
    # Start processing - move to IN_PROGRESS
    monitor.update_task(
        task_id=task_id,
        status=CrawlStatus.IN_PROGRESS,
        start_time=time.time(),
        wait_time=wait_time
    )
    
    # Simulate task processing with memory usage changes
    total_process_time = random.uniform(2.0, 10.0)
    step_time = total_process_time / 5  # Update in 5 steps
    
    for step in range(5):
        # Simulate increasing then decreasing memory usage
        if step < 3:  # First 3 steps - increasing
            memory_usage = random.uniform(5.0, 20.0) * (step + 1)
        else:  # Last 2 steps - decreasing
            memory_usage = random.uniform(5.0, 20.0) * (5 - step)
            
        # Update peak memory if this is higher
        peak = max(memory_usage, monitor.get_task_stats(task_id).get("peak_memory", 0))
        
        monitor.update_task(
            task_id=task_id,
            memory_usage=memory_usage,
            peak_memory=peak
        )
        
        time.sleep(step_time)
    
    # Determine final state - 80% success, 20% failure
    if index % 5 == 0:  # Every 5th task fails
        monitor.update_task(
            task_id=task_id,
            status=CrawlStatus.FAILED,
            end_time=time.time(),
            memory_usage=0.0,
            error_message="Connection timeout"
        )
    else:
        monitor.update_task(
            task_id=task_id,
            status=CrawlStatus.COMPLETED,
            end_time=time.time(),
            memory_usage=0.0
        )

def update_queue_stats(monitor):
    """Update queue statistics based on current tasks."""
    task_stats = monitor.get_all_task_stats()
    
    # Count queued tasks
    queued_tasks = [
        stats for stats in task_stats.values() 
        if stats["status"] == CrawlStatus.QUEUED.name
    ]
    
    total_queued = len(queued_tasks)
    
    if total_queued > 0:
        current_time = time.time()
        # Calculate wait times
        wait_times = [
            current_time - stats.get("enqueue_time", current_time)
            for stats in queued_tasks
        ]
        highest_wait_time = max(wait_times) if wait_times else 0.0
        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0.0
    else:
        highest_wait_time = 0.0
        avg_wait_time = 0.0
    
    # Update monitor
    monitor.update_queue_statistics(
        total_queued=total_queued,
        highest_wait_time=highest_wait_time,
        avg_wait_time=avg_wait_time
    )

def main():
    # Initialize the monitor
    monitor = CrawlerMonitor(
        urls_total=20,  # Total URLs to process
        refresh_rate=0.5,  # Update UI twice per second
        enable_ui=True,    # Enable terminal UI
        max_width=120     # Set maximum width to 120 characters
    )
    
    # Start the monitor
    monitor.start()
    
    try:
        # Run simulation
        simulate_webcrawler_operations(monitor)
        
        # Keep monitor running a bit to see final state
        print("Waiting to view final state...")
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    finally:
        # Stop the monitor
        monitor.stop()
        print("Example completed!")
        
        # Print some statistics
        summary = monitor.get_summary()
        print("\nCrawler Statistics Summary:")
        print(f"Total URLs: {summary['urls_total']}")
        print(f"Completed: {summary['urls_completed']}")
        print(f"Completion percentage: {summary['completion_percentage']:.1f}%")
        print(f"Peak memory usage: {summary['peak_memory_percent']:.1f}%")
        
        # Print task status counts
        status_counts = summary['status_counts']
        print("\nTask Status Counts:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

if __name__ == "__main__":
    main()