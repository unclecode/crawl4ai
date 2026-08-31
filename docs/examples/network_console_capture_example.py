import asyncio
import json
import os
import base64
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, CrawlResult
from crawl4ai import BrowserConfig

__cur_dir__ = Path(__file__).parent

# Create temp directory if it doesn't exist
os.makedirs(os.path.join(__cur_dir__, "tmp"), exist_ok=True)

async def demo_basic_network_capture():
    """Basic network request capturing example"""
    print("\n=== 1. Basic Network Request Capturing ===")
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            capture_network_requests=True,
            wait_until="networkidle"  # Wait for network to be idle
        )
        
        result = await crawler.arun(
            url="https://example.com/",
            config=config
        )
        
        if result.success and result.network_requests:
            print(f"Captured {len(result.network_requests)} network events")
            
            # Count by event type
            event_types = {}
            for req in result.network_requests:
                event_type = req.get("event_type", "unknown")
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            print("Event types:")
            for event_type, count in event_types.items():
                print(f"  - {event_type}: {count}")
            
            # Show a sample request and response
            request = next((r for r in result.network_requests if r.get("event_type") == "request"), None)
            response = next((r for r in result.network_requests if r.get("event_type") == "response"), None)
            
            if request:
                print("\nSample request:")
                print(f"  URL: {request.get('url')}")
                print(f"  Method: {request.get('method')}")
                print(f"  Headers: {list(request.get('headers', {}).keys())}")
            
            if response:
                print("\nSample response:")
                print(f"  URL: {response.get('url')}")
                print(f"  Status: {response.get('status')} {response.get('status_text', '')}")
                print(f"  Headers: {list(response.get('headers', {}).keys())}")

