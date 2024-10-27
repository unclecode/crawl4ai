# Features

## Current Features
1. Async-first architecture for high-performance web crawling
2. Built-in anti-bot detection bypass ("magic mode")
3. Multiple browser engine support (Chromium, Firefox, WebKit)
4. Smart session management with automatic cleanup
5. Automatic content cleaning and relevance scoring
6. Built-in markdown generation with formatting preservation
7. Intelligent image scoring and filtering
8. Automatic popup and overlay removal
9. Smart wait conditions (CSS/JavaScript based)
10. Multi-provider LLM integration (OpenAI, HuggingFace, Ollama)
11. Schema-based structured data extraction
12. Automated iframe content processing
13. Intelligent link categorization (internal/external)
14. Multiple chunking strategies for large content
15. Real-time HTML cleaning and sanitization
16. Automatic screenshot capabilities
17. Social media link filtering
18. Semantic similarity-based content clustering
19. Human behavior simulation for anti-bot bypass
20. Proxy support with authentication
21. Automatic resource cleanup
22. Custom CSS selector-based extraction
23. Automatic content relevance scoring ("fit" content)
24. Recursive website crawling capabilities
25. Flexible hook system for customization
26. Built-in caching system
27. Domain-based content filtering
28. Dynamic content handling with JavaScript execution
29. Automatic media content extraction and classification
30. Metadata extraction and processing
31. Customizable HTML to Markdown conversion
32. Token-aware content chunking for LLM processing
33. Automatic response header and status code handling
34. Browser fingerprint customization
35. Multiple extraction strategies (LLM, CSS, Cosine, XPATH)
36. Automatic error image generation for failed screenshots
37. Smart content overlap handling for large texts
38. Built-in rate limiting for batch processing
39. Automatic cookie handling
40. Browser Console logging and debugging capabilities

## Feature Techs
• Browser Management
  - Asynchronous browser control
  - Multi-browser support (Chromium, Firefox, WebKit)
  - Headless mode support
  - Browser cleanup and resource management
  - Custom browser arguments and configuration
  - Context management with `__aenter__` and `__aexit__`

• Session Handling
  - Session management with TTL (Time To Live)
  - Session reuse capabilities
  - Session cleanup for expired sessions
  - Session-based context preservation

• Stealth Features
  - Playwright stealth configuration
  - Navigator properties override
  - WebDriver detection evasion
  - Chrome app simulation
  - Plugin simulation
  - Language preferences simulation
  - Hardware concurrency simulation
  - Media codecs simulation

• Network Features
  - Proxy support with authentication
  - Custom headers management
  - Cookie handling
  - Response header capture
  - Status code tracking
  - Network idle detection

• Page Interaction
  - Smart wait functionality for multiple conditions
  - CSS selector-based waiting
  - JavaScript condition waiting
  - Custom JavaScript execution
  - User interaction simulation (mouse/keyboard)
  - Page scrolling
  - Timeout management
  - Load state monitoring

• Content Processing
  - HTML content extraction
  - Iframe processing and content extraction
  - Delayed content retrieval
  - Content caching
  - Cache file management
  - HTML cleaning and processing

• Image Handling
  - Screenshot capabilities (full page)
  - Base64 encoding of screenshots
  - Image dimension updating
  - Image filtering (size/visibility)
  - Error image generation
  - Natural width/height preservation

• Overlay Management
  - Popup removal
  - Cookie notice removal
  - Newsletter dialog removal
  - Modal removal
  - Fixed position element removal
  - Z-index based overlay detection
  - Visibility checking

• Hook System
  - Browser creation hooks
  - User agent update hooks
  - Execution start hooks
  - Navigation hooks (before/after goto)
  - HTML retrieval hooks
  - HTML return hooks

• Error Handling
  - Browser error catching
  - Network error handling
  - Timeout handling
  - Screenshot error recovery
  - Invalid selector handling
  - General exception management

• Performance Features
  - Concurrent URL processing
  - Semaphore-based rate limiting
  - Async gathering of results
  - Resource cleanup
  - Memory management

• Debug Features
  - Console logging
  - Page error logging
  - Verbose mode
  - Error message generation
  - Warning system

• Security Features
  - Certificate error handling
  - Sandbox configuration
  - GPU handling
  - CSP (Content Security Policy) compliant waiting

• Configuration
  - User agent customization
  - Viewport configuration
  - Timeout configuration
  - Browser type selection
  - Proxy configuration
  - Header configuration

• Data Models
  - Pydantic model for responses
  - Type hints throughout code
  - Structured response format
  - Optional response fields

• File System Integration
  - Cache directory management
  - File path handling
  - Cache metadata storage
  - File read/write operations

• Metadata Handling
  - Response headers capture
  - Status code tracking
  - Cache metadata
  - Session tracking
  - Timestamp management

