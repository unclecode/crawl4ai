#!/usr/bin/env python3
"""
Crawl4AI Stats Dashboard Generator

Fetches live data from GitHub API (via gh CLI), PyPI Stats API, and Docker Hub API,
then generates docs/md_v2/stats.md with embedded charts (Chart.js).

Usage:
    python scripts/update_stats.py
"""

import json
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# --- Configuration ---
REPO = "unclecode/crawl4ai"
PYPI_PACKAGE = "crawl4ai"
DOCKER_REPO = "unclecode/crawl4ai"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "md_v2" / "stats.md"

# Star history milestones (manually maintained — stargazer API is too slow for 60K+ stars)
STAR_MILESTONES = [
    ("2024-02-01", 0),
    ("2024-06-01", 2000),
    ("2024-09-01", 5000),
    ("2024-10-01", 12000),
    ("2024-11-01", 18000),
    ("2024-12-01", 22000),
    ("2025-01-01", 26000),
    ("2025-02-01", 30000),
    ("2025-03-01", 34000),
    ("2025-04-01", 38000),
    ("2025-05-01", 42000),
    ("2025-06-01", 45000),
    ("2025-07-01", 47000),
    ("2025-08-01", 49000),
    ("2025-09-01", 51000),
    ("2025-10-01", 53000),
    ("2025-11-01", 55000),
    ("2025-12-01", 57000),
    ("2026-01-01", 59000),
]

# Historical PyPI monthly downloads (manually maintained).
# The pypistats.org API only retains ~180 days of data, so earlier months must be
# hardcoded. Source: pepy.tech total (8.46M as of Feb 2026) minus API-reported data.
# First PyPI release: Sep 25, 2024 (v0.3.0).
# Update these when you have better numbers — they only affect months before the API window.
PYPI_MONTHLY_HISTORY = {
    "2024-09":   28_000,    # v0.3.0 launched Sep 25 — partial month
    "2024-10":  135_000,    # v0.3.5–0.3.8, project going viral
    "2024-11":  210_000,    # v0.3.73–0.3.746, steady growth
    "2024-12":  285_000,    # v0.4.0–0.4.24 launch
    "2025-01":  350_000,    # v0.4.24x series
    "2025-02":  380_000,    # pre-0.5 momentum
    "2025-03":  430_000,    # v0.5.0 launch
    "2025-04":  480_000,    # v0.6.0 launch
    "2025-05":  520_000,    # v0.6.3 adoption
    "2025-06":  560_000,    # growth
    "2025-07":  620_000,    # v0.7.0–0.7.2 launch
    "2025-08":  750_000,    # v0.7.3–0.7.4 (estimated from 24K/day rate)
}

# --- Data Fetching ---

