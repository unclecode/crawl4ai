/* The Crawl4AI Cloud strip: click events and the anonymous id on its links.
   Events go to the gate's beacon sink as one small POST per click (a click usually leaves the page, so
   nothing is batched); DNT and GPC turn the events off, never the strip. */
(function () {
  "use strict";
  /* the theme loads this file in <head>: wait for the markup when the page is still parsing */
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", init); } else { init(); }
  function init() {
    var root = document.getElementById("c4s"); if (!root) return;
    var html = document.documentElement, SINK = "https://gate.crawl4ai.com/v1/t";

    /* ---- the anonymous id (the same shape as the landing's beacon) and the event sender ---- */
    var quiet = navigator.doNotTrack == "1" || navigator.doNotTrack == "yes" || window.globalPrivacyControl;
    var anon = "";
    try { anon = localStorage.getItem("c4a") || ""; if (!anon) { anon = Array.from(crypto.getRandomValues(new Uint8Array(8))).map(function (b) { return b.toString(16).padStart(2, "0"); }).join(""); localStorage.setItem("c4a", anon); } } catch (e) {}
    function ev(name, props) {
      if (quiet) return;
      props = props || {}; props.pg = "docs"; props.path = location.pathname; props.ref = root.getAttribute("data-ref");
      props.state = html.getAttribute("data-c4s") || "full";
      var body = JSON.stringify({ a: anon, e: [{ n: name, p: props }] });
      try { if (navigator.sendBeacon) navigator.sendBeacon(SINK, new Blob([body], { type: "text/plain" })); else fetch(SINK, { method: "POST", body: body, keepalive: true, mode: "no-cors" }); } catch (e) {}
    }
    /* the anonymous id rides every link to crawl4ai.com, so the site can tie the sign-up to this visitor */
    if (anon && !quiet) document.querySelectorAll('.c4s a[href^="https://crawl4ai.com"], .c4s-box a[href^="https://crawl4ai.com"]').forEach(function (a) { a.href += "&aid=" + anon; });

    document.addEventListener("click", function (e) {
      var t = e.target.closest("[data-c4s-ev]"); if (t) ev(t.getAttribute("data-c4s-ev"));
    });

    /* plain links to crawl4ai.com (the Cloud menu item, the footer row): crawlers see the plain href; the
       ref and the anonymous id are added only when a person opens the link (any button, or the keyboard) */
    function tagHome(e) {
      var a = e.target.closest && e.target.closest("a[data-c4s-home]"); if (!a || a.getAttribute("data-c4s-tagged")) return;
      var ref = a.getAttribute("data-c4s-home");
      a.href += (a.href.indexOf("?") < 0 ? "?" : "&") + "ref=" + encodeURIComponent(ref) + (anon && !quiet ? "&aid=" + anon : "");
      a.setAttribute("data-c4s-tagged", "1");
      ev("cloud_home_clicked", { to: a.pathname, ref: ref });
    }
    document.addEventListener("mousedown", tagHome);
    document.addEventListener("keydown", function (e) { if (e.key === "Enter") tagHome(e); });

    /* ---- a full strip shrinks to one line on scroll, and grows back at the top of the page ---- */
    var shrunk = false, tick = false;
    function onScroll() {
      if (tick) return; tick = true;
      requestAnimationFrame(function () {
        tick = false;
        if (html.getAttribute("data-c4s") !== "full") return;
        var y = window.scrollY || 0;
        /* two thresholds, so a page resting near the top does not flicker between the states */
        if (!shrunk && y > 40) { shrunk = true; html.classList.add("c4s-shrunk"); }
        else if (shrunk && y < 8) { shrunk = false; html.classList.remove("c4s-shrunk"); }
      });
    }
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    ev("banner_shown");
  }
})();
