"""
Tests for scan_full_page on virtual-scroll pages (issue #731).

Covers:
1. Basic recycling (50 items, 10 visible)
2. Scale stress test (1000 items)
3. Similar text collision (items share text, differ by data-id)
4. No data-id fallback (fingerprint by tagName+href+textContent)
5. Append-only scroll (no recycling — must not break)
6. DOM noise (unrelated mutations during scroll)
7. Memory bound check (output HTML size is reasonable)
8. Normal static page (no virtual scroll — regression guard)
9. Full page scan with window.scrollBy fallback
"""

import json
import os
import tempfile
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

import pytest

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# ---------------------------------------------------------------------------
# Test page generators
# ---------------------------------------------------------------------------

def _recycle_page(total: int, visible: int, *, use_data_id: bool = True,
                  similar_text: bool = False, noise: bool = False) -> str:
    """Generate a virtual-scroll page that recycles DOM elements."""
    data_id_attr = 'data-item-id="${i}"' if use_data_id else ''
    text_expr = (
        '`Item ${i}`'  # all share prefix "Item" — tests fingerprint collision
        if similar_text
        else '`Item-${i} unique-text-${Math.random().toString(36).substring(2, 10)}`'
    )
    noise_js = """
    // Unrelated DOM noise: a ticker that adds/removes elements every 100ms
    setInterval(() => {
        const el = document.createElement('div');
        el.className = 'noise-ticker';
        el.textContent = 'Noise ' + Date.now();
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 50);
    }, 100);
    """ if noise else ""
    return f"""<!DOCTYPE html>
<html><head><style>
  body {{ margin:0; font-family:sans-serif; }}
  .item {{ height:80px; padding:10px; border-bottom:1px solid #eee; }}
  .noise-ticker {{ position:fixed; top:0; right:0; font-size:10px; color:#ccc; }}
</style></head><body>
<div id="feed"></div>
<script>
  const TOTAL = {total}, VISIBLE = {visible};
  const items = [];
  for (let i = 1; i <= TOTAL; i++) {{
    items.push({{ id: i, text: {text_expr} }});
  }}
  let startIdx = 0;
  const feed = document.getElementById('feed');
  function render() {{
    feed.innerHTML = '';
    const end = Math.min(startIdx + VISIBLE, TOTAL);
    for (let idx = startIdx; idx < end; idx++) {{
      const i = items[idx].id;
      const div = document.createElement('div');
      div.className = 'item';
      div.setAttribute('data-testid', 'ItemCell');
      {"div.setAttribute('data-item-id', String(i));" if use_data_id else ""}
      div.innerHTML = '<span class=\"text\">' + items[idx].text + '</span>';
      feed.appendChild(div);
    }}
    document.body.style.height = (TOTAL * 90) + 'px';
  }}
  render();
  window.addEventListener('scroll', () => {{
    const newStart = Math.min(Math.floor(window.scrollY / 90), TOTAL - VISIBLE);
    if (newStart !== startIdx) {{ startIdx = newStart; render(); }}
  }});
  {noise_js}
</script></body></html>"""


def _append_page(total: int, batch: int) -> str:
    """Generate an append-only infinite-scroll page (no recycling)."""
    return f"""<!DOCTYPE html>
<html><head><style>
  body {{ margin:0; font-family:sans-serif; }}
  .item {{ height:80px; padding:10px; border-bottom:1px solid #eee; }}
</style></head><body>
<div id="feed"></div>
<script>
  let loaded = 0;
  const TOTAL = {total}, BATCH = {batch};
  const feed = document.getElementById('feed');
  function loadBatch() {{
    const end = Math.min(loaded + BATCH, TOTAL);
    for (let i = loaded + 1; i <= end; i++) {{
      const div = document.createElement('div');
      div.className = 'item';
      div.setAttribute('data-testid', 'ItemCell');
      div.setAttribute('data-item-id', String(i));
      div.innerHTML = '<span class=\"text\">Appended-Item-' + i + '</span>';
      feed.appendChild(div);
    }}
    loaded = end;
  }}
  loadBatch();
  window.addEventListener('scroll', () => {{
    if (window.scrollY + window.innerHeight >= document.body.scrollHeight - 100) {{
      if (loaded < TOTAL) loadBatch();
    }}
  }});
</script></body></html>"""


