I want to enhance the `AsyncPlaywrightCrawlerStrategy` to optionally capture network requests and console messages during a crawl, storing them in the final `CrawlResult`.

Here's a breakdown of the proposed changes across the relevant files:

**1. Configuration (`crawl4ai/async_configs.py`)**

*   **Goal:** Add flags to `CrawlerRunConfig` to enable/disable capturing.
*   **Changes:**
    *   Add two new boolean attributes to `CrawlerRunConfig`:
        *   `capture_network_requests: bool = False`
        *   `capture_console_messages: bool = False`
    *   Update `__init__`, `from_kwargs`, `to_dict`, and implicitly `clone`/`dump`/`load` to include these new attributes.

```python
# ==== File: crawl4ai/async_configs.py ====
# ... (imports) ...

class CrawlerRunConfig():
    # ... (existing attributes) ...

    # NEW: Network and Console Capturing Parameters
    capture_network_requests: bool = False
    capture_console_messages: bool = False

    # Experimental Parameters
    experimental: Dict[str, Any] = None,

    def __init__(
        self,
        # ... (existing parameters) ...

        # NEW: Network and Console Capturing Parameters
        capture_network_requests: bool = False,
        capture_console_messages: bool = False,

        # Experimental Parameters
        experimental: Dict[str, Any] = None,
    ):
        # ... (existing assignments) ...

        # NEW: Assign new parameters
        self.capture_network_requests = capture_network_requests
        self.capture_console_messages = capture_console_messages

        # Experimental Parameters
        self.experimental = experimental or {}

        # ... (rest of __init__) ...

    @staticmethod
    def from_kwargs(kwargs: dict) -> "CrawlerRunConfig":
        return CrawlerRunConfig(
            # ... (existing kwargs gets) ...

            # NEW: Get new parameters
            capture_network_requests=kwargs.get("capture_network_requests", False),
            capture_console_messages=kwargs.get("capture_console_messages", False),

            # Experimental Parameters
            experimental=kwargs.get("experimental"),
        )

    def to_dict(self):
        return {
            # ... (existing dict entries) ...

            # NEW: Add new parameters to dict
            "capture_network_requests": self.capture_network_requests,
            "capture_console_messages": self.capture_console_messages,

            "experimental": self.experimental,
        }

    # clone(), dump(), load() should work automatically if they rely on to_dict() and from_kwargs()
    # or the serialization logic correctly handles all attributes.
```

**2. Data Models (`crawl4ai/models.py`)**

*   **Goal:** Add fields to store the captured data in the response/result objects.
*   **Changes:**
    *   Add `network_requests: Optional[List[Dict[str, Any]]] = None` and `console_messages: Optional[List[Dict[str, Any]]] = None` to `AsyncCrawlResponse`.
    *   Add the same fields to `CrawlResult`.

```python
# ==== File: crawl4ai/models.py ====
# ... (imports) ...

# ... (Existing dataclasses/models) ...

class AsyncCrawlResponse(BaseModel):
    html: str
    response_headers: Dict[str, str]
    js_execution_result: Optional[Dict[str, Any]] = None
    status_code: int
    screenshot: Optional[str] = None
    pdf_data: Optional[bytes] = None
    get_delayed_content: Optional[Callable[[Optional[float]], Awaitable[str]]] = None
    downloaded_files: Optional[List[str]] = None
    ssl_certificate: Optional[SSLCertificate] = None
    redirected_url: Optional[str] = None
    # NEW: Fields for captured data
    network_requests: Optional[List[Dict[str, Any]]] = None
    console_messages: Optional[List[Dict[str, Any]]] = None

    class Config:
        arbitrary_types_allowed = True

# ... (Existing models like MediaItem, Link, etc.) ...

class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: Optional[str] = None
    media: Dict[str, List[Dict]] = {}
    links: Dict[str, List[Dict]] = {}
    downloaded_files: Optional[List[str]] = None
    js_execution_result: Optional[Dict[str, Any]] = None
    screenshot: Optional[str] = None
    pdf: Optional[bytes] = None
    mhtml: Optional[str] = None # Added mhtml based on the provided models.py
    _markdown: Optional[MarkdownGenerationResult] = PrivateAttr(default=None)
    extracted_content: Optional[str] = None
    metadata: Optional[dict] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    response_headers: Optional[dict] = None
    status_code: Optional[int] = None
    ssl_certificate: Optional[SSLCertificate] = None
    dispatch_result: Optional[DispatchResult] = None
    redirected_url: Optional[str] = None
    # NEW: Fields for captured data
    network_requests: Optional[List[Dict[str, Any]]] = None
    console_messages: Optional[List[Dict[str, Any]]] = None

    class Config:
        arbitrary_types_allowed = True

    # ... (Existing __init__, properties, model_dump for markdown compatibility) ...

# ... (Rest of the models) ...
```

