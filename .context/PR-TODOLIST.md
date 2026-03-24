# PR Review Todolist

> Last updated: 2026-03-07 | Total open PRs: 6

---

## Remaining Open PRs (6)

### Bug Fixes (2)

| PR | Author | Description | Notes |
|----|--------|-------------|-------|
| #1207 | moncapitaine | Fix streaming error handling | Old PR, likely needs rebase |
| #462 | jtanningbed | Fix: Add newline before pre codeblock start in html2text. 1-line fix | Very old, may still apply |

### Docs/Maintenance (2)

| PR | Author | Description | Notes |
|----|--------|-------------|-------|
| #1756 | VasiliyRad | Added AG2 community integration example and Quickstart pointer | Community example |
| #1533 | unclecode | Add Claude Code GitHub Workflow | Owner's PR, CI |

### Skipped (owner PRs)

| PR | Author | Description |
|----|--------|-------------|
| #1533 | unclecode | Add Claude Code GitHub Workflow |
| #1124 | unclecode | Add VNC streaming support |

---

## Previously Closed PRs (won't merge)

| PR | Author | Description | Reason |
|----|--------|-------------|--------|
| #999 | loliw | Regex-based filters for deep crawling | URLPatternFilter already supports regex |
| #1180 | kunalmanelkar | CallbackURLFilter for deep crawling | Breaks sync apply() interface |
| #1425 | denrusio | OpenRouter API support | litellm handles openrouter/ natively |
| #1702 | YxmMyth | CSS background image extraction | Too invasive for niche feature |
| #1707 | dillonledoux | Crawl-delay from robots.txt | Too complex for non-standard directive |
| #1729 | hoi | External Redis support | Docker infra - maintainer territory |
| #1592 | Ahmed-Tawfik94 | CDP page leaks and race conditions | Superseded by develop page lifecycle system |

## Previously Closed PRs (from old todolist)

| PR | Author | Original Description | What happened |
|----|--------|---------------------|---------------|
| #1572 | Ahmed-Tawfik94 | Fix CDP setting with managed browser | Closed |
| #1234 | AdarsHH30 | Fix TypeError when keep_data_attributes=False | Closed |
| #1211 | Praneeth1-O-1 | Fix: safely create new page if no page exists | Closed |
| #1200 | fischerdr | Bugfix browser manager session handling | Closed |
| #1106 | devxpain | Fix: Adapt to CrawlerMonitor constructor change | Closed |
| #1081 | Joorrit | Fix deep crawl scorer logic was inverted | Closed |
| #1065 | mccullya | Fix: Update deprecated Groq models | Closed |
| #1059 | Aaron2516 | Fix wrong proxy config type in proxy demo example | Closed |
| #1058 | Aaron2516 | Fix dict-type proxy_config not handled properly | Closed |
| #983 | umerkhan95 | Fix memory leak and empty responses in streaming mode | Closed |
| #948 | GeorgeVince | Fix summarize_page.py example | Closed |
| #1689 | mzyfree | Docker: optimize concurrency performance | Closed (contributor acknowledged) |
| #1706 | vikas-gits-good | Fix arun_many not working with DeepCrawlStrategy | Closed |
| #1683 | Vaccarini-Lorenzo | Implement double config for AdaptiveCrawler | Closed |
| #1674 | blentz | Add output pagination/control for MCP endpoints | Closed |
| #1650 | KennyStryker | Add support for Vertex AI in LLM Extraction Strategy | Closed |
| #1580 | arpagon | Add Azure OpenAI configuration support | Closed |
| #1417 | NickMandylas | Add CDP headers support for remote browser auth | Closed |
| #1255 | itsskofficial | Fix JsonCssSelector to handle adjacent sibling CSS selectors | Closed |
| #1245 | mukul-atomicwork | Feature: GitHub releases integration | Closed |
| #1238 | yerik515 | Fix ManagedBrowser constructor and Windows encoding issues | Closed |
| #1220 | dcieslak19973 | Allow OPENAI_BASE_URL for LLM base_url | Closed |
| #901 | gbe3hunna | CrawlResult model: add pydantic fields and descriptions | Closed |
| #800 | atomlong | ensure_ascii=False for json.dumps | Closed |
| #799 | atomlong | Allow setting base_url for LLM extraction strategy in CLI | Closed |
| #741 | atomlong | Add config option to control Content-Security-Policy header | Closed |
| #723 | alexandreolives | Optional close page after screenshot | Closed |
| #681 | ksallee | JS execution should happen after waiting | Closed |
| #416 | dar0xt | Add keep-aria-label-attribute option | Closed |
| #332 | nelzomal | Add remove_invisible_texts method to crawler strategy | Closed |
| #312 | AndreaFrancis | Add save to HuggingFace support | Closed |
| #1488 | AkosLukacs | Fix syntax error in README JSON example | Closed |
| #1483 | NiclasLindqvist | Update README.md with latest docker image | Closed |
| #1416 | adityaagre | Fix missing bracket in README code block | Closed |
| #1272 | zhenjunMa | Fix get title bug in amazon example | Closed |
| #1263 | vvanglro | Fix: consistent with sdk behavior | Closed |
| #1225 | albertkim | Fix docker deployment guide URL | Closed |
| #1223 | dowithless | Docs: add links to other language versions of README | Closed |
| #1159 | lbeziaud | Fix cleanup warning when no process on debug port | Closed |
| #1098 | B-X-Y | Docs: fix outdated links to Docker guide | Closed |
| #1093 | Aaron2516 | Docs: Fixed incorrect elapsed calculation | Closed |
| #967 | prajjwalnag | Update README.md | Closed |
| #671 | SteveAlphaVantage | Update README.md | Closed |
| #605 | mochamadsatria | Fix typo in docker-deployment.md filename | Closed |
| #335 | amanagarwal042 | Add Documentation for Monitoring with OpenTelemetry | Closed |
| #1722 | YuriNachos | Add missing docstring to MCP md endpoint | Merged directly |

