import psutil
import platform
import subprocess
from typing import Tuple


def get_true_available_memory_gb() -> float:
    """Get truly available memory including inactive pages (cross-platform)"""
    vm = psutil.virtual_memory()

    if platform.system() == 'Darwin':  # macOS
        # On macOS, we need to include inactive memory too
        try:
            # Use vm_stat to get accurate values
            result = subprocess.run(['vm_stat'], capture_output=True, text=True)
            lines = result.stdout.split('\n')

            page_size = 16384  # macOS page size
            pages = {}

            for line in lines:
                if 'Pages free:' in line:
                    pages['free'] = int(line.split()[-1].rstrip('.'))
                elif 'Pages inactive:' in line:
                    pages['inactive'] = int(line.split()[-1].rstrip('.'))
                elif 'Pages speculative:' in line:
                    pages['speculative'] = int(line.split()[-1].rstrip('.'))
                elif 'Pages purgeable:' in line:
                    pages['purgeable'] = int(line.split()[-1].rstrip('.'))

            # Calculate total available (free + inactive + speculative + purgeable)
            total_available_pages = (
                pages.get('free', 0) + 
                pages.get('inactive', 0) + 
                pages.get('speculative', 0) + 
                pages.get('purgeable', 0)
            )
            available_gb = (total_available_pages * page_size) / (1024**3)

            return available_gb
        except:
            # Fallback to psutil
            return vm.available / (1024**3)
    else:
        # For Windows and Linux, psutil.available is accurate
        return vm.available / (1024**3)


def get_true_memory_usage_percent() -> float:
    """
    Get memory usage percentage that accounts for platform differences.
    
    Returns:
        float: Memory usage percentage (0-100)
    """
    vm = psutil.virtual_memory()
    total_gb = vm.total / (1024**3)
    available_gb = get_true_available_memory_gb()
    
    # Calculate used percentage based on truly available memory
    used_percent = 100.0 * (total_gb - available_gb) / total_gb
    
    # Ensure it's within valid range
    return max(0.0, min(100.0, used_percent))


def get_memory_stats() -> Tuple[float, float, float]:
    """
    Get comprehensive memory statistics.
    
    Returns:
        Tuple[float, float, float]: (used_percent, available_gb, total_gb)
    """
    vm = psutil.virtual_memory()
    total_gb = vm.total / (1024**3)
    available_gb = get_true_available_memory_gb()
    used_percent = get_true_memory_usage_percent()
    
    return used_percent, available_gb, total_gb