import asyncio
import httpx
import json
import os
import time
from typing import List, Dict, Any, AsyncGenerator, Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table

# --- Setup & Configuration ---
load_dotenv()  # Load environment variables from .env file

console = Console()

# --- Configuration ---
BASE_URL = os.getenv("CRAWL4AI_TEST_URL", "http://localhost:11235")
BASE_URL = os.getenv("CRAWL4AI_TEST_URL", "http://localhost:8020")
# Target URLs
SIMPLE_URL = "https://httpbin.org/html"
LINKS_URL = "https://httpbin.org/links/10/0"
FORMS_URL = "https://httpbin.org/forms/post" # For JS demo
BOOKS_URL = "http://books.toscrape.com/" # For CSS extraction
PYTHON_URL = "https://python.org" # For deeper crawl
# Use the same sample site as deep crawl tests for consistency
DEEP_CRAWL_BASE_URL = os.getenv("DEEP_CRAWL_TEST_SITE", "https://docs.crawl4ai.com/samples/deepcrawl/")
DEEP_CRAWL_DOMAIN = "docs.crawl4ai.com"

# --- Helper Functions ---

async def check_server_health(client: httpx.AsyncClient):
    """Check if the server is healthy before running tests."""
    console.print("[bold cyan]Checking server health...[/]", end="")
    try:
        response = await client.get("/health", timeout=10.0)
        response.raise_for_status()
        health_data = response.json()
        console.print(f"[bold green] Server OK! Version: {health_data.get('version', 'N/A')}[/]")
        return True
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        console.print(f"\n[bold red]Server health check FAILED:[/]")
        console.print(f"Error: {e}")
        console.print(f"Is the server running at {BASE_URL}?")
        return False
    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred during health check:[/]")
        console.print(e)
        return False

def print_payload(payload: Dict[str, Any]):
    """Prints the JSON payload nicely."""
    syntax = Syntax(json.dumps(payload, indent=2), "json", theme="default", line_numbers=False)
    console.print(Panel(syntax, title="Request Payload", border_style="blue", expand=False))

def print_result_summary(results: List[Dict[str, Any]], title: str = "Crawl Results Summary", max_items: int = 3):
    """Prints a concise summary of crawl results."""
    if not results:
        console.print(f"[yellow]{title}: No results received.[/]")
        return

    console.print(Panel(f"[bold]{title}[/]", border_style="green", expand=False))
    count = 0
    for result in results:
        if count >= max_items:
            console.print(f"... (showing first {max_items} of {len(results)} results)")
            break
        count += 1
        success_icon = "[green]✔[/]" if result.get('success') else "[red]✘[/]"
        url = result.get('url', 'N/A')
        status = result.get('status_code', 'N/A')
        content_info = ""
        if result.get('extracted_content'):
            content_str = json.dumps(result['extracted_content'])
            snippet = (content_str[:70] + '...') if len(content_str) > 70 else content_str
            content_info = f" | Extracted: [cyan]{snippet}[/]"
        elif result.get('markdown'):
             content_info = f" | Markdown: [cyan]Present[/]"
        elif result.get('html'):
            content_info = f" | HTML Size: [cyan]{len(result['html'])}[/]"

        console.print(f"{success_icon} URL: [link={url}]{url}[/link] (Status: {status}){content_info}")
        if "metadata" in result and "depth" in result["metadata"]:
            console.print(f"  Depth: {result['metadata']['depth']}")
        if not result.get('success') and result.get('error_message'):
            console.print(f"  [red]Error: {result['error_message']}[/]")


async def make_request(client: httpx.AsyncClient, endpoint: str, payload: Dict[str, Any], title: str) -> Optional[List[Dict[str, Any]]]:
    """Handles non-streaming POST requests."""
    console.rule(f"[bold blue]{title}[/]", style="blue")
    print_payload(payload)
    console.print(f"Sending POST request to {client.base_url}{endpoint}...")
    try:
        start_time = time.time()
        response = await client.post(endpoint, json=payload)
        duration = time.time() - start_time
        console.print(f"Response Status: [bold {'green' if response.is_success else 'red'}]{response.status_code}[/] (took {duration:.2f}s)")
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            results = data.get("results", [])
            print_result_summary(results, title=f"{title} Results")
            return results
        else:
            console.print("[bold red]Request reported failure:[/]")
            console.print(data)
            return None
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]HTTP Error:[/]")
        console.print(f"Status: {e.response.status_code}")
        try:
            console.print(Panel(Syntax(json.dumps(e.response.json(), indent=2), "json", theme="default"), title="Error Response"))
        except json.JSONDecodeError:
            console.print(f"Response Body: {e.response.text}")
    except httpx.RequestError as e:
        console.print(f"[bold red]Request Error: {e}[/]")
    except Exception as e:
        console.print(f"[bold red]Unexpected Error: {e}[/]")
    return None

