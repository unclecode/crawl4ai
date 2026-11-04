# Crawl4AI

**The open-source web crawler for LLMs and AI agents, as a server you run yourself.** This image is the Crawl4AI Docker server: send it a URL, get clean Markdown, structured JSON or a screenshot back. Apache-2.0.

Don't want to run browsers and proxies yourself? **[Crawl4AI Cloud](https://crawl4ai.com/?ref=dockerhub)** is the hosted API: free key, 1,000 credits a month, no card.

[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai)
[![Downloads](https://static.pepy.tech/badge/crawl4ai/month)](https://pepy.tech/project/crawl4ai)
[![Discord](https://img.shields.io/badge/Discord-join%20us-5865F2?logo=discord&logoColor=white)](https://discord.gg/jP8KfhDhyN)

---

## Run it

The server needs a token. Without one it answers only inside its container.

```bash
export CRAWL4AI_API_TOKEN="$(openssl rand -hex 32)"
docker run -d -p 11235:11235 --name crawl4ai --shm-size=1g \
  -e CRAWL4AI_API_TOKEN="$CRAWL4AI_API_TOKEN" \
  unclecode/crawl4ai:latest
```

Test it (allow about 10 seconds for the start):

```bash
curl -s http://localhost:11235/md \
  -H "Authorization: Bearer $CRAWL4AI_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://news.ycombinator.com"}' | jq -r .markdown
```

The dashboard is at `http://localhost:11235/dashboard`, the playground at `http://localhost:11235/playground`.

Images are multi-arch (`amd64`, `arm64`). Tags: `latest`, or a version such as `0.9.5`.

---

## Docs

- Self-hosting guide (LLM keys, MCP, every setting): [docs.crawl4ai.com/core/self-hosting](https://docs.crawl4ai.com/core/self-hosting/)
- Source and issues: [github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
- Hosted API docs: [crawl4ai.com/docs](https://crawl4ai.com/docs?ref=dockerhub)

---

[Star on GitHub](https://github.com/unclecode/crawl4ai) · [Follow @unclecode on X](https://x.com/unclecode) · [Discord](https://discord.gg/jP8KfhDhyN)