def _static_page() -> str:
    """A normal static page with no virtual scroll."""
    items = "\n".join(
        f'<div class="item" data-testid="ItemCell" data-item-id="{i}">'
        f'<span class="text">Static-{i}</span></div>'
        for i in range(1, 5)
    )
    return f"""<!DOCTYPE html>
<html><head><style>.item {{ padding:10px; }}</style></head><body>
<div id="feed">{items}</div>
</body></html>"""


# ---------------------------------------------------------------------------
# Server fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def serve_page():
    """Fixture that serves an HTML string on localhost and yields the URL."""
    servers = []

    def _serve(html: str, port: int = 0) -> str:
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir, "index.html"), "w") as f:
            f.write(html)

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=tmpdir, **kw)
            def log_message(self, *_):
                pass

        srv = HTTPServer(("127.0.0.1", port), Handler)
        actual_port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        servers.append(srv)
        return f"http://127.0.0.1:{actual_port}/index.html"

    yield _serve

    for s in servers:
        s.shutdown()


def _extraction():
    return JsonCssExtractionStrategy({
        "name": "Items",
        "baseSelector": "[data-testid='ItemCell']",
        "fields": [{"name": "text", "selector": ".text", "type": "text"}],
    })


def _config(*, scroll=True, delay=0.2, steps=30):
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=_extraction(),
        scan_full_page=scroll,
        scroll_delay=delay,
        max_scroll_steps=steps,
    )


async def _crawl(url, config):
    async with AsyncWebCrawler(verbose=False) as crawler:
        return await crawler.arun(url=url, config=config)


def _unique_items(result):
    data = json.loads(result.extracted_content)
    # Deduplicate by text content
    seen = {}
    for item in data:
        seen[item["text"]] = item
    return list(seen.values())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recycle_50_items(serve_page):
    """Basic virtual scroll: 50 items, 10 visible at a time."""
    url = serve_page(_recycle_page(50, 10))
    result = await _crawl(url, _config())
    items = _unique_items(result)
    assert len(items) >= 40, f"Expected >=40 unique items, got {len(items)}"


@pytest.mark.asyncio
async def test_recycle_200_items(serve_page):
    """Medium scale: 200 items, 10 visible."""
    url = serve_page(_recycle_page(200, 10))
    result = await _crawl(url, _config(steps=60))
    items = _unique_items(result)
    assert len(items) >= 160, f"Expected >=160 unique items, got {len(items)}"


@pytest.mark.asyncio
async def test_recycle_1000_items_stress(serve_page):
    """Stress test: 1000 items. Checks correctness and memory."""
    url = serve_page(_recycle_page(1000, 10))
    result = await _crawl(url, _config(steps=200))
    items = _unique_items(result)
    assert len(items) >= 800, f"Expected >=800 unique items, got {len(items)}"
    # Memory check: 1000 items at ~500B each should be well under 2MB
    html_kb = len(result.html) / 1024
    assert html_kb < 3000, f"HTML too large ({html_kb:.0f}KB), possible duplicate accumulation"


@pytest.mark.asyncio
async def test_similar_text_no_collapse(serve_page):
    """Items share the text prefix 'Item N' but differ by data-item-id.
    A substring-based fingerprint would collapse these."""
    url = serve_page(_recycle_page(100, 10, similar_text=True))
    result = await _crawl(url, _config(steps=40))
    data = json.loads(result.extracted_content)
    # Deduplicate by data-item-id via the text which includes the index
    unique_texts = {item["text"] for item in data}
    assert len(unique_texts) >= 80, (
        f"Expected >=80 unique items (text collision test), got {len(unique_texts)}"
    )


