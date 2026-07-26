---
name: crawl-with-crwl
description: Crawl public web pages and extract Markdown or structured content with the crwl CLI. Use when an agent needs current page content, focused extraction, a deep crawl, or machine-readable crawl results and the crwl command is available.
---

# Crawl with crwl

Use only the `crwl` executable. Do not call `crwl-remote` directly. A user may
alias `crwl` to a remote backend, so keep commands backend-agnostic.

## Workflow

1. Confirm the target URL and requested output.
2. Run the smallest suitable crawl:

```bash
crwl 'https://example.com' -o markdown
```

3. Use JSON only when structured output is needed:

```bash
crwl 'https://example.com/products' -o json
```

4. Use deep crawling only when the task requires linked pages:

```bash
crwl 'https://example.com/docs' --deep-crawl bfs --max-pages 10 -o markdown
```

5. Inspect the exit status and stderr. Report authentication, connectivity,
robots, or extraction failures rather than silently substituting content.

Quote URLs in shell commands. Never place API tokens or other credentials in
command output, prompts, logs, or committed files.
