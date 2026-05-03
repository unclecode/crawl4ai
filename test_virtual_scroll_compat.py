"""
Comprehensive virtual scroll compatibility test suite.

Covers 13 distinct scroll/virtualisation patterns:

  Test 1  — Transform-based virtual scroll (50 items, translateY)
  Test 2  — innerHTML-wipe virtual scroll (50 items, PR #1853 exact pattern)
  Test 3  — Append-based infinite scroll (100 quotes, no DOM recycling)
  Test 4  — Container-level virtual scroll (200 rows, overflow-y: scroll)
  Test 5  — Transform-based stress test (1000 items)
  Test 6  — Real site: quotes.toscrape.com/scroll
  Test 7  — Variable row heights (80 items, non-uniform heights)
  Test 8  — Horizontal virtual scroll (60 items, translateX)
  Test 9  — 2D grid virtualisation (10x10 = 100 cells)
  Test 10 — Multiple virtual containers on same page (40 + 30 items)
  Test 11 — Nested virtual scroll (5 categories x 10 items)
  Test 12 — Async/setTimeout-loaded items (50 items)
  Test 13 — Small virtual section in large static page (60 items)

Each local test is served from a self-contained HTML file via HTTPServer
on a unique port.  All tests use JsonCssExtractionStrategy + scan_full_page=True.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# ---------------------------------------------------------------------------
# HTML fixtures
# ---------------------------------------------------------------------------

# Test 1 — Transform-based virtual scroll
# Items are positioned with CSS transform: translateY(Npx).
# Container has an explicit style.height = TOTAL * ITEM_HEIGHT.
# Only ~10 items exist in the DOM at any time.
# On scroll the transform of each live node is updated (moved into / out of
# the visible band) — this mirrors how React/Next.js virtual lists work
# (e.g. skills.sh, Twitter feed, Tanstack Virtual).
TRANSFORM_SCROLL_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: sans-serif; }
  #container {
    position: relative;
    width: 600px;
    margin: 0 auto;
  }
  .item {
    position: absolute;
    left: 0; right: 0;
    height: 60px;
    padding: 10px 14px;
    border-bottom: 1px solid #eee;
    background: #fff;
  }
  .item .title { font-weight: bold; font-size: 14px; }
  .item .meta  { color: #777; font-size: 12px; margin-top: 4px; }
</style>
</head>
<body>
<div id="container"></div>
<script>
(function () {
  var TOTAL      = 50;
  var ITEM_H     = 60;
  var OVERSCAN   = 3;          // extra items above/below viewport
  var VISIBLE    = Math.ceil(window.innerHeight / ITEM_H) + OVERSCAN * 2;

  // Build full data array up-front
  var allItems = [];
  for (var i = 0; i < TOTAL; i++) {
    allItems.push({ id: i + 1, title: 'Item ' + (i + 1), slug: 'item-' + (i + 1) });
  }

  var container = document.getElementById('container');
  container.style.height = (TOTAL * ITEM_H) + 'px';

  // Pool of DOM nodes — we recycle exactly VISIBLE nodes
  var pool = [];
  for (var j = 0; j < VISIBLE; j++) {
    var el = document.createElement('div');
    el.className = 'item';
    el.style.transform = 'translateY(-9999px)'; // hidden until assigned
    el.innerHTML = '<div class="title"></div><div class="meta"></div>';
    container.appendChild(el);
    pool.push({ el: el, assignedIndex: -1 });
  }

  var lastStart = -1;

  function render() {
    var scrollY = window.scrollY;
    var start = Math.max(0, Math.floor(scrollY / ITEM_H) - OVERSCAN);
    var end   = Math.min(TOTAL, start + VISIBLE);

    if (start === lastStart) return;
    lastStart = start;

    // Assign pool slots to visible range
    for (var k = 0; k < pool.length; k++) {
      var idx = start + k;
      if (idx >= end) {
        // Park unused nodes off-screen
        pool[k].el.style.transform = 'translateY(-9999px)';
        pool[k].assignedIndex = -1;
        continue;
      }
      var item = allItems[idx];
      pool[k].assignedIndex = idx;
      pool[k].el.style.transform = 'translateY(' + (idx * ITEM_H) + 'px)';
      pool[k].el.querySelector('.title').textContent = item.title;
      pool[k].el.querySelector('.meta').innerHTML =
        '<a href="/item/' + item.id + '">#' + item.id + '</a>';
    }
  }

  render();
  window.addEventListener('scroll', render);
})();
</script>
</body>
</html>
"""

# Test 2 — innerHTML-wipe virtual scroll (PR #1853 exact pattern)
# Container.innerHTML = '' then new items are appended on every scroll.
# No transforms, no explicit height on the container itself.
# Body height is set to TOTAL * ITEM_HEIGHT to allow the window to scroll.
INNERHTML_WIPE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; font-family: sans-serif; }
  .item { height: 80px; padding: 10px; border-bottom: 1px solid #eee; }
  .item .name   { font-weight: bold; }
  .item .handle { color: #666; }
</style>
</head>
<body>
<div id="feed"></div>
<script>
  var TOTAL   = 50;
  var VISIBLE = 10;
  var ITEM_H  = 80;

  var allUsers = [];
  for (var i = 0; i < TOTAL; i++) {
    allUsers.push({ name: 'User ' + (i + 1), handle: '@user' + (i + 1) });
  }

  var feed     = document.getElementById('feed');
  var startIdx = 0;

  function render() {
    feed.innerHTML = '';
    var end = Math.min(startIdx + VISIBLE, TOTAL);
    for (var i = startIdx; i < end; i++) {
      var div = document.createElement('div');
      div.className = 'item';
      div.setAttribute('data-testid', 'UserCell');
      div.innerHTML =
        '<div class="name">' + allUsers[i].name + '</div>' +
        '<div class="handle">' +
          '<a href="/profile/' + (i + 1) + '">' + allUsers[i].handle + '</a>' +
        '</div>';
      feed.appendChild(div);
    }
    document.body.style.height = (TOTAL * ITEM_H) + 'px';
  }

  render();

  window.addEventListener('scroll', function () {
    var newStart = Math.min(
      Math.floor(window.scrollY / ITEM_H),
      TOTAL - VISIBLE
    );
    if (newStart !== startIdx) {
      startIdx = newStart;
      render();
    }
  });
</script>
</body>
</html>
"""

# Test 3 — Append-based infinite scroll (no DOM recycling)
# Items are only ever appended; nothing is ever removed.
APPEND_SCROLL_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; font-family: sans-serif; }
  .quote { padding: 15px; border-bottom: 1px solid #ddd; }
  .quote .text   { font-style: italic; }
  .quote .author { color: #555; margin-top: 5px; }
</style>
</head>
<body>
<div id="quotes"></div>
<script>
  var TOTAL     = 100;
  var BATCH     = 10;
  var loaded    = 0;
  var container = document.getElementById('quotes');

  function loadBatch() {
    var end = Math.min(loaded + BATCH, TOTAL);
    for (var i = loaded; i < end; i++) {
      var div = document.createElement('div');
      div.className = 'quote';
      div.innerHTML =
        '<div class="text">"Quote number ' + (i + 1) + ' — a test quote."</div>' +
        '<div class="author">' +
          '<a href="/author/' + (i + 1) + '">Author ' + (i + 1) + '</a>' +
        '</div>';
      container.appendChild(div);
    }
    loaded = end;
  }

  loadBatch();

  window.addEventListener('scroll', function () {
    if (window.scrollY + window.innerHeight >= document.body.scrollHeight - 100) {
      if (loaded < TOTAL) loadBatch();
    }
  });
</script>
</body>
</html>
"""

# Test 4 — Container-level virtual scroll (overflow-y: scroll on a div)
# The container element itself scrolls (not the window).
# Items inside use position: absolute + top offset — recycled on container scroll.
CONTAINER_SCROLL_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: sans-serif; padding: 16px; }
  h1   { margin-bottom: 12px; font-size: 18px; }
  #scroller {
    height: 400px;
    overflow-y: scroll;
    border: 1px solid #ccc;
    position: relative;
    width: 640px;
  }
  #inner { position: relative; }
  .row {
    position: absolute;
    left: 0; right: 0;
    height: 40px;
    line-height: 40px;
    padding: 0 12px;
    border-bottom: 1px solid #eee;
    font-size: 13px;
  }
