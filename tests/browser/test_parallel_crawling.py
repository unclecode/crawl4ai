"""
Test examples for parallel crawling with the browser module.

These examples demonstrate the functionality of parallel page creation
and serve as functional tests for multi-page crawling performance.
"""

import asyncio
import os
import sys
import time
from typing import List

# Add the project root to Python path if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from crawl4ai.browser import BrowserManager
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger

# Create a logger for clear terminal output
logger = AsyncLogger(verbose=True, log_file=None)

async def test_get_pages_basic():
    """Test basic functionality of get_pages method."""
    logger.info("Testing basic get_pages functionality", tag="TEST")
    
    browser_config = BrowserConfig(headless=True)
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        await manager.start()
        
        # Request 3 pages
        crawler_config = CrawlerRunConfig()
        pages = await manager.get_pages(crawler_config, count=3)
        
        # Verify we got the correct number of pages
        assert len(pages) == 3, f"Expected 3 pages, got {len(pages)}"
        
        # Verify each page is valid
        for i, (page, context) in enumerate(pages):
            await page.goto("https://example.com")
            title = await page.title()
            logger.info(f"Page {i+1} title: {title}", tag="TEST")
            assert title, f"Page {i+1} has no title"
        
        await manager.close()
        logger.success("Basic get_pages test completed successfully", tag="TEST")
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await manager.close()
        except:
            pass
        return False

async def test_parallel_approaches_comparison():
    """Compare two parallel crawling approaches:
    1. Create a page for each URL on-demand (get_page + gather)
    2. Get all pages upfront with get_pages, then use them (get_pages + gather)
    """
    logger.info("Comparing different parallel crawling approaches", tag="TEST")
    
    urls = [
        "https://example.com/page1",
        "https://crawl4ai.com",
        "https://kidocode.com",
        "https://bbc.com",
        # "https://example.com/page1",
        # "https://example.com/page2",
        # "https://example.com/page3",
        # "https://example.com/page4",
    ]
    
    browser_config = BrowserConfig(headless=False)
    manager = BrowserManager(browser_config=browser_config, logger=logger)
    
    try:
        await manager.start()
        
        # Approach 1: Create a page for each URL on-demand and run in parallel
        logger.info("Testing approach 1: get_page for each URL + gather", tag="TEST")
        start_time = time.time()
        
        async def fetch_title_approach1(url):
            """Create a new page for each URL, go to the URL, and get title"""
            crawler_config = CrawlerRunConfig(url=url)
            page, context = await manager.get_page(crawler_config)
            try:
                await page.goto(url)
                title = await page.title()
                return title
            finally:
                await page.close()
        
        # Run fetch_title_approach1 for each URL in parallel
        tasks = [fetch_title_approach1(url) for url in urls]
        approach1_results = await asyncio.gather(*tasks)
        
        approach1_time = time.time() - start_time
        logger.info(f"Approach 1 time (get_page + gather): {approach1_time:.2f}s", tag="TEST")
        
        # Approach 2: Get all pages upfront with get_pages, then use them in parallel
        logger.info("Testing approach 2: get_pages upfront + gather", tag="TEST")
        start_time = time.time()
        
        # Get all pages upfront
        crawler_config = CrawlerRunConfig()
        pages = await manager.get_pages(crawler_config, count=len(urls))
        
        async def fetch_title_approach2(page_ctx, url):
            """Use a pre-created page to go to URL and get title"""
            page, _ = page_ctx
            try:
                await page.goto(url)
                title = await page.title()
                return title
            finally:
                await page.close()
        
        # Use the pre-created pages to fetch titles in parallel
        tasks = [fetch_title_approach2(page_ctx, url) for page_ctx, url in zip(pages, urls)]
        approach2_results = await asyncio.gather(*tasks)
        
        approach2_time = time.time() - start_time
        logger.info(f"Approach 2 time (get_pages + gather): {approach2_time:.2f}s", tag="TEST")
        
        # Compare results and performance
        speedup = approach1_time / approach2_time if approach2_time > 0 else 0
        if speedup > 1:
            logger.success(f"Approach 2 (get_pages upfront) was {speedup:.2f}x faster", tag="TEST")
        else:
            logger.info(f"Approach 1 (get_page + gather) was {1/speedup:.2f}x faster", tag="TEST")
        
        # Verify same content was retrieved in both approaches
        assert len(approach1_results) == len(approach2_results), "Result count mismatch"
        
        # Sort results for comparison since parallel execution might complete in different order
        assert sorted(approach1_results) == sorted(approach2_results), "Results content mismatch"
        
        await manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        try:
            await manager.close()
        except:
            pass
        return False