**3. Crawler Strategy (`crawl4ai/async_crawler_strategy.py`)**

*   **Goal:** Implement the actual capturing logic within `AsyncPlaywrightCrawlerStrategy._crawl_web`.
*   **Changes:**
    *   Inside `_crawl_web`, initialize empty lists `captured_requests = []` and `captured_console = []`.
    *   Conditionally attach Playwright event listeners (`page.on(...)`) based on the `config.capture_network_requests` and `config.capture_console_messages` flags.
    *   Define handler functions for these listeners to extract relevant data and append it to the respective lists. Include timestamps.
    *   Pass the captured lists to the `AsyncCrawlResponse` constructor at the end of the method.

```python
# ==== File: crawl4ai/async_crawler_strategy.py ====
# ... (imports) ...
import time # Make sure time is imported

class AsyncPlaywrightCrawlerStrategy(AsyncCrawlerStrategy):
    # ... (existing methods like __init__, start, close, etc.) ...

    async def _crawl_web(
        self, url: str, config: CrawlerRunConfig
    ) -> AsyncCrawlResponse:
        """
        Internal method to crawl web URLs with the specified configuration.
        Includes optional network and console capturing. # MODIFIED DOCSTRING
        """
        config.url = url
        response_headers = {}
        execution_result = None
        status_code = None
        redirected_url = url

        # Reset downloaded files list for new crawl
        self._downloaded_files = []

        # Initialize capture lists - IMPORTANT: Reset per crawl
        captured_requests: List[Dict[str, Any]] = []
        captured_console: List[Dict[str, Any]] = []

        # Handle user agent ... (existing code) ...

        # Get page for session
        page, context = await self.browser_manager.get_page(crawlerRunConfig=config)

        # ... (existing code for cookies, navigator overrides, hooks) ...

        # --- Setup Capturing Listeners ---
        # NOTE: These listeners are attached *before* page.goto()

        # Network Request Capturing
        if config.capture_network_requests:
            async def handle_request_capture(request):
                try:
                    post_data_str = None
                    try:
                        # Be cautious with large post data
                        post_data = request.post_data_buffer
                        if post_data:
                             # Attempt to decode, fallback to base64 or size indication
                             try:
                                 post_data_str = post_data.decode('utf-8', errors='replace')
                             except UnicodeDecodeError:
                                 post_data_str = f"[Binary data: {len(post_data)} bytes]"
                    except Exception:
                        post_data_str = "[Error retrieving post data]"

                    captured_requests.append({
                        "event_type": "request",
                        "url": request.url,
                        "method": request.method,
                        "headers": dict(request.headers), # Convert Header dict
                        "post_data": post_data_str,
                        "resource_type": request.resource_type,
                        "is_navigation_request": request.is_navigation_request(),
                        "timestamp": time.time()
                    })
                except Exception as e:
                    self.logger.warning(f"Error capturing request details for {request.url}: {e}", tag="CAPTURE")
                    captured_requests.append({"event_type": "request_capture_error", "url": request.url, "error": str(e), "timestamp": time.time()})

            async def handle_response_capture(response):
                try:
                    # Avoid capturing full response body by default due to size/security
                    # security_details = await response.security_details() # Optional: More SSL info
                    captured_requests.append({
                        "event_type": "response",
                        "url": response.url,
                        "status": response.status,
                        "status_text": response.status_text,
                        "headers": dict(response.headers), # Convert Header dict
                        "from_service_worker": response.from_service_worker,
                        # "security_details": security_details, # Uncomment if needed
                        "request_timing": response.request.timing, # Detailed timing info
                        "timestamp": time.time()
                    })
                except Exception as e:
                    self.logger.warning(f"Error capturing response details for {response.url}: {e}", tag="CAPTURE")
                    captured_requests.append({"event_type": "response_capture_error", "url": response.url, "error": str(e), "timestamp": time.time()})

            async def handle_request_failed_capture(request):
                 try:
                    captured_requests.append({
                        "event_type": "request_failed",
                        "url": request.url,
                        "method": request.method,
                        "resource_type": request.resource_type,
                        "failure_text": request.failure.error_text if request.failure else "Unknown failure",
                        "timestamp": time.time()
                    })
                 except Exception as e:
                    self.logger.warning(f"Error capturing request failed details for {request.url}: {e}", tag="CAPTURE")
                    captured_requests.append({"event_type": "request_failed_capture_error", "url": request.url, "error": str(e), "timestamp": time.time()})

            page.on("request", handle_request_capture)
            page.on("response", handle_response_capture)
            page.on("requestfailed", handle_request_failed_capture)

        # Console Message Capturing
        if config.capture_console_messages:
            def handle_console_capture(msg):
                 try:
                    location = msg.location()
                    # Attempt to resolve JSHandle args to primitive values
                    resolved_args = []
                    try:
                        for arg in msg.args:
                            resolved_args.append(arg.json_value()) # May fail for complex objects
                    except Exception:
                         resolved_args.append("[Could not resolve JSHandle args]")

                    captured_console.append({
                        "type": msg.type(), # e.g., 'log', 'error', 'warning'
                        "text": msg.text(),
                        "args": resolved_args, # Captured arguments
                        "location": f"{location['url']}:{location['lineNumber']}:{location['columnNumber']}" if location else "N/A",
                        "timestamp": time.time()
                    })
                 except Exception as e:
                    self.logger.warning(f"Error capturing console message: {e}", tag="CAPTURE")
                    captured_console.append({"type": "console_capture_error", "error": str(e), "timestamp": time.time()})

            def handle_pageerror_capture(err):
                 try:
                    captured_console.append({
                        "type": "error", # Consistent type for page errors
                        "text": err.message,
                        "stack": err.stack,
                        "timestamp": time.time()
                    })
                 except Exception as e:
                    self.logger.warning(f"Error capturing page error: {e}", tag="CAPTURE")
                    captured_console.append({"type": "pageerror_capture_error", "error": str(e), "timestamp": time.time()})

            page.on("console", handle_console_capture)
            page.on("pageerror", handle_pageerror_capture)
        # --- End Setup Capturing Listeners ---


        # Set up console logging if requested (Keep original logging logic separate or merge carefully)
        if config.log_console:
            # ... (original log_console setup using page.on(...) remains here) ...
            # This allows logging to screen *and* capturing to the list if both flags are True
            def log_consol(msg, console_log_type="debug"):
                # ... existing implementation ...
                pass # Placeholder for existing code

            page.on("console", lambda msg: log_consol(msg, "debug"))
            page.on("pageerror", lambda e: log_consol(e, "error"))


        try:
            # ... (existing code for SSL, downloads, goto, waits, JS execution, etc.) ...

            # Get final HTML content
            # ... (existing code for selector logic or page.content()) ...
            if config.css_selector:
                # ... existing selector logic ...
                html = f"<div class='crawl4ai-result'>\n" + "\n".join(html_parts) + "\n</div>"
            else:
                html = await page.content()

            await self.execute_hook(
                "before_return_html", page=page, html=html, context=context, config=config
            )

            # Handle PDF and screenshot generation
            # ... (existing code) ...

            # Define delayed content getter
            # ... (existing code) ...

            # Return complete response - ADD CAPTURED DATA HERE
            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                js_execution_result=execution_result,
                status_code=status_code,
                screenshot=screenshot_data,
                pdf_data=pdf_data,
                get_delayed_content=get_delayed_content,
                ssl_certificate=ssl_cert,
                downloaded_files=(
                    self._downloaded_files if self._downloaded_files else None
                ),
                redirected_url=redirected_url,
                # NEW: Pass captured data conditionally
                network_requests=captured_requests if config.capture_network_requests else None,
                console_messages=captured_console if config.capture_console_messages else None,
            )

        except Exception as e:
            raise e # Re-raise the original exception

        finally:
            # If no session_id is given we should close the page
            if not config.session_id:
                # Detach listeners before closing to prevent potential errors during close
                if config.capture_network_requests:
                    page.remove_listener("request", handle_request_capture)
                    page.remove_listener("response", handle_response_capture)
                    page.remove_listener("requestfailed", handle_request_failed_capture)
                if config.capture_console_messages:
                    page.remove_listener("console", handle_console_capture)
                    page.remove_listener("pageerror", handle_pageerror_capture)
                # Also remove logging listeners if they were attached
                if config.log_console:
                    # Need to figure out how to remove the lambdas if necessary,
                    # or ensure they don't cause issues on close. Often, it's fine.
                    pass

                await page.close()

    # ... (rest of AsyncPlaywrightCrawlerStrategy methods) ...

```