</style>
</head>
<body>
<h1>Container Scroll (200 rows)</h1>
<div id="scroller">
  <div id="inner"></div>
</div>
<script>
(function () {
  var TOTAL   = 200;
  var ITEM_H  = 40;
  var VISIBLE = 15;
  var OVERSCAN = 3;

  var scroller = document.getElementById('scroller');
  var inner    = document.getElementById('inner');
  inner.style.height = (TOTAL * ITEM_H) + 'px';

  var poolSize = VISIBLE + OVERSCAN * 2;
  var pool = [];
  for (var j = 0; j < poolSize; j++) {
    var el = document.createElement('div');
    el.className = 'row';
    el.style.top = '-9999px';
    inner.appendChild(el);
    pool.push(el);
  }

  var lastStart = -1;

  function render() {
    var scrollTop = scroller.scrollTop;
    var start = Math.max(0, Math.floor(scrollTop / ITEM_H) - OVERSCAN);
    var end   = Math.min(TOTAL, start + poolSize);

    if (start === lastStart) return;
    lastStart = start;

    for (var k = 0; k < pool.length; k++) {
      var idx = start + k;
      if (idx >= end) {
        pool[k].style.top = '-9999px';
        pool[k].textContent = '';
        continue;
      }
      pool[k].style.top  = (idx * ITEM_H) + 'px';
      pool[k].setAttribute('data-row', idx + 1);
      pool[k].innerHTML =
        'Row ' + (idx + 1) + ' — ' +
        '<a href="/row/' + (idx + 1) + '">detail #' + (idx + 1) + '</a>';
    }
  }

  render();
  scroller.addEventListener('scroll', render);
})();
</script>
</body>
</html>
"""

# Test 8 — Horizontal virtual scroll (60 items, translateX)
# Container scrolls horizontally via overflow-x: scroll.
# Items are positioned with transform: translateX(Npx) and recycled
# from a pool of ~8 DOM nodes — same pattern as vertical virtual scroll
# but on the X axis.
HORIZONTAL_SCROLL_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: sans-serif; padding: 16px; }
  h1   { margin-bottom: 12px; font-size: 18px; }
  #hscroller {
    position: relative;
    overflow-x: scroll;
    white-space: nowrap;
    height: 200px;
    width: 800px;
    border: 1px solid #ccc;
  }
  #hinner {
    position: relative;
    height: 100%;
  }
  .hitem {
    position: absolute;
    top: 0;
    width: 150px;
    height: 180px;
    padding: 10px;
    border-right: 1px solid #eee;
    background: #fff;
    white-space: normal;
  }
  .hitem .card-title { font-weight: bold; font-size: 14px; }
  .hitem .card-link  { display: block; margin-top: 8px; font-size: 12px; }
</style>
</head>
<body>
<h1>Horizontal Virtual Scroll (60 items)</h1>
<div id="hscroller">
  <div id="hinner"></div>
</div>
<script>
(function () {
  var TOTAL    = 60;
  var ITEM_W   = 150;
  var OVERSCAN = 2;
  var POOL_SIZE = 8;

  var allItems = [];
  for (var i = 0; i < TOTAL; i++) {
    allItems.push({ id: i + 1, title: 'Card ' + (i + 1) });
  }

  var scroller = document.getElementById('hscroller');
  var inner    = document.getElementById('hinner');
  inner.style.width = (TOTAL * ITEM_W) + 'px';

  var pool = [];
  for (var j = 0; j < POOL_SIZE; j++) {
    var el = document.createElement('div');
    el.className = 'hitem';
    el.style.transform = 'translateX(-9999px)';
    el.innerHTML = '<div class="card-title"></div><div class="card-link"></div>';
    inner.appendChild(el);
    pool.push({ el: el, assignedIndex: -1 });
  }

  var lastStart = -1;

  function render() {
    var scrollX = scroller.scrollLeft;
    var visibleCount = Math.ceil(scroller.clientWidth / ITEM_W) + OVERSCAN * 2;
    var start = Math.max(0, Math.floor(scrollX / ITEM_W) - OVERSCAN);
    var end   = Math.min(TOTAL, start + visibleCount);

    if (start === lastStart) return;
    lastStart = start;

    for (var k = 0; k < pool.length; k++) {
      var idx = start + k;
      if (idx >= end || k >= visibleCount) {
        pool[k].el.style.transform = 'translateX(-9999px)';
        pool[k].assignedIndex = -1;
        continue;
      }
      var item = allItems[idx];
      pool[k].assignedIndex = idx;
      pool[k].el.style.transform = 'translateX(' + (idx * ITEM_W) + 'px)';
      pool[k].el.querySelector('.card-title').textContent = item.title;
      pool[k].el.querySelector('.card-link').innerHTML =
        '<a href="/hscroll/' + item.id + '">Link #' + item.id + '</a>';
    }
  }

  render();
  scroller.addEventListener('scroll', render);
})();
</script>
</body>
</html>
"""

# Test 5 — Transform-based, 1000 items (stress test)
# Identical logic to Test 1 but scaled to 1000 items.
TRANSFORM_SCROLL_1000_HTML = TRANSFORM_SCROLL_HTML.replace(
    "var TOTAL      = 50;",
    "var TOTAL      = 1000;",
)