async def test_multi_browser_scaling(num_browsers=3, pages_per_browser=5):
    """Test performance with multiple browsers and pages per browser.
    Compares two approaches:
    1. On-demand page creation (get_page + gather)
    2. Pre-created pages (get_pages + gather)
    """
    logger.info(f"Testing multi-browser scaling with {num_browsers} browsers × {pages_per_browser} pages", tag="TEST")
    
    # Generate test URLs
    total_pages = num_browsers * pages_per_browser
    urls = [f"https://example.com/page_{i}" for i in range(total_pages)]
    
    # Create browser managers
    managers = []
    base_port = 9222
    
    try:
        # Start all browsers in parallel
        start_tasks = []
        for i in range(num_browsers):
            browser_config = BrowserConfig(
                headless=True  # Using default browser mode like in test_parallel_approaches_comparison
            )
            manager = BrowserManager(browser_config=browser_config, logger=logger)
            start_tasks.append(manager.start())
            managers.append(manager)
        
        await asyncio.gather(*start_tasks)
        
        # Distribute URLs among managers
        urls_per_manager = {}
        for i, manager in enumerate(managers):
            start_idx = i * pages_per_browser
            end_idx = min(start_idx + pages_per_browser, len(urls))
            urls_per_manager[manager] = urls[start_idx:end_idx]
        
        # Approach 1: Create a page for each URL on-demand and run in parallel
        logger.info("Testing approach 1: get_page for each URL + gather", tag="TEST")
        start_time = time.time()
        
        async def fetch_title_approach1(manager, url):
            """Create a new page for the URL, go to the URL, and get title"""
            crawler_config = CrawlerRunConfig(url=url)
            page, context = await manager.get_page(crawler_config)
            try:
                await page.goto(url)
                title = await page.title()
                return title
            finally:
                await page.close()
        
        # Run fetch_title_approach1 for each URL in parallel
        tasks = []
        for manager, manager_urls in urls_per_manager.items():
            for url in manager_urls:
                tasks.append(fetch_title_approach1(manager, url))
        
        approach1_results = await asyncio.gather(*tasks)
        
        approach1_time = time.time() - start_time
        logger.info(f"Approach 1 time (get_page + gather): {approach1_time:.2f}s", tag="TEST")
        
        # Approach 2: Get all pages upfront with get_pages, then use them in parallel
        logger.info("Testing approach 2: get_pages upfront + gather", tag="TEST")
        start_time = time.time()
        
        # Get all pages upfront for each manager
        all_pages = []
        for manager, manager_urls in urls_per_manager.items():
            crawler_config = CrawlerRunConfig()
            pages = await manager.get_pages(crawler_config, count=len(manager_urls))
            all_pages.extend(zip(pages, manager_urls))
        
        async def fetch_title_approach2(page_ctx, url):
            """Use a pre-created page to go to URL and get title"""
            page, _ = page_ctx
            try:
                await page.goto(url)
                title = await page.title()
                return title
            finally:
                await page.close()
        
        # Use the pre-created pages to fetch titles in parallel
        tasks = [fetch_title_approach2(page_ctx, url) for page_ctx, url in all_pages]
        approach2_results = await asyncio.gather(*tasks)
        
        approach2_time = time.time() - start_time
        logger.info(f"Approach 2 time (get_pages + gather): {approach2_time:.2f}s", tag="TEST")
        
        # Compare results and performance
        speedup = approach1_time / approach2_time if approach2_time > 0 else 0
        pages_per_second = total_pages / approach2_time
        
        # Show a simple summary
        logger.info(f"📊 Summary: {num_browsers} browsers × {pages_per_browser} pages = {total_pages} total crawls", tag="TEST")
        logger.info(f"⚡ Performance: {pages_per_second:.1f} pages/second ({pages_per_second*60:.0f} pages/minute)", tag="TEST")
        logger.info(f"🚀 Total crawl time: {approach2_time:.2f} seconds", tag="TEST")
        
        if speedup > 1:
            logger.success(f"✅ Approach 2 (get_pages upfront) was {speedup:.2f}x faster", tag="TEST")
        else:
            logger.info(f"✅ Approach 1 (get_page + gather) was {1/speedup:.2f}x faster", tag="TEST")
        
        # Close all managers
        for manager in managers:
            await manager.close()
        
        return True
    
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", tag="TEST")
        # Clean up
        for manager in managers:
            try:
                await manager.close()
            except:
                pass
        return False