async def stream_request(client: httpx.AsyncClient, endpoint: str, payload: Dict[str, Any], title: str):
    """Handles streaming POST requests."""
    console.rule(f"[bold magenta]{title}[/]", style="magenta")
    print_payload(payload)
    console.print(f"Sending POST stream request to {client.base_url}{endpoint}...")
    all_results = []
    try:
        start_time = time.time()
        async with client.stream("POST", endpoint, json=payload) as response:
            duration = time.time() - start_time # Time to first byte potentially
            console.print(f"Initial Response Status: [bold {'green' if response.status_code == 200 else 'red'}]{response.status_code}[/] (first byte ~{duration:.2f}s)")
            response.raise_for_status()

            console.print("[magenta]--- Streaming Results ---[/]")
            completed = False
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("status") == "completed":
                            completed = True
                            console.print("[bold green]--- Stream Completed ---[/]")
                            break
                        elif data.get("url"): # Looks like a result
                            all_results.append(data)
                            success_icon = "[green]✔[/]" if data.get('success') else "[red]✘[/]"
                            url = data.get('url', 'N/A')
                            console.print(f"  {success_icon} Received: [link={url}]{url}[/link]")
                        else:
                            console.print(f"  [yellow]Stream meta-data:[/yellow] {data}")
                    except json.JSONDecodeError:
                        console.print(f"  [red]Stream decode error for line:[/red] {line}")
            if not completed:
                 console.print("[bold yellow]Warning: Stream ended without 'completed' marker.[/]")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]HTTP Error:[/]")
        console.print(f"Status: {e.response.status_code}")
        try:
            console.print(Panel(Syntax(json.dumps(e.response.json(), indent=2), "json", theme="default"), title="Error Response"))
        except json.JSONDecodeError:
            console.print(f"Response Body: {e.response.text}")
    except httpx.RequestError as e:
        console.print(f"[bold red]Request Error: {e}[/]")
    except Exception as e:
        console.print(f"[bold red]Unexpected Error: {e}[/]")

    print_result_summary(all_results, title=f"{title} Collected Results")


def load_proxies_from_env() -> List[Dict]:
    """
    Load proxies from the PROXIES environment variable.
    Expected format: IP:PORT:USER:PASS,IP:PORT,IP2:PORT2:USER2:PASS2,...
    Returns a list of dictionaries suitable for the 'params' of ProxyConfig.
    """
    proxies_params_list = []
    proxies_str = os.getenv("PROXIES", "")
    if not proxies_str:
        # console.print("[yellow]PROXIES environment variable not set or empty.[/]")
        return proxies_params_list # Return empty list if not set

    try:
        proxy_entries = proxies_str.split(",")
        for entry in proxy_entries:
            entry = entry.strip()
            if not entry:
                continue

            parts = entry.split(":")
            proxy_dict = {}

            if len(parts) == 4: # Format: IP:PORT:USER:PASS
                ip, port, username, password = parts
                proxy_dict = {
                    "server": f"http://{ip}:{port}", # Assuming http protocol
                    "username": username,
                    "password": password,
                    # "ip": ip # 'ip' is not a standard ProxyConfig param, 'server' contains it
                }
            elif len(parts) == 2: # Format: IP:PORT
                ip, port = parts
                proxy_dict = {
                    "server": f"http://{ip}:{port}",
                    # "ip": ip
                }
            else:
                 console.print(f"[yellow]Skipping invalid proxy string format:[/yellow] {entry}")
                 continue

            proxies_params_list.append(proxy_dict)

    except Exception as e:
        console.print(f"[red]Error loading proxies from environment:[/red] {e}")

    if proxies_params_list:
        console.print(f"[cyan]Loaded {len(proxies_params_list)} proxies from environment.[/]")
    # else:
    #     console.print("[yellow]No valid proxies loaded from environment.[/]")

    return proxies_params_list



# --- Demo Functions ---

