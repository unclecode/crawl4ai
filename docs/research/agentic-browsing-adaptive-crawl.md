# A Research-Grounded Adaptive Focused Crawling Loop for Agentic Browsing

**Authors:** Doffy (GrandFleet Logistics) / Hermes Agent Phase 2
**Date:** 2026-07-10
**Repository:** `https://github.com/unclecode/crawl4ai` (local fork at `/Users/impeldown/crawl4ai`)

---

## Abstract

We present an improvement to Crawl4AI's adaptive crawling system that makes the crawl decision process transparent, auditable, and theoretically grounded. The adaptive focused crawling loop uses a query-conditioned utility function combining coverage, consistency, and saturation metrics to determine when sufficient information has been gathered. We identify four defects in the existing implementation that made crawl decisions invisible: hardcoded confidence weights, missing stop reasons, frontier-destroying link filtering, and embedding metric inconsistency. After fixing these, we argue analytically that under explicit assumptions about relevance estimates and diminishing marginal utility, greedy best-first link selection is a bounded rational approximation for budgeted information gathering. We verify the fixes with deterministic unit tests on a synthetic site graph designed to test frontier recall and tunneling behavior. The bounded proposition — that transparent decisions lead to reproducible outcomes — is supported by test evidence, and its limitations are explicitly named.

---

## 1. Introduction

Web crawling for information gathering faces a fundamental tension: crawl too few pages and miss relevant content; crawl too many and waste resources on irrelevant pages. **Focused crawling** (Chakrabarti et al., 1999) addresses this by prioritizing links likely to lead to topic-relevant pages. **Adaptive crawling** extends this by introducing stopping criteria that determine when sufficient information has been gathered.

Crawl4AI is an open-source LLM-friendly web crawler with an `AdaptiveCrawler` module that implements query-guided adaptive crawling. However, the existing implementation has several issues that make its decisions opaque: confidence weights are hardcoded rather than configurable, stopping decisions do not record their reasons, links without metadata are silently dropped, and the embedding-based strategy stores inconsistent metrics.

This paper makes the following contributions:
1. We identify and fix four defects in Crawl4AI's adaptive crawler that made decisions invisible.
2. We formalize the adaptive crawling loop as a query-conditioned utility maximization under budget constraints.
3. We provide an analytic argument that greedy best-first selection is bounded-rational under stated assumptions.
4. We design a deterministic evaluation protocol using a synthetic site graph and verify all fixes with unit tests.

---

## 2. Related Work

### 2.1 Focused Crawling

Chakrabarti et al. (1999) introduced focused crawling as a topic-specific web resource discovery approach that prioritizes links likely to lead to relevant pages. Bergmark et al. (2002) extended this work by studying "tunneling" — the observation that focused crawlers must sometimes traverse low-relevance pages to reach highly relevant regions, warning against over-aggressive frontier pruning. Johnson et al. (2003) studied evolving strategies for focused web crawling, establishing that crawl-frontier ordering is the core policy decision. Lu et al. (2016) combined page classification and link priority evaluation for improved focused crawling. Dahiwale et al. (2014) proposed the PDD Crawler using link and content analysis for relevance prediction.

### 2.2 Adaptive Retrieval Agents

Menczer and Belew (2000) developed adaptive retrieval agents that internalize local context and scale to the web. Menczer and Monge (1999) demonstrated scalable web search via adaptive online agents (InfoSpiders), showing that iterative policy updates based on local feedback can guide web retrieval effectively.

### 2.3 Information Foraging

Card et al. (1996) introduced the WebBook and Web Forager, framing web browsing as an information-foraging problem where users follow information scent. Fu and Pirolli (2007) developed SNIF-ACT, a cognitive model of user navigation on the web, showing that users follow information scent — mapping directly to link text and head-data relevance in crawling.

### 2.4 Retrieval Methods

