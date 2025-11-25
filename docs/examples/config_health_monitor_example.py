"""
Example: Using ConfigHealthMonitor for Crawler Configuration Health Monitoring

This example demonstrates how to:
1. Initialize a ConfigHealthMonitor
2. Register multiple crawler configurations
3. Set up custom resolution strategies
4. Monitor health status and metrics
5. Handle configuration failures automatically
"""

import asyncio
import copy
from crawl4ai.config_health_monitor import ConfigHealthMonitor, ResolutionResult, ConfigHealthState
from crawl4ai import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_configs import CacheMode


# ============================================================================
# Custom Resolution Strategies
# ============================================================================

async def incremental_backoff_strategy(
    state: ConfigHealthState,
    monitor: ConfigHealthMonitor
) -> ResolutionResult:
    """
    Increase timeouts progressively when health checks fail.
    """
    print(f"  Applying incremental backoff for '{state.config_id}'...")
    
    new_config = copy.deepcopy(state.config)
    
    # Increase timeouts by 100%
    new_config.page_timeout = int(state.config.page_timeout * 2)
    if state.config.delay_before_return_html:
        new_config.delay_before_return_html = state.config.delay_before_return_html + 2.0
    
    print(f"     -> Increased page_timeout to {new_config.page_timeout}ms")
    
    return ResolutionResult(
        success=True,
        action="timeout_increased",
        modified_config=new_config,
        metadata={
            "old_timeout": state.config.page_timeout,
            "new_timeout": new_config.page_timeout
        }
    )


async def toggle_magic_mode_strategy(
    state: ConfigHealthState,
    monitor: ConfigHealthMonitor
) -> ResolutionResult:
    """
    Enable/disable magic mode for anti-bot handling.
    """
    print(f"  Toggling magic mode for '{state.config_id}'...")
    
    new_config = copy.deepcopy(state.config)
    new_config.magic = not state.config.magic
    
    action = f"magic_{'enabled' if new_config.magic else 'disabled'}"
    print(f"     -> Magic mode now: {new_config.magic}")
    
    return ResolutionResult(
        success=True,
        action=action,
        modified_config=new_config
    )


async def log_and_alert_strategy(
    state: ConfigHealthState,
    monitor: ConfigHealthMonitor
) -> ResolutionResult:
    """
    Log failure and send alert (in production, this would send to monitoring system).
    """
    print(f"  ALERT: Config '{state.config_id}' has failed!")
    print(f"     → Error: {state.last_error}")
    print(f"     → Consecutive failures: {state.consecutive_failures}")
    print(f"     → Resolution attempts: {state.resolution_attempts}")
    
    # In production, send to Slack, email, PagerDuty, etc.
    # await send_slack_alert(state)
    # await send_email_alert(state)
    
    return ResolutionResult(
        success=False,
        action="alerted",
        metadata={"alert_sent": True}
    )


def create_resolution_chain(strategies):
    """
    Create a resolution chain that tries strategies sequentially.
    
    After each successful strategy we immediately run a health check. If the
    check still fails, we continue to the next strategy until one succeeds or
    we exhaust the chain.
    """
    async def chained_strategy(
        state: ConfigHealthState,
        monitor: ConfigHealthMonitor
    ) -> ResolutionResult:
        if not strategies:
            return ResolutionResult(success=False, action="no_strategies_configured")
        
        print(f"\nStarting resolution chain for '{state.config_id}'")
        
        steps_metadata = []
        
        for i, strategy in enumerate(strategies, 1):
            print(f"\n  Step {i}/{len(strategies)}: {strategy.__name__}")
            result = await strategy(state, monitor)
            steps_metadata.append({
                "step": i,
                "strategy": strategy.__name__,
                "success": result.success,
                "action": result.action,
                "metadata": result.metadata
            })
            
            if result.success:
                action_label = result.action or strategy.__name__
                print(f"  Resolution applied: {action_label}")
                
                if result.modified_config:
                    state.config = result.modified_config
                
                print("  Running validation health check...")
                try:
                    validation_passed = await monitor._perform_health_check(state)
                except Exception as exc:
                    print(f"  Validation error: {exc}")
                    validation_passed = False
                
                steps_metadata[-1]["validation_passed"] = validation_passed
                
                if validation_passed:
                    print("  Validation succeeded. Resolution chain complete.")
                    return ResolutionResult(
                        success=True,
                        action=action_label,
                        modified_config=state.config,
                        metadata={"steps": steps_metadata}
                    )
                
                print("  Validation failed. Trying next strategy...")
            else:
                print(f"  Resolution failed: {result.action}")
        
        print(f"\n  All resolution strategies failed")
        return ResolutionResult(
            success=False,
            action="all_strategies_failed",
            metadata={"steps": steps_metadata}
        )
    
    return chained_strategy