---

## Resolved This Session (batch 5)

| PR | Author | Description | Date |
|----|--------|-------------|------|
| #1622 | Ahmed-Tawfik94 | fix: verify redirect targets in URL seeder | 2026-03-07 |
| #1786 | Br1an67 | fix: wire mean_delay/max_range into dispatcher | 2026-03-07 |
| #1796 | Br1an67 | fix: DOMParser in process_iframes | 2026-03-07 |
| #1795 | Br1an67 | fix: require api_token for /token endpoint | 2026-03-07 |
| #1798 | SohamKukreti | fix: deep-crawl streaming mirrors Python library | 2026-03-07 |
| #1734 | pgoslatara | chore: update GitHub Actions versions | 2026-03-07 |
| #1290 | 130347665 | feat: type-list pipeline in JSON extraction | 2026-03-07 |
| #1668 | microHoffman | feat: --json-ensure-ascii CLI flag | 2026-03-07 |

## Resolved (batch 4)

| PR | Author | Description | Date |
|----|--------|-------------|------|
| #1494 | AkosLukacs | docs: fix docstring param name crawler_config -> config | 2026-03-07 |
| #1715 | YuriNachos | docs: add missing CacheMode import in quickstart | 2026-03-07 |
| #1716 | YuriNachos | docs: fix return types to RunManyReturn | 2026-03-07 |
| #1308 | dominicx | docs: fix css_selector type from list to string | 2026-03-07 |
| #1789 | Br1an67 | fix: UTF-8 encoding for CLI file output | 2026-03-07 |
| #1793 | Br1an67 | fix: configurable link_preview_timeout in AdaptiveConfig | 2026-03-07 |
| #1792 | Br1an67 | fix: wait_for_images on screenshot endpoint | 2026-03-07 |
| #1794 | Br1an67 | fix: cross-platform terminal input in CrawlerMonitor | 2026-03-07 |
| #1784 | Br1an67 | fix: UnicodeEncodeError in URL seeder + zero-width chars | 2026-03-07 |
| #1730 | hoi | fix: add TTL expiry for Redis task data | 2026-03-07 |

## Previously Resolved (batches 1-3)

| PR | Author | Description | Date |
|----|--------|-------------|------|
| #1805 | nightcityblade | fix: prevent AdaptiveCrawler from crawling external domains | 2026-03-07 |
| #1763 | Otman404 | fix: return in finally block silently suppressing exceptions | 2026-03-07 |
| #1803 | SohamKukreti | fix: from_serializable_dict ignoring plain data dicts | 2026-03-07 |
| #1804 | nightcityblade | feat: add score_threshold to BestFirstCrawlingStrategy | 2026-03-07 |
| #1790 | Br1an67 | fix: handle nested brackets in LINK_PATTERN regex | 2026-03-07 |
| #1787 | Br1an67 | fix: strip markdown fences in LLM JSON responses | 2026-03-07 |
| #1782 | Br1an67 | fix: preserve class/id in cleaned_html | 2026-03-07 |
| #1788 | Br1an67 | fix: guard against None LLM content | 2026-03-07 |
| #1783 | Br1an67 | fix: strip port from domain in is_external_url | 2026-03-07 |
| #1179 | phamngocquy | fix: raw HTML URL token leak | 2026-03-07 |
| #1694 | theredrad | feat: add force viewport screenshot | 2026-02-01 |
| #1746 | ChiragBellara | fix: avoid Common Crawl calls for sitemap-only seeding | 2026-02-01 |
| #1714 | YuriNachos | fix: replace tf-playwright-stealth with playwright-stealth | 2026-02-01 |
| #1721 | YuriNachos | fix: respect base tag for relative link resolution | 2026-02-01 |
| #1719 | YuriNachos | fix: include GoogleSearchCrawler script.js in package | 2026-02-01 |
| #1717 | YuriNachos | fix: allow local embeddings by removing OpenAI fallback | 2026-02-01 |
| #1667 | christian-oudard | fix: deep-crawl CLI outputting only first page | 2026-02-01 |
| #1296 | vladmandic | fix: VersionManager ignoring CRAWL4_AI_BASE_DIRECTORY | 2026-02-01 |
| #1364 | nnxiong | fix: script tag removal losing adjacent text | 2026-02-01 |
| #1077 | RoyLeviLangware | fix: bs4 deprecation warning (text -> string) | 2026-02-01 |
| #1281 | garyluky | fix: proxy auth ERR_INVALID_AUTH_CREDENTIALS | 2026-02-01 |
| #1463 | TristanDonze | feat: device_scale_factor for screenshot quality | 2026-02-06 |
| #1435 | charlaie | feat: redirected_status_code in CrawlResult | 2026-02-06 |