Robertson and Zaragoza's probabilistic relevance framework, best known through the BM25 scoring function, provides a probabilistic lexical ranking baseline. Crawl4AI uses the `rank-bm25` package for contextual link scoring. Karpukhin et al. (2020) showed that Dense Passage Retrieval (DPR) can outperform sparse BM25 retrieval by 9-19% in top-20 passage retrieval accuracy for open-domain question answering. Khattab and Zaharia (2020) introduced ColBERT, a late-interaction model that balances efficiency and effectiveness in semantic retrieval. Fu et al. (2013) evaluated focused crawler features on topical harvest accuracy.

### 2.5 Web Agent Evaluation

Zhou et al. (2023) built WebArena, a realistic web environment for building autonomous agents. Deng et al. (2023) introduced Mind2Web, a dataset for developing generalist web agents across diverse domains. Liu et al. (2023) created AgentBench, a multi-dimensional benchmark for evaluating LLMs as agents. Shi et al. (2017) developed World of Bits, an open-domain platform for web-based agents. Yao et al. (2022) built WebShop for scalable real-world web interaction. These benchmarks establish that web agent evaluation requires reproducible environments and multi-dimensional metrics, not just anecdotal success.

---

## 3. System Model

### 3.1 Web as a Directed Graph

We model the web as a directed graph $G = (V, E)$ where $V$ is the set of web pages (vertices) and $E$ is the set of hyperlinks (directed edges). Each page $v \in V$ has content $c(v)$ and a set of outgoing links $L(v) \subseteq V$.

### 3.2 Crawl Frontier

Given a start URL $v_0$ and a query $q$, the adaptive crawler maintains:
- **Crawled set** $S \subseteq V$: pages already fetched and processed.
- **Pending frontier** $F \subseteq V$: discovered but not-yet-crawled pages.
- **Knowledge base** $KB$: content of pages in $S$, indexed for retrieval.

### 3.3 Utility Function

The crawler's confidence that it has gathered sufficient information is measured by a utility function:

$$U(S, q) = w_c \cdot \text{Coverage}(S, q) + w_k \cdot \text{Consistency}(S) + w_s \cdot \text{Saturation}(S)$$

where:
- **Coverage**$(S, q)$ measures the fraction of query terms present across the knowledge base, weighted by document frequency.
- **Consistency**$(S)$ measures inter-page term overlap (Jaccard similarity), indicating coherent topic coverage.
- **Saturation**$(S)$ measures diminishing returns — the rate at which new pages add new terms.
- $w_c + w_k + w_s = 1$ are configurable weights.

### 3.4 Budget Constraint

The crawler operates under a budget $B$ (maximum pages to crawl, `max_pages`) and a depth limit $D$ (`max_depth`). The goal is to maximize $U(S, q)$ within these constraints.

---

## 4. Method

We identify and fix four defects in Crawl4AI's adaptive crawler (`crawl4ai/adaptive_crawler.py`):

### 4.1 Configurable Confidence Weights

**Defect:** `StatisticalStrategy.calculate_confidence()` (line 324) hardcoded the weights as `0.4 * coverage + 0.3 * consistency + 0.3 * saturation`, ignoring `AdaptiveConfig.coverage_weight`, `consistency_weight`, and `saturation_weight`.

**Fix:** Read weights from the config object, falling back to defaults:

```python
config = getattr(self, "config", None)
coverage_weight = getattr(config, "coverage_weight", 0.4)
consistency_weight = getattr(config, "consistency_weight", 0.3)
saturation_weight = getattr(config, "saturation_weight", 0.3)
confidence = (
    coverage_weight * coverage
    + consistency_weight * consistency
    + saturation_weight * saturation
)
```

**Rationale:** Making the utility function explicit and configurable is a prerequisite for reproducible evaluation. Users can tune the tradeoff between precision (coverage), coherence (consistency), and early stopping (saturation).

### 4.2 Structured Stop Reasons

**Defect:** `StatisticalStrategy.should_stop()` (lines 527-546) returned booleans without recording why the crawler stopped. The `digest()` method's low-gain break (line 1404) similarly lacked a reason.

**Fix:** Set `state.metrics['stopped_reason']` before each `return True`:

