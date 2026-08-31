#!/usr/bin/env python3
"""
Test script for LLM temperature and base_url parameters in Crawl4AI Docker API.
This demonstrates the new hierarchical configuration system:
1. Request-level parameters (highest priority)
2. Provider-specific environment variables
3. Global environment variables
4. System defaults (lowest priority)
"""

import asyncio
import httpx
import json
import os
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table


console = Console()

# Configuration
BASE_URL = "http://localhost:11235"  # Docker API endpoint
TEST_URL = "https://httpbin.org/html"     # Simple test page

# --- Helper Functions ---

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

def print_response(response: dict, title: str = "Response"):
    """Pretty print relevant parts of the response."""
    # Extract only the relevant parts
    relevant = {}
    if "markdown" in response:
        relevant["markdown"] = response["markdown"][:200] + "..." if len(response.get("markdown", "")) > 200 else response.get("markdown", "")
    if "success" in response:
        relevant["success"] = response["success"]
    if "url" in response:
        relevant["url"] = response["url"]
    if "filter" in response:
        relevant["filter"] = response["filter"]
    
    console.print(Panel.fit(
        Syntax(json.dumps(relevant, indent=2), "json", theme="monokai"),
        title=f"[bold green]{title}[/]",
        border_style="green"
    ))

# --- Test Functions ---