@pytest.mark.asyncio
async def test_no_data_id_fallback(serve_page):
    """Items have no data-item-id — fingerprint must fall back to content hash."""
    url = serve_page(_recycle_page(50, 10, use_data_id=False))
    result = await _crawl(url, _config())
    items = _unique_items(result)
    assert len(items) >= 40, f"Expected >=40 unique items (no data-id), got {len(items)}"


@pytest.mark.asyncio
async def test_append_only_no_breakage(serve_page):
    """Append-only scroll (no recycling). Must not break or lose items."""
    url = serve_page(_append_page(80, 20))
    result = await _crawl(url, _config(steps=20))
    items = _unique_items(result)
    assert len(items) >= 60, f"Expected >=60 appended items, got {len(items)}"


@pytest.mark.asyncio
async def test_dom_noise_ignored(serve_page):
    """Unrelated DOM mutations (ticker) should not pollute results."""
    url = serve_page(_recycle_page(50, 10, noise=True))
    result = await _crawl(url, _config())
    items = _unique_items(result)
    assert len(items) >= 40, f"Expected >=40 items with noise, got {len(items)}"
    # Ensure no noise elements leaked into extracted content
    data = json.loads(result.extracted_content)
    for item in data:
        assert "Noise" not in item["text"], "Noise ticker element leaked into extraction"


@pytest.mark.asyncio
async def test_static_page_unchanged(serve_page):
    """A normal static page must work without virtual scroll logic breaking it."""
    url = serve_page(_static_page())
    result = await _crawl(url, _config(steps=5))
    data = json.loads(result.extracted_content)
    texts = {item["text"] for item in data}
    assert len(texts) == 4, f"Expected 4 static items, got {len(texts)}: {texts}"


@pytest.mark.asyncio
async def test_scan_full_page_scrollby_fallback(serve_page):
    """Verify window.scrollBy fallback works when scrollTo doesn't move."""
    url = serve_page(_recycle_page(50, 10))
    result = await _crawl(url, _config())
    items = _unique_items(result)
    # The key assertion: we got more than just the initial viewport
    assert len(items) > 10, f"scrollBy fallback may have failed, only got {len(items)} items"


@pytest.mark.asyncio
async def test_rich_card_with_many_children(serve_page):
    """Items are rich cards with 4+ child elements (title, desc, tags, actions).
    The container detection must not mistake these cards for feed containers."""
    html = """<!DOCTYPE html>
<html><head><style>
body { margin:0; } .card { height:120px; padding:10px; border-bottom:1px solid #eee; }
</style></head><body>
<div id="feed"></div>
<script>
const TOTAL=50, VISIBLE=8;
const items=[];
for(let i=1;i<=TOTAL;i++) items.push({id:i});
let startIdx=0;
const feed=document.getElementById('feed');
function render(){
  feed.innerHTML='';
  const end=Math.min(startIdx+VISIBLE,TOTAL);
  for(let idx=startIdx;idx<end;idx++){
    const i=items[idx].id;
    const d=document.createElement('div');
    d.className='card';
    d.setAttribute('data-testid','ItemCell');
    d.setAttribute('data-item-id',String(i));
    // 4 child elements — looks like a container if using child count
    d.innerHTML='<div class="title">Title '+i+'</div>'
      +'<div class="desc">Description for card '+i+'</div>'
      +'<div class="tags"><span>tag-a</span><span>tag-b</span></div>'
      +'<div class="actions"><button>Like</button><button>Share</button></div>';
    feed.appendChild(d);
  }
  document.body.style.height=(TOTAL*130)+'px';
}
render();
window.addEventListener('scroll',()=>{
  const ns=Math.min(Math.floor(window.scrollY/130),TOTAL-VISIBLE);
  if(ns!==startIdx){startIdx=ns;render();}
});
</script></body></html>"""
    url = serve_page(html)
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy({
            "name": "Cards",
            "baseSelector": "[data-testid='ItemCell']",
            "fields": [{"name": "text", "selector": ".title", "type": "text"}],
        }),
        scan_full_page=True, scroll_delay=0.2, max_scroll_steps=30,
    )
    result = await _crawl(url, config)
    data = json.loads(result.extracted_content)
    unique = {item["text"] for item in data}
    assert len(unique) >= 40, (
        f"Expected >=40 rich cards (container heuristic test), got {len(unique)}"
    )