| Condition | Stop reason |
|-----------|-------------|
| `confidence >= threshold` | `confidence_threshold_reached` |
| `len(crawled_urls) >= max_pages` | `max_pages_reached` |
| `not pending_links` | `no_pending_links` |
| `saturation >= threshold` | `saturation_threshold_reached` |
| `ranked_links[0][1] < min_gain_threshold` | `low_expected_gain` |
| while loop exits by depth limit | `max_depth_reached` |

**Rationale:** Auditable stop reasons are necessary for reproducible stopping criteria. Without them, a researcher cannot distinguish "stopped because sufficient" from "stopped because budget exhausted."

### 4.3 Preserve No-Head Links for Recall

**Defect:** `_crawl_with_preview()` (lines 1495-1497) filtered out all internal links lacking `head_data` (metadata from a HEAD request preview):

```python
result.links['internal'] = [link for link in result.links['internal'] if link.get('head_data')]
```

This conflicts with `test_merge_head_data_scoring.py`, which verifies that no-head links still receive useful `total_score` from intrinsic scoring. More critically, Bergmark et al. (2002) warn that over-aggressive frontier pruning based on missing metadata is exactly how a crawler silently misses the only valuable path — a phenomenon known as the **tunneling problem**.

**Fix:** Remove the filtering. Retain all internal links and rank them using available evidence: `intrinsic_score`, `contextual_score` (BM25), link text, and title.

### 4.4 Embedding Metric Consistency

**Defect:** `EmbeddingStrategy.calculate_confidence()` (lines 988-1014) stored `coverage_score`, `avg_best_similarity`, and `median_best_similarity`, but `get_quality_confidence()` (lines 1206-1231) read `state.metrics.get('learning_score', 0.0)` — a metric that was never set.

**Fix:** Add `state.metrics['learning_score'] = score` in `calculate_confidence()`.

---

## 5. Theoretical and Analytical Argument

### 5.1 Bounded Rationality of Greedy Best-First Selection

**Claim:** Under the assumptions below, greedy best-first link selection (choosing the highest-scoring link at each step) is a bounded rational approximation to maximizing utility $U(S, q)$ under budget $B$.

**Assumptions:**
- **A1 (Calibrated relevance):** Link scores are positively correlated with the expected information gain of crawling that link.
- **A2 (Diminishing marginal utility):** Each additional page adds less to $U(S, q)$ than the previous one, after an initial exploration phase.
- **A3 (Budget constraint):** The number of pages crawlable is bounded by $B$.
- **A4 (Non-adversarial web):** The web graph does not actively deceive the crawler (no adversarial link injection).

**Argument:**

Under A1, selecting the highest-scoring link maximizes expected immediate information gain. Under A2, the marginal utility of additional pages decreases, so the order of selection matters most for the first few pages. Under A3, we must select at most $B$ pages. Under A4, we assume link scores are not systematically misleading.

Greedy selection picks the link with highest expected gain at each step. Under A1, this is locally optimal. Under A2, the total utility is dominated by the first few selections (which have the highest marginal gain), so local optimality in the first few steps is a good approximation to global optimality. The greedy approach does not guarantee global optimality (that would require solving a combinatorial optimization over the frontier), but under A2, the gap between greedy and optimal is bounded by the tail of the marginal utility curve, which is small when A2 holds.

### 5.2 Transparency Implies Reproducibility

**Claim:** If crawl decisions (what to crawl next, when to stop) are recorded as observable metrics, then the crawl is reproducible: a fresh agent reading the same metrics would make the same decisions.

**Argument:** Configurable weights make the utility function explicit. Stop reasons make termination criteria inspectable. Preserved frontier links make the set of candidate decisions complete. Together, these three transparency properties mean that given the same starting URL, query, and config, a fresh agent can reproduce the same crawl trajectory by reading the same metrics and applying the same decision rules.

### 5.3 Frontier Preservation and Tunneling

**Claim:** Removing links from the frontier based on missing metadata reduces recall.

