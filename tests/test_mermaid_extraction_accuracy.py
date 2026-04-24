"""
Mermaid Diagram Extraction Accuracy Test

Single-pass approach using crawl4ai's init_scripts + js_code to:
1. Capture <pre class="mermaid"> source BEFORE mermaid.js renders (ground truth)
2. Extract all visible text from rendered SVGs (black-box extraction)
3. Compare the two and report accuracy per diagram type

Separation guarantee:
- init_script captures raw source (no knowledge of SVGs)
- js_code extracts from SVGs (no knowledge of ground truth)
- Only this Python harness sees both sides

Capture strategy (defense-in-depth):
- MutationObserver: catches dynamically injected <pre class="mermaid"> nodes
  (handles React/Vue/Angular SPAs, AJAX-loaded content)
- DOMContentLoaded snapshot: fallback for static pages where all <pre> tags
  are already in the DOM at parse time
- Together these cover both SSR/static and CSR/dynamic rendering patterns
"""

import json
import os
import threading
import functools
from collections import defaultdict
from http.server import HTTPServer, SimpleHTTPRequestHandler

import pytest

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# ---------------------------------------------------------------------------
# Local HTTP server — serves tests/ directory for CDN access
# ---------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=TEST_DIR, **kwargs)

    def log_message(self, *a):
        pass  # suppress request logging


class _Server(HTTPServer):
    allow_reuse_address = True


@pytest.fixture(scope="module")
def srv():
    s = _Server(("127.0.0.1", 0), _Handler)
    port = s.server_address[1]
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    s.shutdown()


# ---------------------------------------------------------------------------
# JavaScript: Ground truth capture (runs BEFORE mermaid.js)
# ---------------------------------------------------------------------------

INIT_SCRIPT = """
(function() {
    window.__mermaidSources = {};

    // Mermaid source selector: covers both official conventions.
    // - pre.mermaid  → official docs, most JS-framework integrations
    // - div.mermaid  → older convention, most WordPress/Drupal/PHP plugins
    const MERMAID_SEL = 'pre.mermaid, div.mermaid';

    // Helper: record any mermaid source node, keyed by its closest diagram-group id.
    function captureMermaidNode(el) {
        const group = el.closest('.diagram-group');
        if (!group) return;
        const id = group.getAttribute('data-diagram-id');
        if (id && !(id in window.__mermaidSources)) {
            window.__mermaidSources[id] = el.textContent.trim();
        }
    }

    // Layer 1: MutationObserver — catches dynamically injected nodes
    // (React/Vue/Angular SPAs, AJAX-loaded content, lazy rendering, Livewire)
    const observer = new MutationObserver(mutations => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType !== 1) continue; // elements only
                // Direct match
                if (node.matches && node.matches(MERMAID_SEL)) {
                    captureMermaidNode(node);
                }
                // Descendant match
                if (node.querySelectorAll) {
                    node.querySelectorAll(MERMAID_SEL).forEach(captureMermaidNode);
                }
            }
            // Attribute changes: some libs add the 'mermaid' class after insertion
            if (
                mutation.type === 'attributes' &&
                mutation.target.matches &&
                mutation.target.matches(MERMAID_SEL)
            ) {
                captureMermaidNode(mutation.target);
            }
        }
    });
    // Observe document (always exists at script-inject time).
    // document.documentElement (<html>) may be null this early in Playwright's
    // addInitScript phase — observing document directly is always safe.
    observer.observe(document, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class'],
    });

    // Layer 2: DOMContentLoaded snapshot — captures static nodes already in
    // the HTML at parse time (PHP/WordPress/static sites)
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll(MERMAID_SEL).forEach(captureMermaidNode);
    }, { once: true });
})();
"""

# ---------------------------------------------------------------------------
# JavaScript: Black-box SVG text extraction (runs AFTER rendering)
# ---------------------------------------------------------------------------

