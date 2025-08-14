1. **BrowserConfig** – Controlling the Browser
==============================================

`BrowserConfig` focuses on **how** the browser is launched and behaves. This includes headless mode, proxies, user agents, and other environment tweaks.

```
from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_cfg = BrowserConfig(
    browser_type="chromium",
    headless=True,
    viewport_width=1280,
    viewport_height=720,
    proxy="http://user:pass@proxy:8080",
    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36",
)
```

1.1 Parameter Highlights
------------------------

| **Parameter** | **Type / Default** | **What It Does** |
| --- | --- | --- |
| **`browser_type`** | `"chromium"`, `"firefox"`, `"webkit"` *(default: `"chromium"`)* | Which browser engine to use. `"chromium"` is typical for many sites, `"firefox"` or `"webkit"` for specialized tests. |
| **`headless`** | `bool` (default: `True`) | Headless means no visible UI. `False` is handy for debugging. |
| **`viewport_width`** | `int` (default: `1080`) | Initial page width (in px). Useful for testing responsive layouts. |
| **`viewport_height`** | `int` (default: `600`) | Initial page height (in px). |
| **`proxy`** | `str` (default: `None`) | Single-proxy URL if you want all traffic to go through it, e.g. `"http://user:pass@proxy:8080"`. |
| **`proxy_config`** | `dict` (default: `None`) | For advanced or multi-proxy needs, specify details like `{"server": "...", "username": "...", ...}`. |
| **`use_persistent_context`** | `bool` (default: `False`) | If `True`, uses a **persistent** browser context (keep cookies, sessions across runs). Also sets `use_managed_browser=True`. |
| **`user_data_dir`** | `str or None` (default: `None`) | Directory to store user data (profiles, cookies). Must be set if you want permanent sessions. |
| **`ignore_https_errors`** | `bool` (default: `True`) | If `True`, continues despite invalid certificates (common in dev/staging). |
| **`java_script_enabled`** | `bool` (default: `True`) | Disable if you want no JS overhead, or if only static content is needed. |
| **`cookies`** | `list` (default: `[]`) | Pre-set cookies, each a dict like `{"name": "session", "value": "...", "url": "..."}`. |
| **`headers`** | `dict` (default: `{}`) | Extra HTTP headers for every request, e.g. `{"Accept-Language": "en-US"}`. |
| **`user_agent`** | `str` (default: Chrome-based UA) | Your custom or random user agent. `user_agent_mode="random"` can shuffle it. |
| **`light_mode`** | `bool` (default: `False`) | Disables some background features for performance gains. |
| **`text_mode`** | `bool` (default: `False`) | If `True`, tries to disable images/other heavy content for speed. |
| **`use_managed_browser`** | `bool` (default: `False`) | For advanced “managed” interactions (debugging, CDP usage). Typically set automatically if persistent context is on. |
| **`extra_args`** | `list` (default: `[]`) | Additional flags for the underlying browser process, e.g. `["--disable-extensions"]`. |

**Tips**:
- Set `headless=False` to visually **debug** how pages load or how interactions proceed.
- If you need **authentication** storage or repeated sessions, consider `use_persistent_context=True` and specify `user_data_dir`.
- For large pages, you might need a bigger `viewport_width` and `viewport_height` to handle dynamic content.

---

2. **CrawlerRunConfig** – Controlling Each Crawl
================================================

While `BrowserConfig` sets up the **environment**, `CrawlerRunConfig` details **how** each **crawl operation** should behave: caching, content filtering, link or domain blocking, timeouts, JavaScript code, etc.

```
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

run_cfg = CrawlerRunConfig(
    wait_for="css:.main-content",
    word_count_threshold=15,
    excluded_tags=["nav", "footer"],
    exclude_external_links=True,
    stream=True,  # Enable streaming for arun_many()
)
```

2.1 Parameter Highlights
------------------------

We group them by category.

### A) **Content Processing**

| **Parameter** | **Type / Default** | **What It Does** |
| --- | --- | --- |
| **`word_count_threshold`** | `int` (default: ~200) | Skips text blocks below X words. Helps ignore trivial sections. |
| **`extraction_strategy`** | `ExtractionStrategy` (default: None) | If set, extracts structured data (CSS-based, LLM-based, etc.). |
| **`markdown_generator`** | `MarkdownGenerationStrategy` (None) | If you want specialized markdown output (citations, filtering, chunking, etc.). Can be customized with options such as `content_source` parameter to select the HTML input source ('cleaned\_html', 'raw\_html', or 'fit\_html'). |
| **`css_selector`** | `str` (None) | Retains only the part of the page matching this selector. Affects the entire extraction process. |
| **`target_elements`** | `List[str]` (None) | List of CSS selectors for elements to focus on for markdown generation and data extraction, while still processing the entire page for links, media, etc. Provides more flexibility than `css_selector`. |
| **`excluded_tags`** | `list` (None) | Removes entire tags (e.g. `["script", "style"]`). |
| **`excluded_selector`** | `str` (None) | Like `css_selector` but to exclude. E.g. `"#ads, .tracker"`. |
| **`only_text`** | `bool` (False) | If `True`, tries to extract text-only content. |
| **`prettiify`** | `bool` (False) | If `True`, beautifies final HTML (slower, purely cosmetic). |
| **`keep_data_attributes`** | `bool` (False) | If `True`, preserve `data-*` attributes in cleaned HTML. |
| **`remove_forms`** | `bool` (False) | If `True`, remove all `<form>` elements. |

---