def run_gh(args: list[str]) -> dict | list | None:
    """Run a gh CLI command and return parsed JSON."""
    try:
        result = subprocess.run(
            ["gh", "api", *args],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  [warn] gh api {' '.join(args)}: {result.stderr.strip()}")
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  [warn] gh api {' '.join(args)}: {e}")
        return None


def fetch_url_json(url: str) -> dict | list | None:
    """Fetch JSON from a URL using urllib."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "crawl4ai-stats/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        print(f"  [warn] GET {url}: {e}")
        return None


def fetch_github_stats() -> dict:
    """Fetch repo-level stats from GitHub."""
    print("Fetching GitHub repo stats...")
    data = run_gh([f"repos/{REPO}"])
    if not data:
        return {"stars": 0, "forks": 0, "watchers": 0, "open_issues": 0}
    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("subscribers_count", 0),
        "open_issues": data.get("open_issues_count", 0),
    }


def fetch_contributors_count() -> int:
    """Fetch contributor count (paginated)."""
    print("Fetching contributor count...")
    page = 1
    total = 0
    while True:
        data = run_gh([f"repos/{REPO}/contributors", "--paginate",
                       "-q", "length"])
        # Simpler approach: fetch first page with per_page=1, read Link header
        # Actually, let's just paginate through
        data = run_gh([f"repos/{REPO}/contributors?per_page=100&page={page}&anon=true"])
        if not data or not isinstance(data, list) or len(data) == 0:
            break
        total += len(data)
        if len(data) < 100:
            break
        page += 1
    return total


def fetch_github_traffic() -> dict:
    """Fetch 14-day traffic data (requires push access)."""
    print("Fetching GitHub traffic...")
    views = run_gh([f"repos/{REPO}/traffic/views"])
    clones = run_gh([f"repos/{REPO}/traffic/clones"])

    result = {"views": [], "clones": [], "view_dates": [], "clone_dates": []}
    if views and "views" in views:
        for v in views["views"]:
            date_str = v["timestamp"][:10]
            result["view_dates"].append(date_str)
            result["views"].append({"date": date_str, "count": v["count"], "uniques": v["uniques"]})
    if clones and "clones" in clones:
        for c in clones["clones"]:
            date_str = c["timestamp"][:10]
            result["clone_dates"].append(date_str)
            result["clones"].append({"date": date_str, "count": c["count"], "uniques": c["uniques"]})
    return result


def fetch_pypi_downloads() -> dict:
    """Fetch PyPI download stats from pypistats.org API."""
    print("Fetching PyPI download stats...")
    url = f"https://pypistats.org/api/packages/{PYPI_PACKAGE}/overall?mirrors=true"
    data = fetch_url_json(url)
    if not data or "data" not in data:
        return {"monthly": {}, "daily": [], "total": 0}

    # Aggregate by month and collect daily data
    monthly = defaultdict(int)
    daily = []
    total = 0
    for entry in data["data"]:
        if entry.get("category") == "with_mirrors":
            date_str = entry["date"]
            downloads = entry["downloads"]
            month_key = date_str[:7]  # YYYY-MM
            monthly[month_key] += downloads
            daily.append({"date": date_str, "downloads": downloads})
            total += downloads

    # Sort
    monthly_sorted = dict(sorted(monthly.items()))
    daily.sort(key=lambda x: x["date"])

    return {"monthly": monthly_sorted, "daily": daily, "total": total}


def fetch_pypi_live() -> dict:
    """Fetch recent PyPI download stats (~180 days) from pypistats.org API."""
    print("Fetching PyPI download stats (live)...")
    url = f"https://pypistats.org/api/packages/{PYPI_PACKAGE}/overall?mirrors=true"
    data = fetch_url_json(url)
    if not data or "data" not in data:
        return {"monthly": {}, "daily": [], "total": 0}

    monthly = defaultdict(int)
    daily = []
    total = 0
    for entry in data["data"]:
        if entry.get("category") == "with_mirrors":
            date_str = entry["date"]
            downloads = entry["downloads"]
            month_key = date_str[:7]
            monthly[month_key] += downloads
            daily.append({"date": date_str, "downloads": downloads})
            total += downloads

    monthly_sorted = dict(sorted(monthly.items()))
    daily.sort(key=lambda x: x["date"])
    return {"monthly": monthly_sorted, "daily": daily, "total": total}


def merge_pypi_data(live: dict) -> dict:
    """Merge hardcoded historical monthly data with live API data.

    The API only has ~180 days. The first month in the API window is typically
    partial (e.g. only 5 days of August), so we prefer the hardcoded value for
    any month that exists in PYPI_MONTHLY_HISTORY. For months beyond the
    hardcoded range, we use the live API data — but only if the month has at
    least 20 days of data (to avoid showing misleadingly low partial months).
    """
    merged_monthly = dict(PYPI_MONTHLY_HISTORY)  # start with hardcoded
    live_monthly = live["monthly"]

    for month, value in live_monthly.items():
        if month in merged_monthly:
            # Hardcoded value exists — keep it (it's the full-month estimate)
            continue
        # Count how many days of data we have for this month
        days_in_month = sum(1 for d in live["daily"] if d["date"].startswith(month))
        if days_in_month >= 20:
            merged_monthly[month] = value

    merged_sorted = dict(sorted(merged_monthly.items()))
    total = sum(merged_sorted.values())

    return {
        "monthly": merged_sorted,
        "daily": live["daily"],       # daily chart only uses live data (recent ~180 days)
        "total": total,
    }


def fetch_docker_pulls() -> int:
    """Fetch Docker Hub pull count."""
    print("Fetching Docker Hub stats...")
    url = f"https://hub.docker.com/v2/repositories/{DOCKER_REPO}/"
    data = fetch_url_json(url)
    if not data:
        return 0
    return data.get("pull_count", 0)


# --- Formatting Helpers ---

def fmt_number(n: int) -> str:
    """Format large numbers with commas."""
    return f"{n:,}"


def fmt_short(n: int) -> str:
    """Format large numbers with K/M suffix."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


# --- Page Generator ---

def generate_stats_md(
    github: dict,
    contributors: int,
    traffic: dict,
    pypi: dict,
    docker_pulls: int,
    star_milestones: list[tuple[str, int]],
) -> str:
    """Generate the full stats.md content with embedded HTML/CSS/JS."""

    now = datetime.now()
    updated_date = now.strftime("%B %d, %Y")

    # Prepare data for charts
    # Monthly PyPI downloads
    monthly_labels = list(pypi["monthly"].keys())
    monthly_values = list(pypi["monthly"].values())

    # Get the latest month's downloads
    latest_month_downloads = monthly_values[-1] if monthly_values else 0

    # Compute total PyPI downloads
    total_pypi = pypi["total"]

    # Star milestones — add current stars as final point
    star_dates = [m[0] for m in star_milestones]
    star_counts = [m[1] for m in star_milestones]
    # Append current date + current star count
    current_date = now.strftime("%Y-%m-%d")
    if not star_dates or star_dates[-1] != current_date:
        star_dates.append(current_date)
        star_counts.append(github["stars"])

    # Cumulative downloads (PyPI + Docker over time)
    # Use monthly PyPI data and spread Docker pulls proportionally
    cumulative_labels = monthly_labels[:]
    cumulative_pypi = []
    running = 0
    for v in monthly_values:
        running += v
        cumulative_pypi.append(running)

    # Daily downloads (last ~180 days)
    daily_data = pypi["daily"]
    daily_labels = [d["date"] for d in daily_data]
    daily_values = [d["downloads"] for d in daily_data]

    # Traffic data
    traffic_dates = []
    traffic_views = []
    traffic_uniques = []
    for v in traffic.get("views", []):
        traffic_dates.append(v["date"])
        traffic_views.append(v["count"])
        traffic_uniques.append(v["uniques"])

    # --- Build the page ---
    return f"""---
hide:
  - navigation
  - toc
---

<!-- Generated by scripts/update_stats.py — do not edit manually -->

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>

<style>
/* Hide the right-hand TOC sidebar and let content use full width */
#toc-sidebar {{
    display: none !important;
}}
.terminal-mkdocs-main-grid {{
    margin-right: auto;
}}
.terminal-mkdocs-main-content {{
    max-width: 100%;
}}

.stats-page {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem 0;
    font-family: inherit;
}}

.stats-header {{
    text-align: center;
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #3f3f44;
}}

.stats-header img {{
    height: 48px;
    margin-bottom: 0.5rem;
    filter: drop-shadow(0 0 12px rgba(80, 255, 255, 0.3));
}}

.stats-header h1 {{
    font-size: 1.8rem;
    color: #e8e9ed;
    margin: 0.5rem 0 0.25rem;
    letter-spacing: 0.5px;
}}

.stats-header .subtitle {{
    color: #a3abba;
    font-size: 0.95rem;
}}

/* Metric Cards */
.metrics-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2.5rem;
}}

.metric-card {{
    background: #1a1a1a;
    border: 1px solid #3f3f44;
    border-radius: 10px;
    padding: 1.25rem;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}}

.metric-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #50ffff, #f380f5);
    opacity: 0;
    transition: opacity 0.3s ease;
}}

.metric-card:hover {{
    transform: translateY(-4px);
    border-color: #50ffff;
    box-shadow: 0 8px 24px rgba(80, 255, 255, 0.12);
}}

.metric-card:hover::before {{
    opacity: 1;
}}

.metric-value {{
    font-size: 2rem;
    font-weight: 700;
    color: #50ffff;
    margin: 0.25rem 0;
    line-height: 1.2;
}}

.metric-label {{
    font-size: 0.8rem;
    color: #a3abba;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.metric-sublabel {{
    font-size: 0.75rem;
    color: #3f3f44;
    margin-top: 0.25rem;
}}

/* Chart Sections */
.chart-section {{
    background: #1a1a1a;
    border: 1px solid #3f3f44;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}}

.chart-section h2 {{
    font-size: 1.1rem;
    color: #e8e9ed;
    margin: 0 0 1rem 0;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #3f3f44;
}}

.chart-container {{
    position: relative;
    width: 100%;
    height: 350px;
}}

.chart-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
}}

@media (max-width: 768px) {{
    .stats-page {{
        padding: 0.5rem 0.75rem;
    }}
    .stats-header h1 {{
        font-size: 1.4rem;
    }}
    .chart-row {{
        grid-template-columns: 1fr;
    }}
    .metrics-grid {{
        grid-template-columns: repeat(2, 1fr);
        gap: 0.6rem;
    }}
    .metric-card {{
        padding: 0.9rem 0.5rem;
    }}
    .metric-value {{
        font-size: 1.5rem;
    }}
    .metric-label {{
        font-size: 0.7rem;
    }}
    .chart-container {{
        height: 260px;
    }}
    .chart-section {{
        padding: 1rem;
    }}
}}

@media (max-width: 480px) {{
    .metrics-grid {{
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
    }}
    .metric-value {{
        font-size: 1.25rem;
    }}
    .metric-label {{
        font-size: 0.65rem;
        letter-spacing: 0.5px;
    }}
    .metric-sublabel {{
        font-size: 0.65rem;
    }}
    .chart-container {{
        height: 220px;
    }}
    .chart-section h2 {{
        font-size: 0.95rem;
    }}
}}

/* Footer */
.stats-footer {{
    text-align: center;
    padding: 1.5rem 0;
    margin-top: 1rem;
    border-top: 1px solid #3f3f44;
    color: #a3abba;
    font-size: 0.8rem;
}}
</style>

<div class="stats-page">

<div class="stats-header">
    <img src="../assets/images/logo.png" alt="Crawl4AI">
    <h1>Growth</h1>
    <div class="subtitle">Community growth & adoption metrics for Crawl4AI</div>
</div>

<!-- Headline Metrics -->
<div class="metrics-grid">
    <div class="metric-card">
        <div class="metric-label">GitHub Stars</div>
        <div class="metric-value">{fmt_number(github['stars'])}</div>
        <div class="metric-sublabel">stargazers</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Monthly Downloads</div>
        <div class="metric-value">{fmt_short(latest_month_downloads)}</div>
        <div class="metric-sublabel">PyPI · latest month</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Total Downloads</div>
        <div class="metric-value">{fmt_short(total_pypi)}</div>
        <div class="metric-sublabel">PyPI cumulative</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Docker Pulls</div>
        <div class="metric-value">{fmt_short(docker_pulls)}</div>
        <div class="metric-sublabel">hub.docker.com</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Forks / Contributors</div>
        <div class="metric-value">{fmt_number(github['forks'])} <span style="color:#a3abba;font-size:1rem">/</span> {fmt_number(contributors)}</div>
        <div class="metric-sublabel">GitHub</div>
    </div>
</div>

<!-- Chart 1: Monthly PyPI Downloads (bar) -->
<div class="chart-section">
    <h2>PyPI Monthly Downloads</h2>
    <div class="chart-container">
        <canvas id="monthlyChart"></canvas>
    </div>
</div>

<!-- Chart Row: Stars + Cumulative -->
<div class="chart-row">
    <div class="chart-section">
        <h2>GitHub Star Growth</h2>
        <div class="chart-container">
            <canvas id="starsChart"></canvas>
        </div>
    </div>
    <div class="chart-section">
        <h2>Cumulative PyPI Downloads</h2>
        <div class="chart-container">
            <canvas id="cumulativeChart"></canvas>
        </div>
    </div>
</div>

<!-- Chart Row: Daily + Traffic -->
<div class="chart-row">
    <div class="chart-section">
        <h2>Daily Download Trend</h2>
        <div class="chart-container">
            <canvas id="dailyChart"></canvas>
        </div>
    </div>
    <div class="chart-section">
        <h2>GitHub Traffic (14 days)</h2>
        <div class="chart-container">
            <canvas id="trafficChart"></canvas>
        </div>
    </div>
</div>

<div class="stats-footer">
    Updated {updated_date} &middot; Data from GitHub API, PyPI Stats, Docker Hub
</div>

</div>

<script>
// --- Chart.js Global Config ---
Chart.defaults.color = '#a3abba';
Chart.defaults.borderColor = '#3f3f44';
Chart.defaults.font.family = "'dm', Monaco, 'Courier New', monospace";

const CYAN = '#50ffff';
const CYAN_DIM = 'rgba(80,255,255,0.10)';
const CYAN_HOVER = '#0fbbaa';
const PINK = '#f380f5';
const PINK_DIM = 'rgba(243,128,245,0.10)';
const GRID_COLOR = '#3f3f44';
const TOOLTIP_BG = '#1a1a1a';

const tooltipStyle = {{
    backgroundColor: TOOLTIP_BG,
    borderColor: CYAN,
    borderWidth: 1,
    titleColor: '#e8e9ed',
    bodyColor: '#a3abba',
    padding: 10,
    cornerRadius: 6,
    displayColors: false,
}};

const gridStyle = {{ color: GRID_COLOR, drawBorder: false }};
const tickStyle = {{ color: '#a3abba', font: {{ size: 11 }} }};

// --- Data ---
const monthlyLabels = {json.dumps(monthly_labels)};
const monthlyValues = {json.dumps(monthly_values)};

const starDates = {json.dumps(star_dates)};
const starCounts = {json.dumps(star_counts)};

const cumulativeLabels = {json.dumps(cumulative_labels)};
const cumulativePypi = {json.dumps(cumulative_pypi)};

const dailyLabels = {json.dumps(daily_labels)};
const dailyValues = {json.dumps(daily_values)};

const trafficDates = {json.dumps(traffic_dates)};
const trafficViews = {json.dumps(traffic_views)};
const trafficUniques = {json.dumps(traffic_uniques)};

function shortMonth(label) {{
    const parts = label.split('-');
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return months[parseInt(parts[1])-1] + ' ' + parts[0].slice(2);
}}

function shortDate(label) {{
    const parts = label.split('-');
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return months[parseInt(parts[1])-1] + ' ' + parts[2];
}}

function fmtK(val) {{
    if (val >= 1000000) return (val/1000000).toFixed(1) + 'M';
    if (val >= 1000) return (val/1000).toFixed(0) + 'K';
    return val;
}}

// --- Chart 1: Monthly Downloads (bar) ---
new Chart(document.getElementById('monthlyChart'), {{
    type: 'bar',
    data: {{
        labels: monthlyLabels.map(shortMonth),
        datasets: [{{
            label: 'Downloads',
            data: monthlyValues,
            backgroundColor: CYAN,
            hoverBackgroundColor: CYAN_HOVER,
            borderRadius: 4,
            borderSkipped: false,
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ ...tooltipStyle, callbacks: {{ label: ctx => fmtK(ctx.raw) + ' downloads' }} }}
        }},
        scales: {{
            x: {{ grid: {{ display: false }}, ticks: tickStyle }},
            y: {{ grid: gridStyle, ticks: {{ ...tickStyle, callback: fmtK }} }}
        }}
    }}
}});

// --- Chart 2: Star Growth (area) ---
new Chart(document.getElementById('starsChart'), {{
    type: 'line',
    data: {{
        labels: starDates.map(shortMonth),
        datasets: [{{
            label: 'Stars',
            data: starCounts,
            borderColor: CYAN,
            backgroundColor: CYAN_DIM,
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointBackgroundColor: CYAN,
            pointHoverRadius: 6,
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ ...tooltipStyle, callbacks: {{ label: ctx => fmtK(ctx.raw) + ' stars' }} }}
        }},
        scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ ...tickStyle, maxTicksLimit: 8 }} }},
            y: {{ grid: gridStyle, ticks: {{ ...tickStyle, callback: fmtK }} }}
        }}
    }}
}});

// --- Chart 3: Cumulative Downloads (area) ---
new Chart(document.getElementById('cumulativeChart'), {{
    type: 'line',
    data: {{
        labels: cumulativeLabels.map(shortMonth),
        datasets: [{{
            label: 'Cumulative PyPI',
            data: cumulativePypi,
            borderColor: PINK,
            backgroundColor: PINK_DIM,
            fill: true,
            tension: 0.35,
            pointRadius: 3,
            pointBackgroundColor: PINK,
            pointHoverRadius: 6,
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ ...tooltipStyle, callbacks: {{ label: ctx => fmtK(ctx.raw) + ' total downloads' }} }}
        }},
        scales: {{
            x: {{ grid: {{ display: false }}, ticks: tickStyle }},
            y: {{ grid: gridStyle, ticks: {{ ...tickStyle, callback: fmtK }} }}
        }}
    }}
}});

// --- Chart 4: Daily Downloads (area) ---
(function() {{
    // Sample daily data to avoid overcrowding (show every 7th day)
    const step = Math.max(1, Math.floor(dailyLabels.length / 60));
    const sampledLabels = dailyLabels.filter((_, i) => i % step === 0);
    const sampledValues = dailyValues.filter((_, i) => i % step === 0);

    new Chart(document.getElementById('dailyChart'), {{
        type: 'line',
        data: {{
            labels: sampledLabels.map(shortDate),
            datasets: [{{
                label: 'Daily Downloads',
                data: sampledValues,
                borderColor: CYAN,
                backgroundColor: CYAN_DIM,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 1.5,
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{ ...tooltipStyle, callbacks: {{ label: ctx => fmtK(ctx.raw) + ' downloads' }} }}
            }},
            scales: {{
                x: {{ grid: {{ display: false }}, ticks: {{ ...tickStyle, maxTicksLimit: 8 }} }},
                y: {{ grid: gridStyle, ticks: {{ ...tickStyle, callback: fmtK }}, beginAtZero: true }}
            }}
        }}
    }});
}})();

// --- Chart 5: GitHub Traffic (dual bar) ---
new Chart(document.getElementById('trafficChart'), {{
    type: 'bar',
    data: {{
        labels: trafficDates.map(shortDate),
        datasets: [
            {{
                label: 'Page Views',
                data: trafficViews,
                backgroundColor: CYAN,
                hoverBackgroundColor: CYAN_HOVER,
                borderRadius: 4,
                borderSkipped: false,
            }},
            {{
                label: 'Unique Visitors',
                data: trafficUniques,
                backgroundColor: PINK,
                hoverBackgroundColor: '#d060d0',
                borderRadius: 4,
                borderSkipped: false,
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{
                labels: {{ color: '#a3abba', boxWidth: 12, padding: 16 }}
            }},
            tooltip: tooltipStyle,
        }},
        scales: {{
            x: {{ grid: {{ display: false }}, ticks: tickStyle }},
            y: {{ grid: gridStyle, ticks: tickStyle }}
        }}
    }}
}});
</script>
"""


def main():
    print("=" * 50)
    print("Crawl4AI Stats Dashboard Generator")
    print("=" * 50)

    github = fetch_github_stats()
    print(f"  Stars: {github['stars']}, Forks: {github['forks']}")

    contributors = fetch_contributors_count()
    print(f"  Contributors: {contributors}")

    traffic = fetch_github_traffic()
    print(f"  Traffic data points: {len(traffic.get('views', []))} days")

    pypi_live = fetch_pypi_live()
    print(f"  PyPI live: {len(pypi_live['monthly'])} months, {len(pypi_live['daily'])} daily points")
    pypi = merge_pypi_data(pypi_live)
    print(f"  PyPI merged: {len(pypi['monthly'])} months, total: {pypi['total']:,}")

    docker_pulls = fetch_docker_pulls()
    print(f"  Docker pulls: {docker_pulls}")

    # Generate the page
    content = generate_stats_md(github, contributors, traffic, pypi, docker_pulls, STAR_MILESTONES)

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content)
    print(f"\nWrote {OUTPUT_PATH} ({len(content):,} bytes)")
    print("Done!")


if __name__ == "__main__":
    main()
