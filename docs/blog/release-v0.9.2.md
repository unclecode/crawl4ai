# Crawl4AI v0.9.2: Maintenance Bug Fixes

*July 2026 - 2 min read*

---

I'm releasing Crawl4AI v0.9.2, a small maintenance patch that cleans up a dispatcher resource leak and fixes a handful of Docker and GPU build issues. No new features, no breaking changes.

If you're on v0.9.1, upgrade freely.

## What's new at a glance

- **Dispatcher cleanup**: `MemoryAdaptiveDispatcher` no longer leaves crawl tasks and browser pages running after a streaming crawl is closed
- **Docker Playground**: "Advanced Config" no longer returns a 400
- **Docker Monitor**: the dashboard WebSocket no longer returns a 500 under JWT auth
- **Docker image**: Playwright headless shell is now included
- **GPU builds**: `ENABLE_GPU=true` Docker builds no longer fail on the CUDA toolkit

## Bug fixes

### Dispatcher (1 fix)

- **Streaming cleanup leak**: When the async generator from `MemoryAdaptiveDispatcher.run_urls_stream()` was closed or cancelled mid-stream, its per-URL crawl tasks kept running in the background. A later `arun_many()` on the same crawler could then overlap the old tasks while they still held the same browser, contexts, and pages — leaking pages and emitting stray Playwright `TargetClosedError`s. Closing the stream now cancels and awaits every in-flight task and drains any queued-but-unstarted URLs before returning. (#2071, thanks @reallav0)

### Docker (3 fixes)

- **Playground "Advanced Config" 400**: `/config/dump` requires a `type`, but the playground's `pyConfigToJson` only sent `code`. The request now includes the config type, aligns the stream fallback with the dump shape, and teaches `shouldUseStream` both nestings. (#2059, thanks @Pitchfork-and-Torch)
- **Monitor WebSocket 500**: the monitor dashboard's `/monitor/ws` endpoint 500'd because a router-level `token_dep` is HTTP-request-only and can't inject into WebSocket scopes. Auth is now enforced solely by `AuthGateMiddleware`; admin routes keep `require_admin`. (#2060, thanks @Pitchfork-and-Torch)
- **Headless shell packaging**: the Playwright headless shell is now installed in the Docker image. (#2067, thanks @reallav0)

### GPU / Build (1 fix)

- **CUDA toolkit on Bookworm**: `ENABLE_GPU=true` builds failed with "Package has no installation candidate" because `nvidia-cuda-toolkit` lives in Debian Bookworm's `non-free` component, which the `python:3.12-slim-bookworm` base image omits. The Dockerfile now adds the `non-free` (and contrib) apt sources before the GPU install block. (#2020, thanks @harshmathurx)

## Tests

- Regression test added for the dispatcher stream-close cleanup, asserting in-flight tasks are cancelled, the queue is drained, and session count returns to zero.
- Updated the monitor auth test for the WebSocket-safe router config, and corrected a regex group name and the Playwright cache-copy target in the Docker tests.

## Breaking changes

None.

## Upgrade

```bash
pip install -U crawl4ai
crawl4ai-doctor  # verify installation
```

Docker users: pull the latest image once the Docker release workflow finishes.

## Verification

```bash
python docs/releases_review/demo_v0.9.2.py
```

## Acknowledgments

Thanks to the community contributors who made this release possible: @reallav0 (#2071, #2067), @Pitchfork-and-Torch (#2059, #2060), @harshmathurx (#2020).

## Support & Resources

- [Documentation](https://docs.crawl4ai.com)
- [GitHub Issues](https://github.com/unclecode/crawl4ai/issues)
- [Discord Community](https://discord.gg/crawl4ai)