async def demo_basic_console_capture():
    """Basic console message capturing example"""
    print("\n=== 2. Basic Console Message Capturing ===")
    
    # Create a simple HTML file with console messages
    html_file = os.path.join(__cur_dir__, "tmp", "console_test.html")
    with open(html_file, "w") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Console Test</title>
        </head>
        <body>
            <h1>Console Message Test</h1>
            <script>
                console.log("This is a basic log message");
                console.info("This is an info message");
                console.warn("This is a warning message");
                console.error("This is an error message");
                
                // Generate an error
                try {
                    nonExistentFunction();
                } catch (e) {
                    console.error("Caught error:", e);
                }
            </script>
        </body>
        </html>
        """)
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            capture_console_messages=True,
            wait_until="networkidle"  # Wait to make sure all scripts execute
        )
        
        result = await crawler.arun(
            url=f"file://{html_file}",
            config=config
        )
        
        if result.success and result.console_messages:
            print(f"Captured {len(result.console_messages)} console messages")
            
            # Count by message type
            message_types = {}
            for msg in result.console_messages:
                msg_type = msg.get("type", "unknown")
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            print("Message types:")
            for msg_type, count in message_types.items():
                print(f"  - {msg_type}: {count}")
            
            # Show all messages
            print("\nAll console messages:")
            for i, msg in enumerate(result.console_messages, 1):
                print(f"  {i}. [{msg.get('type', 'unknown')}] {msg.get('text', '')}")

async def demo_combined_capture():
    """Capturing both network requests and console messages"""
    print("\n=== 3. Combined Network and Console Capture ===")
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            capture_network_requests=True,
            capture_console_messages=True,
            wait_until="networkidle"
        )
        
        result = await crawler.arun(
            url="https://httpbin.org/html",
            config=config
        )
        
        if result.success:
            network_count = len(result.network_requests) if result.network_requests else 0
            console_count = len(result.console_messages) if result.console_messages else 0
            
            print(f"Captured {network_count} network events and {console_count} console messages")
            
            # Save the captured data to a JSON file for analysis
            output_file = os.path.join(__cur_dir__, "tmp", "capture_data.json")
            with open(output_file, "w") as f:
                json.dump({
                    "url": result.url,
                    "timestamp": datetime.now().isoformat(),
                    "network_requests": result.network_requests,
                    "console_messages": result.console_messages
                }, f, indent=2)
            
            print(f"Full capture data saved to {output_file}")

async def analyze_spa_network_traffic():
    """Analyze network traffic of a Single-Page Application"""
    print("\n=== 4. Analyzing SPA Network Traffic ===")
    
    async with AsyncWebCrawler(config=BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800
    )) as crawler:
        config = CrawlerRunConfig(
            capture_network_requests=True,
            capture_console_messages=True,
            # Wait longer to ensure all resources are loaded
            wait_until="networkidle",
            page_timeout=60000,  # 60 seconds
        )
        
        result = await crawler.arun(
            url="https://weather.com",
            config=config
        )
        
        if result.success and result.network_requests:
            # Extract different types of requests
            requests = []
            responses = []
            failures = []
            
            for event in result.network_requests:
                event_type = event.get("event_type")
                if event_type == "request":
                    requests.append(event)
                elif event_type == "response":
                    responses.append(event)
                elif event_type == "request_failed":
                    failures.append(event)
            
            print(f"Captured {len(requests)} requests, {len(responses)} responses, and {len(failures)} failures")
            
            # Analyze request types
            resource_types = {}
            for req in requests:
                resource_type = req.get("resource_type", "unknown")
                resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
            
            print("\nResource types:")
            for resource_type, count in sorted(resource_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {resource_type}: {count}")
            
            # Analyze API calls
            api_calls = [r for r in requests if "api" in r.get("url", "").lower()]
            if api_calls:
                print(f"\nDetected {len(api_calls)} API calls:")
                for i, call in enumerate(api_calls[:5], 1):  # Show first 5
                    print(f"  {i}. {call.get('method')} {call.get('url')}")
                if len(api_calls) > 5:
                    print(f"     ... and {len(api_calls) - 5} more")
            
            # Analyze response status codes
            status_codes = {}
            for resp in responses:
                status = resp.get("status", 0)
                status_codes[status] = status_codes.get(status, 0) + 1
            
            print("\nResponse status codes:")
            for status, count in sorted(status_codes.items()):
                print(f"  - {status}: {count}")
            
            # Analyze failures
            if failures:
                print("\nFailed requests:")
                for i, failure in enumerate(failures[:5], 1):  # Show first 5
                    print(f"  {i}. {failure.get('url')} - {failure.get('failure_text')}")
                if len(failures) > 5:
                    print(f"     ... and {len(failures) - 5} more")
            
            # Check for console errors
            if result.console_messages:
                errors = [msg for msg in result.console_messages if msg.get("type") == "error"]
                if errors:
                    print(f"\nDetected {len(errors)} console errors:")
                    for i, error in enumerate(errors[:3], 1):  # Show first 3
                        print(f"  {i}. {error.get('text', '')[:100]}...")
                    if len(errors) > 3:
                        print(f"     ... and {len(errors) - 3} more")
            
            # Save analysis to file
            output_file = os.path.join(__cur_dir__, "tmp", "weather_network_analysis.json")
            with open(output_file, "w") as f:
                json.dump({
                    "url": result.url,
                    "timestamp": datetime.now().isoformat(),
                    "statistics": {
                        "request_count": len(requests),
                        "response_count": len(responses),
                        "failure_count": len(failures),
                        "resource_types": resource_types,
                        "status_codes": {str(k): v for k, v in status_codes.items()},
                        "api_call_count": len(api_calls),
                        "console_error_count": len(errors) if result.console_messages else 0
                    },
                    "network_requests": result.network_requests,
                    "console_messages": result.console_messages
                }, f, indent=2)
            
            print(f"\nFull analysis saved to {output_file}")

async def demo_security_analysis():
    """Using network capture for security analysis"""
    print("\n=== 5. Security Analysis with Network Capture ===")
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            capture_network_requests=True,
            capture_console_messages=True,
            wait_until="networkidle"
        )
        
        # A site that makes multiple third-party requests
        result = await crawler.arun(
            url="https://www.nytimes.com/",
            config=config
        )
        
        if result.success and result.network_requests:
            print(f"Captured {len(result.network_requests)} network events")
            
            # Extract all domains
            domains = set()
            for req in result.network_requests:
                if req.get("event_type") == "request":
                    url = req.get("url", "")
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        if domain:
                            domains.add(domain)
                    except:
                        pass
            
            print(f"\nDetected requests to {len(domains)} unique domains:")
            main_domain = urlparse(result.url).netloc
            
            # Separate first-party vs third-party domains
            first_party = [d for d in domains if main_domain in d]
            third_party = [d for d in domains if main_domain not in d]
            
            print(f"  - First-party domains: {len(first_party)}")
            print(f"  - Third-party domains: {len(third_party)}")
            
            # Look for potential trackers/analytics
            tracking_keywords = ["analytics", "tracker", "pixel", "tag", "stats", "metric", "collect", "beacon"]
            potential_trackers = []
            
            for domain in third_party:
                if any(keyword in domain.lower() for keyword in tracking_keywords):
                    potential_trackers.append(domain)
            
            if potential_trackers:
                print(f"\nPotential tracking/analytics domains ({len(potential_trackers)}):")
                for i, domain in enumerate(sorted(potential_trackers)[:10], 1):
                    print(f"  {i}. {domain}")
                if len(potential_trackers) > 10:
                    print(f"     ... and {len(potential_trackers) - 10} more")
            
            # Check for insecure (HTTP) requests
            insecure_requests = [
                req.get("url") for req in result.network_requests 
                if req.get("event_type") == "request" and req.get("url", "").startswith("http://")
            ]
            
            if insecure_requests:
                print(f"\nWarning: Found {len(insecure_requests)} insecure (HTTP) requests:")
                for i, url in enumerate(insecure_requests[:5], 1):
                    print(f"  {i}. {url}")
                if len(insecure_requests) > 5:
                    print(f"     ... and {len(insecure_requests) - 5} more")
            
            # Save security analysis to file
            output_file = os.path.join(__cur_dir__, "tmp", "security_analysis.json")
            with open(output_file, "w") as f:
                json.dump({
                    "url": result.url,
                    "main_domain": main_domain,
                    "timestamp": datetime.now().isoformat(),
                    "analysis": {
                        "total_requests": len([r for r in result.network_requests if r.get("event_type") == "request"]),
                        "unique_domains": len(domains),
                        "first_party_domains": first_party,
                        "third_party_domains": third_party,
                        "potential_trackers": potential_trackers,
                        "insecure_requests": insecure_requests
                    }
                }, f, indent=2)
            
            print(f"\nFull security analysis saved to {output_file}")

async def demo_performance_analysis():
    """Using network capture for performance analysis"""
    print("\n=== 6. Performance Analysis with Network Capture ===")
    
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            capture_network_requests=True,
            page_timeout=60 * 2 * 1000  # 120 seconds
        )
        
        result = await crawler.arun(
            url="https://www.cnn.com/",
            config=config
        )
        
        if result.success and result.network_requests:
            # Filter only response events with timing information
            responses_with_timing = [
                r for r in result.network_requests 
                if r.get("event_type") == "response" and r.get("request_timing")
            ]
            
            if responses_with_timing:
                print(f"Analyzing timing for {len(responses_with_timing)} network responses")
                
                # Group by resource type
                resource_timings = {}
                for resp in responses_with_timing:
                    url = resp.get("url", "")
                    timing = resp.get("request_timing", {})
                    
                    # Determine resource type from URL extension
                    ext = url.split(".")[-1].lower() if "." in url.split("/")[-1] else "unknown"
                    if ext in ["jpg", "jpeg", "png", "gif", "webp", "svg", "ico"]:
                        resource_type = "image"
                    elif ext in ["js"]:
                        resource_type = "javascript"
                    elif ext in ["css"]:
                        resource_type = "css"
                    elif ext in ["woff", "woff2", "ttf", "otf", "eot"]:
                        resource_type = "font"
                    else:
                        resource_type = "other"
                    
                    if resource_type not in resource_timings:
                        resource_timings[resource_type] = []
                    
                    # Calculate request duration if timing information is available
                    if isinstance(timing, dict) and "requestTime" in timing and "receiveHeadersEnd" in timing:
                        # Convert to milliseconds
                        duration = (timing["receiveHeadersEnd"] - timing["requestTime"]) * 1000
                        resource_timings[resource_type].append({
                            "url": url,
                            "duration_ms": duration
                        })
                    if isinstance(timing, dict) and "requestStart" in timing and "responseStart" in timing and "startTime" in timing:
                        # Convert to milliseconds
                        duration = (timing["responseStart"] - timing["requestStart"]) * 1000
                        resource_timings[resource_type].append({
                            "url": url,
                            "duration_ms": duration
                        })
                
                # Calculate statistics for each resource type
                print("\nPerformance by resource type:")
                for resource_type, timings in resource_timings.items():
                    if timings:
                        durations = [t["duration_ms"] for t in timings]
                        avg_duration = sum(durations) / len(durations)
                        max_duration = max(durations)
                        slowest_resource = next(t["url"] for t in timings if t["duration_ms"] == max_duration)
                        
                        print(f"  {resource_type.upper()}:")
                        print(f"    - Count: {len(timings)}")
                        print(f"    - Avg time: {avg_duration:.2f} ms")
                        print(f"    - Max time: {max_duration:.2f} ms")
                        print(f"    - Slowest: {slowest_resource}")
                
                # Identify the slowest resources overall
                all_timings = []
                for resource_type, timings in resource_timings.items():
                    for timing in timings:
                        timing["type"] = resource_type
                        all_timings.append(timing)
                
                all_timings.sort(key=lambda x: x["duration_ms"], reverse=True)
                
                print("\nTop 5 slowest resources:")
                for i, timing in enumerate(all_timings[:5], 1):
                    print(f"  {i}. [{timing['type']}] {timing['url']} - {timing['duration_ms']:.2f} ms")
                
                # Save performance analysis to file
                output_file = os.path.join(__cur_dir__, "tmp", "performance_analysis.json")
                with open(output_file, "w") as f:
                    json.dump({
                        "url": result.url,
                        "timestamp": datetime.now().isoformat(),
                        "resource_timings": resource_timings,
                        "slowest_resources": all_timings[:10]  # Save top 10
                    }, f, indent=2)
                
                print(f"\nFull performance analysis saved to {output_file}")

async def main():
    """Run all demo functions sequentially"""
    print("=== Network and Console Capture Examples ===")
    
    # Make sure tmp directory exists
    os.makedirs(os.path.join(__cur_dir__, "tmp"), exist_ok=True)
    
    # Run basic examples
    # await demo_basic_network_capture()
    await demo_basic_console_capture()
    # await demo_combined_capture()
    
    # Run advanced examples
    # await analyze_spa_network_traffic()
    # await demo_security_analysis()
    # await demo_performance_analysis()
    
    print("\n=== Examples Complete ===")
    print(f"Check the tmp directory for output files: {os.path.join(__cur_dir__, 'tmp')}")

if __name__ == "__main__":
    asyncio.run(main())