async def grid_search_optimal_configuration(total_urls=50):
    """Perform a grid search to find the optimal balance between number of browsers and pages per browser.
    
    This function tests different combinations of browser count and pages per browser,
    while keeping the total number of URLs constant. It measures performance metrics
    for each configuration to find the "sweet spot" that provides the best speed 
    with reasonable memory usage.
    
    Args:
        total_urls: Total number of URLs to crawl (default: 50)
    """
    logger.info(f"=== GRID SEARCH FOR OPTIMAL CRAWLING CONFIGURATION ({total_urls} URLs) ===", tag="TEST")
    
    # Generate test URLs once
    urls = [f"https://example.com/page_{i}" for i in range(total_urls)]
    
    # Define grid search configurations
    # We'll use more flexible approach: test all browser counts from 1 to min(20, total_urls)
    # and distribute pages evenly (some browsers may have 1 more page than others)
    configurations = []
    
    # Maximum number of browsers to test
    max_browsers_to_test = min(20, total_urls)
    
    # Try configurations with 1 to max_browsers_to_test browsers
    for num_browsers in range(1, max_browsers_to_test + 1):
        base_pages_per_browser = total_urls // num_browsers
        remainder = total_urls % num_browsers
        
        # Generate exact page distribution array
        if remainder > 0:
            # First 'remainder' browsers get one more page
            page_distribution = [base_pages_per_browser + 1] * remainder + [base_pages_per_browser] * (num_browsers - remainder)
            pages_distribution = f"{base_pages_per_browser+1} pages × {remainder} browsers, {base_pages_per_browser} pages × {num_browsers - remainder} browsers"
        else:
            # All browsers get the same number of pages
            page_distribution = [base_pages_per_browser] * num_browsers
            pages_distribution = f"{base_pages_per_browser} pages × {num_browsers} browsers"
        
        # Format the distribution as a tuple string like (4, 4, 3, 3)
        distribution_str = str(tuple(page_distribution))
            
        configurations.append((num_browsers, base_pages_per_browser, pages_distribution, page_distribution, distribution_str))
    
    # Track results
    results = []
    
    # Test each configuration
    for num_browsers, pages_per_browser, pages_distribution, page_distribution, distribution_str in configurations:
        logger.info("-" * 80, tag="TEST")
        logger.info(f"Testing configuration: {num_browsers} browsers with distribution: {distribution_str}", tag="TEST")
        logger.info(f"Details: {pages_distribution}", tag="TEST")
        # Sleep a bit for randomness
        await asyncio.sleep(0.5)
        
        try:
            # Import psutil for memory tracking
            try:
                import psutil
                process = psutil.Process()
                initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
            except ImportError:
                logger.warning("psutil not available, memory metrics will not be tracked", tag="TEST")
                initial_memory = 0
            
            # Create and start browser managers
            managers = []
            start_time = time.time()
            
            # Start all browsers in parallel
            start_tasks = []
            for i in range(num_browsers):
                browser_config = BrowserConfig(
                    headless=True
                )
                manager = BrowserManager(browser_config=browser_config, logger=logger)
                start_tasks.append(manager.start())
                managers.append(manager)
            
            await asyncio.gather(*start_tasks)
            browser_startup_time = time.time() - start_time
            
            # Measure memory after browser startup
            if initial_memory > 0:
                browser_memory = process.memory_info().rss / (1024 * 1024) - initial_memory
            else:
                browser_memory = 0
            
            # Distribute URLs among managers using the exact page distribution
            urls_per_manager = {}
            total_assigned = 0
            
            for i, manager in enumerate(managers):
                if i < len(page_distribution):
                    # Get the exact number of pages for this browser from our distribution
                    manager_pages = page_distribution[i]
                    
                    # Get the URL slice for this manager
                    start_idx = total_assigned
                    end_idx = start_idx + manager_pages
                    urls_per_manager[manager] = urls[start_idx:end_idx]
                    total_assigned += manager_pages
                else:
                    # If we have more managers than our distribution (should never happen)
                    urls_per_manager[manager] = []
            
            # Use the more efficient approach (pre-created pages)
            logger.info("Running page crawling test...", tag="TEST")
            crawl_start_time = time.time()
            
            # Get all pages upfront for each manager
            all_pages = []
            for manager, manager_urls in urls_per_manager.items():
                if not manager_urls:  # Skip managers with no URLs
                    continue
                crawler_config = CrawlerRunConfig()
                pages = await manager.get_pages(crawler_config, count=len(manager_urls))
                all_pages.extend(zip(pages, manager_urls))
            
            # Measure memory after page creation
            if initial_memory > 0:
                pages_memory = process.memory_info().rss / (1024 * 1024) - browser_memory - initial_memory
            else:
                pages_memory = 0
                
            # Function to crawl a URL with a pre-created page
            async def fetch_title(page_ctx, url):
                page, _ = page_ctx
                try:
                    await page.goto(url)
                    title = await page.title()
                    return title
                finally:
                    await page.close()
            
            # Use the pre-created pages to fetch titles in parallel
            tasks = [fetch_title(page_ctx, url) for page_ctx, url in all_pages]
            crawl_results = await asyncio.gather(*tasks)
            
            crawl_time = time.time() - crawl_start_time
            total_time = time.time() - start_time
            
            # Final memory measurement
            if initial_memory > 0:
                peak_memory = max(browser_memory + pages_memory, process.memory_info().rss / (1024 * 1024) - initial_memory)
            else:
                peak_memory = 0
                
            # Close all managers
            for manager in managers:
                await manager.close()
                
            # Calculate metrics
            pages_per_second = total_urls / crawl_time
            
            # Store result metrics
            result = {
                "num_browsers": num_browsers,
                "pages_per_browser": pages_per_browser,
                "page_distribution": page_distribution,
                "distribution_str": distribution_str,
                "total_urls": total_urls,
                "browser_startup_time": browser_startup_time,
                "crawl_time": crawl_time,
                "total_time": total_time,
                "browser_memory": browser_memory,
                "pages_memory": pages_memory,
                "peak_memory": peak_memory,
                "pages_per_second": pages_per_second,
                # Calculate efficiency score (higher is better)
                # This balances speed vs memory usage
                "efficiency_score": pages_per_second / (peak_memory + 1) if peak_memory > 0 else pages_per_second,
            }
            
            results.append(result)
            
            # Log the results
            logger.info(f"Browser startup: {browser_startup_time:.2f}s", tag="TEST")
            logger.info(f"Crawl time: {crawl_time:.2f}s", tag="TEST")
            logger.info(f"Total time: {total_time:.2f}s", tag="TEST")
            logger.info(f"Performance: {pages_per_second:.1f} pages/second", tag="TEST")
            
            if peak_memory > 0:
                logger.info(f"Browser memory: {browser_memory:.1f}MB", tag="TEST")
                logger.info(f"Pages memory: {pages_memory:.1f}MB", tag="TEST")
                logger.info(f"Peak memory: {peak_memory:.1f}MB", tag="TEST")
                logger.info(f"Efficiency score: {result['efficiency_score']:.6f}", tag="TEST")
                
        except Exception as e:
            logger.error(f"Error testing configuration: {str(e)}", tag="TEST")
            import traceback
            traceback.print_exc()
            
            # Clean up
            for manager in managers:
                try:
                    await manager.close()
                except:
                    pass
                    
    # Print summary of all configurations
    logger.info("=" * 100, tag="TEST")
    logger.info("GRID SEARCH RESULTS SUMMARY", tag="TEST")
    logger.info("=" * 100, tag="TEST")
    
    # Rank configurations by efficiency score
    ranked_results = sorted(results, key=lambda x: x["efficiency_score"], reverse=True)
    
    # Also determine rankings by different metrics
    fastest = sorted(results, key=lambda x: x["crawl_time"])[0]
    lowest_memory = sorted(results, key=lambda x: x["peak_memory"] if x["peak_memory"] > 0 else float('inf'))[0]
    most_efficient = ranked_results[0]
    
    # Print top performers by category
    logger.info("🏆 TOP PERFORMERS BY CATEGORY:", tag="TEST")
    logger.info(f"⚡ Fastest: {fastest['num_browsers']} browsers × ~{fastest['pages_per_browser']} pages " + 
                f"({fastest['crawl_time']:.2f}s, {fastest['pages_per_second']:.1f} pages/s)", tag="TEST")
    
    if lowest_memory["peak_memory"] > 0:
        logger.info(f"💾 Lowest memory: {lowest_memory['num_browsers']} browsers × ~{lowest_memory['pages_per_browser']} pages " +
                    f"({lowest_memory['peak_memory']:.1f}MB)", tag="TEST")
    
    logger.info(f"🌟 Most efficient: {most_efficient['num_browsers']} browsers × ~{most_efficient['pages_per_browser']} pages " +
                f"(score: {most_efficient['efficiency_score']:.6f})", tag="TEST")
    
    # Print result table header
    logger.info("\n📊 COMPLETE RANKING TABLE (SORTED BY EFFICIENCY SCORE):", tag="TEST")
    logger.info("-" * 120, tag="TEST")
    
    # Define table header
    header = f"{'Rank':<5} | {'Browsers':<8} | {'Distribution':<55} | {'Total Time(s)':<12} | {'Speed(p/s)':<12} | {'Memory(MB)':<12} | {'Efficiency':<10} | {'Notes'}"
    logger.info(header, tag="TEST")
    logger.info("-" * 120, tag="TEST")
    
    # Print each configuration in ranked order
    for rank, result in enumerate(ranked_results, 1):
        # Add special notes for top performers
        notes = []
        if result == fastest:
            notes.append("⚡ Fastest")
        if result == lowest_memory:
            notes.append("💾 Lowest Memory")
        if result == most_efficient:
            notes.append("🌟 Most Efficient")
        
        notes_str = " | ".join(notes) if notes else ""
        
        # Format memory if available
        memory_str = f"{result['peak_memory']:.1f}" if result['peak_memory'] > 0 else "N/A"
        
        # Get the distribution string
        dist_str = result.get('distribution_str', str(tuple([result['pages_per_browser']] * result['num_browsers'])))
        
        # Build the row
        row = f"{rank:<5} | {result['num_browsers']:<8} | {dist_str:<55} | {result['total_time']:.2f}s{' ':<7} | "
        row += f"{result['pages_per_second']:.2f}{' ':<6} | {memory_str}{' ':<6} | {result['efficiency_score']:.4f}{' ':<4} | {notes_str}"
        
        logger.info(row, tag="TEST")
    
    logger.info("-" * 120, tag="TEST")
    
    # Generate visualization if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Extract data for plotting from ranked results
        browser_counts = [r["num_browsers"] for r in ranked_results]
        efficiency_scores = [r["efficiency_score"] for r in ranked_results]
        crawl_times = [r["crawl_time"] for r in ranked_results]
        total_times = [r["total_time"] for r in ranked_results]
        
        # Filter results with memory data
        memory_results = [r for r in ranked_results if r["peak_memory"] > 0]
        memory_browser_counts = [r["num_browsers"] for r in memory_results]
        peak_memories = [r["peak_memory"] for r in memory_results]
        
        # Create figure with clean design
        plt.figure(figsize=(14, 12), facecolor='white')
        plt.style.use('ggplot')
        
        # Create grid for subplots
        gs = plt.GridSpec(3, 1, height_ratios=[1, 1, 1], hspace=0.3)
        
        # Plot 1: Efficiency Score (higher is better)
        ax1 = plt.subplot(gs[0])
        bar_colors = ['#3498db'] * len(browser_counts)
        
        # Highlight the most efficient
        most_efficient_idx = browser_counts.index(most_efficient["num_browsers"])
        bar_colors[most_efficient_idx] = '#e74c3c'  # Red for most efficient
        
        bars = ax1.bar(range(len(browser_counts)), efficiency_scores, color=bar_colors)
        ax1.set_xticks(range(len(browser_counts)))
        ax1.set_xticklabels([f"{bc}" for bc in browser_counts], rotation=45)
        ax1.set_xlabel('Number of Browsers')
        ax1.set_ylabel('Efficiency Score (higher is better)')
        ax1.set_title('Browser Configuration Efficiency (higher is better)')
        
        # Add value labels on top of bars
        for bar, score in zip(bars, efficiency_scores):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02*max(efficiency_scores),
                    f'{score:.3f}', ha='center', va='bottom', rotation=90, fontsize=8)
        
        # Highlight best configuration
        ax1.text(0.02, 0.90, f"🌟 Most Efficient: {most_efficient['num_browsers']} browsers with ~{most_efficient['pages_per_browser']} pages",
                transform=ax1.transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))
        
        # Plot 2: Time Performance
        ax2 = plt.subplot(gs[1])
        
        # Plot both total time and crawl time
        ax2.plot(browser_counts, crawl_times, 'bo-', label='Crawl Time (s)', linewidth=2)
        ax2.plot(browser_counts, total_times, 'go--', label='Total Time (s)', linewidth=2, alpha=0.6)
        
        # Mark the fastest configuration
        fastest_idx = browser_counts.index(fastest["num_browsers"])
        ax2.plot(browser_counts[fastest_idx], crawl_times[fastest_idx], 'ro', ms=10, 
                label=f'Fastest: {fastest["num_browsers"]} browsers')
        
        ax2.set_xlabel('Number of Browsers')
        ax2.set_ylabel('Time (seconds)')
        ax2.set_title(f'Time Performance for {total_urls} URLs by Browser Count')
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend(loc='upper right')
        
        # Plot pages per second on second y-axis
        pages_per_second = [total_urls/t for t in crawl_times]
        ax2_twin = ax2.twinx()
        ax2_twin.plot(browser_counts, pages_per_second, 'r^--', label='Pages/second', alpha=0.5)
        ax2_twin.set_ylabel('Pages per second')
        
        # Add note about the fastest configuration
        ax2.text(0.02, 0.90, f"⚡ Fastest: {fastest['num_browsers']} browsers with ~{fastest['pages_per_browser']} pages" +
                f"\n   {fastest['crawl_time']:.2f}s ({fastest['pages_per_second']:.1f} pages/s)",
                transform=ax2.transAxes, fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.3))
        
        # Plot 3: Memory Usage (if available)
        if memory_results:
            ax3 = plt.subplot(gs[2])
            
            # Prepare data for grouped bar chart
            memory_per_browser = [m/n for m, n in zip(peak_memories, memory_browser_counts)]
            memory_per_page = [m/(n*p) for m, n, p in zip(
                [r["peak_memory"] for r in memory_results],
                [r["num_browsers"] for r in memory_results],
                [r["pages_per_browser"] for r in memory_results])]
            
            x = np.arange(len(memory_browser_counts))
            width = 0.35
            
            # Create grouped bars
            ax3.bar(x - width/2, peak_memories, width, label='Total Memory (MB)', color='#9b59b6')
            ax3.bar(x + width/2, memory_per_browser, width, label='Memory per Browser (MB)', color='#3498db')
            
            # Configure axis
            ax3.set_xticks(x)
            ax3.set_xticklabels([f"{bc}" for bc in memory_browser_counts], rotation=45)
            ax3.set_xlabel('Number of Browsers')
            ax3.set_ylabel('Memory (MB)')
            ax3.set_title('Memory Usage by Browser Configuration')
            ax3.legend(loc='upper left')
            ax3.grid(True, linestyle='--', alpha=0.7)
            
            # Add second y-axis for memory per page
            ax3_twin = ax3.twinx()
            ax3_twin.plot(x, memory_per_page, 'ro-', label='Memory per Page (MB)')
            ax3_twin.set_ylabel('Memory per Page (MB)')
            
            # Get lowest memory configuration
            lowest_memory_idx = memory_browser_counts.index(lowest_memory["num_browsers"])
            
            # Add note about lowest memory configuration
            ax3.text(0.02, 0.90, f"💾 Lowest Memory: {lowest_memory['num_browsers']} browsers with ~{lowest_memory['pages_per_browser']} pages" +
                    f"\n   {lowest_memory['peak_memory']:.1f}MB ({lowest_memory['peak_memory']/total_urls:.2f}MB per page)",
                    transform=ax3.transAxes, fontsize=12, verticalalignment='top',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.3))
        
        # Add overall title
        plt.suptitle(f'Browser Scaling Grid Search Results for {total_urls} URLs', fontsize=16, y=0.98)
        
        # Add timestamp and info at the bottom
        plt.figtext(0.5, 0.01, f"Generated by Crawl4AI at {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                   ha="center", fontsize=10, style='italic')
        
        # Get current directory and save the figure there
        import os
        __current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(__current_file)
        output_file = os.path.join(current_dir, 'browser_scaling_grid_search.png')
        
        # Adjust layout and save figure with high DPI
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        plt.savefig(output_file, dpi=200, bbox_inches='tight')
        logger.success(f"Visualization saved to {output_file}", tag="TEST")
        
    except ImportError:
        logger.warning("matplotlib not available, skipping visualization", tag="TEST")
    
    return most_efficient["num_browsers"], most_efficient["pages_per_browser"]
    
async def find_optimal_browser_config(total_urls=50, verbose=True, rate_limit_delay=0.2):
    """Find optimal browser configuration for crawling a specific number of URLs.
    
    Args:
        total_urls: Number of URLs to crawl
        verbose: Whether to print progress
        rate_limit_delay: Delay between page loads to avoid rate limiting
        
    Returns:
        dict: Contains fastest, lowest_memory, and optimal configurations
    """
    if verbose:
        print(f"\n=== Finding optimal configuration for crawling {total_urls} URLs ===\n")
    
    # Generate test URLs with timestamp to avoid caching
    timestamp = int(time.time())
    urls = [f"https://example.com/page_{i}?t={timestamp}" for i in range(total_urls)]
    
    # Limit browser configurations to test (1 browser to max 10)
    max_browsers = min(10, total_urls)
    configs_to_test = []
    
    # Generate configurations (browser count, pages distribution)
    for num_browsers in range(1, max_browsers + 1):
        base_pages = total_urls // num_browsers
        remainder = total_urls % num_browsers
        
        # Create distribution array like [3, 3, 2, 2] (some browsers get one more page)
        if remainder > 0:
            distribution = [base_pages + 1] * remainder + [base_pages] * (num_browsers - remainder)
        else:
            distribution = [base_pages] * num_browsers
            
        configs_to_test.append((num_browsers, distribution))
    
    results = []
    
    # Test each configuration
    for browser_count, page_distribution in configs_to_test:
        if verbose:
            print(f"Testing {browser_count} browsers with distribution {tuple(page_distribution)}")
        
        try:
            # Track memory if possible
            try:
                import psutil
                process = psutil.Process()
                start_memory = process.memory_info().rss / (1024 * 1024)  # MB
            except ImportError:
                if verbose: 
                    print("Memory tracking not available (psutil not installed)")
                start_memory = 0
            
            # Start browsers in parallel
            managers = []
            start_tasks = []
            start_time = time.time()
            
            for i in range(browser_count):
                config = BrowserConfig(headless=True)
                manager = BrowserManager(browser_config=config, logger=logger)
                start_tasks.append(manager.start())
                managers.append(manager)
            
            await asyncio.gather(*start_tasks)
            
            # Distribute URLs among browsers
            urls_per_manager = {}
            url_index = 0
            
            for i, manager in enumerate(managers):
                pages_for_this_browser = page_distribution[i]
                end_index = url_index + pages_for_this_browser
                urls_per_manager[manager] = urls[url_index:end_index]
                url_index = end_index
            
            # Create pages for each browser
            all_pages = []
            for manager, manager_urls in urls_per_manager.items():
                if not manager_urls:
                    continue
                pages = await manager.get_pages(CrawlerRunConfig(), count=len(manager_urls))
                all_pages.extend(zip(pages, manager_urls))
            
            # Crawl pages with delay to avoid rate limiting
            async def crawl_page(page_ctx, url):
                page, _ = page_ctx
                try:
                    await page.goto(url)
                    if rate_limit_delay > 0:
                        await asyncio.sleep(rate_limit_delay)
                    title = await page.title()
                    return title
                finally:
                    await page.close()
            
            crawl_start = time.time()
            crawl_tasks = [crawl_page(page_ctx, url) for page_ctx, url in all_pages]
            await asyncio.gather(*crawl_tasks)
            crawl_time = time.time() - crawl_start
            total_time = time.time() - start_time
            
            # Measure final memory usage
            if start_memory > 0:
                end_memory = process.memory_info().rss / (1024 * 1024)
                memory_used = end_memory - start_memory
            else:
                memory_used = 0
            
            # Close all browsers
            for manager in managers:
                await manager.close()
            
            # Calculate metrics
            pages_per_second = total_urls / crawl_time
            
            # Calculate efficiency score (higher is better)
            # This balances speed vs memory
            if memory_used > 0:
                efficiency = pages_per_second / (memory_used + 1)
            else:
                efficiency = pages_per_second
            
            # Store result
            result = {
                "browser_count": browser_count,
                "distribution": tuple(page_distribution),
                "crawl_time": crawl_time,
                "total_time": total_time,
                "memory_used": memory_used,
                "pages_per_second": pages_per_second, 
                "efficiency": efficiency
            }
            
            results.append(result)
            
            if verbose:
                print(f"  ✓ Crawled {total_urls} pages in {crawl_time:.2f}s ({pages_per_second:.1f} pages/sec)")
                if memory_used > 0:
                    print(f"  ✓ Memory used: {memory_used:.1f}MB ({memory_used/total_urls:.1f}MB per page)")
                print(f"  ✓ Efficiency score: {efficiency:.4f}")
            
        except Exception as e:
            if verbose:
                print(f"  ✗ Error: {str(e)}")
            
            # Clean up
            for manager in managers:
                try:
                    await manager.close()
                except:
                    pass
    
    # If no successful results, return None
    if not results:
        return None
    
    # Find best configurations
    fastest = sorted(results, key=lambda x: x["crawl_time"])[0]
    
    # Only consider memory if available
    memory_results = [r for r in results if r["memory_used"] > 0]
    if memory_results:
        lowest_memory = sorted(memory_results, key=lambda x: x["memory_used"])[0]
    else:
        lowest_memory = fastest
    
    # Find most efficient (balanced speed vs memory)
    optimal = sorted(results, key=lambda x: x["efficiency"], reverse=True)[0]
    
    # Print summary
    if verbose:
        print("\n=== OPTIMAL CONFIGURATIONS ===")
        print(f"⚡ Fastest: {fastest['browser_count']} browsers {fastest['distribution']}")
        print(f"   {fastest['crawl_time']:.2f}s, {fastest['pages_per_second']:.1f} pages/sec")
        
        print(f"💾 Memory-efficient: {lowest_memory['browser_count']} browsers {lowest_memory['distribution']}")
        if lowest_memory["memory_used"] > 0:
            print(f"   {lowest_memory['memory_used']:.1f}MB, {lowest_memory['memory_used']/total_urls:.2f}MB per page")
        
        print(f"🌟 Balanced optimal: {optimal['browser_count']} browsers {optimal['distribution']}")
        print(f"   {optimal['crawl_time']:.2f}s, {optimal['pages_per_second']:.1f} pages/sec, score: {optimal['efficiency']:.4f}")
    
    return {
        "fastest": fastest,
        "lowest_memory": lowest_memory,
        "optimal": optimal,
        "all_configs": results
    }

async def run_tests():
    """Run all tests sequentially."""
    results = []
    
    # Find optimal configuration using our utility function
    configs = await find_optimal_browser_config(
        total_urls=20,  # Use a small number for faster testing
        verbose=True,
        rate_limit_delay=0.2  # 200ms delay between page loads to avoid rate limiting
    )
    
    if configs:
        # Show the optimal configuration
        optimal = configs["optimal"]
        print(f"\n🎯 Recommended configuration for production use:")
        print(f"   {optimal['browser_count']} browsers with distribution {optimal['distribution']}")
        print(f"   Estimated performance: {optimal['pages_per_second']:.1f} pages/second")
        results.append(True)
    else:
        print("\n❌ Failed to find optimal configuration")
        results.append(False)
    
    # Print summary
    total = len(results)
    passed = sum(results)
    print(f"\nTests complete: {passed}/{total} passed")
    
    if passed == total:
        print("All tests passed!")
    else:
        print(f"{total - passed} tests failed")

if __name__ == "__main__":
    asyncio.run(run_tests())