# Test 7 — Variable Row Heights virtual scroll
# 80 items where each item N has height 40 + (N % 5) * 20 px (40-120px).
# Uses transform-based recycling (translateY) with a pool of ~15 DOM nodes.
# Container style.height is the SUM of all item heights.
# The scroll render uses cumulative-sum lookup to find visible items.
VARIABLE_ROW_HEIGHTS_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: sans-serif; }
  #container {
    position: relative;
    width: 600px;
    margin: 0 auto;
  }
  .item {
    position: absolute;
    left: 0; right: 0;
    padding: 10px 14px;
    border-bottom: 1px solid #eee;
    background: #fff;
    overflow: hidden;
  }
  .item .title { font-weight: bold; font-size: 14px; }
  .item .meta  { color: #777; font-size: 12px; margin-top: 4px; }
</style>
</head>
<body>
<div id="container"></div>
<script>
(function () {
  var TOTAL    = 80;
  var POOL     = 15;
  var OVERSCAN = 3;

  // Build data + cumulative offsets
  var allItems = [];
  var offsets  = [0];  // offsets[i] = top of item i
  for (var i = 0; i < TOTAL; i++) {
    var h = 40 + (i % 5) * 20;  // heights: 40, 60, 80, 100, 120, 40, 60, ...
    allItems.push({ id: i + 1, title: 'VarH Item ' + (i + 1), height: h });
    offsets.push(offsets[i] + h);
  }
  var totalHeight = offsets[TOTAL];

  var container = document.getElementById('container');
  container.style.height = totalHeight + 'px';

  // Pool of DOM nodes
  var pool = [];
  for (var j = 0; j < POOL; j++) {
    var el = document.createElement('div');
    el.className = 'item';
    el.style.transform = 'translateY(-9999px)';
    el.innerHTML = '<div class="title"></div><div class="meta"></div>';
    container.appendChild(el);
    pool.push({ el: el, assignedIndex: -1 });
  }

  // Binary search: find first item whose top <= scrollY
  function findStart(scrollY) {
    var lo = 0, hi = TOTAL - 1;
    while (lo < hi) {
      var mid = (lo + hi + 1) >> 1;
      if (offsets[mid] <= scrollY) lo = mid;
      else hi = mid - 1;
    }
    return lo;
  }

  var lastStart = -1;

  function render() {
    var scrollY = window.scrollY;
    var vpBottom = scrollY + window.innerHeight;

    var rawStart = findStart(scrollY);
    var start = Math.max(0, rawStart - OVERSCAN);

    // Find end: first item whose top > vpBottom, + overscan
    var end = start;
    while (end < TOTAL && offsets[end] < vpBottom) end++;
    end = Math.min(TOTAL, end + OVERSCAN);

    if (start === lastStart) return;
    lastStart = start;

    for (var k = 0; k < pool.length; k++) {
      var idx = start + k;
      if (idx >= end || idx >= TOTAL) {
        pool[k].el.style.transform = 'translateY(-9999px)';
        pool[k].el.style.height = '0px';
        pool[k].assignedIndex = -1;
        continue;
      }
      var item = allItems[idx];
      pool[k].assignedIndex = idx;
      pool[k].el.style.transform = 'translateY(' + offsets[idx] + 'px)';
      pool[k].el.style.height = item.height + 'px';
      pool[k].el.querySelector('.title').textContent = item.title;
      pool[k].el.querySelector('.meta').innerHTML =
        '<a href="/varh/' + item.id + '">#' + item.id + '</a>';
    }
  }

  render();
  window.addEventListener('scroll', render);
})();
</script>
</body>
</html>
"""

# Test 8 — 2D Grid Virtualisation
# A 10x10 grid (100 cells total) where only ~20 DOM nodes exist at any time.
# Both horizontal AND vertical scrolling is needed to reveal all cells.
# Each cell is position: absolute with left/top computed from col/row.
# On scroll, the pool is recycled for the visible 2D viewport region.
GRID_2D_SCROLL_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: sans-serif; padding: 16px; }
  h1 { margin-bottom: 12px; font-size: 18px; }
  #grid-container {
    overflow: auto;
    height: 500px;
    width: 600px;
    position: relative;
    border: 2px solid #333;
  }
  #grid-inner {
    position: relative;
  }
  .cell {
    position: absolute;
    width: 110px;
    height: 90px;
    padding: 8px;
    border: 1px solid #ccc;
    background: #f9f9f9;
    font-size: 12px;
    overflow: hidden;
  }
  .cell a { color: #0066cc; text-decoration: none; }
</style>
</head>
<body>
<h1>2D Grid Virtual Scroll (10x10 = 100 cells)</h1>
<div id="grid-container">
  <div id="grid-inner"></div>
</div>
<script>
(function () {
  var ROWS     = 10;
  var COLS     = 10;
  var CELL_W   = 120;
  var CELL_H   = 100;
  var POOL_SIZE = 50;

  var container = document.getElementById('grid-container');
  var inner     = document.getElementById('grid-inner');

  inner.style.width  = (COLS * CELL_W) + 'px';
  inner.style.height = (ROWS * CELL_H) + 'px';

  var allCells = [];
  for (var r = 0; r < ROWS; r++) {
    for (var c = 0; c < COLS; c++) {
      allCells.push({ row: r, col: c, label: 'Cell ' + r + '-' + c });
    }
  }

  var pool = [];
  for (var i = 0; i < POOL_SIZE; i++) {
    var el = document.createElement('div');
    el.className = 'cell';
    el.style.left = '-9999px';
    el.style.top  = '-9999px';
    inner.appendChild(el);
    pool.push({ el: el, assignedKey: null });
  }

  var lastVisKey = '';

  function render() {
    var scrollLeft = container.scrollLeft;
    var scrollTop  = container.scrollTop;
    var vpW = container.clientWidth;
    var vpH = container.clientHeight;

    var startCol = Math.max(0, Math.floor(scrollLeft / CELL_W) - 1);
    var endCol   = Math.min(COLS, Math.ceil((scrollLeft + vpW) / CELL_W) + 1);
    var startRow = Math.max(0, Math.floor(scrollTop / CELL_H) - 1);
    var endRow   = Math.min(ROWS, Math.ceil((scrollTop + vpH) / CELL_H) + 1);

    var visKey = startCol + ',' + endCol + ',' + startRow + ',' + endRow;
    if (visKey === lastVisKey) return;
    lastVisKey = visKey;

    var visible = [];
    for (var r = startRow; r < endRow; r++) {
      for (var c = startCol; c < endCol; c++) {
        visible.push(allCells[r * COLS + c]);
      }
    }

    for (var p = 0; p < pool.length; p++) {
      if (p < visible.length) {
        var cell = visible[p];
        var key = cell.row + '-' + cell.col;
        pool[p].assignedKey = key;
        pool[p].el.style.left = (cell.col * CELL_W) + 'px';
        pool[p].el.style.top  = (cell.row * CELL_H) + 'px';
        pool[p].el.innerHTML =
          '<strong>' + cell.label + '</strong><br>' +
          '<a href="/cell/' + cell.row + '-' + cell.col + '">Link ' + cell.row + '-' + cell.col + '</a>';
      } else {
        pool[p].assignedKey = null;
        pool[p].el.style.left = '-9999px';
        pool[p].el.style.top  = '-9999px';
        pool[p].el.innerHTML  = '';
      }
    }
  }

  render();
  container.addEventListener('scroll', render);
})();
</script>
</body>
</html>
"""

# Test 9 — WebSocket/Async-Loaded Items (setTimeout simulating async fetch)
# Items are appended in batches of 10 (50 total) via setTimeout when the
# user scrolls near the bottom.  A loading spinner appears during the 300ms
# delay.  Items are never recycled — this is an append pattern, but with an
# async gap that can trip up crawlers that check "at bottom" before the new
# content has arrived.
ASYNC_LOADED_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { margin: 0; font-family: sans-serif; }
  .feed-item { padding: 16px; border-bottom: 1px solid #eee; }
  .feed-item .title { font-weight: bold; font-size: 14px; }
  .feed-item .link  { color: #0066cc; font-size: 12px; margin-top: 4px; }
  #spinner {
    display: none;
    text-align: center;
    padding: 20px;
    color: #999;
    font-size: 14px;
  }
  #spinner.active { display: block; }
</style>
</head>
<body>
<div id="feed"></div>
<div id="spinner">Loading...</div>
<script>
(function () {
  var TOTAL   = 50;
  var BATCH   = 10;
  var DELAY   = 300;  // ms — simulates network/async latency
  var loaded  = 0;
  var loading = false;

  var feed    = document.getElementById('feed');
  var spinner = document.getElementById('spinner');

  function appendBatch() {
    var end = Math.min(loaded + BATCH, TOTAL);
    for (var i = loaded; i < end; i++) {
      var div = document.createElement('div');
      div.className = 'feed-item';
      div.innerHTML =
        '<div class="title">Async Item ' + (i + 1) + '</div>' +
        '<div class="link">' +
          '<a href="/async/' + (i + 1) + '">Link #' + (i + 1) + '</a>' +
        '</div>';
      feed.appendChild(div);
    }
    loaded = end;
    loading = false;
    spinner.classList.remove('active');
  }

  // Load first batch synchronously
  appendBatch();

  window.addEventListener('scroll', function () {
    if (loading || loaded >= TOTAL) return;
    // Trigger when within 150px of the bottom
    if (window.scrollY + window.innerHeight >= document.body.scrollHeight - 150) {
      loading = true;
      spinner.classList.add('active');
      setTimeout(appendBatch, DELAY);
    }
  });
})();
</script>
</body>
</html>
"""

# Test 10 — Nested Virtual Scroll (outer vertical + inner horizontal)
# OUTER: 5 categories recycled vertically via window scroll (each 200px tall).
# INNER: Each visible category contains a HORIZONTAL scrollable list of 10 items,
#         recycled horizontally via overflow-x: scroll.
# Total: 5 category links + 50 inner item links = 55 unique links.
NESTED_VIRTUAL_SCROLL_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: sans-serif; }
  #outer-container {
    position: relative;
    width: 800px;
    margin: 0 auto;
  }
  .category {
    position: absolute;
    left: 0; right: 0;
    height: 200px;
    padding: 10px;
    border-bottom: 2px solid #ccc;
    background: #fafafa;
  }
  .category .cat-title { font-weight: bold; font-size: 16px; margin-bottom: 8px; }
  .inner-scroll {
    overflow-x: scroll;
    white-space: nowrap;
    height: 150px;
    position: relative;
    border: 1px solid #ddd;
    background: #fff;
  }
  .inner-spacer {
    display: inline-block;
    height: 1px;
  }
  .inner-item {
    position: absolute;
    top: 10px;
    width: 120px;
    height: 130px;
    display: inline-block;
    padding: 8px;
    border: 1px solid #eee;
    background: #f5f5f5;
    white-space: normal;
    font-size: 12px;
    vertical-align: top;
  }
  .inner-item a { color: #0066cc; }
</style>
</head>
<body>
<div id="outer-container"></div>
<script>
(function () {
  var NUM_CATS     = 5;
  var ITEMS_PER    = 10;
  var CAT_H        = 200;
  var ITEM_W       = 130;
  var OVERSCAN     = 1;
  var VISIBLE_CATS = Math.ceil(window.innerHeight / CAT_H) + OVERSCAN * 2;
  var VISIBLE_ITEMS = 4;

  var container = document.getElementById('outer-container');
  container.style.height = (NUM_CATS * CAT_H) + 'px';

  var catPool = [];
  for (var c = 0; c < VISIBLE_CATS; c++) {
    var el = document.createElement('div');
    el.className = 'category';
    el.style.transform = 'translateY(-9999px)';
    el.innerHTML =
      '<div class="cat-title"></div>' +
      '<div class="inner-scroll"><div class="inner-spacer"></div></div>';
    container.appendChild(el);
    catPool.push({ el: el, assignedCat: -1, itemPool: [], lastInnerStart: -1 });
  }

  for (var p = 0; p < catPool.length; p++) {
    var innerScroll = catPool[p].el.querySelector('.inner-scroll');
    for (var ii = 0; ii < VISIBLE_ITEMS + 2; ii++) {
      var itemEl = document.createElement('div');
      itemEl.className = 'inner-item';
      itemEl.style.left = '-9999px';
      innerScroll.appendChild(itemEl);
      catPool[p].itemPool.push(itemEl);
    }
  }

  var lastOuterStart = -1;

  function renderOuter() {
    var scrollY = window.scrollY;
    var start = Math.max(0, Math.floor(scrollY / CAT_H) - OVERSCAN);
    var end   = Math.min(NUM_CATS, start + VISIBLE_CATS);

    if (start === lastOuterStart) return;
    lastOuterStart = start;

    for (var k = 0; k < catPool.length; k++) {
      var catIdx = start + k;
      if (catIdx >= end) {
        catPool[k].el.style.transform = 'translateY(-9999px)';
        catPool[k].assignedCat = -1;
        continue;
      }
      catPool[k].assignedCat = catIdx;
      catPool[k].el.style.transform = 'translateY(' + (catIdx * CAT_H) + 'px)';
      var catNum = catIdx + 1;
      catPool[k].el.querySelector('.cat-title').innerHTML =
        '<a href="/cat/' + catNum + '">Category ' + catNum + '</a>';

      var spacer = catPool[k].el.querySelector('.inner-spacer');
      spacer.style.width = (ITEMS_PER * ITEM_W) + 'px';

      catPool[k].lastInnerStart = -1;
      var innerScroll = catPool[k].el.querySelector('.inner-scroll');
      innerScroll.scrollLeft = 0;
      renderInner(k);
    }
  }

  function renderInner(poolIdx) {
    var catInfo = catPool[poolIdx];
    if (catInfo.assignedCat < 0) return;
    var catNum = catInfo.assignedCat + 1;
    var innerScroll = catInfo.el.querySelector('.inner-scroll');
    var scrollLeft = innerScroll.scrollLeft;
    var start = Math.max(0, Math.floor(scrollLeft / ITEM_W) - 1);
    var end   = Math.min(ITEMS_PER, start + VISIBLE_ITEMS + 2);

    if (start === catInfo.lastInnerStart) return;
    catInfo.lastInnerStart = start;

    for (var j = 0; j < catInfo.itemPool.length; j++) {
      var itemIdx = start + j;
      if (itemIdx >= end) {
        catInfo.itemPool[j].style.left = '-9999px';
        continue;
      }
      var itemNum = itemIdx + 1;
      catInfo.itemPool[j].style.left = (itemIdx * ITEM_W) + 'px';
      catInfo.itemPool[j].innerHTML =
        '<a href="/cat/' + catNum + '/item/' + itemNum + '">Item ' + itemNum + '</a>' +
        '<br><small>Cat ' + catNum + '</small>';
    }
  }

  for (var p = 0; p < catPool.length; p++) {
    (function(idx) {
      var innerScroll = catPool[idx].el.querySelector('.inner-scroll');
      innerScroll.addEventListener('scroll', function() { renderInner(idx); });
    })(p);
  }

  renderOuter();
  window.addEventListener('scroll', renderOuter);
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Server helper
# ---------------------------------------------------------------------------

def start_server(html_dir: str, port: int) -> HTTPServer:
    """Start a simple HTTP server in a daemon thread."""

    class _Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=html_dir, **kwargs)

        def log_message(self, fmt, *args):  # silence access log
            pass

    server = HTTPServer(("127.0.0.1", port), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ---------------------------------------------------------------------------
# Individual test coroutines
# ---------------------------------------------------------------------------

async def test_transform_virtual_scroll() -> bool:
    """
    Test 1: Transform-based virtual scroll — 50 items.

    Items use CSS transform: translateY(Npx).  The container has an explicit
    style.height.  Only ~10 DOM nodes exist at a time; on scroll the pool is
    recycled by updating each node's transform.  This is how React/Next.js
    virtual lists work (skills.sh, Twitter, Tanstack Virtual).

    Fingerprint: each item has a unique <a href="/item/N"> link.
    Expected: capture all 50 items.
    """
    print("=" * 70)
    print("TEST 1: Transform-based virtual scroll — 50 items (translateY)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(TRANSFORM_SCROLL_HTML)
        server = start_server(tmpdir, 9741)
        try:
            schema = {
                "name": "Items",
                "baseSelector": ".item",
                "fields": [
                    {"name": "title", "selector": ".title", "type": "text"},
                    {"name": "link",  "selector": ".meta a", "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.3,
                )
                result = await crawler.arun(url="http://127.0.0.1:9741/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            # Deduplicate by unique href (/item/1 … /item/50)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/item/{i}" for i in range(1, 51)}
            missing      = sorted(expected - unique_links, key=lambda s: int(s.split("/")[-1]))

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/50")
            if missing:
                show = missing[:10]
                tail = "..." if len(missing) > 10 else ""
                print(f"  Missing       : {show}{tail}")
            passed = len(unique_links) >= 45
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


async def test_innerhtml_wipe_virtual_scroll() -> bool:
    """
    Test 2: innerHTML-wipe virtual scroll — 50 items (PR #1853 exact pattern).

    On every scroll event the container's innerHTML is cleared and freshly
    rendered items are appended.  No transforms, no explicit container height.
    Body height is set to TOTAL * ITEM_HEIGHT so the window can scroll.

    Fingerprint: each item has a unique <a href="/profile/N"> link.
    Expected: capture all 50 items.
    """
    print("\n" + "=" * 70)
    print("TEST 2: innerHTML-wipe virtual scroll — 50 items (PR #1853 pattern)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(INNERHTML_WIPE_HTML)
        server = start_server(tmpdir, 9742)
        try:
            schema = {
                "name": "Users",
                "baseSelector": "[data-testid='UserCell']",
                "fields": [
                    {"name": "name",   "selector": ".name",        "type": "text"},
                    {"name": "handle", "selector": ".handle",      "type": "text"},
                    {"name": "link",   "selector": ".handle a",    "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.2,
                )
                result = await crawler.arun(url="http://127.0.0.1:9742/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/profile/{i}" for i in range(1, 51)}
            missing      = sorted(expected - unique_links, key=lambda s: int(s.split("/")[-1]))

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/50")
            if missing:
                show = missing[:10]
                tail = "..." if len(missing) > 10 else ""
                print(f"  Missing       : {show}{tail}")
            passed = len(unique_links) >= 45
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


async def test_append_infinite_scroll() -> bool:
    """
    Test 3: Append-based infinite scroll — 100 quotes.

    Items are only ever appended to the DOM; nothing is ever removed.
    This is the classic infinite scroll pattern (no virtualisation at all).
    This test must not regress — crawl4ai has always handled this correctly.

    Fingerprint: each quote has a unique <a href="/author/N"> link.
    Expected: capture all 100 items.
    """
    print("\n" + "=" * 70)
    print("TEST 3: Append-based infinite scroll — 100 quotes (regression guard)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(APPEND_SCROLL_HTML)
        server = start_server(tmpdir, 9743)
        try:
            schema = {
                "name": "Quotes",
                "baseSelector": ".quote",
                "fields": [
                    {"name": "text",   "selector": ".text",     "type": "text"},
                    {"name": "author", "selector": ".author",   "type": "text"},
                    {"name": "link",   "selector": ".author a", "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.2,
                )
                result = await crawler.arun(url="http://127.0.0.1:9743/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/author/{i}" for i in range(1, 101)}
            missing      = sorted(expected - unique_links, key=lambda s: int(s.split("/")[-1]))

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/100")
            if missing:
                show = missing[:10]
                tail = "..." if len(missing) > 10 else ""
                print(f"  Missing       : {show}{tail}")
            passed = len(unique_links) >= 90
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


async def test_container_scroll() -> bool:
    """
    Test 4: Container-level virtual scroll — 200 rows.

    The scrolling happens on a fixed-height div (overflow-y: scroll), not on
    the window.  Inside the container a tall inner wrapper provides scroll
    height; rows use position: absolute + top offset and are recycled on
    container scroll events.

    Fingerprint: each row has a unique <a href="/row/N"> link.
    Expected: capture all 200 rows.
    """
    print("\n" + "=" * 70)
    print("TEST 4: Container-level virtual scroll — 200 rows (overflow-y: scroll)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(CONTAINER_SCROLL_HTML)
        server = start_server(tmpdir, 9744)
        try:
            schema = {
                "name": "Rows",
                "baseSelector": ".row",
                "fields": [
                    {"name": "label", "selector": "",    "type": "text"},
                    {"name": "link",  "selector": "a",   "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.1,
                )
                result = await crawler.arun(url="http://127.0.0.1:9744/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/row/{i}" for i in range(1, 201)}
            missing      = sorted(expected - unique_links, key=lambda s: int(s.split("/")[-1]))

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/200")
            if missing:
                show = missing[:10]
                tail = "..." if len(missing) > 10 else ""
                print(f"  Missing       : {show}{tail}")
            passed = len(unique_links) >= 180
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


async def test_transform_stress_1000() -> bool:
    """
    Test 5: Transform-based virtual scroll — 1000 items (stress test).

    Same DOM-recycling / translateY mechanism as Test 1 but scaled to 1000
    items.  Validates that the crawler's snapshot-and-deduplicate strategy
    holds up under a large item count without running out of memory or
    missing large swathes of the list.

    Fingerprint: each item has a unique <a href="/item/N"> link.
    Expected: capture all 1000 items.
    """
    print("\n" + "=" * 70)
    print("TEST 5: Transform-based virtual scroll — 1000 items (stress test)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(TRANSFORM_SCROLL_1000_HTML)
        server = start_server(tmpdir, 9745)
        try:
            schema = {
                "name": "Items",
                "baseSelector": ".item",
                "fields": [
                    {"name": "title", "selector": ".title", "type": "text"},
                    {"name": "link",  "selector": ".meta a", "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.05,
                )
                result = await crawler.arun(url="http://127.0.0.1:9745/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/item/{i}" for i in range(1, 1001)}
            missing_count = len(expected - unique_links)

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/1000")
            print(f"  Missing       : {missing_count}")
            passed = len(unique_links) >= 950
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


async def test_real_site_quotes() -> bool:
    """
    Test 6: Real site — quotes.toscrape.com/scroll.

    Append-based infinite scroll on a live public site.  This validates that
    real-world behaviour matches what the synthetic Test 3 exercises.

    Expected: capture all 100 quotes (or >=90 to allow for network variance).
    """
    print("\n" + "=" * 70)
    print("TEST 6: Real site — quotes.toscrape.com/scroll")
    print("=" * 70)

    schema = {
        "name": "Quotes",
        "baseSelector": ".quote",
        "fields": [
            {"name": "text",   "selector": ".text",   "type": "text"},
            {"name": "author", "selector": ".author", "type": "text"},
        ],
    }

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=JsonCssExtractionStrategy(schema),
            scan_full_page=True,
            scroll_delay=0.5,
        )
        result = await crawler.arun(url="https://quotes.toscrape.com/scroll", config=cfg)

    data   = json.loads(result.extracted_content)
    unique = {d["text"]: d for d in data if d.get("text")}

    print(f"  Raw extracted : {len(data)}")
    print(f"  Unique quotes : {len(unique)}/100")
    passed = len(unique) >= 90
    print(f"  Result        : {'PASS' if passed else 'FAIL'}")
    return passed


async def test_variable_row_heights() -> bool:
    """
    Test 7: Variable Row Heights virtual scroll -- 80 items.

    Items use CSS transform: translateY(Npx) but each item has a DIFFERENT
    height (40 + (N % 5) * 20 px, ranging from 40px to 120px).  Container
    style.height is the sum of all item heights.  The scroll render uses a
    cumulative-sum / binary-search approach to find visible items.  Pool of
    ~15 DOM nodes recycled on window scroll.

    This tests whether _handle_full_page_scan works when itemHeight is NOT
    uniform -- the Phase 4 scroll step calculation must not skip items.

    Fingerprint: each item has a unique <a href="/varh/N"> link.
    Expected: capture >=72 of 80 items (90%).
    """
    print("\n" + "=" * 70)
    print("TEST 7: Variable Row Heights virtual scroll -- 80 items")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(VARIABLE_ROW_HEIGHTS_HTML)
        server = start_server(tmpdir, 9751)
        try:
            schema = {
                "name": "Items",
                "baseSelector": ".item",
                "fields": [
                    {"name": "title", "selector": ".title", "type": "text"},
                    {"name": "link",  "selector": ".meta a", "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.3,
                )
                result = await crawler.arun(url="http://127.0.0.1:9751/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/varh/{i}" for i in range(1, 81)}
            missing      = sorted(expected - unique_links, key=lambda s: int(s.split("/")[-1]))

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/80")
            if missing:
                show = missing[:10]
                tail = "..." if len(missing) > 10 else ""
                print(f"  Missing       : {show}{tail}")
            passed = len(unique_links) >= 72
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


async def test_horizontal_virtual_scroll() -> bool:
    """
    Test 8: Horizontal virtual scroll — 60 items (translateX).

    Container scrolls horizontally (overflow-x: scroll) with items positioned
    via transform: translateX(Npx).  Pool of ~8 DOM nodes recycled on
    horizontal scroll.  This tests that _handle_full_page_scan detects and
    scrolls horizontal virtual scroll containers, not just vertical ones.

    Fingerprint: each item has a unique <a href="/hscroll/N"> link.
    Expected: capture >=54 of 60 items (90%).
    """
    print("\n" + "=" * 70)
    print("TEST 8: Horizontal virtual scroll — 60 items (translateX)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(HORIZONTAL_SCROLL_HTML)
        server = start_server(tmpdir, 9752)
        try:
            schema = {
                "name": "Cards",
                "baseSelector": ".hitem",
                "fields": [
                    {"name": "title", "selector": ".card-title", "type": "text"},
                    {"name": "link",  "selector": ".card-link a", "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.3,
                )
                result = await crawler.arun(url="http://127.0.0.1:9752/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/hscroll/{i}" for i in range(1, 61)}
            missing      = sorted(expected - unique_links, key=lambda s: int(s.split("/")[-1]))

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/60")
            if missing:
                show = missing[:10]
                tail = "..." if len(missing) > 10 else ""
                print(f"  Missing       : {show}{tail}")
            passed = len(unique_links) >= 54
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


async def test_2d_grid_virtual_scroll() -> bool:
    """
    Test 9: 2D Grid Virtualisation — 10x10 = 100 cells.

    A grid container scrolls both horizontally AND vertically.  Only ~20
    DOM nodes exist at any time; they are recycled as the user scrolls in
    either direction.  Each cell uses position: absolute with left/top
    calculated from its column/row.

    This tests whether _handle_full_page_scan can handle containers where
    scrollWidth > clientWidth AND scrollHeight > clientHeight — it needs
    to scroll in a zigzag pattern to visit all 2D regions.

    Fingerprint: each cell has a unique <a href="/cell/R-C"> link.
    Expected: capture >=90 of 100 cells (90%).
    """
    print("\n" + "=" * 70)
    print("TEST 9: 2D Grid Virtualisation — 10x10 = 100 cells")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(GRID_2D_SCROLL_HTML)
        server = start_server(tmpdir, 9753)
        try:
            schema = {
                "name": "Cells",
                "baseSelector": ".cell",
                "fields": [
                    {"name": "label", "selector": "strong",  "type": "text"},
                    {"name": "link",  "selector": "a",       "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.3,
                )
                result = await crawler.arun(url="http://127.0.0.1:9753/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/cell/{r}-{c}" for r in range(10) for c in range(10)}
            missing      = sorted(expected - unique_links)

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/100")
            if missing:
                show = missing[:10]
                tail = "..." if len(missing) > 10 else ""
                print(f"  Missing       : {show}{tail}")
            passed = len(unique_links) >= 90
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


async def test_async_loaded_items() -> bool:
    """
    Test 10: WebSocket/Async-Loaded Items — 50 items.

    Simulates async-loaded content (like a chat feed or real-time dashboard).
    50 items total, loaded in batches of 10 via setTimeout with a 300ms delay.
    On scroll near the bottom, a loading spinner appears, then after the delay
    new items are appended.  Items are NOT recycled — they accumulate.

    The async delay is the key challenge: the crawler may detect "at bottom"
    before the new batch has been appended by setTimeout, causing early exit.

    Fingerprint: each item has a unique <a href="/async/N"> link.
    Expected: capture >=45 of 50 items (90%).
    """
    print("\n" + "=" * 70)
    print("TEST 10: WebSocket/Async-Loaded Items — 50 items (setTimeout)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(ASYNC_LOADED_HTML)
        server = start_server(tmpdir, 9756)
        try:
            schema = {
                "name": "FeedItems",
                "baseSelector": ".feed-item",
                "fields": [
                    {"name": "title", "selector": ".title", "type": "text"},
                    {"name": "link",  "selector": ".link a", "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.5,
                )
                result = await crawler.arun(url="http://127.0.0.1:9756/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/async/{i}" for i in range(1, 51)}
            missing      = sorted(expected - unique_links, key=lambda s: int(s.split("/")[-1]))

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/50")
            if missing:
                show = missing[:10]
                tail = "..." if len(missing) > 10 else ""
                print(f"  Missing       : {show}{tail}")
            passed = len(unique_links) >= 45
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


async def test_nested_virtual_scroll() -> bool:
    """
    Test 11: Nested Virtual Scroll — 5 categories x 10 items = 55 links.

    OUTER: 5 categories recycled vertically via window scroll (translateY).
    Each category div has a link <a href="/cat/N">.
    INNER: Each visible category contains a HORIZONTAL scrollable list of
    10 items, recycled horizontally via overflow-x: scroll with position
    absolute + left offset.  Each item has <a href="/cat/N/item/M">.

    Total: 5 category links + 50 inner item links = 55 unique links.
    This tests nested scroll-within-scroll: the outer vertical scroll
    recycles categories, while each category's inner horizontal scroll
    recycles items.

    Expected: capture >=45 of 55 total unique links.
    """
    print("\n" + "=" * 70)
    print("TEST 11: Nested Virtual Scroll — 5 cats x 10 items = 55 links")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(NESTED_VIRTUAL_SCROLL_HTML)
        server = start_server(tmpdir, 9755)
        try:
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    scan_full_page=True,
                    scroll_delay=0.3,
                )
                result = await crawler.arun(url="http://127.0.0.1:9755/index.html", config=cfg)

            # Extract links from result.links (internal) and also
            # scan the raw HTML for /cat/ hrefs as a fallback.
            import re
            unique_links = set()
            # From result.links
            if hasattr(result, "links") and result.links:
                for link in result.links.get("internal", []):
                    href = link.get("href", "")
                    # Normalise: strip origin, keep path
                    if "/cat/" in href:
                        path = "/" + href.split("/cat/", 1)[1]
                        unique_links.add("/cat/" + path.lstrip("/"))
            # Also scan raw HTML for any /cat/ hrefs
            for m in re.findall(r'href="(/cat/[^"]+)"', result.html or ""):
                if m.startswith("/cat/"):
                    unique_links.add(m)

            # Expected links
            cat_links  = {f"/cat/{i}" for i in range(1, 6)}
            item_links = {f"/cat/{c}/item/{m}" for c in range(1, 6) for m in range(1, 11)}
            expected   = cat_links | item_links  # 55 total

            found_cats  = cat_links & unique_links
            found_items = item_links & unique_links
            missing     = sorted(expected - unique_links)

            print(f"  Unique links  : {len(unique_links & expected)}/55")
            print(f"  Cat links     : {len(found_cats)}/5")
            print(f"  Item links    : {len(found_items)}/50")
            if missing:
                show = missing[:15]
                tail = "..." if len(missing) > 15 else ""
                print(f"  Missing       : {show}{tail}")
            passed = len(unique_links & expected) >= 45
            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


# Test 9 — Multiple virtual containers on same page
# TWO independent pool-based virtual scroll containers side-by-side.
# Container A (#scroller-a): 40 items, height 400px, overflow-y: scroll
# Container B (#scroller-b): 30 items, height 300px, overflow-y: scroll
# Both use position: absolute + pool recycling independently.
MULTIPLE_CONTAINERS_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: sans-serif; padding: 20px; }
  h1 { margin-bottom: 16px; font-size: 20px; }
  .page-layout { display: flex; gap: 40px; align-items: flex-start; }
  .panel { flex: 1; }
  .panel h2 { margin-bottom: 8px; font-size: 16px; }
  .panel p  { margin-bottom: 12px; color: #666; font-size: 13px; }
  .scroller-a {
    height: 400px;
    overflow-y: scroll;
    border: 1px solid #ccc;
    position: relative;
    width: 100%;
  }
  .scroller-b {
    height: 300px;
    overflow-y: scroll;
    border: 1px solid #ccc;
    position: relative;
    width: 100%;
  }
  .inner-a, .inner-b { position: relative; }
  .entry {
    position: absolute;
    left: 0; right: 0;
    height: 50px;
    line-height: 50px;
    padding: 0 12px;
    border-bottom: 1px solid #eee;
    font-size: 13px;
  }
  .static-content {
    text-align: center;
    padding: 20px;
    flex: 0 0 auto;
  }
  .static-content h2 { font-size: 15px; margin-bottom: 8px; }
  .static-content p  { color: #888; font-size: 12px; }
</style>
</head>
<body>
<h1>Multiple Virtual Containers</h1>
<div class="page-layout">
  <div class="panel">
    <h2>List A (40 items)</h2>
    <p>Product catalog items</p>
    <div class="scroller-a" id="scroller-a">
      <div class="inner-a" id="inner-a"></div>
    </div>
  </div>

  <div class="static-content">
    <h2>Dashboard</h2>
    <p>This is static content between two virtual scroll lists.</p>
    <p>Both lists scroll independently with their own recycling pools.</p>
  </div>

  <div class="panel">
    <h2>List B (30 items)</h2>
    <p>Recent activity feed</p>
    <div class="scroller-b" id="scroller-b">
      <div class="inner-b" id="inner-b"></div>
    </div>
  </div>
</div>
<script>
(function () {
  // Container A: 40 items
  var TOTAL_A   = 40;
  var ITEM_H_A  = 50;
  var VISIBLE_A = 12;
  var OVERSCAN_A = 3;

  var scrollerA = document.getElementById('scroller-a');
  var innerA    = document.getElementById('inner-a');
  innerA.style.height = (TOTAL_A * ITEM_H_A) + 'px';

  var poolSizeA = VISIBLE_A + OVERSCAN_A * 2;
  var poolA = [];
  for (var j = 0; j < poolSizeA; j++) {
    var el = document.createElement('div');
    el.className = 'entry';
    el.style.top = '-9999px';
    innerA.appendChild(el);
    poolA.push(el);
  }

  var lastStartA = -1;

  function renderA() {
    var scrollTop = scrollerA.scrollTop;
    var start = Math.max(0, Math.floor(scrollTop / ITEM_H_A) - OVERSCAN_A);
    var end   = Math.min(TOTAL_A, start + poolSizeA);

    if (start === lastStartA) return;
    lastStartA = start;

    for (var k = 0; k < poolA.length; k++) {
      var idx = start + k;
      if (idx >= end) {
        poolA[k].style.top = '-9999px';
        poolA[k].textContent = '';
        continue;
      }
      poolA[k].style.top  = (idx * ITEM_H_A) + 'px';
      poolA[k].setAttribute('data-row', idx + 1);
      poolA[k].innerHTML =
        'Product ' + (idx + 1) + ' &mdash; ' +
        '<a href="/list-a/' + (idx + 1) + '">view #' + (idx + 1) + '</a>';
    }
  }

  renderA();
  scrollerA.addEventListener('scroll', renderA);

  // Container B: 30 items
  var TOTAL_B   = 30;
  var ITEM_H_B  = 50;
  var VISIBLE_B = 10;
  var OVERSCAN_B = 2;

  var scrollerB = document.getElementById('scroller-b');
  var innerB    = document.getElementById('inner-b');
  innerB.style.height = (TOTAL_B * ITEM_H_B) + 'px';

  var poolSizeB = VISIBLE_B + OVERSCAN_B * 2;
  var poolB = [];
  for (var j = 0; j < poolSizeB; j++) {
    var el = document.createElement('div');
    el.className = 'entry';
    el.style.top = '-9999px';
    innerB.appendChild(el);
    poolB.push(el);
  }

  var lastStartB = -1;

  function renderB() {
    var scrollTop = scrollerB.scrollTop;
    var start = Math.max(0, Math.floor(scrollTop / ITEM_H_B) - OVERSCAN_B);
    var end   = Math.min(TOTAL_B, start + poolSizeB);

    if (start === lastStartB) return;
    lastStartB = start;

    for (var k = 0; k < poolB.length; k++) {
      var idx = start + k;
      if (idx >= end) {
        poolB[k].style.top = '-9999px';
        poolB[k].textContent = '';
        continue;
      }
      poolB[k].style.top  = (idx * ITEM_H_B) + 'px';
      poolB[k].setAttribute('data-row', idx + 1);
      poolB[k].innerHTML =
        'Activity ' + (idx + 1) + ' &mdash; ' +
        '<a href="/list-b/' + (idx + 1) + '">detail #' + (idx + 1) + '</a>';
    }
  }

  renderB();
  scrollerB.addEventListener('scroll', renderB);
})();
</script>
</body>
</html>
"""


async def test_multiple_virtual_containers() -> bool:
    """
    Test 9: Multiple virtual containers on same page.

    TWO independent pool-based virtual scroll containers side-by-side.
    Container A (#scroller-a): 40 items, height 400px, overflow-y: scroll
    Container B (#scroller-b): 30 items, height 300px, overflow-y: scroll
    Both use position: absolute + pool recycling independently.

    Fingerprint: /list-a/N links in container A, /list-b/N links in container B.
    Expected: capture >=36 items from list-a AND >=27 items from list-b (90% each).
    """
    print("\n" + "=" * 70)
    print("TEST 9: Multiple virtual containers -- 40 + 30 items (side by side)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(MULTIPLE_CONTAINERS_HTML)
        server = start_server(tmpdir, 9754)
        try:
            schema = {
                "name": "Entries",
                "baseSelector": ".entry",
                "fields": [
                    {"name": "label", "selector": "",  "type": "text"},
                    {"name": "link",  "selector": "a", "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.1,
                )
                result = await crawler.arun(url="http://127.0.0.1:9754/index.html", config=cfg)

            data = json.loads(result.extracted_content)

            # Separate links by container
            links_a = {d["link"] for d in data if d.get("link") and d["link"].startswith("/list-a/")}
            links_b = {d["link"] for d in data if d.get("link") and d["link"].startswith("/list-b/")}
            expected_a = {f"/list-a/{i}" for i in range(1, 41)}
            expected_b = {f"/list-b/{i}" for i in range(1, 31)}
            missing_a  = sorted(expected_a - links_a, key=lambda s: int(s.split("/")[-1]))
            missing_b  = sorted(expected_b - links_b, key=lambda s: int(s.split("/")[-1]))

            print(f"  Raw extracted  : {len(data)}")
            print(f"  List A by href : {len(links_a)}/40")
            if missing_a:
                show = missing_a[:10]
                tail = "..." if len(missing_a) > 10 else ""
                print(f"  List A missing : {show}{tail}")
            print(f"  List B by href : {len(links_b)}/30")
            if missing_b:
                show = missing_b[:10]
                tail = "..." if len(missing_b) > 10 else ""
                print(f"  List B missing : {show}{tail}")

            passed_a = len(links_a) >= 36
            passed_b = len(links_b) >= 27
            passed = passed_a and passed_b
            print(f"  List A         : {'PASS' if passed_a else 'FAIL'} (>=36)")
            print(f"  List B         : {'PASS' if passed_b else 'FAIL'} (>=27)")
            print(f"  Result         : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


# Test — Large page with small virtual scroll section in the middle
# A ~2000px+ page of static content with a 400px overflow-y:scroll container
# embedded in the middle.  The container has 60 virtual items (pool of ~12 DOM
# nodes, position: absolute, recycled on container scroll).
SMALL_VIRTUAL_IN_LARGE_PAGE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: sans-serif; }

  .site-header {
    height: 200px; background: #2c3e50; color: #fff;
    display: flex; align-items: center; justify-content: center;
  }
  .site-header nav a { color: #ecf0f1; margin: 0 12px; text-decoration: none; }

  .hero {
    height: 500px; background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff; display: flex; flex-direction: column;
    align-items: center; justify-content: center; text-align: center;
    padding: 40px;
  }
  .hero h1 { font-size: 36px; margin-bottom: 16px; }
  .hero p  { font-size: 18px; max-width: 600px; line-height: 1.6; }

  .static-text {
    min-height: 300px; padding: 40px 60px; font-size: 16px; line-height: 1.8;
    background: #f9f9f9;
  }

  .widget-section { padding: 20px 60px; background: #fff; }
  .widget-section h2 { margin-bottom: 12px; font-size: 20px; }
  #vscroll-container {
    height: 400px; overflow-y: scroll; border: 2px solid #ccc;
    position: relative; width: 100%; max-width: 700px;
  }
  #vscroll-inner { position: relative; }
  .vitem {
    position: absolute; left: 0; right: 0; height: 50px;
    line-height: 50px; padding: 0 14px; border-bottom: 1px solid #eee;
    font-size: 14px; background: #fff;
  }
  .vitem a { color: #3498db; }

  .site-footer {
    min-height: 300px; background: #2c3e50; color: #ecf0f1;
    padding: 40px 60px; font-size: 14px; line-height: 1.8;
  }
  .site-footer a { color: #3498db; }

  .bottom-text {
    min-height: 200px; padding: 40px 60px; font-size: 16px; line-height: 1.8;
    background: #fafafa;
  }
</style>
</head>
<body>

<header class="site-header">
  <nav>
    <a href="/nav/home" id="nav-home">Home</a>
    <a href="/nav/about" id="nav-about">About</a>
    <a href="/nav/services" id="nav-services">Services</a>
    <a href="/nav/contact" id="nav-contact">Contact</a>
  </nav>
</header>

<section class="hero">
  <h1 id="hero-title">Welcome to Our Platform</h1>
  <p id="hero-desc">This is a large page with a virtual scroll widget embedded in the
  middle. The scanner must handle both the static content and the virtual
  scroll container to capture everything.</p>
</section>

<section class="static-text">
  <p id="above-text">This is static content that appears ABOVE the virtual scroll
  section. It contains important information that must be captured by the crawler.
  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
  incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
  nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
</section>

<section class="widget-section">
  <h2>Data Feed</h2>
  <div id="vscroll-container">
    <div id="vscroll-inner"></div>
  </div>
</section>

<footer class="site-footer">
  <p id="footer-text">This is the site footer with links and information that appears
  BELOW the virtual scroll section.</p>
  <p>
    <a href="/footer/privacy" id="footer-privacy">Privacy Policy</a> |
    <a href="/footer/terms" id="footer-terms">Terms of Service</a> |
    <a href="/footer/sitemap" id="footer-sitemap">Sitemap</a>
  </p>
</footer>

<section class="bottom-text">
  <p id="below-text">Final section of static content at the very bottom of the page.
  This must also be captured by the scanner. The page total height exceeds 2000px
  with the virtual scroll widget in the middle.</p>
</section>

<script>
(function () {
  var TOTAL    = 60;
  var ITEM_H   = 50;
  var POOL     = 12;
  var OVERSCAN = 2;

  var allItems = [];
  for (var i = 0; i < TOTAL; i++) {
    allItems.push({ id: i + 1, label: 'Mid Item ' + (i + 1) });
  }

  var container = document.getElementById('vscroll-container');
  var inner     = document.getElementById('vscroll-inner');
  inner.style.height = (TOTAL * ITEM_H) + 'px';

  var pool = [];
  for (var j = 0; j < POOL; j++) {
    var el = document.createElement('div');
    el.className = 'vitem';
    el.style.top = '-9999px';
    inner.appendChild(el);
    pool.push(el);
  }

  var lastStart = -1;

  function render() {
    var scrollTop = container.scrollTop;
    var start = Math.max(0, Math.floor(scrollTop / ITEM_H) - OVERSCAN);
    var end   = Math.min(TOTAL, start + POOL);

    if (start === lastStart) return;
    lastStart = start;

    for (var k = 0; k < pool.length; k++) {
      var idx = start + k;
      if (idx >= end || idx >= TOTAL) {
        pool[k].style.top = '-9999px';
        pool[k].textContent = '';
        continue;
      }
      var item = allItems[idx];
      pool[k].style.top = (idx * ITEM_H) + 'px';
      pool[k].setAttribute('data-row', idx + 1);
      pool[k].innerHTML =
        'Mid Item ' + item.id + ' &mdash; ' +
        '<a href="/mid/' + item.id + '">detail #' + item.id + '</a>';
    }
  }

  render();
  container.addEventListener('scroll', render);
})();
</script>
</body>
</html>
"""


async def test_small_virtual_in_large_page() -> bool:
    """
    Test: Large page with small virtual scroll section in the middle.

    A 2000px+ page of static content (header, hero, text, footer) with a
    400px overflow-y:scroll container embedded in the middle.  The container
    holds 60 virtual items (pool of ~12 DOM nodes, position: absolute,
    recycled on container scroll).

    The scanner must:
      1. Scroll the page to reach the container (it is ~1000px down)
      2. Scroll the container to capture all 60 items
      3. Continue scrolling the page to capture static content below

    Fingerprint: each item has a unique <a href="/mid/N"> link.
    Expected: capture >=54 of 60 items (90%) from the virtual section.
    Also verify that static content above and below is in result.html.
    """
    print("\n" + "=" * 70)
    print("TEST 13: Large page with small virtual scroll in the middle — 60 items")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "index.html"), "w") as fh:
            fh.write(SMALL_VIRTUAL_IN_LARGE_PAGE_HTML)
        server = start_server(tmpdir, 9757)
        try:
            schema = {
                "name": "MidItems",
                "baseSelector": ".vitem",
                "fields": [
                    {"name": "label", "selector": "",  "type": "text"},
                    {"name": "link",  "selector": "a", "type": "attribute", "attribute": "href"},
                ],
            }
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=JsonCssExtractionStrategy(schema),
                    scan_full_page=True,
                    scroll_delay=0.2,
                )
                result = await crawler.arun(url="http://127.0.0.1:9757/index.html", config=cfg)

            data = json.loads(result.extracted_content)
            unique_links = {d["link"] for d in data if d.get("link")}
            expected     = {f"/mid/{i}" for i in range(1, 61)}
            missing      = sorted(expected - unique_links, key=lambda s: int(s.split("/")[-1]))

            print(f"  Raw extracted : {len(data)}")
            print(f"  Unique by href: {len(unique_links)}/60")
            if missing:
                show = missing[:10]
                tail = "..." if len(missing) > 10 else ""
                print(f"  Missing       : {show}{tail}")

            # Check static content above/below is present in result.html
            html = result.html or ""
            has_hero     = "hero-title" in html or "Welcome to Our Platform" in html
            has_above    = "above-text" in html or "ABOVE the virtual scroll" in html
            has_footer   = "footer-text" in html or "BELOW the virtual scroll" in html
            has_below    = "below-text" in html or "very bottom of the page" in html
            has_nav      = "nav-home" in html or "/nav/home" in html

            print(f"  Static content checks:")
            print(f"    Navigation : {'OK' if has_nav else 'MISSING'}")
            print(f"    Hero       : {'OK' if has_hero else 'MISSING'}")
            print(f"    Above text : {'OK' if has_above else 'MISSING'}")
            print(f"    Footer     : {'OK' if has_footer else 'MISSING'}")
            print(f"    Below text : {'OK' if has_below else 'MISSING'}")

            static_ok = has_hero and has_above and has_footer and has_below and has_nav
            items_ok  = len(unique_links) >= 54  # 90% of 60
            passed    = items_ok and static_ok

            if not items_ok:
                print(f"  FAIL: Only captured {len(unique_links)}/60 items (need >=54)")
            if not static_ok:
                print(f"  FAIL: Some static content is missing from result.html")

            print(f"  Result        : {'PASS' if passed else 'FAIL'}")
            return passed
        finally:
            server.shutdown()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    results: dict[str, bool] = {}

    results["Test 1 — Transform virtual scroll (50 items)"]    = await test_transform_virtual_scroll()
    results["Test 2 — innerHTML-wipe virtual scroll (50 items)"]= await test_innerhtml_wipe_virtual_scroll()
    results["Test 3 — Append infinite scroll (100 quotes)"]    = await test_append_infinite_scroll()
    results["Test 4 — Container scroll (200 rows)"]            = await test_container_scroll()
    results["Test 5 — Transform stress test (1000 items)"]     = await test_transform_stress_1000()
    results["Test 6 — Real site: quotes.toscrape.com"]         = await test_real_site_quotes()
    results["Test 7 — Variable Row Heights (80 items)"]          = await test_variable_row_heights()
    results["Test 8 — Horizontal virtual scroll (60 items)"]     = await test_horizontal_virtual_scroll()
    results["Test 9 — 2D grid virtualisation (100 cells)"]       = await test_2d_grid_virtual_scroll()
    results["Test 10 — Multiple virtual containers (40+30)"]     = await test_multiple_virtual_containers()
    results["Test 11 — Nested virtual scroll (55 links)"]        = await test_nested_virtual_scroll()
    results["Test 12 — Async-loaded items (50 items)"]           = await test_async_loaded_items()
    results["Test 13 — Small virtual in large page (60 items)"]  = await test_small_virtual_in_large_page()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        tag = "PASS" if passed else "FAIL"
        print(f"  [{tag}] {name}")
    print("=" * 70)

    total = sum(results.values())
    print(f"\n  {total}/{len(results)} tests passed\n")


if __name__ == "__main__":
    asyncio.run(main())
