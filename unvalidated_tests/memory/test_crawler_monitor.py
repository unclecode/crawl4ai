"""
Test script for the CrawlerMonitor component.
This script simulates a crawler with multiple tasks to demonstrate the real-time monitoring capabilities.
"""

import time
import uuid
import random
import threading
import sys
import os

# Add the parent directory to the path to import crawl4ai
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from crawl4ai.components.crawler_monitor import CrawlerMonitor
from crawl4ai.models import CrawlStatus

def simulate_crawler_task(monitor, task_id, url, simulate_failure=False):
    """Simulate a crawler task with different states."""
    # Task starts in the QUEUED state
    wait_time = random.uniform(0.5, 3.0)
    time.sleep(wait_time)
    
    # Update to IN_PROGRESS state
    monitor.update_task(
        task_id=task_id,
        status=CrawlStatus.IN_PROGRESS,
        start_time=time.time(),
        wait_time=wait_time
    )
    
    # Simulate task running
    process_time = random.uniform(1.0, 5.0)
    for i in range(int(process_time * 2)):
        # Simulate memory usage changes
        memory_usage = random.uniform(5.0, 25.0)
        monitor.update_task(
            task_id=task_id,
            memory_usage=memory_usage,
            peak_memory=max(memory_usage, monitor.get_task_stats(task_id).get("peak_memory", 0))
        )
        time.sleep(0.5)
    
    # Update to COMPLETED or FAILED state
    if simulate_failure and random.random() < 0.8:  # 80% chance of failure if simulate_failure is True
        monitor.update_task(
            task_id=task_id,
            status=CrawlStatus.FAILED,
            end_time=time.time(),
            error_message="Simulated failure: Connection timeout",
            memory_usage=0.0
        )
    else:
        monitor.update_task(
            task_id=task_id,
            status=CrawlStatus.COMPLETED,
            end_time=time.time(),
            memory_usage=0.0
        )

def update_queue_stats(monitor, num_queued_tasks):
    """Update queue statistics periodically."""
    while monitor.is_running:
        queued_tasks = [
            task for task_id, task in monitor.get_all_task_stats().items()
            if task["status"] == CrawlStatus.QUEUED.name
        ]
        
        total_queued = len(queued_tasks)
        
        if total_queued > 0:
            current_time = time.time()
            wait_times = [
                current_time - task.get("enqueue_time", current_time)
                for task in queued_tasks
            ]
            highest_wait_time = max(wait_times) if wait_times else 0.0
            avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0.0
        else:
            highest_wait_time = 0.0
            avg_wait_time = 0.0
        
        monitor.update_queue_statistics(
            total_queued=total_queued,
            highest_wait_time=highest_wait_time,
            avg_wait_time=avg_wait_time
        )
        
        # Simulate memory pressure based on number of active tasks
        active_tasks = len([
            task for task_id, task in monitor.get_all_task_stats().items()
            if task["status"] == CrawlStatus.IN_PROGRESS.name
        ])
        
        if active_tasks > 8:
            monitor.update_memory_status("CRITICAL")
        elif active_tasks > 4:
            monitor.update_memory_status("PRESSURE")
        else:
            monitor.update_memory_status("NORMAL")
            
        time.sleep(1.0)

def test_crawler_monitor():
    """Test the CrawlerMonitor with simulated crawler tasks."""
    # Total number of URLs to crawl
    total_urls = 50
    
    # Initialize the monitor
    monitor = CrawlerMonitor(urls_total=total_urls, refresh_rate=0.5)
    
    # Start the monitor
    monitor.start()
    
    # Start thread to update queue statistics
    queue_stats_thread = threading.Thread(target=update_queue_stats, args=(monitor, total_urls))
    queue_stats_thread.daemon = True
    queue_stats_thread.start()
    
    try:
        # Create task threads
        threads = []
        for i in range(total_urls):
            task_id = str(uuid.uuid4())
            url = f"https://example.com/page{i}"
            
            # Add task to monitor
            monitor.add_task(task_id, url)
            
            # Determine if this task should simulate failure
            simulate_failure = (i % 10 == 0)  # Every 10th task
            
            # Create and start thread for this task
            thread = threading.Thread(
                target=simulate_crawler_task,
                args=(monitor, task_id, url, simulate_failure)
            )
            thread.daemon = True
            threads.append(thread)
        
        # Start threads with delay to simulate tasks being added over time
        batch_size = 5
        for i in range(0, len(threads), batch_size):
            batch = threads[i:i+batch_size]
            for thread in batch:
                thread.start()
                time.sleep(0.5)  # Small delay between starting threads
            
            # Wait a bit before starting the next batch
            time.sleep(2.0)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        # Keep monitor running a bit longer to see the final state
        time.sleep(5.0)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        # Stop the monitor
        monitor.stop()
        print("\nCrawler monitor test completed")

if __name__ == "__main__":
    test_crawler_monitor()