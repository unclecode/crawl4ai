# browser_adapter.py
"""
Browser adapter for Crawl4AI to support both Playwright and undetected browsers
with minimal changes to existing codebase.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
import time
import json

# Import both, but use conditionally
try:
    from playwright.async_api import Page
except ImportError:
    Page = Any

try:
    from patchright.async_api import Page as UndetectedPage
except ImportError:
    UndetectedPage = Any


class BrowserAdapter(ABC):
    """Abstract adapter for browser-specific operations"""
    
    @abstractmethod
    async def evaluate(self, page: Page, expression: str, arg: Any = None) -> Any:
        """Execute JavaScript in the page"""
        pass
    
    @abstractmethod
    async def setup_console_capture(self, page: Page, captured_console: List[Dict]) -> Optional[Callable]:
        """Setup console message capturing, returns handler function if needed"""
        pass
    
    @abstractmethod
    async def setup_error_capture(self, page: Page, captured_console: List[Dict]) -> Optional[Callable]:
        """Setup error capturing, returns handler function if needed"""
        pass
    
    @abstractmethod
    async def retrieve_console_messages(self, page: Page) -> List[Dict]:
        """Retrieve captured console messages (for undetected browsers)"""
        pass
    
    @abstractmethod
    async def cleanup_console_capture(self, page: Page, handle_console: Optional[Callable], handle_error: Optional[Callable]):
        """Clean up console event listeners"""
        pass
    
    @abstractmethod
    def get_imports(self) -> tuple:
        """Get the appropriate imports for this adapter"""
        pass


class PlaywrightAdapter(BrowserAdapter):
    """Adapter for standard Playwright"""
    
    async def evaluate(self, page: Page, expression: str, arg: Any = None) -> Any:
        """Standard Playwright evaluate"""
        if arg is not None:
            return await page.evaluate(expression, arg)
        return await page.evaluate(expression)
    
    async def setup_console_capture(self, page: Page, captured_console: List[Dict]) -> Optional[Callable]:
        """Setup console capture using Playwright's event system"""
        def handle_console_capture(msg):
            try:
                message_type = "unknown"
                try:
                    message_type = msg.type
                except:
                    pass
                    
                message_text = "unknown"
                try:
                    message_text = msg.text
                except:
                    pass
                    
                entry = {
                    "type": message_type,
                    "text": message_text,
                    "timestamp": time.time()
                }
                
                captured_console.append(entry)
                
            except Exception as e:
                captured_console.append({
                    "type": "console_capture_error", 
                    "error": str(e), 
                    "timestamp": time.time()
                })
        
        page.on("console", handle_console_capture)
        return handle_console_capture
    
    async def setup_error_capture(self, page: Page, captured_console: List[Dict]) -> Optional[Callable]:
        """Setup error capture using Playwright's event system"""
        def handle_pageerror_capture(err):
            try:
                error_message = "Unknown error"
                try:
                    error_message = err.message
                except:
                    pass
                    
                error_stack = ""
                try:
                    error_stack = err.stack
                except:
                    pass
                    
                captured_console.append({
                    "type": "error",
                    "text": error_message,
                    "stack": error_stack,
                    "timestamp": time.time()
                })
            except Exception as e:
                captured_console.append({
                    "type": "pageerror_capture_error", 
                    "error": str(e), 
                    "timestamp": time.time()
                })
        
        page.on("pageerror", handle_pageerror_capture)
        return handle_pageerror_capture
    
    async def retrieve_console_messages(self, page: Page) -> List[Dict]:
        """Not needed for Playwright - messages are captured via events"""
        return []
    
    async def cleanup_console_capture(self, page: Page, handle_console: Optional[Callable], handle_error: Optional[Callable]):
        """Remove event listeners"""
        if handle_console:
            page.remove_listener("console", handle_console)
        if handle_error:
            page.remove_listener("pageerror", handle_error)
    
    def get_imports(self) -> tuple:
        """Return Playwright imports"""
        from playwright.async_api import Page, Error
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        return Page, Error, PlaywrightTimeoutError


