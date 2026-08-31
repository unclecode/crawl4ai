import asyncio
import time
import psutil
import logging
import random
from typing import List, Dict
import uuid
import sys
import os

# Import your crawler components
from crawl4ai.models import DisplayMode, CrawlStatus, CrawlResult
from crawl4ai.async_configs import CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai import AsyncWebCrawler
from crawl4ai import MemoryAdaptiveDispatcher, CrawlerMonitor

# Global configuration
STREAM = False  # Toggle between streaming and non-streaming modes

# Configure logging to file only (to avoid breaking the rich display)
os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/memory_stress_test.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

# Root logger - only to file, not console
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)

# Our test logger also writes to file only
logger = logging.getLogger("memory_stress_test")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.propagate = False  # Don't propagate to root logger

# Create a memory restrictor to simulate limited memory environment
class MemorySimulator:
    def __init__(self, target_percent: float = 85.0, aggressive: bool = False):
        """Simulates memory pressure by allocating memory"""
        self.target_percent = target_percent
        self.memory_blocks: List[bytearray] = []
        self.aggressive = aggressive
        
    def apply_pressure(self, additional_percent: float = 0.0):
        """Fill memory until we reach target percentage"""
        current_percent = psutil.virtual_memory().percent
        target = self.target_percent + additional_percent
        
        if current_percent >= target:
            return  # Already at target
            
        logger.info(f"Current memory: {current_percent}%, target: {target}%")
        
        # Calculate how much memory we need to allocate
        total_memory = psutil.virtual_memory().total
        target_usage = (target / 100.0) * total_memory
        current_usage = (current_percent / 100.0) * total_memory
        bytes_to_allocate = int(target_usage - current_usage)
        
        if bytes_to_allocate <= 0:
            return
            
        # Allocate in smaller chunks to avoid overallocation
        if self.aggressive:
            # Use larger chunks for faster allocation in aggressive mode
            chunk_size = min(bytes_to_allocate, 200 * 1024 * 1024)  # 200MB chunks
        else:
            chunk_size = min(bytes_to_allocate, 50 * 1024 * 1024)   # 50MB chunks
        
        try:
            logger.info(f"Allocating {chunk_size / (1024 * 1024):.1f}MB to reach target memory usage")
            self.memory_blocks.append(bytearray(chunk_size))
            time.sleep(0.5)  # Give system time to register the allocation
        except MemoryError:
            logger.warning("Unable to allocate more memory")
            
    def release_pressure(self, percent: float = None):
        """
        Release allocated memory
        If percent is specified, release that percentage of blocks
        """
        if not self.memory_blocks:
            return
            
        if percent is None:
            # Release all
            logger.info(f"Releasing all {len(self.memory_blocks)} memory blocks")
            self.memory_blocks.clear()
        else:
            # Release specified percentage
            blocks_to_release = int(len(self.memory_blocks) * (percent / 100.0))
            if blocks_to_release > 0:
                logger.info(f"Releasing {blocks_to_release} of {len(self.memory_blocks)} memory blocks ({percent}%)")
                self.memory_blocks = self.memory_blocks[blocks_to_release:]
                
    def spike_pressure(self, duration: float = 5.0):
        """
        Create a temporary spike in memory pressure then release
        Useful for forcing requeues
        """
        logger.info(f"Creating memory pressure spike for {duration} seconds")
        # Save current blocks count
        initial_blocks = len(self.memory_blocks)
        
        # Create spike with extra 5%
        self.apply_pressure(additional_percent=5.0)
        
        # Schedule release after duration
        asyncio.create_task(self._delayed_release(duration, initial_blocks))
        
    async def _delayed_release(self, delay: float, target_blocks: int):
        """Helper for spike_pressure - releases extra blocks after delay"""
        await asyncio.sleep(delay)
        
        # Remove blocks added since spike started
        if len(self.memory_blocks) > target_blocks:
            logger.info(f"Releasing memory spike ({len(self.memory_blocks) - target_blocks} blocks)")
            self.memory_blocks = self.memory_blocks[:target_blocks]
            