EXTRACTION_JS = """
return (function() {
    const sources = window.__mermaidSources || {};
    const extracted = {};

    document.querySelectorAll('.diagram-group').forEach(group => {
        const id = group.getAttribute('data-diagram-id');
        const svg = group.querySelector('svg[id^="mermaid-"]');
        if (!id || !svg) return;

        const type = svg.getAttribute('aria-roledescription') || 'unknown';
        const texts = new Set();

        // Method 1: Native SVG <text> and <tspan> elements
        svg.querySelectorAll('text').forEach(textEl => {
            // Get direct text, not children's text (avoid double-counting)
            const t = textEl.textContent.trim();
            if (t && t.length > 0 && t.length < 500) {
                texts.add(t);
            }
        });

        // Method 2: foreignObject HTML content (used for complex labels)
        svg.querySelectorAll('foreignObject div, foreignObject span, foreignObject p').forEach(el => {
            const t = el.textContent.trim();
            if (t && t.length > 0 && t.length < 500) {
                texts.add(t);
            }
        });

        // Method 3: Known CSS class selectors per diagram type
        const classSelectors = [
            '.nodeLabel', '.edgeLabel', '.label',
            '.actor', '.messageText', '.loopText', '.noteText',
            '.classLabel', '.classTitle',
            '.entityLabel', '.relationshipLabel',
            '.taskText', '.sectionTitle', '.titleText',
            '.slice', '.pieCircle',
            '.commit-label', '.branch-label',
            '.mindmap-node',
            '.timeline-text', '.event-text',
            '.quadrant-point-text', '.quadrant-label',
        ];
        classSelectors.forEach(sel => {
            svg.querySelectorAll(sel).forEach(el => {
                const t = el.textContent.trim();
                if (t && t.length > 0 && t.length < 500) {
                    texts.add(t);
                }
            });
        });

        extracted[id] = {
            type: type,
            texts: Array.from(texts),
            svg_id: svg.id,
        };
    });

    return { sources: sources, extracted: extracted };
})();
"""

# ---------------------------------------------------------------------------
# Accuracy computation
# ---------------------------------------------------------------------------

# All ground truth keys that contain expected labels
LABEL_KEYS = [
    "expected_nodes", "expected_messages", "expected_members",
    "expected_tasks", "expected_entities", "expected_slices",
    "expected_events", "expected_fields", "expected_components",
    "expected_requirements", "expected_elements",
    "expected_participants", "expected_categories",
    "expected_causes", "expected_sets", "expected_intersections",
    "expected_axes", "expected_curves", "expected_columns",
    "expected_labels", "expected_transitions",
    "expected_relationships", "expected_sections",
    "expected_commits", "expected_branches", "expected_periods",
    "expected_points", "expected_groups", "expected_tags",
]


def flatten_expected_labels(gt_entry):
    """Extract all expected labels from a ground truth entry."""
    labels = set()
    for key in LABEL_KEYS:
        val = gt_entry.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            labels.update(str(v) for v in val)
        elif isinstance(val, dict):
            labels.update(str(k) for k in val.keys())
    return labels


def compute_accuracy(gt_entry, extracted_entry):
    """Compare extracted SVG texts against ground truth labels."""
    expected_labels = flatten_expected_labels(gt_entry)
    extracted_texts = set(extracted_entry.get("texts", []))

    if not expected_labels:
        return {
            "recall": 1.0,
            "found": set(),
            "missed": set(),
            "type_match": True,
            "expected_type": gt_entry.get("aria_roledescription", ""),
            "actual_type": extracted_entry.get("type", ""),
        }

    # Join all extracted texts into one blob for substring matching
    extracted_blob = " ".join(extracted_texts).lower()

    found = set()
    for label in expected_labels:
        label_lower = label.lower()
        # Check: is the label contained in any extracted text (substring match)?
        if label_lower in extracted_blob:
            found.add(label)
            continue
        # Check: is any extracted text contained in the label?
        for text in extracted_texts:
            if text.lower() in label_lower and len(text) > 1:
                found.add(label)
                break

    recall = len(found) / len(expected_labels)

    expected_type = gt_entry.get("aria_roledescription", "")
    actual_type = extracted_entry.get("type", "")
    type_match = expected_type == actual_type if expected_type else True

    return {
        "recall": recall,
        "found": found,
        "missed": expected_labels - found,
        "type_match": type_match,
        "expected_type": expected_type,
        "actual_type": actual_type,
    }


def print_report(results_by_type):
    """Print a formatted accuracy report table."""
    print("\n" + "=" * 90)
    print("MERMAID EXTRACTION ACCURACY REPORT")
    print("=" * 90)
    print(
        f"{'Type':<20} {'Count':>5} {'Recall':>8} {'Type OK':>8}  "
        f"{'Missed Labels'}"
    )
    print("-" * 90)

    all_recalls = []
    all_type_matches = 0
    all_count = 0

    for dtype in sorted(results_by_type.keys()):
        entries = results_by_type[dtype]
        count = len(entries)
        avg_recall = sum(e["recall"] for e in entries) / count
        type_ok = sum(1 for e in entries if e["type_match"])
        all_missed = set()
        for e in entries:
            all_missed.update(e["missed"])

        missed_str = ", ".join(sorted(all_missed)[:5])
        if len(all_missed) > 5:
            missed_str += f" (+{len(all_missed) - 5} more)"

        print(
            f"{dtype:<20} {count:>5} {avg_recall:>7.1%} {type_ok:>4}/{count:<3}  "
            f"{missed_str if missed_str else '-'}"
        )

        all_recalls.extend(e["recall"] for e in entries)
        all_type_matches += type_ok
        all_count += count

    overall_recall = sum(all_recalls) / len(all_recalls) if all_recalls else 0
    print("-" * 90)
    print(
        f"{'OVERALL':<20} {all_count:>5} {overall_recall:>7.1%} "
        f"{all_type_matches:>4}/{all_count:<3}"
    )
    print("=" * 90)
    return overall_recall


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