class UndetectedAdapter(BrowserAdapter):
    """Adapter for undetected browser automation with stealth features"""
    
    def __init__(self):
        self._console_script_injected = {}
    
    async def evaluate(self, page: UndetectedPage, expression: str, arg: Any = None) -> Any:
        """Undetected browser evaluate with isolated context"""
        # For most evaluations, use isolated context for stealth
        # Only use non-isolated when we need to access our injected console capture
        isolated = not (
            "__console" in expression or 
            "__captured" in expression or
            "__error" in expression or
            "window.__" in expression
        )
        
        if arg is not None:
            return await page.evaluate(expression, arg, isolated_context=isolated)
        return await page.evaluate(expression, isolated_context=isolated)
    
    async def setup_console_capture(self, page: UndetectedPage, captured_console: List[Dict]) -> Optional[Callable]:
        """Setup console capture using JavaScript injection for undetected browsers"""
        if not self._console_script_injected.get(page, False):
            await page.add_init_script("""
                // Initialize console capture
                window.__capturedConsole = [];
                window.__capturedErrors = [];
                
                // Store original console methods
                const originalConsole = {};
                ['log', 'info', 'warn', 'error', 'debug'].forEach(method => {
                    originalConsole[method] = console[method];
                    console[method] = function(...args) {
                        try {
                            window.__capturedConsole.push({
                                type: method,
                                text: args.map(arg => {
                                    try {
                                        if (typeof arg === 'object') {
                                            return JSON.stringify(arg);
                                        }
                                        return String(arg);
                                    } catch (e) {
                                        return '[Object]';
                                    }
                                }).join(' '),
                                timestamp: Date.now()
                            });
                        } catch (e) {
                            // Fail silently to avoid detection
                        }
                        
                        // Call original method
                        originalConsole[method].apply(console, args);
                    };
                });
            """)
            self._console_script_injected[page] = True
        
        return None  # No handler function needed for undetected browser
    
    async def setup_error_capture(self, page: UndetectedPage, captured_console: List[Dict]) -> Optional[Callable]:
        """Setup error capture using JavaScript injection for undetected browsers"""
        if not self._console_script_injected.get(page, False):
            await page.add_init_script("""
                // Capture errors
                window.addEventListener('error', (event) => {
                    try {
                        window.__capturedErrors.push({
                            type: 'error',
                            text: event.message,
                            stack: event.error ? event.error.stack : '',
                            filename: event.filename,
                            lineno: event.lineno,
                            colno: event.colno,
                            timestamp: Date.now()
                        });
                    } catch (e) {
                        // Fail silently
                    }
                });
                
                // Capture unhandled promise rejections
                window.addEventListener('unhandledrejection', (event) => {
                    try {
                        window.__capturedErrors.push({
                            type: 'unhandledrejection',
                            text: event.reason ? String(event.reason) : 'Unhandled Promise Rejection',
                            stack: event.reason && event.reason.stack ? event.reason.stack : '',
                            timestamp: Date.now()
                        });
                    } catch (e) {
                        // Fail silently
                    }
                });
            """)
            self._console_script_injected[page] = True
        
        return None  # No handler function needed for undetected browser
    
    async def retrieve_console_messages(self, page: UndetectedPage) -> List[Dict]:
        """Retrieve captured console messages and errors from the page"""
        messages = []
        
        try:
            # Get console messages
            console_messages = await page.evaluate(
                "() => { const msgs = window.__capturedConsole || []; window.__capturedConsole = []; return msgs; }",
                isolated_context=False
            )
            messages.extend(console_messages)
            
            # Get errors
            errors = await page.evaluate(
                "() => { const errs = window.__capturedErrors || []; window.__capturedErrors = []; return errs; }",
                isolated_context=False
            )
            messages.extend(errors)
            
            # Convert timestamps from JS to Python format
            for msg in messages:
                if 'timestamp' in msg and isinstance(msg['timestamp'], (int, float)):
                    msg['timestamp'] = msg['timestamp'] / 1000.0  # Convert from ms to seconds
                    
        except Exception:
            # If retrieval fails, return empty list
            pass
        
        return messages
    
    async def cleanup_console_capture(self, page: UndetectedPage, handle_console: Optional[Callable], handle_error: Optional[Callable]):
        """Clean up for undetected browser - retrieve final messages"""
        # For undetected browser, we don't have event listeners to remove
        # but we should retrieve any final messages
        final_messages = await self.retrieve_console_messages(page)
        return final_messages
    
    def get_imports(self) -> tuple:
        """Return undetected browser imports"""
        from patchright.async_api import Page, Error
        from patchright.async_api import TimeoutError as PlaywrightTimeoutError
        return Page, Error, PlaywrightTimeoutError