**Argument:** Bergmark et al. (2002) showed that focused crawlers must sometimes traverse low-relevance or sparse-metadata pages to reach highly relevant regions. If links without `head_data` are removed, pages that serve as "tunnels" to relevant content are lost. By retaining all links and ranking them using available evidence (intrinsic scores, link text, BM25 contextual scores), the frontier remains complete and the ranking function determines which links are prioritized, not which links are visible.

### 5.4 Lexical vs. Semantic Scoring

The statistical strategy uses lexical scoring (BM25, term overlap) which is fast, free, and effective for queries with specific terminology. The embedding strategy uses dense semantic similarity (cosine distance in embedding space) which captures meaning beyond exact term matches. DPR (Karpukhin et al., 2020) showed that dense retrieval can outperform sparse retrieval by 9-19% in semantic matching tasks. However, lexical methods remain valuable for their speed, zero-cost, and precision on well-defined queries. The configurable weights allow users to balance these tradeoffs.

---

## 6. Evaluation Protocol

### 6.1 Synthetic Site Graph

We construct a deterministic synthetic site graph with known page labels:

| Page | URL | Content | Links to |
|------|-----|---------|----------|
| Root | `http://example.com/root` | Contains query terms | relevant, irrelevant, tunnel |
| Relevant | `http://example.com/relevant` | Detailed query terms | (none) |
| Irrelevant | `http://example.com/irrelevant` | No query terms | (none) |
| Tunnel | `http://example.com/tunnel` | Sparse, no `head_data` | highly-relevant |
| Highly Relevant | `http://example.com/highly-relevant` | Many query terms | (none) |

The tunnel page tests frontier recall: it has no `head_data` and sparse content, but links to the most relevant page. If the crawler filters no-head links, the tunnel is lost and highly-relevant is never discovered.

### 6.2 Test Cases

Six deterministic unit tests verify the four fixes plus the evaluation harness:

| Test | Behavior verified | Source |
|------|-------------------|--------|
| `test_statistical_confidence_uses_configurable_weights` | Confidence uses config weights, not hardcoded | `StatisticalStrategy.calculate_confidence` |
| `test_statistical_should_stop_records_confidence_reason` | Stop reason set for confidence threshold | `StatisticalStrategy.should_stop` |
| `test_statistical_should_stop_records_saturation_reason` | Stop reason set for saturation threshold | `StatisticalStrategy.should_stop` |
| `test_embedding_confidence_sets_learning_score` | `learning_score` metric is set | `EmbeddingStrategy.calculate_confidence` |
| `test_crawl_with_preview_preserves_links_without_head_data` | No-head links survive `_crawl_with_preview` | `AdaptiveCrawler._crawl_with_preview` |
| `test_adaptive_policy_retains_tunnel_link_and_stop_reason_present` | Tunnel link retained + stop reason present after `digest()` | `AdaptiveCrawler.digest` |

### 6.3 Metrics

- **Frontier recall:** fraction of relevant candidate links retained in `pending_links`. Target: 1.0 (all relevant links retained).
- **Stop reason presence:** `state.metrics['stopped_reason']` is non-empty after `digest()`. Target: always present.
- **Config weight correctness:** confidence with `coverage_weight=1.0` equals coverage value. Target: exact match.
- **Metric consistency:** `learning_score` equals returned confidence score for embedding strategy. Target: exact match.

---

## 7. Results

All tests were run with:
```bash
source .venv/bin/activate
python -m pytest tests/adaptive/test_adaptive_crawler_unit.py -v
python -m pytest tests/test_merge_head_data_scoring.py -v
python -m pytest tests/regression/test_reg_deep_crawl.py::test_keyword_scorer -v
python -m pytest tests/regression/test_reg_deep_crawl.py::test_composite_scorer -v
python -m pytest tests/regression/test_reg_deep_crawl.py::test_keyword_scorer_case_insensitive -v
python -m pytest tests/regression/test_reg_deep_crawl.py::test_keyword_scorer_no_match -v
```

**Result: 6 new tests passed, 10 regression tests passed, 4 deep-crawl scorer tests passed — 20/20 total.**

### Live Integration Crawl

