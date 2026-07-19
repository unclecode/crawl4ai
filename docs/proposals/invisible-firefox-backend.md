# Stealth patched-Firefox backend (proposal)

> Status: Draft proposal / interest check
> Tracking discussion: TBD

## Goal

Let crawl4ai optionally drive a fingerprint-patched Firefox 150 binary through the
existing `browser_type="firefox"` path, for targets where the standard Chromium
crawl (even with patchright / playwright-stealth) still trips Cloudflare,
Datadome, PerimeterX, or Akamai.

## Why

The recurring pain in this repo is bot detection: Cloudflare "Verifying you are
human" interstitials, Turnstile, and similar walls returning the challenge page
instead of the real content (see the stealth / bot-detection / cloudflare issue
threads). patchright and playwright-stealth patch Chromium at the JavaScript
layer, which still leaves a detectable surface: anti-bot scripts enumerate native
function `.toString()`, check for the CDP attach signature, and weight
Chromium-shaped traffic as higher risk because most residential-proxy bot traffic
is Chromium-based.

A Firefox build with fingerprint patches applied at the C++ source level (canvas
readback, WebGL getParameter, font metrics, audio, navigator, system colors) has
no JS shim and no CDP attach signature to detect, and presents a non-Chrome engine
that some anti-bot stacks score more leniently. It is not a silver bullet (IP
reputation and server-side scoring still apply), but it removes the
JS-shim-and-Chromium-shape part of the problem.

## Proposed change

This is small because the hook already exists. `browser_manager.py` already
launches Firefox via Playwright:

```python
# crawl4ai/browser_manager.py (around the launch dispatch)
if self.config.browser_type == "firefox":
    self.browser = await self.playwright.firefox.launch(**browser_args)
```

The only additions needed are to let `BrowserConfig` pass through:

1. `executable_path` for the firefox launch (point Playwright at the patched
   binary instead of the system Firefox), and
2. `firefox_user_prefs` (the patched binary is fully pref-driven; the spoofed
   values are selected via prefs, no hardcoding).

The patched binary lives at https://github.com/feder-cr/invisible_firefox
(MPL-2.0, same license as Firefox upstream) and auto-downloads to a cache dir on
first run via the https://github.com/feder-cr/invisible_playwright wrapper. The
returned object is a standard Playwright Browser, so the rest of crawl4ai
(extraction, screenshots, markdown, hooks) is unchanged.

## Out of scope

No change to the default Chromium path. No change to extraction / markdown /
screenshot logic. Firefox-stealth stays opt-in via config.

## Honest caveats

- crawl4ai is Python and so is the wrapper, so the wrapper itself can drop in;
  but the simplest integration is just `executable_path` + `firefox_user_prefs`
  on the existing firefox launch, no hard dependency required.
- This helps with the fingerprint/engine layer. It does not solve IP reputation
  or solve a Press & Hold challenge once it fires.
- Firefox via Playwright does not support CDP, so anything in crawl4ai that
  depends on `connect_over_cdp` is Chromium-only and unaffected.

If this is in scope I can wire the two config passthroughs and add a docs example.
If not, happy to close without noise.