# 1. Basic Crawling
async def demo_basic_single_url(client: httpx.AsyncClient):
    payload = {
        "urls": [SIMPLE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {"type": "CrawlerRunConfig", "params": {"cache_mode": "BYPASS"}}
    }
    result = await make_request(client, "/crawl", payload, "Demo 1a: Basic Single URL Crawl")
    return result

async def demo_basic_multi_url(client: httpx.AsyncClient):
    payload = {
        "urls": [SIMPLE_URL, LINKS_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {"type": "CrawlerRunConfig", "params": {"cache_mode": "BYPASS"}}
    }
    result = await make_request(client, "/crawl", payload, "Demo 1b: Basic Multi URL Crawl")
    return result

async def demo_streaming_multi_url(client: httpx.AsyncClient):
    payload = {
        "urls": [SIMPLE_URL, LINKS_URL, FORMS_URL], # Add another URL
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {"type": "CrawlerRunConfig", "params": {"stream": True, "cache_mode": "BYPASS"}}
    }
    result =  stream_request(client, "/crawl/stream", payload, "Demo 1c: Streaming Multi URL Crawl")
    return result

# 2. Markdown Generation & Content Filtering
async def demo_markdown_default(client: httpx.AsyncClient):
    payload = {
        "urls": [SIMPLE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "markdown_generator": {"type": "DefaultMarkdownGenerator", "params": {}} # Explicitly default
            }
        }
    }
    result = await make_request(client, "/crawl", payload, "Demo 2a: Default Markdown Generation")
    return result

async def demo_markdown_pruning(client: httpx.AsyncClient):
    payload = {
        "urls": [PYTHON_URL], # Use a more complex page
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "markdown_generator": {
                    "type": "DefaultMarkdownGenerator",
                    "params": {
                        "content_filter": {
                            "type": "PruningContentFilter",
                            "params": {"threshold": 0.6, "threshold_type": "relative"}
                        }
                    }
                }
            }
        }
    }
    result = await make_request(client, "/crawl", payload, "Demo 2b: Markdown with Pruning Filter")
    return result

async def demo_markdown_bm25(client: httpx.AsyncClient):
    payload = {
        "urls": [PYTHON_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "markdown_generator": {
                    "type": "DefaultMarkdownGenerator",
                    "params": {
                        "content_filter": {
                            "type": "BM25ContentFilter",
                            "params": {"user_query": "Python documentation language reference"}
                        }
                    }
                }
            }
        }
    }
    result = await make_request(client, "/crawl", payload, "Demo 2c: Markdown with BM25 Filter")
    return result

# 3. Specific Parameters
# Corrected Demo Function: demo_param_css_selector
async def demo_param_css_selector(client: httpx.AsyncClient):
    target_selector = ".main-content" # Using the suggested correct selector
    payload = {
        "urls": [PYTHON_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "css_selector": target_selector # Target specific div
                # No extraction strategy is needed to demo this parameter's effect on input HTML
            }
        }
    }
    results = await make_request(client, "/crawl", payload, f"Demo 3a: Using css_selector ('{target_selector}')")

    if results:
        result = results[0]
        if result['success'] and result.get('html'):
            # Check if the returned HTML is likely constrained
            # A simple check: does it contain expected content from within the selector,
            # and does it LACK content known to be outside (like footer links)?
            html_content = result['html']
            content_present = 'Python Software Foundation' in html_content # Text likely within .main-content somewhere
            footer_absent = 'Legal Statements' not in html_content # Text likely in the footer, outside .main-content

            console.print(f"  Content Check: Text inside '{target_selector}' likely present? {'[green]Yes[/]' if content_present else '[red]No[/]'}")
            console.print(f"  Content Check: Text outside '{target_selector}' (footer) likely absent? {'[green]Yes[/]' if footer_absent else '[red]No[/]'}")

            if not content_present or not footer_absent:
                 console.print(f"  [yellow]Note:[/yellow] HTML filtering might not be precise or page structure changed. Result HTML length: {len(html_content)}")
            else:
                 console.print(f"  [green]Verified:[/green] Returned HTML appears limited by css_selector. Result HTML length: {len(html_content)}")

        elif result['success']:
            console.print("[yellow]HTML content was empty in the successful result.[/]")
        # Error message is handled by print_result_summary called by make_request

