# Nix

```bash
nix build
```

`packages.default` is the self-hosted API/MCP server (`crawl4ai-server`).
It listens on `0.0.0.0:11235` when `CRAWL4AI_API_TOKEN` and `REDIS_PASSWORD`
are set. The MCP SSE endpoint is `/mcp/sse`.

Playwright Chromium comes from nixpkgs (`PLAYWRIGHT_BROWSERS_PATH`). The
package relaxes upstream dependency pins to nixpkgs versions, uses nixpkgs
`litellm` instead of the `unclecode-litellm` pin, and does not install
`patchright` or `alphashape`. Undetected-browser mode is unavailable; the
server's default browser path uses Playwright.

`nixosModules.default` runs Redis and the server. The token file is
`/run/secrets/crawl4ai-api-token` (raw token, not `KEY=value`).

`nixosModules.isolation` is a host nftables bridge filter for a container
veth. It drops new connections from that interface to local and other
non-global addresses, including the host, while allowing replies and DHCP.
