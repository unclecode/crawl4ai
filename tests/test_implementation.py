#!/usr/bin/env python3
"""
Test script for the new URL discovery functionality.
This tests the handler function directly without running the full server.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the repo to Python path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "deploy" / "docker"))

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

async def test_url_discovery_handler():
    """Test the URL discovery handler function directly."""
    try:
        # Import the handler function and dependencies
        from api import handle_url_discovery
        from crawl4ai.async_configs import SeedingConfig
        
        console.print("[bold cyan]Testing URL Discovery Handler Function[/bold cyan]")
        
        # Test 1: Basic functionality
        console.print("\n[cyan]Test 1: Basic URL discovery[/cyan]")
        
        domain = "docs.crawl4ai.com"
        seeding_config = {
            "source": "sitemap",
            "max_urls": 3,
            "verbose": True
        }
        
        console.print(f"[blue]Domain:[/blue] {domain}")
        console.print(f"[blue]Config:[/blue] {seeding_config}")
        
        # Call the handler directly
        result = await handle_url_discovery(domain, seeding_config)
        
        console.print(f"[green]✓ Handler executed successfully[/green]")
        console.print(f"[green]✓ Result type: {type(result)}[/green]")
        console.print(f"[green]✓ Result length: {len(result)}[/green]")
        
        # Print first few results if any
        if result and len(result) > 0:
            console.print("\n[blue]Sample results:[/blue]")
            for i, url_obj in enumerate(result[:2]):
                console.print(f"  {i+1}. {url_obj}")
        
        return True
        
    except ImportError as e:
        console.print(f"[red]✗ Import error: {e}[/red]")
        console.print("[yellow]This suggests missing dependencies or module structure issues[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Handler error: {e}[/red]")
        return False

async def test_seeding_config_validation():
    """Test SeedingConfig validation."""
    try:
        from crawl4ai.async_configs import SeedingConfig
        
        console.print("\n[cyan]Test 2: SeedingConfig validation[/cyan]")
        
        # Test valid config
        valid_config = {
            "source": "sitemap",
            "max_urls": 5,
            "pattern": "*"
        }
        
        config = SeedingConfig(**valid_config)
        console.print(f"[green]✓ Valid config created: {config.source}, max_urls={config.max_urls}[/green]")
        
        # Test invalid config
        try:
            invalid_config = {
                "source": "invalid_source",
                "max_urls": 5
            }
            config = SeedingConfig(**invalid_config)
            console.print(f"[yellow]? Invalid config unexpectedly accepted[/yellow]")
        except Exception as e:
            console.print(f"[green]✓ Invalid config correctly rejected: {str(e)[:50]}...[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ SeedingConfig test error: {e}[/red]")
        return False

async def test_schema_validation():
    """Test the URLDiscoveryRequest schema."""
    try:
        from schemas import URLDiscoveryRequest
        
        console.print("\n[cyan]Test 3: URLDiscoveryRequest schema validation[/cyan]")
        
        # Test valid request
        valid_request_data = {
            "domain": "example.com",
            "seeding_config": {
                "source": "sitemap",
                "max_urls": 10
            }
        }
        
        request = URLDiscoveryRequest(**valid_request_data)
        console.print(f"[green]✓ Valid request created: domain={request.domain}[/green]")
        
        # Test request with default config
        minimal_request_data = {
            "domain": "example.com"
        }
        
        request = URLDiscoveryRequest(**minimal_request_data)
        console.print(f"[green]✓ Minimal request created with defaults[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Schema test error: {e}[/red]")
        return False

async def main():
    """Run all tests."""
    console.print("[bold blue]🔍 URL Discovery Implementation Tests[/bold blue]")
    
    results = []
    
    # Test the implementation components
    results.append(await test_seeding_config_validation())
    results.append(await test_schema_validation())
    results.append(await test_url_discovery_handler())
    
    # Summary
    console.print("\n[bold cyan]Test Summary[/bold cyan]")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        console.print(f"[bold green]✓ All {total} implementation tests passed![/bold green]")
        console.print("[green]The URL discovery endpoint is ready for integration testing[/green]")
    else:
        console.print(f"[bold yellow]⚠ {passed}/{total} tests passed[/bold yellow]")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())