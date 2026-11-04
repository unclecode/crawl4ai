# Crawl4AI

**Crawl4AI Cloud is the hosted web crawler API for LLMs and AI agents. No servers to run. Start free at [crawl4ai.com](https://crawl4ai.com/?ref=dockerhub).** Prefer to self-host? This image is the open-source Crawl4AI server (Apache-2.0).

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

[![Want this without the ops work? Try Crawl4AI Cloud.](https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/dockerhub-cta.svg)](https://crawl4ai.com/?ref=dockerhub-cta)

---

[Star on GitHub](https://github.com/unclecode/crawl4ai) · [Follow @unclecode on X](https://x.com/unclecode) · [Discord](https://discord.gg/jP8KfhDhyN)
