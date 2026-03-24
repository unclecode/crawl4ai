# Crawl4AI Blog

Welcome to the Crawl4AI blog! Here you'll find detailed release notes, technical insights, and updates about the project. Whether you're looking for the latest improvements or want to dive deep into web crawling techniques, this is the place.

## Featured Articles

### [When to Stop Crawling: The Art of Knowing "Enough"](articles/adaptive-crawling-revolution.md)
*January 29, 2025*

Traditional crawlers are like tourists with unlimited time—they'll visit every street, every alley, every dead end. But what if your crawler could think like a researcher with a deadline? Discover how Adaptive Crawling revolutionizes web scraping by knowing when to stop. Learn about the three-layer intelligence system that evaluates coverage, consistency, and saturation to build focused knowledge bases instead of endless page collections.

[Read the full article →](articles/adaptive-crawling-revolution.md)

### [The LLM Context Protocol: Why Your AI Assistant Needs Memory, Reasoning, and Examples](articles/llm-context-revolution.md)
*January 24, 2025*

Ever wondered why your AI coding assistant struggles with your library despite comprehensive documentation? This article introduces the three-dimensional context protocol that transforms how AI understands code. Learn why memory, reasoning, and examples together create wisdom—not just information.

[Read the full article →](articles/llm-context-revolution.md)

## Latest Release

### [Crawl4AI v0.8.5 – Anti-Bot Detection, Shadow DOM & 60+ Bug Fixes](../blog/release-v0.8.5.md)
*March 2026*

Crawl4AI v0.8.5 is the biggest release since v0.8.0, bringing automatic anti-bot detection with proxy escalation, Shadow DOM flattening, deep crawl cancellation, and over 60 bug fixes.

Key highlights:
- **🛡️ Anti-Bot Detection & Proxy Escalation**: 3-tier detection with automatic retry, proxy chain, and fallback
- **🌑 Shadow DOM Flattening**: Extract content hidden inside shadow DOM components
- **🛑 Deep Crawl Cancellation**: Stop long crawls gracefully with `cancel()` or `should_cancel` callback
- **🔒 Critical Security Fixes**: RCE via deserialization patched, Redis CVE-2025-49844 fixed

[Read full release notes →](../blog/release-v0.8.5.md)

## Recent Releases

### [Crawl4AI v0.8.0 – Crash Recovery & Prefetch Mode](../blog/release-v0.8.0.md)
*January 2026*

Crawl4AI v0.8.0 introduces crash recovery for deep crawls, a new prefetch mode for fast URL discovery, and critical security fixes for Docker deployments.

Key highlights:
- **🔄 Deep Crawl Crash Recovery**: `on_state_change` callback for real-time state persistence, `resume_state` to continue from checkpoints
- **⚡ Prefetch Mode**: `prefetch=True` for 5-10x faster URL discovery, perfect for two-phase crawling patterns
- **🔒 Security Fixes**: Hooks disabled by default, `file://` URLs blocked on Docker API, `__import__` removed from sandbox

[Read full release notes →](../blog/release-v0.8.0.md)

### [Crawl4AI v0.7.8 – Stability & Bug Fix Release](../blog/release-v0.7.8.md)
*December 2025*

Crawl4AI v0.7.8 is a focused stability release addressing 11 bugs reported by the community. Fixes for Docker deployments, LLM extraction, URL handling, and dependency compatibility.

Key highlights:
- **🐳 Docker API Fixes**: ContentRelevanceFilter deserialization, ProxyConfig serialization, cache folder permissions
- **🤖 LLM Improvements**: Configurable rate limiter backoff, HTML input format support
- **📦 Dependencies**: Replaced deprecated PyPDF2 with pypdf, Pydantic v2 ConfigDict compatibility

[Read full release notes →](../blog/release-v0.7.8.md)

---

## Older Releases

| Version | Date | Highlights |
|---------|------|------------|
| [v0.7.7](../blog/release-v0.7.7.md) | November 2025 | Self-hosting platform, real-time monitoring, smart browser pool |
| [v0.7.6](../blog/release-v0.7.6.md) | October 2025 | Webhook infrastructure, reliable delivery, custom auth |
| [v0.7.5](../blog/release-v0.7.5.md) | September 2025 | Docker Hooks System, enhanced LLM integration, HTTPS preservation |
| [v0.7.4](../blog/release-v0.7.4.md) | August 2025 | LLM-powered table extraction, performance improvements |
| [v0.7.3](../blog/release-v0.7.3.md) | July 2025 | Undetected browser, multi-URL config, memory monitoring |
| [v0.7.1](../blog/release-v0.7.1.md) | June 2025 | Bug fixes and stability improvements |
| [v0.7.0](../blog/release-v0.7.0.md) | May 2025 | Adaptive crawling, virtual scroll, link analysis |

## Project History

Curious about how Crawl4AI has evolved? Check out our [complete changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md) for a detailed history of all versions and updates.

## Stay Updated

- Star us on [GitHub](https://github.com/unclecode/crawl4ai)
- Follow [@unclecode](https://twitter.com/unclecode) on Twitter
- Join our community discussions on GitHub