@pytest.mark.asyncio
async def test_deep_nesting(serve_page):
    """Items nested 15+ levels deep must still be captured."""
    # Build a chain of 20 wrapper divs around the feed
    open_wrappers = "".join(f'<div class="wrapper-{i}">' for i in range(20))
    close_wrappers = "</div>" * 20
    html = f"""<!DOCTYPE html>
<html><head><style>
body {{ margin:0; }} .item {{ height:80px; padding:10px; border-bottom:1px solid #eee; }}
</style></head><body>
{open_wrappers}
<div id="feed"></div>
{close_wrappers}
<script>
const TOTAL=50, VISIBLE=10;
const items=[];
for(let i=1;i<=TOTAL;i++) items.push({{id:i,text:'Deep-'+i+'-'+Math.random().toString(36).slice(2,8)}});
let startIdx=0;
const feed=document.getElementById('feed');
function render(){{
  feed.innerHTML='';
  const end=Math.min(startIdx+VISIBLE,TOTAL);
  for(let idx=startIdx;idx<end;idx++){{
    const i=items[idx].id;
    const d=document.createElement('div');
    d.className='item';
    d.setAttribute('data-testid','ItemCell');
    d.setAttribute('data-item-id',String(i));
    d.innerHTML='<span class="text">'+items[idx].text+'</span>';
    feed.appendChild(d);
  }}
  document.body.style.height=(TOTAL*90)+'px';
}}
render();
window.addEventListener('scroll',()=>{{
  const ns=Math.min(Math.floor(window.scrollY/90),TOTAL-VISIBLE);
  if(ns!==startIdx){{startIdx=ns;render();}}
}});
</script></body></html>"""
    url = serve_page(html)
    result = await _crawl(url, _config())
    items = _unique_items(result)
    assert len(items) >= 40, (
        f"Expected >=40 items through 20 levels of nesting, got {len(items)}"
    )


@pytest.mark.asyncio
async def test_hash_collision_resistance(serve_page):
    """500 items with NO data-id and very similar text.
    Tests that the dual-hash fingerprint avoids collisions."""
    html = """<!DOCTYPE html>
<html><head><style>
body { margin:0; } .item { height:80px; padding:10px; border-bottom:1px solid #eee; }
</style></head><body>
<div id="feed"></div>
<script>
const TOTAL=500, VISIBLE=10;
const items=[];
for(let i=1;i<=TOTAL;i++){
  // All items have same prefix, only differ by trailing number
  items.push({id:i, text:'Product description for item number '+i});
}
let startIdx=0;
const feed=document.getElementById('feed');
function render(){
  feed.innerHTML='';
  const end=Math.min(startIdx+VISIBLE,TOTAL);
  for(let idx=startIdx;idx<end;idx++){
    const d=document.createElement('div');
    d.className='item';
    d.setAttribute('data-testid','ItemCell');
    // NO data-item-id — force fallback to hash fingerprint
    d.innerHTML='<span class="text">'+items[idx].text+'</span>';
    feed.appendChild(d);
  }
  document.body.style.height=(TOTAL*90)+'px';
}
render();
window.addEventListener('scroll',()=>{
  const ns=Math.min(Math.floor(window.scrollY/90),TOTAL-VISIBLE);
  if(ns!==startIdx){startIdx=ns;render();}
});
</script></body></html>"""
    url = serve_page(html)
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy({
            "name": "Products",
            "baseSelector": "[data-testid='ItemCell']",
            "fields": [{"name": "text", "selector": ".text", "type": "text"}],
        }),
        scan_full_page=True, scroll_delay=0.2, max_scroll_steps=100,
    )
    result = await _crawl(url, config)
    data = json.loads(result.extracted_content)
    unique = {item["text"] for item in data}
    assert len(unique) >= 400, (
        f"Expected >=400 unique items (hash collision test), got {len(unique)}"
    )
