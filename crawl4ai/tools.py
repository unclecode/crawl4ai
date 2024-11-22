import time
import cProfile
import pstats
from functools import wraps

def profile_and_time(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Start timer
        start_time = time.perf_counter()
        
        # Setup profiler
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Run function
        result = func(self, *args, **kwargs)
        
        # Stop profiler
        profiler.disable()
        
        # Calculate elapsed time
        elapsed_time = time.perf_counter() - start_time
        
        # Print timing
        print(f"[PROFILER] Scraping completed in {elapsed_time:.2f} seconds")
        
        # Print profiling stats
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')  # Sort by cumulative time
        stats.print_stats(20)  # Print top 20 time-consuming functions
        
        return result
    return wrapper