# ============================================================================
# Main Example
# ============================================================================

async def main():
    print("=" * 70)
    print("ConfigHealthMonitor Example")
    print("=" * 70)
    
    # Initialize monitor
    print("\nInitializing ConfigHealthMonitor...")
    monitor = ConfigHealthMonitor(
        browser_config=BrowserConfig(
            headless=True,
            verbose=False
        ),
        check_interval=15.0,  # Check every 15 seconds
        failure_threshold=2,   # Trigger resolution after 2 failures
        resolution_retry_limit=2,  # Try resolution twice max
        enable_metrics=True
    )
    
    await monitor.start()
    print(f"   Monitor started (check_interval={monitor.check_interval}s)")
    
    # ========================================================================
    # Register Configurations
    # ========================================================================
    
    print("\nRegistering configurations...")
    
    # Config 1: Reliable website (should stay healthy)
    config_1_id = monitor.register_config(
        config=CrawlerRunConfig(
            page_timeout=30000,
            cache_mode=CacheMode.BYPASS,
            magic=True,
        ),
        test_url="https://www.olly.com/",
        config_id="olly_scraper",
        resolution_strategy=create_resolution_chain([
            toggle_magic_mode_strategy,
        ])
    )
    print(f"   Registered: {config_1_id} with resolution chain")
    
    # Config 2: Another reliable website
    config_2_id = monitor.register_config(
        config=CrawlerRunConfig(
            page_timeout=20000,
            magic=True,
        ),
        test_url="https://example.com",
        config_id="example_scraper"
    )
    print(f"   Registered: {config_2_id}")
    
    # Config 3: Intentionally problematic (very short timeout)
    # This will trigger resolution strategies
    config_3_id = monitor.register_config(
        config=CrawlerRunConfig(
            page_timeout=100,  # 100ms - will likely timeout
            cache_mode=CacheMode.BYPASS,
        ),
        test_url="https://httpbin.org/delay/5",  # Delays response by 5 seconds
        config_id="impossible_scraper",
        resolution_strategy=create_resolution_chain([
            incremental_backoff_strategy,
            toggle_magic_mode_strategy,
            log_and_alert_strategy
        ])
    )
    print(f"   Registered: {config_3_id} (with resolution chain)")
    
    print(f"\n   Total configs registered: {monitor.registered_count}")
    
    # ========================================================================
    # Perform Manual Health Checks
    # ========================================================================
    
    print("\nPerforming initial health checks...")
    
    for config_id in [config_1_id, config_2_id, config_3_id]:
        is_healthy = await monitor.check_health(config_id)
        status = monitor.get_health_status(config_id)
        
        status_label = "healthy" if is_healthy else "unhealthy"
        print(f"   {config_id}: {status.status} ({status_label})")
        if not is_healthy:
            print(f"      Error: {status.last_error}")
    
    # ========================================================================
    # Monitor for a Period
    # ========================================================================
    
    print("\nMonitoring for 60 seconds (background loop running)...")
    print("   The monitor will automatically check all configs every 15s")
    print("   and apply resolution strategies when failures are detected.\n")
    
    # Check status every 20 seconds
    for i in range(3):
        await asyncio.sleep(20)
        
        print(f"\nStatus Check #{i+1}")
        print("-" * 70)
        
        all_statuses = monitor.get_health_status()
        
        for config_id, state in all_statuses.items():
            # Status emoji
            print(f"\n{config_id}")
            print(f"   Status: {state.status}")
            print(f"   Consecutive failures: {state.consecutive_failures}")
            print(f"   Consecutive successes: {state.consecutive_successes}")
            print(f"   Resolution attempts: {state.resolution_attempts}")
            
            if state.last_check_time:
                print(f"   Last checked: {state.last_check_time.strftime('%H:%M:%S')}")
            if state.last_success_time:
                print(f"   Last success: {state.last_success_time.strftime('%H:%M:%S')}")
            if state.last_error:
                print(f"   Last error: {state.last_error[:100]}...")
    
    # ========================================================================
    # Final Metrics Report
    # ========================================================================
    
    print("\n" + "=" * 70)
    print("Final Metrics Report")
    print("=" * 70)
    
    metrics = monitor.get_metrics()
    
    # Global metrics
    print("\nGlobal Metrics:")
    print(f"   Total checks: {metrics['total_checks']}")
    print(f"   Successful checks: {metrics['successful_checks']}")
    print(f"   Failed checks: {metrics['failed_checks']}")
    print(f"   Success rate: {metrics['success_rate']:.1%}")
    print(f"   Total resolutions: {metrics['total_resolutions']}")
    print(f"   Successful resolutions: {metrics['successful_resolutions']}")
    if metrics['total_resolutions'] > 0:
        print(f"   Resolution success rate: {metrics['resolution_success_rate']:.1%}")
    print(f"   Uptime: {metrics['uptime_seconds']:.1f}s")
    
    # Per-config metrics
    print("\nPer-Config Metrics:")
    for config_id, config_metrics in metrics['configs'].items():
        print(f"\n   {config_id}:")
        print(f"      Status: {config_metrics['status']}")
        print(f"      Uptime: {config_metrics['uptime_percent']:.1f}%")
        print(f"      Avg response time: {config_metrics['avg_response_time']:.3f}s")
        print(f"      Total checks: {config_metrics['total_checks']}")
        print(f"      Successful: {config_metrics['successful_checks']}")
        print(f"      Failed: {config_metrics['failed_checks']}")
        print(f"      Resolution attempts: {config_metrics['resolution_attempts']}")
    
    # ========================================================================
    # Cleanup
    # ========================================================================
    
    print("\nStopping monitor...")
    await monitor.stop()
    print("   Monitor stopped successfully")
    
    print("\n" + "=" * 70)
    print("Example completed!")
    print("=" * 70)


# ============================================================================
# Alternative: Using Context Manager
# ============================================================================

async def example_with_context_manager():
    """
    Simplified example using context manager for automatic cleanup.
    """
    print("\nExample: Using Context Manager\n")
    
    async with ConfigHealthMonitor(
        browser_config=BrowserConfig(headless=True, verbose=False),
        check_interval=30.0,
        failure_threshold=3
    ) as monitor:
        
        # Register configs
        monitor.register_config(
            config=CrawlerRunConfig(page_timeout=30000),
            test_url="https://httpbin.org/html",
            config_id="example"
        )
        
        # Monitor automatically runs in background
        print("Monitor running...")
        await asyncio.sleep(10)
        
        # Get status
        status = monitor.get_health_status("example")
        print(f"Status: {status.status}")
        
        # Context manager automatically stops on exit
    
    print("Monitor automatically stopped")


if __name__ == "__main__":
    # Run main example
    asyncio.run(main())
    
    # Uncomment to run context manager example
    # asyncio.run(example_with_context_manager())