After unit tests passed, a live integration crawl was run against `https://docs.python.org/3/library/asyncio.html` with query `"async await coroutine task event loop"`.

**Command:**
```bash
source .venv/bin/activate
python -c "
import asyncio
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig
async def main():
    config = AdaptiveConfig(confidence_threshold=0.75, max_pages=8, max_depth=3, top_k_links=2, min_gain_threshold=0.01)
    async with AsyncWebCrawler() as crawler:
        adaptive = AdaptiveCrawler(crawler=crawler, config=config)
        state = await adaptive.digest(start_url='https://docs.python.org/3/library/asyncio.html', query='async await coroutine task event loop')
    print(f'Stop reason: {state.metrics[\"stopped_reason\"]}')
    print(f'Confidence: {state.metrics[\"confidence\"]:.4f}')
    print(f'Pages crawled: {len(state.crawled_urls)}')
asyncio.run(main())
"
```

**Live results:**

| Metric | Value |
|--------|-------|
| Pages crawled | 5 |
| Depth reached | 2 |
| Confidence | 0.7338 |
| Coverage | 1.0000 |
| Consistency | 0.2997 |
| Saturation | 0.8131 |
| **Stop reason** | **`saturation_threshold_reached`** |
| Pending links | 142 |
| Unique terms | 1,587 |
| Total terms | 20,300 |

**Crawl order and new-term discovery:**

| # | URL | New terms |
|---|-----|-----------|
| 1 | `docs.python.org/3/library/asyncio.html` | +305 |
| 2 | `docs.python.org/3/library/asyncio-runner.html` | +189 |
| 3 | `docs.python.org/3/library/asyncio-api-index.html` | +86 |
| 4 | `docs.python.org/3/library/asyncio-eventloop.html` | +950 |
| 5 | `docs.python.org/3/library/asyncio-extending.html` | +57 |

**Key observations from the live crawl:**

1. **Stop reason worked in production:** The crawler stopped with `saturation_threshold_reached` — saturation hit 0.8131 (above the 0.8 threshold) after page 5. Before the fix, this stop would have been silent.

2. **Coverage reached 1.0 after the first page:** The root asyncio page contains all five query terms. Coverage stayed at 1.0 throughout.

3. **Diminishing returns visible:** New-term history shows `[305, 189, 86, 950, 57]`. Page 4 (eventloop) was a large content page adding 950 terms, but page 5 added only 57 — the saturation signal correctly detected this drop.

4. **Frontier preserved:** 142 pending links remained after the crawl. This live site's `LinkPreview` system fetched `head_data` for all links successfully, so no no-head links were present in this particular crawl. The fix's value is most visible on sites where `head_data` extraction fails or times out, which the synthetic graph test covers.

| Test | Result |
|------|--------|
| `test_statistical_confidence_uses_configurable_weights` | PASS |
| `test_statistical_should_stop_records_confidence_reason` | PASS |
| `test_statistical_should_stop_records_saturation_reason` | PASS |
| `test_embedding_confidence_sets_learning_score` | PASS |
| `test_crawl_with_preview_preserves_links_without_head_data` | PASS |
| `test_adaptive_policy_retains_tunnel_link_and_stop_reason_present` | PASS |
| 10x `test_merge_head_data_scoring.py` (regression) | PASS |
| 4x deep-crawl scorer tests | PASS |

**Tunnel link retention:** The tunnel page link (`http://example.com/tunnel`) was confirmed present in `pending_links` after `digest()`, verifying that the frontier-preserving fix works.

**Stop reason:** `state.metrics['stopped_reason']` was `max_depth_reached` after `digest()` with high confidence threshold, confirming that the fallback stop reason is set when the while loop exits by depth limit.

**Config weight correctness:** Confidence with `coverage_weight=1.0, consistency_weight=0.0, saturation_weight=0.0` returned `0.2` (matching coverage), not `0.44` (the old hardcoded value).

**Metric consistency:** `state.metrics['learning_score']` was set and equal to the returned confidence score for the embedding strategy.

---

## 8. Threats to Validity and Limitations

### 8.1 Synthetic Graph vs. Real Web