MERMAID_VERSIONS = ["11.14.0", "11.6.0", "11.0.0", "10.9.1"]

# JS injected before wait_for: switches Mermaid version then waits for re-render.
# Uses a template so the version string is embedded at test-parameterization time.
def _version_switch_js(version: str) -> str:
    return f"""
    (function() {{
        const sel = document.getElementById('mermaid-version');
        if (!sel) return;
        sel.value = '{version}';
        sel.dispatchEvent(new Event('change'));
    }})();
    """


@pytest.mark.asyncio
@pytest.mark.parametrize("version", MERMAID_VERSIONS)
async def test_mermaid_extraction_accuracy(srv, version):
    """
    Single-pass mermaid extraction accuracy test, run once per Mermaid version.

    Uses init_scripts to capture ground truth before rendering,
    js_code to extract from rendered SVGs, then compares.
    """

    browser_config = BrowserConfig(
        headless=True,
        init_scripts=[INIT_SCRIPT],
    )
    run_config = CrawlerRunConfig(
        js_code_before_wait=_version_switch_js(version),
        wait_for='js:() => document.querySelectorAll(\'svg[id^="mermaid-"]\').length >= 40',
        delay_before_return_html=5.0,
        js_code=EXTRACTION_JS,
        page_timeout=120000,
        cache_mode=CacheMode.BYPASS,
    )

    url = f"{srv}/test_mermaid_comprehensive.html"

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url, config=run_config)

    assert result.success, f"Crawl failed: {result.error_message}"

    # --- Parse js_execution_result ---
    # robust_execute_user_script returns {"success": True, "results": [<per-script-result>]}
    exec_result = result.js_execution_result
    assert exec_result, "js_execution_result is None — js_code may not have run"

    # Navigate the nested structure: top-level dict -> results list -> first script result
    if isinstance(exec_result, dict) and "results" in exec_result:
        script_results = exec_result["results"]
        data = script_results[0] if script_results else {}
    elif isinstance(exec_result, list):
        data = exec_result[0] if exec_result else {}
    else:
        data = exec_result

    sources = data.get("sources", {})
    extracted = data.get("extracted", {})

    print(f"\n=== Mermaid v{version} ===")
    print(f"--- Captured {len(sources)} mermaid sources via init_script")
    print(f"--- Extracted text from {len(extracted)} rendered SVGs")

    # --- Parse ground truth from HTML ---
    # The <script id="ground-truth"> survives mermaid rendering
    import re

    gt_match = re.search(
        r'<script[^>]*id="ground-truth"[^>]*>(.*?)</script>',
        result.html,
        re.DOTALL,
    )
    assert gt_match, "Ground truth JSON not found in crawled HTML"
    ground_truth = json.loads(gt_match.group(1))

    print(f"--- Ground truth contains {len(ground_truth)} diagram definitions")

    # --- Compute accuracy ---
    results_by_type = defaultdict(list)
    diagrams_without_extraction = []

    for diagram_id, gt_entry in ground_truth.items():
        ext_entry = extracted.get(diagram_id)
        if ext_entry is None:
            diagrams_without_extraction.append(diagram_id)
            continue

        acc = compute_accuracy(gt_entry, ext_entry)
        acc["diagram_id"] = diagram_id
        acc["source_captured"] = diagram_id in sources
        results_by_type[gt_entry["type"]].append(acc)

    if diagrams_without_extraction:
        print(
            f"\n--- WARNING: {len(diagrams_without_extraction)} diagrams had no "
            f"extraction: {diagrams_without_extraction}"
        )

    # --- Print report ---
    overall_recall = print_report(results_by_type)

    # --- Source capture rate ---
    source_captured = sum(
        1
        for entries in results_by_type.values()
        for e in entries
        if e["source_captured"]
    )
    total_diagrams = sum(len(v) for v in results_by_type.values())
    print(f"\nMermaid v{version} — source capture: {source_captured}/{total_diagrams} | label recall: {overall_recall:.1%}")

    # --- No hard assertion on recall — this is a diagnostic test ---
    # Just ensure we got results for most diagrams
    assert len(extracted) >= 40, (
        f"Only extracted {len(extracted)} diagrams, expected at least 40"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
