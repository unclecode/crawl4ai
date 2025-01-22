import time, re
from crawl4ai.content_scraping_strategy import WebScrapingStrategy,  LXMLWebScrapingStrategy
import time
import functools
from collections import defaultdict

class TimingStats:
    def __init__(self):
        self.stats = defaultdict(lambda: defaultdict(lambda: {"calls": 0, "total_time": 0}))
        
    def add(self, strategy_name, func_name, elapsed):
        self.stats[strategy_name][func_name]["calls"] += 1
        self.stats[strategy_name][func_name]["total_time"] += elapsed
        
    def report(self):
        for strategy_name, funcs in self.stats.items():
            print(f"\n{strategy_name} Timing Breakdown:")
            print("-" * 60)
            print(f"{'Function':<30} {'Calls':<10} {'Total(s)':<10} {'Avg(ms)':<10}")
            print("-" * 60)
            
            for func, data in sorted(funcs.items(), key=lambda x: x[1]["total_time"], reverse=True):
                avg_ms = (data["total_time"] / data["calls"]) * 1000
                print(f"{func:<30} {data['calls']:<10} {data['total_time']:<10.3f} {avg_ms:<10.2f}")

timing_stats = TimingStats()

# Modify timing decorator
def timing_decorator(strategy_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            timing_stats.add(strategy_name, func.__name__, elapsed)
            return result
        return wrapper
    return decorator

# Modified decorator application
def apply_decorators(cls, method_name, strategy_name):
    try:
        original_method = getattr(cls, method_name)
        decorated_method = timing_decorator(strategy_name)(original_method)
        setattr(cls, method_name, decorated_method)
    except AttributeError:
        print(f"Method {method_name} not found in class {cls.__name__}.")

# Apply to key methods
methods_to_profile = [
    '_scrap',
    # 'process_element', 
    '_process_element', 
    'process_image',
]


# Apply decorators to both strategies
for strategy, name in [(WebScrapingStrategy, "Original"), (LXMLWebScrapingStrategy, "LXML")]:
    for method in methods_to_profile:
        apply_decorators(strategy, method, name)


def generate_large_html(n_elements=1000):
    html = ['<!DOCTYPE html><html><head></head><body>']
    for i in range(n_elements):
        html.append(f'''
            <div class="article">
                <h2>Heading {i}</h2>
                <div>
                    <div>
                        <p>This is paragraph {i} with some content and a <a href="http://example.com/{i}">link</a></p>
                    </div>
                </div>
                <img src="image{i}.jpg" alt="Image {i}">
                <ul>
                    <li>List item {i}.1</li>
                    <li>List item {i}.2</li>
                </ul>
            </div>
        ''')
    html.append('</body></html>')
    return ''.join(html)

def test_scraping():
    # Initialize both scrapers
    original_scraper = WebScrapingStrategy()
    selected_scraper = LXMLWebScrapingStrategy()
    
    # Generate test HTML
    print("Generating HTML...")
    html = generate_large_html(5000)
    print(f"HTML Size: {len(html)/1024:.2f} KB")
    
    # Time the scraping
    print("\nStarting scrape...")
    start_time = time.time()
    
    kwargs = {
        "url": "http://example.com",
        "html": html,
        "word_count_threshold": 5,
        "keep_data_attributes": True
    }
    
    t1 = time.perf_counter()
    result_selected = selected_scraper.scrap(**kwargs)
    t2 = time.perf_counter()
    
    result_original = original_scraper.scrap(**kwargs)
    t3 = time.perf_counter()
    
    elapsed = t3 - start_time
    print(f"\nScraping completed in {elapsed:.2f} seconds")
    
    timing_stats.report()
    
    # Print stats of LXML output
    print("\Turbo Output:")
    print(f"\nExtracted links: {len(result_selected.links.internal) + len(result_selected.links.external)}")
    print(f"Extracted images: {len(result_selected.media.images)}")
    print(f"Clean HTML size: {len(result_selected.cleaned_html)/1024:.2f} KB")
    print(f"Scraping time: {t2 - t1:.2f} seconds")

    # Print stats of original output
    print("\nOriginal Output:")
    print(f"\nExtracted links: {len(result_original.links.internal) + len(result_original.links.external)}")
    print(f"Extracted images: {len(result_original.media.images)}")
    print(f"Clean HTML size: {len(result_original.cleaned_html)/1024:.2f} KB")
    print(f"Scraping time: {t3 - t1:.2f} seconds")
        
        
if __name__ == "__main__":
    test_scraping()