#!/usr/bin/env python3
"""
Test script for the new /urls/discover endpoint in Crawl4AI Docker API.
"""

import asyncio
import httpx
import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

# Configuration
BASE_URL = "http://localhost:11235"
TEST_DOMAIN = "docs.crawl4ai.com"

async def check_server_health(client: httpx.AsyncClient) -> bool:
    """Check if the server is healthy."""
    console.print("[bold cyan]Checking server health...[/]", end="")
    try:
        response = await client.get("/health", timeout=10.0)
        response.raise_for_status()
        console.print(" [bold green]✓ Server is healthy![/]")
        return True
    except Exception as e:
        console.print(f"\n[bold red]✗ Server health check failed: {e}[/]")
        console.print(f"Is the server running at {BASE_URL}?")
        return False

def print_request(endpoint: str, payload: dict, title: str = "Request"):
    """Pretty print the request."""
    syntax = Syntax(json.dumps(payload, indent=2), "json", theme="monokai")
    console.print(Panel.fit(
        f"[cyan]POST {endpoint}[/cyan]\n{syntax}",
        title=f"[bold blue]{title}[/]",
        border_style="blue"
    ))

def print_response(response_data: dict, title: str = "Response"):
    """Pretty print the response."""
    syntax = Syntax(json.dumps(response_data, indent=2), "json", theme="monokai")
    console.print(Panel.fit(
        syntax,
        title=f"[bold green]{title}[/]",
        border_style="green"
    ))

async def test_urls_discover_basic():
    """Test basic URL discovery functionality."""
    console.print("\n[bold yellow]Testing URL Discovery Endpoint[/bold yellow]")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Check server health first
        if not await check_server_health(client):
            return False
        
        # Test 1: Basic discovery with sitemap
        console.print("\n[cyan]Test 1: Basic URL discovery from sitemap[/cyan]")
        
        payload = {
            "domain": TEST_DOMAIN,
            "seeding_config": {
                "source": "sitemap",
                "max_urls": 5
            }
        }
        
        print_request("/urls/discover", payload, "Basic Discovery Request")
        
        try:
            response = await client.post("/urls/discover", json=payload)
            response.raise_for_status()
            response_data = response.json()
            
            print_response(response_data, "Basic Discovery Response")
            
            # Validate response structure
            if isinstance(response_data, list):
                console.print(f"[green]✓ Discovered {len(response_data)} URLs[/green]")
                return True
            else:
                console.print(f"[red]✗ Expected list, got {type(response_data)}[/red]")
                return False
                
        except httpx.HTTPStatusError as e:
            console.print(f"[red]✗ HTTP Error: {e.response.status_code} - {e.response.text}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return False

async def test_urls_discover_invalid_config():
    """Test URL discovery with invalid configuration."""
    console.print("\n[cyan]Test 2: URL discovery with invalid configuration[/cyan]")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        payload = {
            "domain": TEST_DOMAIN,
            "seeding_config": {
                "source": "invalid_source",  # Invalid source
                "max_urls": 5
            }
        }
        
        print_request("/urls/discover", payload, "Invalid Config Request")
        
        try:
            response = await client.post("/urls/discover", json=payload)
            
            if response.status_code == 500:
                console.print("[green]✓ Server correctly rejected invalid config with 500 error[/green]")
                return True
            else:
                console.print(f"[yellow]? Expected 500 error, got {response.status_code}[/yellow]")
                response_data = response.json()
                print_response(response_data, "Unexpected Response")
                return False
                
        except Exception as e:
            console.print(f"[red]✗ Unexpected error: {e}[/red]")
            return False

async def test_urls_discover_with_filtering():
    """Test URL discovery with advanced filtering."""
    console.print("\n[cyan]Test 3: URL discovery with filtering and metadata[/cyan]")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        payload = {
            "domain": TEST_DOMAIN,
            "seeding_config": {
                "source": "sitemap",
                "pattern": "*/docs/*",  # Filter to docs URLs only
                "extract_head": True,   # Extract metadata
                "max_urls": 3
            }
        }
        
        print_request("/urls/discover", payload, "Filtered Discovery Request")
        
        try:
            response = await client.post("/urls/discover", json=payload)
            response.raise_for_status()
            response_data = response.json()
            
            print_response(response_data, "Filtered Discovery Response")
            
            # Validate response structure with metadata
            if isinstance(response_data, list) and len(response_data) > 0:
                sample_url = response_data[0]
                if "url" in sample_url:
                    console.print(f"[green]✓ Discovered {len(response_data)} filtered URLs with metadata[/green]")
                    return True
                else:
                    console.print(f"[red]✗ URL objects missing expected fields[/red]")
                    return False
            else:
                console.print(f"[yellow]? No URLs found with filter pattern[/yellow]")
                return True  # This could be expected
                
        except httpx.HTTPStatusError as e:
            console.print(f"[red]✗ HTTP Error: {e.response.status_code} - {e.response.text}[/red]")
            return False
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            return False

async def main():
    """Run all tests."""
    console.print("[bold cyan]🔍 URL Discovery Endpoint Tests[/bold cyan]")
    
    results = []
    
    # Run tests
    results.append(await test_urls_discover_basic())
    results.append(await test_urls_discover_invalid_config())
    results.append(await test_urls_discover_with_filtering())
    
    # Summary
    console.print("\n[bold cyan]Test Summary[/bold cyan]")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        console.print(f"[bold green]✓ All {total} tests passed![/bold green]")
    else:
        console.print(f"[bold yellow]⚠ {passed}/{total} tests passed[/bold yellow]")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())