The evaluation uses a synthetic site graph with 5 pages and known content. Real web structure is significantly more complex: pages have JavaScript-rendered content, dynamic links, authentication walls, and adversarial structures. The synthetic graph tests the *mechanics* of the adaptive loop (frontier retention, stop reasons, weight configurability) but does not test *performance* on real web crawling. A live integration crawl on `https://docs.python.org/3/library/asyncio.html` (Section 7, Live Integration Crawl) confirmed that the stop reason, confidence, and saturation metrics work correctly on a real site, but a single live crawl does not constitute comprehensive real-world validation. Broader generalization to diverse web structures is a future-work item.

### 8.2 BM25 Assumptions

The lexical scoring (BM25) assumes that query terms are independent and that term frequency follows a specific distribution. For polysemous terms or cross-lingual queries, these assumptions may not hold.

### 8.3 Embedding Quality

The embedding strategy's quality depends on the embedding model (`sentence-transformers/all-MiniLM-L6-v2` by default). Different models may produce different coverage scores. The fix ensures metric consistency but does not guarantee that the embedding strategy is *correct* — only that it is *auditable*.

### 8.4 Bounded Proposition

We do not claim that "agentic browsing works" in the broad sense. We claim the narrower result: under explicit assumptions about relevance estimates and diminishing marginal utility, a query-conditioned adaptive focused-crawling loop with transparent utility weights, auditable stop reasons, and frontier-preserving link selection is a rational approximation for budgeted information gathering, and the implementation exposes enough metrics to make that loop reproducible and falsifiable.

### 8.5 No External API Calls

Tests use mock objects, not real browser crawls. This means we test the decision logic, not the browser interaction layer. Integration with Playwright/Patchright is tested separately in the regression test suite.

---

## 9. Reproducibility

### Setup

```bash
cd /Users/impeldown/crawl4ai
source .venv/bin/activate
python -m pip install pytest pytest-asyncio
```

### Run Tests

```bash
# New unit tests (6 tests)
python -m pytest tests/adaptive/test_adaptive_crawler_unit.py -v

# Regression tests for no-head-link scoring (10 tests)
python -m pytest tests/test_merge_head_data_scoring.py -v

# Deep-crawl scorer tests (4 tests)
python -m pytest tests/regression/test_reg_deep_crawl.py::test_keyword_scorer tests/regression/test_reg_deep_crawl.py::test_composite_scorer tests/regression/test_reg_deep_crawl.py::test_keyword_scorer_case_insensitive tests/regression/test_reg_deep_crawl.py::test_keyword_scorer_no_match -v
```

### Files Modified

| File | Change |
|------|--------|
| `crawl4ai/adaptive_crawler.py` lines 323-332 | Configurable confidence weights |
| `crawl4ai/adaptive_crawler.py` lines 537-555 | Stop reasons in `should_stop()` |
| `crawl4ai/adaptive_crawler.py` lines 1416-1418 | Low-gain stop reason in `digest()` |
| `crawl4ai/adaptive_crawler.py` line 1477-1481 | `max_depth_reached` fallback in `digest()` |
| `crawl4ai/adaptive_crawler.py` lines 1506-1510 | Removed no-head-link filter in `_crawl_with_preview()` |
| `crawl4ai/adaptive_crawler.py` line 1021 | Added `learning_score` metric in `EmbeddingStrategy.calculate_confidence()` |
| `tests/adaptive/test_adaptive_crawler_unit.py` | New: 6 deterministic unit tests |
| `docs/md_v2/core/adaptive-crawling.md` | Added stop reasons, weights, and link preservation docs |
| `docs/research/agentic-browsing-adaptive-crawl.md` | This paper |

---

## 10. Conclusion

We improved Crawl4AI's adaptive crawling system by making four previously invisible decisions visible: utility weights are now configurable, stop reasons are now auditable, frontier links are now preserved for recall, and embedding metrics are now consistent. The theoretical argument shows that under stated assumptions, greedy best-first selection is a bounded rational approximation for budgeted information gathering. The evaluation confirms that all fixes work as designed on a synthetic site graph. The bounded proposition — that transparent decisions lead to reproducible outcomes — is supported by test evidence.

