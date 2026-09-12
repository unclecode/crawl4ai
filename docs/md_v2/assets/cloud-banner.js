/* The Crawl4AI Cloud banner: the paste block per client, the state per browser, the events.
   State: `c4-cloud-banner` in localStorage = {version, state}; the pre-paint script in overrides/main.html
   already set <html data-c4b>. Events go to the gate's beacon sink as one small POST per click (a click
   usually leaves the page, so nothing is batched); DNT and GPC turn the events off, never the banner. */
(function () {
  "use strict";
  /* the theme loads this file in <head>: wait for the markup when the page is still parsing */
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", init); } else { init(); }
  function init() {
  var root = document.getElementById("c4b"); if (!root) return;
  var html = document.documentElement, code = document.getElementById("c4b-code");
  var STORE = "c4-cloud-banner", VERSION = 1, SINK = "https://gate.crawl4ai.com/v1/t";
  var KEY = '<span class="c4b-k">YOUR_KEY</span>';
  var BLOCKS = {
    claude:   '<span class="c4b-cmt"># Claude Code · one line</span>\nclaude mcp add --transport http crawl4ai https://gate.crawl4ai.com/mcp \\\n  --header "Authorization: Bearer ' + KEY + '"',
    codex:    '<span class="c4b-cmt"># Codex · ~/.codex/config.toml</span>\n[mcp_servers.crawl4ai]\nurl = "https://gate.crawl4ai.com/mcp"\nhttp_headers = { Authorization = "Bearer ' + KEY + '" }',
    opencode: '<span class="c4b-cmt"># OpenCode · opencode.json</span>\n{ "mcp": { "crawl4ai": {\n    "type": "remote",\n    "url": "https://gate.crawl4ai.com/mcp",\n    "headers": { "Authorization": "Bearer ' + KEY + '" } } } }',
    cursor:   '<span class="c4b-cmt"># Cursor · .cursor/mcp.json</span>\n{ "mcpServers": { "crawl4ai": {\n    "url": "https://gate.crawl4ai.com/mcp",\n    "headers": { "Authorization": "Bearer ' + KEY + '" } } } }',
    curl:     '<span class="c4b-cmt"># curl · one request</span>\ncurl -s "https://gate.crawl4ai.com/search?q=web+scraping+in+2026" \\\n  -H "Authorization: Bearer ' + KEY + '"'
  };

  /* ---- the anonymous id (the same shape as the landing's beacon) and the event sender ---- */
  var quiet = navigator.doNotTrack == "1" || navigator.doNotTrack == "yes" || window.globalPrivacyControl;
  var anon = "";
  try { anon = localStorage.getItem("c4a") || ""; if (!anon) { anon = Array.from(crypto.getRandomValues(new Uint8Array(8))).map(function (b) { return b.toString(16).padStart(2, "0"); }).join(""); localStorage.setItem("c4a", anon); } } catch (e) {}
  function ev(name, props) {
    if (quiet) return;
    props = props || {}; props.pg = "docs"; props.path = location.pathname; props.state = html.getAttribute("data-c4b") || "big";
    var body = JSON.stringify({ a: anon, e: [{ n: name, p: props }] });
    try { if (navigator.sendBeacon) navigator.sendBeacon(SINK, new Blob([body], { type: "text/plain" })); else fetch(SINK, { method: "POST", body: body, keepalive: true, mode: "no-cors" }); } catch (e) {}
  }
  /* the anonymous id rides every link to crawl4ai.com, so the landing can tie the signup to this visitor */
  if (anon && !quiet) root.querySelectorAll('a[href^="https://crawl4ai.com"]').forEach(function (a) { a.href += "&aid=" + anon; });

  /* ---- the state ---- */
  function save(state) { try { localStorage.setItem(STORE, JSON.stringify({ version: VERSION, state: state })); } catch (e) {} }
  function show(state) { html.setAttribute("data-c4b", state); save(state); if (state !== "off") ev("banner_shown"); }

  /* ---- the paste block ---- */
  function pick(client) {
    root.querySelectorAll(".c4b-tabs button").forEach(function (b) { b.setAttribute("aria-selected", b.getAttribute("data-c4b-client") === client); });
    code.innerHTML = BLOCKS[client] + '<button type="button" class="c4b-copy" data-c4b-act="copy">copy</button>';
    code.setAttribute("data-client", client);
  }

  root.addEventListener("click", function (e) {
    var t = e.target.closest("[data-c4b-act],[data-c4b-client],[data-c4b-ev]"); if (!t) return;
    if (t.hasAttribute("data-c4b-ev")) { ev(t.getAttribute("data-c4b-ev")); return; }
    var client = t.getAttribute("data-c4b-client"), act = t.getAttribute("data-c4b-act");
    if (client) { pick(client); ev("banner_client_picked", { client: client }); }
    if (act === "copy") {
      var txt = code.innerText.replace(/copy$/, "").trim();
      try { navigator.clipboard.writeText(txt); } catch (e) {}
      t.textContent = "copied"; setTimeout(function () { t.textContent = "copy"; }, 1200);
      ev("banner_copy_clicked", { client: code.getAttribute("data-client") });
    }
    if (act === "close") { if (document.getElementById("c4b-never").checked) { ev("banner_hidden_forever"); show("off"); } else { ev("banner_closed"); show("small"); } }
    if (act === "expand") { ev("banner_expanded"); show("big"); }
  });

  /* the fixed side panel starts under the header; while the banner is in view it must start under the
     banner too: --c4b-offset = the banner height still on screen, updated on scroll and resize */
  function offset() { var h = root.getBoundingClientRect().height, y = window.scrollY || 0; html.style.setProperty("--c4b-offset", Math.max(0, h - y) + "px"); }
  var tick = false;
  function onScroll() { if (tick) return; tick = true; requestAnimationFrame(function () { offset(); tick = false; }); }
  addEventListener("scroll", onScroll, { passive: true }); addEventListener("resize", onScroll);
  new MutationObserver(offset).observe(html, { attributes: true, attributeFilter: ["data-c4b"] });
  offset();

  pick("claude");
  if ((html.getAttribute("data-c4b") || "big") !== "off") ev("banner_shown");
  }
})();