# Test statistics collector
class TestResults:
    def __init__(self):
        self.start_time = time.time()
        self.completed_urls: List[str] = []
        self.failed_urls: List[str] = []
        self.requeued_count = 0
        self.memory_warnings = 0
        self.max_memory_usage = 0.0
        self.max_queue_size = 0
        self.max_wait_time = 0.0
        self.url_to_attempt: Dict[str, int] = {}  # Track retries per URL
        
    def log_summary(self):
        duration = time.time() - self.start_time
        logger.info("===== TEST SUMMARY =====")
        logger.info(f"Stream mode: {'ON' if STREAM else 'OFF'}")
        logger.info(f"Total duration: {duration:.1f} seconds")
        logger.info(f"Completed URLs: {len(self.completed_urls)}")
        logger.info(f"Failed URLs: {len(self.failed_urls)}")
        logger.info(f"Requeue events: {self.requeued_count}")
        logger.info(f"Memory warnings: {self.memory_warnings}")
        logger.info(f"Max memory usage: {self.max_memory_usage:.1f}%")
        logger.info(f"Max queue size: {self.max_queue_size}")
        logger.info(f"Max wait time: {self.max_wait_time:.1f} seconds")
        
        # Log URLs with multiple attempts
        retried_urls = {url: count for url, count in self.url_to_attempt.items() if count > 1}
        if retried_urls:
            logger.info(f"URLs with retries: {len(retried_urls)}")
            # Log the top 5 most retried
            top_retries = sorted(retried_urls.items(), key=lambda x: x[1], reverse=True)[:5]
            for url, count in top_retries:
                logger.info(f"  URL {url[-30:]} had {count} attempts")
        
        # Write summary to a separate human-readable file
        with open("logs/test_summary.txt", "w") as f:
            f.write(f"Stream mode: {'ON' if STREAM else 'OFF'}\n")
            f.write(f"Total duration: {duration:.1f} seconds\n")
            f.write(f"Completed URLs: {len(self.completed_urls)}\n")
            f.write(f"Failed URLs: {len(self.failed_urls)}\n")
            f.write(f"Requeue events: {self.requeued_count}\n")
            f.write(f"Memory warnings: {self.memory_warnings}\n")
            f.write(f"Max memory usage: {self.max_memory_usage:.1f}%\n")
            f.write(f"Max queue size: {self.max_queue_size}\n")
            f.write(f"Max wait time: {self.max_wait_time:.1f} seconds\n")
        
# Custom monitor with stats tracking
# Custom monitor that extends CrawlerMonitor with test-specific tracking
class StressTestMonitor(CrawlerMonitor):
    def __init__(self, test_results: TestResults, **kwargs):
        # Initialize the parent CrawlerMonitor
        super().__init__(**kwargs)
        self.test_results = test_results
        
    def update_memory_status(self, status: str):
        if status != self.memory_status:
            logger.info(f"Memory status changed: {self.memory_status} -> {status}")
            if "CRITICAL" in status or "PRESSURE" in status:
                self.test_results.memory_warnings += 1
                
        # Track peak memory usage in test results
        current_memory = psutil.virtual_memory().percent
        self.test_results.max_memory_usage = max(self.test_results.max_memory_usage, current_memory)
        
        # Call parent method to update the dashboard
        super().update_memory_status(status)
        
    def update_queue_statistics(self, total_queued: int, highest_wait_time: float, avg_wait_time: float):
        # Track queue metrics in test results
        self.test_results.max_queue_size = max(self.test_results.max_queue_size, total_queued)
        self.test_results.max_wait_time = max(self.test_results.max_wait_time, highest_wait_time)
        
        # Call parent method to update the dashboard
        super().update_queue_statistics(total_queued, highest_wait_time, avg_wait_time)
        
    def update_task(self, task_id: str, **kwargs):
        # Track URL status changes for test results
        if task_id in self.stats:
            old_status = self.stats[task_id].status
            
            # If this is a requeue event (requeued due to memory pressure)
            if 'error_message' in kwargs and 'requeued' in kwargs['error_message']:
                if not hasattr(self.stats[task_id], 'counted_requeue') or not self.stats[task_id].counted_requeue:
                    self.test_results.requeued_count += 1
                    self.stats[task_id].counted_requeue = True
                    
            # Track completion status for test results
            if 'status' in kwargs:
                new_status = kwargs['status']
                if old_status != new_status:
                    if new_status == CrawlStatus.COMPLETED:
                        if task_id not in self.test_results.completed_urls:
                            self.test_results.completed_urls.append(task_id)
                    elif new_status == CrawlStatus.FAILED:
                        if task_id not in self.test_results.failed_urls:
                            self.test_results.failed_urls.append(task_id)
        
        # Call parent method to update the dashboard
        super().update_task(task_id, **kwargs)
        self.live.update(self._create_table())