**4. Core Crawler (`crawl4ai/async_webcrawler.py`)**

*   **Goal:** Ensure the captured data from `AsyncCrawlResponse` is transferred to the final `CrawlResult`.
*   **Changes:**
    *   In `arun`, when processing a non-cached result (inside the `if not cached_result or not html:` block), after receiving `async_response` and calling `aprocess_html` to get `crawl_result`, copy the `network_requests` and `console_messages` from `async_response` to `crawl_result`.

```python
# ==== File: crawl4ai/async_webcrawler.py ====
# ... (imports) ...

class AsyncWebCrawler:
    # ... (existing methods) ...

    async def arun(
        self,
        url: str,
        config: CrawlerRunConfig = None,
        **kwargs,
    ) -> RunManyReturn:
        # ... (existing setup, cache check) ...

        async with self._lock or self.nullcontext():
            try:
                # ... (existing logging, cache context setup) ...

                if cached_result:
                    # ... (existing cache handling logic) ...
                    # Note: Captured network/console usually not useful from cache
                    # Ensure they are None or empty if read from cache, unless stored explicitly
                    cached_result.network_requests = cached_result.network_requests or None
                    cached_result.console_messages = cached_result.console_messages or None
                    # ... (rest of cache logic) ...

                # Fetch fresh content if needed
                if not cached_result or not html:
                    t1 = time.perf_counter()

                    # ... (existing user agent update, robots.txt check) ...

                    ##############################
                    # Call CrawlerStrategy.crawl #
                    ##############################
                    async_response = await self.crawler_strategy.crawl(
                        url,
                        config=config,
                    )

                    # ... (existing assignment of html, screenshot, pdf, js_result from async_response) ...

                    t2 = time.perf_counter()
                    # ... (existing logging) ...

                    ###############################################################
                    # Process the HTML content, Call CrawlerStrategy.process_html #
                    ###############################################################
                    crawl_result: CrawlResult = await self.aprocess_html(
                        # ... (existing args) ...
                    )

                    # --- Transfer data from AsyncCrawlResponse to CrawlResult ---
                    crawl_result.status_code = async_response.status_code
                    crawl_result.redirected_url = async_response.redirected_url or url
                    crawl_result.response_headers = async_response.response_headers
                    crawl_result.downloaded_files = async_response.downloaded_files
                    crawl_result.js_execution_result = js_execution_result
                    crawl_result.ssl_certificate = async_response.ssl_certificate
                    # NEW: Copy captured data
                    crawl_result.network_requests = async_response.network_requests
                    crawl_result.console_messages = async_response.console_messages
                    # ------------------------------------------------------------

                    crawl_result.success = bool(html)
                    crawl_result.session_id = getattr(config, "session_id", None)

                    # ... (existing logging) ...

                    # Update cache if appropriate
                    if cache_context.should_write() and not bool(cached_result):
                        # crawl_result now includes network/console data if captured
                        await async_db_manager.acache_url(crawl_result)

                    return CrawlResultContainer(crawl_result)

                else: # Cached result was used
                     # ... (existing logging for cache hit) ...
                    cached_result.success = bool(html)
                    cached_result.session_id = getattr(config, "session_id", None)
                    cached_result.redirected_url = cached_result.redirected_url or url
                    return CrawlResultContainer(cached_result)

            except Exception as e:
                # ... (existing error handling) ...
                return CrawlResultContainer(
                    CrawlResult(
                        url=url, html="", success=False, error_message=error_message
                    )
                )

    # ... (aprocess_html remains unchanged regarding capture) ...

    # ... (arun_many remains unchanged regarding capture) ...
```

**Summary of Changes:**

1.  **Configuration:** Added `capture_network_requests` and `capture_console_messages` flags to `CrawlerRunConfig`.
2.  **Models:** Added corresponding `network_requests` and `console_messages` fields (List of Dicts) to `AsyncCrawlResponse` and `CrawlResult`.
3.  **Strategy:** Implemented conditional event listeners in `AsyncPlaywrightCrawlerStrategy._crawl_web` to capture data into lists when flags are true. Populated these fields in the returned `AsyncCrawlResponse`. Added basic error handling within capture handlers. Added timestamps.
4.  **Crawler:** Modified `AsyncWebCrawler.arun` to copy the captured data from `AsyncCrawlResponse` into the final `CrawlResult` for non-cached fetches.

This approach keeps the capturing logic contained within the Playwright strategy, uses clear configuration flags, and integrates the results into the existing data flow. The data format (list of dictionaries) is flexible for storing varied information from requests/responses/console messages.