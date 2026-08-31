# Crawl4AI Prospect‑Wizard – step‑by‑step guide

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/10nRCwmfxPjVrRUHyJsYlX7BH5bvPoGpx?usp=sharing)

A three‑stage demo that goes from **LinkedIn scraping** ➜ **LLM reasoning** ➜ **graph visualisation**.

**Try it in Google Colab!** Click the badge above to run this demo in a cloud environment with zero setup required.

```
prospect‑wizard/
├─ c4ai_discover.py         # Stage 1 – scrape companies + people
├─ c4ai_insights.py         # Stage 2 – embeddings, org‑charts, scores
├─ graph_view_template.html # Stage 3 – graph viewer (static HTML)
└─ data/                    # output lands here (*.jsonl / *.json)
```

---

## 1  Install & boot a LinkedIn profile (one‑time)

### 1.1  Install dependencies
```bash
pip install crawl4ai litellm sentence-transformers pandas rich
```

### 1.2  Create / warm a LinkedIn browser profile
```bash
crwl profiles
```
1. The interactive shell shows **New profile** – hit **enter**.
2. Choose a name, e.g. `profile_linkedin_uc`.
3. A Chromium window opens – log in to LinkedIn, solve whatever CAPTCHA, then close.

> Remember the **profile name**. All future runs take `--profile-name <your_name>`.

---

## 2  Discovery – scrape companies & people

```bash
python c4ai_discover.py full \
  --query "health insurance management" \
  --geo 102713980 \               # Malaysia geoUrn
  --title-filters "" \            # or "Product,Engineering"
  --max-companies 10 \            # default set small for workshops
  --max-people 20 \               # \^ same
  --profile-name profile_linkedin_uc \
  --outdir ./data \
  --concurrency 2 \
  --log-level debug
```
**Outputs** in `./data/`:
* `companies.jsonl` – one JSON per company
* `people.jsonl` – one JSON per employee

🛠️  **Dry‑run:** `C4AI_DEMO_DEBUG=1 python c4ai_discover.py full --query coffee` uses bundled HTML snippets, no network.

### Handy geoUrn cheatsheet
| Location | geoUrn |
|----------|--------|
| Singapore | **103644278** |
| Malaysia | **102713980** |
| United States | **103644922** |
| United Kingdom | **102221843** |
| Australia | **101452733** |
_See more: <https://www.linkedin.com/search/results/companies/?geoUrn=XXX> – the number after `geoUrn=` is what you need._

---

## 3  Insights – embeddings, org‑charts, decision makers

```bash
python c4ai_insights.py \
  --in ./data \
  --out ./data \
  --embed-model all-MiniLM-L6-v2 \
  --llm-provider gemini/gemini-2.0-flash \
  --llm-api-key "" \
  --top-k 10 \
  --max-llm-tokens 8024 \
  --llm-temperature 1.0 \
  --workers 4
```
Emits next to the Stage‑1 files:
* `company_graph.json` – inter‑company similarity graph
* `org_chart_<handle>.json` – one per company
* `decision_makers.csv` – hand‑picked ‘who to pitch’ list

Flags reference (straight from `build_arg_parser()`):
| Flag | Default | Purpose |
|------|---------|---------|
| `--in` | `.` | Stage‑1 output dir |
| `--out` | `.` | Destination dir |
| `--embed_model` | `all-MiniLM-L6-v2` | Sentence‑Transformer model |
| `--top_k` | `10` | Neighbours per company in graph |
| `--openai_model` | `gpt-4.1` | LLM for scoring decision makers |
| `--max_llm_tokens` | `8024` | Token budget per LLM call |
| `--llm_temperature` | `1.0` | Creativity knob |
| `--stub` | off | Skip OpenAI and fabricate tiny charts |
| `--workers` | `4` | Parallel LLM workers |

---

## 4  Visualise – interactive graph

After Stage 2 completes, simply open the HTML viewer from the project root:
```bash
open graph_view_template.html   # or Live Server / Python -http
```
The page fetches `data/company_graph.json` and the `org_chart_*.json` files automatically; keep the `data/` folder beside the HTML file.

* Left pane → list of companies (clans).
* Click a node to load its org‑chart on the right.
* Chat drawer lets you ask follow‑up questions; context is pulled from `people.jsonl`.

---

## 5  Common snags

| Symptom | Fix |
|---------|-----|
| Infinite CAPTCHA | Use a residential proxy: `--proxy http://user:pass@ip:port` |
| 429 Too Many Requests | Lower `--concurrency`, rotate profile, add delay |
| Blank graph | Check JSON paths, clear `localStorage` in browser |

---

### TL;DR
`crwl profiles` → `c4ai_discover.py` → `c4ai_insights.py` → open `graph_view_template.html`.  
Live long and `import crawl4ai`.

