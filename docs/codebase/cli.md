### `cli.py` command surface

| Command | Inputs / flags | What it does |
|---|---|---|
| **profiles** | *(none)* | Opens the interactive profile manager, lets you list, create, delete saved browser profiles that live in `~/.crawl4ai/profiles`. |
| **browser status** | – | Prints whether the always-on *builtin* browser is running, shows its CDP URL, PID, start time. |
| **browser stop** | – | Kills the builtin browser and deletes its status file. |
| **browser view** | `--url, -u` URL *(optional)* | Pops a visible window of the builtin browser, navigates to `URL` or `about:blank`. |
| **config list** | – | Dumps every global setting, showing current value, default, and description. |
| **config get** | `key` | Prints the value of a single setting, falls back to default if unset. |
| **config set** | `key value` | Persists a new value in the global config (stored under `~/.crawl4ai/config.yml`). |
| **examples** | – | Just spits out real-world CLI usage samples. |
| **crawl** | `url` *(positional)*<br>`--browser-config,-B` path<br>`--crawler-config,-C` path<br>`--filter-config,-f` path<br>`--extraction-config,-e` path<br>`--json-extract,-j` [desc]\*<br>`--schema,-s` path<br>`--browser,-b` k=v list<br>`--crawler,-c` k=v list<br>`--output,-o` all,json,markdown,md,markdown-fit,md-fit *(default all)*<br>`--output-file,-O` path<br>`--bypass-cache,-b` *(flag, default true — note flag reuse)*<br>`--question,-q` str<br>`--verbose,-v` *(flag)*<br>`--profile,-p` profile-name | One-shot crawl + extraction. Builds `BrowserConfig` and `CrawlerRunConfig` from inline flags or separate YAML/JSON files, runs `AsyncWebCrawler.run()`, can route through a named saved profile and pipe the result to stdout or a file. |
| **(default)** | Same flags as **crawl**, plus `--example` | Shortcut so you can type just `crwl https://site.com`. When first arg is not a known sub-command, it falls through to *crawl*. |

\* `--json-extract/-j` with no value turns on LLM-based JSON extraction using an auto schema, supplying a string lets you prompt-engineer the field descriptions.

> Quick mental model  
> `profiles` = manage identities,  
> `browser ...` = control long-running headless Chrome that all crawls can piggy-back on,  
> `crawl` = do the actual work,  
> `config` = tweak global defaults,  
> everything else is sugar.

### Quick-fire “profile” usage cheatsheet

| Scenario | Command (copy-paste ready) | Notes |
|---|---|---|
| **Launch interactive Profile Manager UI** | `crwl profiles` | Opens TUI with options: 1 List, 2 Create, 3 Delete, 4 Use-to-crawl, 5 Exit. |
| **Create a fresh profile** | `crwl profiles` → choose **2** → name it → browser opens → log in → press **q** in terminal | Saves to `~/.crawl4ai/profiles/<name>`. |
| **List saved profiles** | `crwl profiles` → choose **1** | Shows name, browser type, size, last-modified. |
| **Delete a profile** | `crwl profiles` → choose **3** → pick the profile index → confirm | Removes the folder. |
| **Crawl with a profile (default alias)** | `crwl https://site.com/dashboard -p my-profile` | Keeps login cookies, sets `use_managed_browser=true` under the hood. |
| **Crawl + verbose JSON output** | `crwl https://site.com -p my-profile -o json -v` | Any other `crawl` flags work the same. |
| **Crawl with extra browser tweaks** | `crwl https://site.com -p my-profile -b "headless=true,viewport_width=1680"` | CLI overrides go on top of the profile. |
| **Same but via explicit sub-command** | `crwl crawl https://site.com -p my-profile` | Identical to default alias. |
| **Use profile from inside Profile Manager** | `crwl profiles` → choose **4** → pick profile → enter URL → follow prompts | Handy when demo-ing to non-CLI folks. |
| **One-off crawl with a profile folder path (no name lookup)** | `crwl https://site.com -b "user_data_dir=$HOME/.crawl4ai/profiles/my-profile,use_managed_browser=true"` | Bypasses registry, useful for CI scripts. |
| **Launch a dev browser on CDP port with the same identity** | `crwl cdp -d $HOME/.crawl4ai/profiles/my-profile -P 9223` | Lets Puppeteer/Playwright attach for debugging. |