async def test_default_no_params(client: httpx.AsyncClient):
    """Test 1: No temperature or base_url specified - uses defaults"""
    console.rule("[bold yellow]Test 1: Default Configuration (No Parameters)[/]")
    
    payload = {
        "url": TEST_URL,
        "f": "llm",
        "q": "What is the main heading of this page? Answer in exactly 5 words."
    }
    
    print_request("/md", payload, "Request without temperature/base_url")
    
    try:
        response = await client.post("/md", json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        print_response(data, "Response (using system defaults)")
        console.print("[dim]→ This used system defaults or environment variables if set[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")

async def test_request_temperature(client: httpx.AsyncClient):
    """Test 2: Request-level temperature (highest priority)"""
    console.rule("[bold yellow]Test 2: Request-Level Temperature[/]")
    
    # Test with low temperature (more focused)
    payload_low = {
        "url": TEST_URL,
        "f": "llm",
        "q": "What is the main heading? Be creative and poetic.",
        "temperature": 0.1  # Very low - should be less creative
    }
    
    print_request("/md", payload_low, "Low Temperature (0.1)")
    
    try:
        response = await client.post("/md", json=payload_low, timeout=30.0)
        response.raise_for_status()
        data_low = response.json()
        print_response(data_low, "Response with Low Temperature")
        console.print("[dim]→ Low temperature (0.1) should produce focused, less creative output[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
    
    console.print()
    
    # Test with high temperature (more creative)
    payload_high = {
        "url": TEST_URL,
        "f": "llm",
        "q": "What is the main heading? Be creative and poetic.",
        "temperature": 1.5  # High - should be more creative
    }
    
    print_request("/md", payload_high, "High Temperature (1.5)")
    
    try:
        response = await client.post("/md", json=payload_high, timeout=30.0)
        response.raise_for_status()
        data_high = response.json()
        print_response(data_high, "Response with High Temperature")
        console.print("[dim]→ High temperature (1.5) should produce more creative, varied output[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")

async def test_provider_override(client: httpx.AsyncClient):
    """Test 3: Provider override with temperature"""
    console.rule("[bold yellow]Test 3: Provider Override with Temperature[/]")
    
    provider = "gemini/gemini-2.5-flash-lite"
    payload = {
        "url": TEST_URL,
        "f": "llm",
        "q": "Summarize this page in one sentence.",
        "provider": provider,  # Explicitly set provider
        "temperature": 0.7
    }
    
    print_request("/md", payload, "Provider + Temperature Override")
    
    try:
        response = await client.post("/md", json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        print_response(data, "Response with Provider Override")
        console.print(f"[dim]→ This explicitly uses {provider} with temperature 0.7[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")

async def test_base_url_custom(client: httpx.AsyncClient):
    """Test 4: Custom base_url (will fail unless you have a custom endpoint)"""
    console.rule("[bold yellow]Test 4: Custom Base URL (Demo Only)[/]")
    
    payload = {
        "url": TEST_URL,
        "f": "llm",
        "q": "What is this page about?",
        "base_url": "https://api.custom-endpoint.com/v1",  # Custom endpoint
        "temperature": 0.5
    }
    
    print_request("/md", payload, "Custom Base URL Request")
    console.print("[yellow]Note: This will fail unless you have a custom endpoint set up[/]")
    
    try:
        response = await client.post("/md", json=payload, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        print_response(data, "Response from Custom Endpoint")
    except httpx.HTTPStatusError as e:
        console.print(f"[yellow]Expected failure (no custom endpoint): Status {e.response.status_code}[/]")
    except Exception as e:
        console.print(f"[yellow]Expected error: {e}[/]")

async def test_llm_job_endpoint(client: httpx.AsyncClient):
    """Test 5: Test the /llm/job endpoint with temperature and base_url"""
    console.rule("[bold yellow]Test 5: LLM Job Endpoint with Parameters[/]")
    
    payload = {
        "url": TEST_URL,
        "q": "Extract the main title and any key information",
        "temperature": 0.3,
        # "base_url": "https://api.openai.com/v1"  # Optional
    }
    
    print_request("/llm/job", payload, "LLM Job with Temperature")
    
    try:
        # Submit the job
        response = await client.post("/llm/job", json=payload, timeout=30.0)
        response.raise_for_status()
        job_data = response.json()
        
        if "task_id" in job_data:
            task_id = job_data["task_id"]
            console.print(f"[green]Job created with task_id: {task_id}[/]")
            
            # Poll for result (simplified - in production use proper polling)
            await asyncio.sleep(3)
            
            status_response = await client.get(f"/llm/job/{task_id}")
            status_data = status_response.json()
            
            if status_data.get("status") == "completed":
                console.print("[green]Job completed successfully![/]")
                if "result" in status_data:
                    console.print(Panel.fit(
                        Syntax(json.dumps(status_data["result"], indent=2), "json", theme="monokai"),
                        title="Extraction Result",
                        border_style="green"
                    ))
            else:
                console.print(f"[yellow]Job status: {status_data.get('status', 'unknown')}[/]")
        else:
            console.print(f"[red]Unexpected response: {job_data}[/]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")


async def test_llm_endpoint(client: httpx.AsyncClient):
    """
    Quick QA round-trip with /llm.
    Asks a trivial question against SIMPLE_URL just to show wiring.
    """
    import time
    import urllib.parse

    page_url = "https://kidocode.com"
    question = "What is the title of this page?"

    enc = urllib.parse.quote_plus(page_url, safe="")
    console.print(f"GET /llm/{enc}?q={question}")

    try:
        t0 = time.time()
        resp = await client.get(f"/llm/{enc}", params={"q": question})
        dt = time.time() - t0
        console.print(
            f"Response Status: [bold {'green' if resp.is_success else 'red'}]{resp.status_code}[/] (took {dt:.2f}s)")
        resp.raise_for_status()
        answer = resp.json().get("answer", "")
        console.print(Panel(answer or "No answer returned",
                      title="LLM answer", border_style="magenta", expand=False))
    except Exception as e:
        console.print(f"[bold red]Error hitting /llm:[/] {e}")


async def show_environment_info():
    """Display current environment configuration"""
    console.rule("[bold cyan]Current Environment Configuration[/]")
    
    table = Table(title="LLM Environment Variables", show_header=True, header_style="bold magenta")
    table.add_column("Variable", style="cyan", width=30)
    table.add_column("Value", style="yellow")
    table.add_column("Description", style="dim")
    
    env_vars = [
        ("LLM_PROVIDER", "Global default provider"),
        ("LLM_TEMPERATURE", "Global default temperature"),
        ("LLM_BASE_URL", "Global custom API endpoint"),
        ("OPENAI_API_KEY", "OpenAI API key"),
        ("OPENAI_TEMPERATURE", "OpenAI-specific temperature"),
        ("OPENAI_BASE_URL", "OpenAI-specific endpoint"),
        ("ANTHROPIC_API_KEY", "Anthropic API key"),
        ("ANTHROPIC_TEMPERATURE", "Anthropic-specific temperature"),
        ("GROQ_API_KEY", "Groq API key"),
        ("GROQ_TEMPERATURE", "Groq-specific temperature"),
    ]
    
    for var, desc in env_vars:
        value = os.environ.get(var, "[not set]")
        if "API_KEY" in var and value != "[not set]":
            # Mask API keys for security
            value = value[:10] + "..." if len(value) > 10 else "***"
        table.add_row(var, value, desc)
    
    console.print(table)
    console.print()

# --- Main Test Runner ---

async def main():
    """Run all tests"""
    console.print(Panel.fit(
        "[bold cyan]Crawl4AI LLM Parameters Test Suite[/]\n" +
        "Testing temperature and base_url configuration hierarchy",
        border_style="cyan"
    ))
    
    # Show current environment
    # await show_environment_info()
    
    # Create HTTP client
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Check server health
        if not await check_server_health(client):
            console.print("[red]Server is not available. Please ensure the Docker container is running.[/]")
            return
        
        # Run tests
        tests = [
            ("Default Configuration", test_default_no_params),
            ("Request Temperature", test_request_temperature),
            ("Provider Override", test_provider_override),
            ("Custom Base URL", test_base_url_custom),
            ("LLM Job Endpoint", test_llm_job_endpoint),
            ("LLM Endpoint", test_llm_endpoint),
        ]
        
        for i, (name, test_func) in enumerate(tests, 1):
            if i > 1:
                console.print()  # Add spacing between tests
            
            try:
                await test_func(client)
            except Exception as e:
                console.print(f"[red]Test '{name}' failed with error: {e}[/]")
                console.print_exception(show_locals=False)
        
        console.rule("[bold green]All Tests Complete![/]", style="green")
        
        # Summary
        console.print("\n[bold cyan]Configuration Hierarchy Summary:[/]")
        console.print("1. [yellow]Request parameters[/] - Highest priority (temperature, base_url in API call)")
        console.print("2. [yellow]Provider-specific env[/] - e.g., OPENAI_TEMPERATURE, GROQ_BASE_URL")
        console.print("3. [yellow]Global env variables[/] - LLM_TEMPERATURE, LLM_BASE_URL")
        console.print("4. [yellow]System defaults[/] - Lowest priority (provider/litellm defaults)")
        console.print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user.[/]")
    except Exception as e:
        console.print(f"\n[bold red]An error occurred:[/]")
        console.print_exception(show_locals=False)