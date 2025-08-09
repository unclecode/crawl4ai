#!/usr/bin/env python3
"""Test script to verify macOS memory calculation accuracy."""

import psutil
import platform
import time
from crawl4ai.memory_utils import get_true_memory_usage_percent, get_memory_stats, get_true_available_memory_gb


def test_memory_calculation():
    """Test and compare memory calculations."""
    print(f"Platform: {platform.system()}")
    print(f"Python version: {platform.python_version()}")
    print("-" * 60)
    
    # Get psutil's view
    vm = psutil.virtual_memory()
    psutil_percent = vm.percent
    psutil_available_gb = vm.available / (1024**3)
    total_gb = vm.total / (1024**3)
    
    # Get our corrected view
    true_percent = get_true_memory_usage_percent()
    true_available_gb = get_true_available_memory_gb()
    true_percent_calc, available_calc, total_calc = get_memory_stats()
    
    print("Memory Statistics Comparison:")
    print(f"Total Memory: {total_gb:.2f} GB")
    print()
    
    print("PSUtil (Standard) Calculation:")
    print(f"  - Memory Used: {psutil_percent:.1f}%")
    print(f"  - Available: {psutil_available_gb:.2f} GB")
    print()
    
    print("Platform-Aware Calculation:")
    print(f"  - Memory Used: {true_percent:.1f}%")
    print(f"  - Available: {true_available_gb:.2f} GB")
    print(f"  - Difference: {true_available_gb - psutil_available_gb:.2f} GB of reclaimable memory")
    print()
    
    # Show the impact on dispatcher behavior
    print("Impact on MemoryAdaptiveDispatcher:")
    thresholds = {
        "Normal": 90.0,
        "Critical": 95.0,
        "Recovery": 85.0
    }
    
    for name, threshold in thresholds.items():
        psutil_triggered = psutil_percent >= threshold
        true_triggered = true_percent >= threshold
        print(f"  - {name} Threshold ({threshold}%):")
        print(f"    PSUtil: {'TRIGGERED' if psutil_triggered else 'OK'}")
        print(f"    Platform-Aware: {'TRIGGERED' if true_triggered else 'OK'}")
        if psutil_triggered != true_triggered:
            print(f"    → Difference: Platform-aware prevents false {'pressure' if psutil_triggered else 'recovery'}")
    print()
    
    # Monitor for a few seconds
    print("Monitoring memory for 10 seconds...")
    for i in range(10):
        vm = psutil.virtual_memory()
        true_pct = get_true_memory_usage_percent()
        print(f"  {i+1}s - PSUtil: {vm.percent:.1f}% | Platform-Aware: {true_pct:.1f}%", end="\r")
        time.sleep(1)
    print("\n")


if __name__ == "__main__":
    test_memory_calculation()