async def demo_param_js_execution(client: httpx.AsyncClient):
    payload = {
        "urls": [FORMS_URL], # Use a page with a form
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                 # Simple JS to fill and maybe click (won't submit without more complex setup)
                "js_code": """
                    () => {
                        document.querySelector('[name="custname"]').value = 'Crawl4AI Demo';
                        return { filled_name: document.querySelector('[name="custname"]').value };
                    }
                """,
                "delay_before_return_html": 0.5 # Give JS time to potentially run
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 3b: Using js_code Parameter")
    if results and results[0].get("js_execution_result"):
         console.print("[cyan]JS Execution Result:[/]", results[0]["js_execution_result"])
    elif results:
         console.print("[yellow]JS Execution Result not found in response.[/]")


async def demo_param_screenshot(client: httpx.AsyncClient):
    payload = {
        "urls": [SIMPLE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"cache_mode": "BYPASS", "screenshot": True}
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 3c: Taking a Screenshot")
    if results and results[0].get("screenshot"):
        console.print(f"[cyan]Screenshot data received (length):[/] {len(results[0]['screenshot'])}")
    elif results:
         console.print("[yellow]Screenshot data not found in response.[/]")

async def demo_param_ssl_fetch(client: httpx.AsyncClient):
    payload = {
        "urls": [PYTHON_URL], # Needs HTTPS
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"cache_mode": "BYPASS", "fetch_ssl_certificate": True}
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 3d: Fetching SSL Certificate")
    if results and results[0].get("ssl_certificate"):
        console.print("[cyan]SSL Certificate Info:[/]")
        console.print(results[0]["ssl_certificate"])
    elif results:
         console.print("[yellow]SSL Certificate data not found in response.[/]")



async def demo_param_proxy(client: httpx.AsyncClient):
    proxy_params_list = load_proxies_from_env() # Get the list of parameter dicts
    if not proxy_params_list:
        console.rule("[bold yellow]Demo 3e: Using Proxies (SKIPPED)[/]", style="yellow")
        console.print("Set the PROXIES environment variable to run this demo.")
        console.print("Format: IP:PORT:USR:PWD,IP:PORT,...")
        return

    payload = {
        "urls": ["https://httpbin.org/ip"], # URL that shows originating IP
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "proxy_rotation_strategy": {
                    "type": "RoundRobinProxyStrategy",
                    "params": {
                        "proxies": [
                            # Filter out the 'ip' key when sending to server, as it's not part of ProxyConfig
                            {"type": "ProxyConfig", "params": {k: v for k, v in p.items() if k != 'ip'}}
                            for p in proxy_params_list
                        ]
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 3e: Using Proxies")

    # --- Verification Logic ---
    if results and results[0].get("success"):
        result = results[0]
        try:
            # httpbin.org/ip returns JSON within the HTML body's <pre> tag
            html_content = result.get('html', '')
            # Basic extraction - find JSON within <pre> tags or just the JSON itself
            json_str = None
            if '<pre' in html_content:
                start = html_content.find('{')
                end = html_content.rfind('}')
                if start != -1 and end != -1:
                    json_str = html_content[start:end+1]
            elif html_content.strip().startswith('{'): # Maybe it's just JSON
                 json_str = html_content.strip()

            if json_str:
                ip_data = json.loads(json_str)
                origin_ip = ip_data.get("origin")
                console.print(f"  Origin IP reported by httpbin: [bold yellow]{origin_ip}[/]")

                # Extract the IPs from the proxy list for comparison
                proxy_ips = {p.get("server").split(":")[1][2:] for p in proxy_params_list}

                if origin_ip and origin_ip in proxy_ips:
                    console.print("[bold green]  Verification SUCCESS: Origin IP matches one of the provided proxies![/]")
                elif origin_ip:
                    console.print("[bold red]  Verification FAILED: Origin IP does not match any provided proxy IPs.[/]")
                    console.print(f"  Provided Proxy IPs: {proxy_ips}")
                else:
                    console.print("[yellow]  Verification SKIPPED: Could not extract origin IP from response.[/]")
            else:
                 console.print("[yellow]  Verification SKIPPED: Could not find JSON in httpbin response HTML.[/]")
                 # console.print(f"HTML Received:\n{html_content[:500]}...") # Uncomment for debugging

        except json.JSONDecodeError:
             console.print("[red]  Verification FAILED: Could not parse JSON from httpbin response HTML.[/]")
        except Exception as e:
             console.print(f"[red]  Verification Error: An unexpected error occurred during IP check: {e}[/]")
    elif results:
        console.print("[yellow]  Verification SKIPPED: Crawl for IP check was not successful.[/]")

# 4. Extraction Strategies (Non-Deep)
async def demo_extract_css(client: httpx.AsyncClient):
    # Schema to extract book titles and prices
    book_schema = {
        "name": "BookList",
        "baseSelector": "ol.row li.col-xs-6",
        "fields": [
            {"name": "title", "selector": "article.product_pod h3 a", "type": "attribute", "attribute": "title"},
            {"name": "price", "selector": "article.product_pod .price_color", "type": "text"},
        ]
    }
    payload = {
        "urls": [BOOKS_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "extraction_strategy": {
                    "type": "JsonCssExtractionStrategy",
                     "params": {"schema": {"type": "dict", "value": book_schema}}
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 4a: JSON/CSS Extraction")

    if results and results[0].get("success") and results[0].get("extracted_content"):
        try:
            extracted_data = json.loads(results[0]["extracted_content"])
            if isinstance(extracted_data, list) and extracted_data:
                 console.print("[cyan]Sample Extracted Books (CSS):[/]")
                 table = Table(show_header=True, header_style="bold magenta")
                 table.add_column("Title", style="dim")
                 table.add_column("Price")
                 for item in extracted_data[:5]: # Show first 5
                     table.add_row(item.get('title', 'N/A'), item.get('price', 'N/A'))
                 console.print(table)
            else:
                 console.print("[yellow]CSS extraction did not return a list of results.[/]")
                 console.print(extracted_data)
        except json.JSONDecodeError:
             console.print("[red]Failed to parse extracted_content as JSON.[/]")
        except Exception as e:
             console.print(f"[red]Error processing extracted CSS content: {e}[/]")

# 5. LLM Extraction
async def demo_extract_llm(client: httpx.AsyncClient):
    if not os.getenv("OPENAI_API_KEY"): # Basic check for a common key
         console.rule("[bold yellow]Demo 4b: LLM Extraction (SKIPPED)[/]", style="yellow")
         console.print("Set an LLM API key (e.g., OPENAI_API_KEY) in your .env file or environment.")
         return

    payload = {
        "urls": [SIMPLE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "extraction_strategy": {
                    "type": "LLMExtractionStrategy",
                    "params": {
                        "instruction": "Extract title and author into JSON.",
                        "llm_config": { # Optional: Specify provider if not default
                            "type": "LLMConfig",
                            "params": {}
                            # Relies on server's default provider from config.yml & keys from .llm.env
                            # "params": {"provider": "openai/gpt-4o-mini"}
                        },
                         "schema": { # Request structured output
                            "type": "dict",
                            "value": {
                                "title": "BookInfo", "type": "object",
                                "properties": {
                                    "book_title": {"type": "string"},
                                    "book_author": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 4b: LLM Extraction")

    if results and results[0].get("success") and results[0].get("extracted_content"):
        try:
            extracted_data = json.loads(results[0]["extracted_content"])
            # Handle potential list wrapper from server
            if isinstance(extracted_data, list) and extracted_data:
                extracted_data = extracted_data[0]

            if isinstance(extracted_data, dict):
                 console.print("[cyan]Extracted Data (LLM):[/]")
                 syntax = Syntax(json.dumps(extracted_data, indent=2), "json", theme="default", line_numbers=False)
                 console.print(Panel(syntax, border_style="cyan", expand=False))
            else:
                 console.print("[yellow]LLM extraction did not return expected dictionary.[/]")
                 console.print(extracted_data)
        except json.JSONDecodeError:
             console.print("[red]Failed to parse LLM extracted_content as JSON.[/]")
        except Exception as e:
             console.print(f"[red]Error processing extracted LLM content: {e}[/]")

# 6. Deep Crawling
async def demo_deep_basic(client: httpx.AsyncClient):
    payload = {
        "urls": [DEEP_CRAWL_BASE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 1,
                        "max_pages": 4,
                        "filter_chain": {
                            "type": "FilterChain",
                            "params": {"filters": [{"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}}]}
                        }
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 5a: Basic Deep Crawl")
    # print_result_summary is called by make_request, showing URLs and depths

# 5. Streaming Deep Crawl
async def demo_deep_streaming(client: httpx.AsyncClient):
    payload = {
        "urls": [DEEP_CRAWL_BASE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "stream": True, # Enable streaming
                "cache_mode": "BYPASS",
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 1,
                        "max_pages": 4,
                        "filter_chain": {
                            "type": "FilterChain",
                            "params": {"filters": [{"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}}]}
                        }
                    }
                }
            }
        }
    }
    # stream_request handles printing results as they arrive
    await stream_request(client, "/crawl/stream", payload, "Demo 5b: Streaming Deep Crawl")

# 6. Deep Crawl with Extraction
async def demo_deep_with_css_extraction(client: httpx.AsyncClient):
    # Schema to extract H1 and first paragraph from any page
    general_schema = {
        "name": "PageContent",
        "baseSelector": "body", # Apply to whole body
        "fields": [
            {"name": "page_title", "selector": "h1", "type": "text", "default": "N/A"},
            {"name": "first_p", "selector": "p", "type": "text", "default": "N/A"}, # Gets first p tag
        ]
    }
    payload = {
        "urls": [DEEP_CRAWL_BASE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                "extraction_strategy": { # Apply CSS extraction to each page
                    "type": "JsonCssExtractionStrategy",
                    "params": {"schema": {"type": "dict", "value": general_schema}}
                },
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 1,
                        "max_pages": 3,
                        "filter_chain": {
                            "type": "FilterChain",
                            "params": {"filters": [
                                {"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}},
                                {"type": "ContentTypeFilter", "params": {"allowed_types": ["text/html"]}}
                                ]}
                        }
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 6a: Deep Crawl + CSS Extraction")

    if results:
        console.print("[cyan]CSS Extraction Summary from Deep Crawl:[/]")
        for result in results:
            if result.get("success") and result.get("extracted_content"):
                try:
                    extracted = json.loads(result["extracted_content"])
                    if isinstance(extracted, list) and extracted: extracted = extracted[0] # Use first item
                    title = extracted.get('page_title', 'N/A') if isinstance(extracted, dict) else 'Parse Error'
                    console.print(f"  [green]✔[/] URL: [link={result['url']}]{result['url']}[/link] | Title: {title}")
                except Exception:
                     console.print(f"  [yellow]![/] URL: [link={result['url']}]{result['url']}[/link] | Failed to parse extracted content")
            elif result.get("success"):
                 console.print(f"  [yellow]-[/] URL: [link={result['url']}]{result['url']}[/link] | No content extracted.")
            else:
                 console.print(f"  [red]✘[/] URL: [link={result['url']}]{result['url']}[/link] | Crawl failed.")

# 6b. Deep Crawl with LLM Extraction
async def demo_deep_with_llm_extraction(client: httpx.AsyncClient):
    if not os.getenv("OPENAI_API_KEY"): # Basic check
         console.rule("[bold yellow]Demo 6b: Deep Crawl + LLM Extraction (SKIPPED)[/]", style="yellow")
         console.print("Set an LLM API key (e.g., OPENAI_API_KEY) in your .env file or environment.")
         return

    payload = {
        "urls": [DEEP_CRAWL_BASE_URL],
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                 "extraction_strategy": { # Apply LLM extraction to each page
                    "type": "LLMExtractionStrategy",
                    "params": {
                        "instruction": "What is the main topic of this page based on the H1 and first paragraph? Respond with just the topic.",
                        # Rely on server default LLM config + .llm.env keys
                    }
                },
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 1,
                        "max_pages": 2, # Reduce pages for LLM cost/time
                         "filter_chain": {
                            "type": "FilterChain",
                            "params": {"filters": [
                                {"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}},
                                {"type": "ContentTypeFilter", "params": {"allowed_types": ["text/html"]}}
                                ]}
                        }
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 6b: Deep Crawl + LLM Extraction")

    if results:
        console.print("[cyan]LLM Extraction Summary from Deep Crawl:[/]")
        for result in results:
            if result.get("success") and result.get("extracted_content"):
                 console.print(f"  [green]✔[/] URL: [link={result['url']}]{result['url']}[/link] | Topic: {result['extracted_content']}")
            elif result.get("success"):
                 console.print(f"  [yellow]-[/] URL: [link={result['url']}]{result['url']}[/link] | No content extracted.")
            else:
                 console.print(f"  [red]✘[/] URL: [link={result['url']}]{result['url']}[/link] | Crawl failed.")


# 6c. Deep Crawl with Proxies
async def demo_deep_with_proxy(client: httpx.AsyncClient):
    proxy_params_list = load_proxies_from_env() # Get the list of parameter dicts
    if not proxy_params_list:
        console.rule("[bold yellow]Demo 6c: Deep Crawl + Proxies (SKIPPED)[/]", style="yellow")
        console.print("Set the PROXIES environment variable to run this demo.")
        return

    payload = {
        "urls": [DEEP_CRAWL_BASE_URL], # Use a site likely accessible via proxies
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "cache_mode": "BYPASS",
                 "proxy_rotation_strategy": {
                    "type": "RoundRobinProxyStrategy",
                     "params": {
                        # Correctly create the list of {"type": ..., "params": ...} structures, excluding the demo 'ip' key
                        "proxies": [
                            {"type": "ProxyConfig", "params": {k: v for k, v in p.items() if k != 'ip'}}
                            for p in proxy_params_list
                        ]
                    }
                },
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 0, # Just crawl start URL via proxy
                        "max_pages": 1,
                    }
                }
            }
        }
    }
    # make_request calls print_result_summary, which shows URL and success status
    await make_request(client, "/crawl", payload, "Demo 6c: Deep Crawl + Proxies")
    # Verification of specific proxy IP usage would require more complex setup or server logs.


# 6d. Deep Crawl with SSL Certificate Fetching
async def demo_deep_with_ssl(client: httpx.AsyncClient):
    """Test BFS deep crawl with fetch_ssl_certificate enabled."""
    payload = {
        "urls": [DEEP_CRAWL_BASE_URL], # Needs HTTPS
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "stream": False,
                "cache_mode": "BYPASS",
                "fetch_ssl_certificate": True, # <-- Enable SSL fetching
                "deep_crawl_strategy": {
                    "type": "BFSDeepCrawlStrategy",
                    "params": {
                        "max_depth": 1, # Crawl a bit deeper
                        "max_pages": 3,
                        "filter_chain": {
                            "type": "FilterChain",
                            "params": {"filters": [{"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}}]}
                        }
                    }
                }
            }
        }
    }
    results = await make_request(client, "/crawl", payload, "Demo 6d: Deep Crawl + Fetch SSL")

    if results:
        console.print("[cyan]SSL Certificate Summary from Deep Crawl:[/]")
        for result in results:
            if result.get("success") and result.get("ssl_certificate"):
                 cert = result["ssl_certificate"]
                 issuer_org = cert.get('issuer', {}).get('O', 'N/A')
                 valid_from = cert.get('not_before', 'N/A')
                 valid_to = cert.get('not_after', 'N/A')
                 console.print(f"  [green]✔[/] URL: [link={result['url']}]{result['url']}[/link] | Issuer: {issuer_org} | Valid: {valid_from} - {valid_to}")
            elif result.get("success"):
                 console.print(f"  [yellow]-[/] URL: [link={result['url']}]{result['url']}[/link] | SSL cert not fetched or N/A.")
            else:
                 console.print(f"  [red]✘[/] URL: [link={result['url']}]{result['url']}[/link] | Crawl failed.")


# --- Update Main Runner to include new demo ---
async def main_demo():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=300.0) as client:
        if not await check_server_health(client):
            return

        # --- Run Demos ---
        # await demo_basic_single_url(client)
        # await demo_basic_multi_url(client)
        # await demo_streaming_multi_url(client)

        # await demo_markdown_default(client)
        # await demo_markdown_pruning(client)
        # await demo_markdown_bm25(client)

        # await demo_param_css_selector(client)
        # await demo_param_js_execution(client)
        # await demo_param_screenshot(client)
        # await demo_param_ssl_fetch(client)
        # await demo_param_proxy(client) # Skips if no PROXIES env var

        # await demo_extract_css(client)
        await demo_extract_llm(client) # Skips if no common LLM key env var

        await demo_deep_basic(client)
        await demo_deep_streaming(client)
        # demo_deep_filtering_scoring skipped for brevity, add if needed

        await demo_deep_with_css_extraction(client)
        await demo_deep_with_llm_extraction(client) # Skips if no common LLM key env var
        await demo_deep_with_proxy(client) # Skips if no PROXIES env var
        await demo_deep_with_ssl(client) # Added the new demo

        console.rule("[bold green]Demo Complete[/]", style="green")


if __name__ == "__main__":
    try:
        asyncio.run(main_demo())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user.[/]")
    except Exception as e:
         console.print(f"\n[bold red]An error occurred during demo execution:[/]")
         console.print_exception(show_locals=False)