# Generate test URLs - use example.com with unique paths to avoid browser caching
def generate_test_urls(count: int) -> List[str]:
    urls = []
    for i in range(count):
        # Add random path and query parameters to create unique URLs
        path = f"/path/{uuid.uuid4()}"
        query = f"?test={i}&random={random.randint(1, 100000)}"
        urls.append(f"https://example.com{path}{query}")
    return urls

# Process result callback
async def process_result(result, test_results: TestResults):
    # Track attempt counts
    if result.url not in test_results.url_to_attempt:
        test_results.url_to_attempt[result.url] = 1
    else:
        test_results.url_to_attempt[result.url] += 1
    
    if "requeued" in result.error_message:
        test_results.requeued_count += 1
        logger.debug(f"Requeued due to memory pressure: {result.url}")
    elif result.success:
        test_results.completed_urls.append(result.url)
        logger.debug(f"Successfully processed: {result.url}")
    else:
        test_results.failed_urls.append(result.url)
        logger.warning(f"Failed to process: {result.url} - {result.error_message}")

# Process multiple results (used in non-streaming mode)
async def process_results(results, test_results: TestResults):
    for result in results:
        await process_result(result, test_results)

# Main test function for extreme memory pressure simulation
async def run_memory_stress_test(
    url_count: int = 100,
    target_memory_percent: float = 92.0,  # Push to dangerous levels
    chunk_size: int = 20,  # Larger chunks for more chaos
    aggressive: bool = False,
    spikes: bool = True
):
    test_results = TestResults()
    memory_simulator = MemorySimulator(target_percent=target_memory_percent, aggressive=aggressive)
    
    logger.info(f"Starting stress test with {url_count} URLs in {'STREAM' if STREAM else 'NON-STREAM'} mode")
    logger.info(f"Target memory usage: {target_memory_percent}%")
    
    # First, elevate memory usage to create pressure
    logger.info("Creating initial memory pressure...")
    memory_simulator.apply_pressure()
    
    # Create test URLs in chunks to simulate real-world crawling where URLs are discovered
    all_urls = generate_test_urls(url_count)
    url_chunks = [all_urls[i:i+chunk_size] for i in range(0, len(all_urls), chunk_size)]
    
    # Set up the crawler components - low memory thresholds to create more requeues
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        verbose=False,
        stream=STREAM  # Use the global STREAM variable to set mode
    )
    
    # Create monitor with reference to test results
    monitor = StressTestMonitor(
        test_results=test_results,
        display_mode=DisplayMode.DETAILED,
        max_visible_rows=20,
        total_urls=url_count  # Pass total URLs count
    )
    
    # Create dispatcher with EXTREME settings - pure survival mode
    # These settings are designed to create a memory battleground
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=63.0,  # Start throttling at just 60% memory
        critical_threshold_percent=70.0,  # Start requeuing at 70% - incredibly aggressive  
        recovery_threshold_percent=55.0,  # Only resume normal ops when plenty of memory available
        check_interval=0.1,  # Check extremely frequently (100ms)
        max_session_permit=20 if aggressive else 10,  # Double the concurrent sessions - pure chaos
        fairness_timeout=10.0,  # Extremely low timeout - rapid priority changes
        monitor=monitor
    )
    
    # Set up spike schedule if enabled
    if spikes:
        spike_intervals = []
        # Create 3-5 random spike times
        num_spikes = random.randint(3, 5)
        for _ in range(num_spikes):
            # Schedule spikes at random chunks
            chunk_index = random.randint(1, len(url_chunks) - 1)
            spike_intervals.append(chunk_index)
        logger.info(f"Scheduled memory spikes at chunks: {spike_intervals}")
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Process URLs in chunks to simulate discovering URLs over time
            for chunk_index, url_chunk in enumerate(url_chunks):
                logger.info(f"Processing chunk {chunk_index+1}/{len(url_chunks)} ({len(url_chunk)} URLs)")
                
                # Regular pressure increases
                if chunk_index % 2 == 0:
                    logger.info("Increasing memory pressure...")
                    memory_simulator.apply_pressure()
                
                # Memory spike if scheduled for this chunk
                if spikes and chunk_index in spike_intervals:
                    logger.info(f"⚠️ CREATING MASSIVE MEMORY SPIKE at chunk {chunk_index+1} ⚠️")
                    # Create a nightmare scenario - multiple overlapping spikes
                    memory_simulator.spike_pressure(duration=10.0)  # 10-second spike
                    
                    # 50% chance of double-spike (pure evil)
                    if random.random() < 0.5:
                        await asyncio.sleep(2.0)  # Wait 2 seconds
                        logger.info("💀 DOUBLE SPIKE - EXTREME MEMORY PRESSURE 💀")
                        memory_simulator.spike_pressure(duration=8.0)  # 8-second overlapping spike
                
                if STREAM:
                    # Stream mode - process results as they come in
                    async for result in dispatcher.run_urls_stream(
                        urls=url_chunk,
                        crawler=crawler,
                        config=run_config
                    ):
                        await process_result(result, test_results)
                else:
                    # Non-stream mode - get all results at once
                    results = await dispatcher.run_urls(
                        urls=url_chunk,
                        crawler=crawler,
                        config=run_config
                    )
                    await process_results(results, test_results)
                    
                # Simulate discovering more URLs while others are still processing
                await asyncio.sleep(1)
                
                # RARELY release pressure - make the system fight for resources
                if chunk_index % 5 == 4:  # Less frequent releases
                    release_percent = random.choice([10, 15, 20])  # Smaller, inconsistent releases
                    logger.info(f"Releasing {release_percent}% of memory blocks - brief respite")
                    memory_simulator.release_pressure(percent=release_percent)
    
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        raise
    finally:
        # Release memory pressure
        memory_simulator.release_pressure()
        # Log final results
        test_results.log_summary()
        
        # Check for success criteria
        if len(test_results.completed_urls) + len(test_results.failed_urls) < url_count:
            logger.error(f"TEST FAILED: Not all URLs were processed. {url_count - len(test_results.completed_urls) - len(test_results.failed_urls)} URLs missing.")
            return False
            
        logger.info("TEST PASSED: All URLs were processed without crashing.")
        return True

# Command-line entry point
if __name__ == "__main__":
    # Parse command line arguments
    url_count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    target_memory = float(sys.argv[2]) if len(sys.argv) > 2 else 85.0
    
    # Check if stream mode is specified
    if len(sys.argv) > 3:
        STREAM = sys.argv[3].lower() in ('true', 'yes', '1', 'stream')
    
    # Check if aggressive mode is specified
    aggressive = False
    if len(sys.argv) > 4:
        aggressive = sys.argv[4].lower() in ('true', 'yes', '1', 'aggressive')
    
    print(f"Starting test with {url_count} URLs, {target_memory}% memory target")
    print(f"Stream mode: {STREAM}, Aggressive: {aggressive}")
    print("Logs will be written to the logs directory")
    print("Live display starting now...")
    
    # Run the test
    result = asyncio.run(run_memory_stress_test(
        url_count=url_count, 
        target_memory_percent=target_memory,
        aggressive=aggressive
    ))
    
    # Exit with status code
    sys.exit(0 if result else 1)