The key insight, surfaced by the hostile council seat (Crocodile), is that "prove the project works" is an overclaim unless the proof is scoped to a formal model and backed by repeatable tests. This paper proves the narrower, defensible claim: under explicit assumptions about relevance estimates and diminishing marginal utility, the adaptive focused crawling loop is theoretically justified and empirically testable, and the implementation exposes enough metrics to make it reproducible and falsifiable.

---

## 11. References

1. Chakrabarti, S., van den Berg, M., & Dom, B. (1999). Focused crawling: a new approach to topic-specific Web resource discovery. *Computer Networks*, 31(11-16), 1623-1640. DOI: `10.1016/S1389-1286(99)00052-3`

2. Bergmark, D., Lagoze, C., & Sbityakov, A. (2002). Focused Crawls, Tunneling, and Digital Libraries. *Proceedings of ECDL 2002*. DOI: `10.1007/3-540-45747-X_7`

3. Johnson, J.M., Tsioutsiouliklis, K., & Giles, C.L. (2003). Evolving strategies for focused web crawling. *Proceedings of ICML 2003*.

4. Lu, H., Donghui, Z., Zhou, L., & He, D. (2016). An Improved Focused Crawler: Using Web Page Classification and Link Priority Evaluation. *Journal of Applied Mathematics*, 2016. DOI: `10.1155/2016/6406901`

5. Menczer, F. & Belew, R.K. (2000). Adaptive Retrieval Agents: Internalizing Local Context and Scaling up to the Web. *Machine Learning*, 41(1-3). DOI: `10.1023/A:1007653114902`

6. Menczer, F. & Monge, A. (1999). Scalable Web Search by Adaptive Online Agents: An InfoSpiders Case Study. *Proceedings of SPIRE 1999*. DOI: `10.1007/978-3-642-60018-0_17`

7. Card, S.K., Robertson, G.G., & York, W. (1996). The WebBook and the Web Forager. *CHI '96*. DOI: `10.1145/238386.238446`

8. Fu, W.-T. & Pirolli, P. (2007). SNIF-ACT: A Cognitive Model of User Navigation on the World Wide Web. *Human-Computer Interaction*, 22(4). DOI: `10.21236/ADA462156`

9. Robertson, S. & Zaragoza, H. The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4).

10. Karpukhin, V., Oguz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W. (2020). Dense Passage Retrieval for Open-Domain Question Answering. *EMNLP 2020*. arXiv: `2004.04906v3`

11. Khattab, O. & Zaharia, M. (2020). ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT. *SIGIR 2020*. arXiv: `2004.12832v2`

12. Yao, S., Chen, H., Yang, J., & Narasimhan, K. (2022). WebShop: Towards Scalable Real-World Web Interaction with Grounded Language Agents. arXiv: `2207.01206v4`

13. Deng, X., Gu, Y., Zheng, B., et al. (2023). Mind2Web: Towards a Generalist Agent for the Web. *NeurIPS 2023*. arXiv: `2306.06070v3`

14. Zhou, S., Xu, F.F., Zhu, H., et al. (2023). WebArena: A Realistic Web Environment for Building Autonomous Agents. arXiv: `2307.13854v4`

15. Liu, X., Yu, H., Zhang, H., et al. (2023). AgentBench: Evaluating LLMs as Agents. arXiv: `2308.03688v3`

16. Shi, T., Karpathy, A., Fan, L., et al. (2017). World of Bits: An Open-Domain Platform for Web-Based Agents. *ICML 2017*.

17. Fu, T., Abbasi, A., Zeng, D., & Chen, H. (2013). Evaluating the Usefulness of Sentiment Information for Focused Crawlers. arXiv: `1309.7270v1`

18. Dahiwale, P., Raghuwanshi, M.M., & Malik, L. (2014). PDD Crawler: A focused web crawler using link and content analysis for relevance prediction. arXiv: `1411.4366v1`
