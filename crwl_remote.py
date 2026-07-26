"""Dependency-light entry point for a remote Crawl4AI API.

Remote crawls are dispatched before importing Crawl4AI's local browser stack.
This lets the command use a hosted or Docker API without browser dependencies.
"""

from __future__ import annotations

import json
import getpass
import os
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CONFIG_PATH = Path.home() / ".crawl4ai" / "remote.json"


def _saved_credentials() -> dict[str, str]:
    if not CONFIG_PATH.is_file():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {key: str(value) for key, value in data.items() if value}


def _option_value(args: list[str], option: str) -> Optional[str]:
    for index, arg in enumerate(args):
        if arg == option and index + 1 < len(args):
            return args[index + 1]
        if arg.startswith(option + "="):
            return arg.split("=", 1)[1]
    return None


def _api_setting(args: list[str], option: str, env_name: str) -> Optional[str]:
    config_key = "api_url" if env_name.endswith("_URL") else "api_token"
    return (
        _option_value(args, option)
        or os.environ.get(env_name)
        or _saved_credentials().get(config_key)
    )


def _configure(args: list[str]) -> int:
    api_url = _option_value(args, "--api-url")
    api_token = _option_value(args, "--api-token")
    if not api_url:
        api_url = input("Crawl4AI API URL: ").strip()
    if not api_token:
        api_token = getpass.getpass("Crawl4AI API token: ").strip()
    if not api_url or not api_token:
        print("Error: both API URL and token are required.", file=sys.stderr)
        return 2

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps({"api_url": api_url.rstrip("/"), "api_token": api_token}, indent=2) + "\n",
        encoding="utf-8",
    )
    CONFIG_PATH.chmod(0o600)
    print(f"Remote credentials saved to {CONFIG_PATH}")
    return 0


def _load_config(path: Optional[str]) -> dict[str, Any]:
    if not path:
        return {}
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith((".yml", ".yaml")):
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("YAML config files require PyYAML; use JSON in a minimal install") from exc
        return yaml.safe_load(text) or {}
    return json.loads(text)


def _parse_values(value: Optional[str]) -> dict[str, Any]:
    if not value:
        return {}
    result: dict[str, Any] = {}
    for item in value.split(","):
        key, separator, raw = item.partition("=")
        if not separator:
            raise ValueError(f"Invalid key=value pair: {item}")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        result[key.strip()] = parsed
    return result


def _remote_args(args: list[str]) -> dict[str, Any]:
    positional = [arg for arg in args if not arg.startswith("-")]
    if positional and positional[0] == "crawl":
        positional.pop(0)
    option_values = {
        value
        for option in ("--api-url", "--api-token", "-B", "--browser-config", "-C",
                       "--crawler-config", "-b", "--browser", "-c", "--crawler",
                       "-o", "--output", "-O", "--output-file", "--deep-crawl",
                       "--max-pages")
        if (value := _option_value(args, option)) is not None
    }
    urls = [value for value in positional if value not in option_values]
    if not urls:
        raise ValueError("URL argument is required")

    browser_path = _option_value(args, "--browser-config") or _option_value(args, "-B")
    crawler_path = _option_value(args, "--crawler-config") or _option_value(args, "-C")
    browser_config = _load_config(browser_path)
    crawler_config = _load_config(crawler_path)
    browser_config.update(_parse_values(_option_value(args, "--browser") or _option_value(args, "-b")))
    crawler_config.update(_parse_values(_option_value(args, "--crawler") or _option_value(args, "-c")))
    if "cache_mode" not in crawler_config:
        crawler_config["cache_mode"] = "bypass"
    deep_crawl = _option_value(args, "--deep-crawl")
    if deep_crawl:
        strategy_types = {
            "bfs": "BFSDeepCrawlStrategy",
            "dfs": "DFSDeepCrawlStrategy",
            "best-first": "BestFirstCrawlingStrategy",
        }
        if deep_crawl not in strategy_types:
            raise ValueError("--deep-crawl must be bfs, dfs, or best-first")
        raw_max_pages = _option_value(args, "--max-pages") or "10"
        crawler_config["deep_crawl_strategy"] = {
            "type": strategy_types[deep_crawl],
            "params": {"max_depth": 3, "max_pages": int(raw_max_pages)},
        }

    return {
        "url": urls[0],
        "browser_config": browser_config,
        "crawler_config": crawler_config,
        "output": _option_value(args, "--output") or _option_value(args, "-o") or "all",
        "output_file": _option_value(args, "--output-file") or _option_value(args, "-O"),
    }


def _render(result: dict[str, Any], output: str) -> str:
    if output in ("markdown", "md"):
        markdown = result.get("markdown") or ""
        return markdown.get("raw_markdown", "") if isinstance(markdown, dict) else str(markdown)
    if output in ("markdown-fit", "md-fit"):
        markdown = result.get("markdown") or ""
        return markdown.get("fit_markdown", "") if isinstance(markdown, dict) else str(markdown)
    if output == "json":
        extracted = result.get("extracted_content")
        if isinstance(extracted, str):
            try:
                extracted = json.loads(extracted)
            except json.JSONDecodeError:
                return extracted
        return json.dumps(extracted, indent=2, ensure_ascii=False)
    return json.dumps(result, indent=2, ensure_ascii=False)


def _render_results(results: list[dict[str, Any]], output: str) -> str:
    if len(results) == 1 or output not in ("markdown", "md", "markdown-fit", "md-fit"):
        return _render(results[0], output)
    sections = []
    for result in results:
        sections.append(
            f"{'=' * 60}\n# {result.get('url', '')}\n{'=' * 60}\n\n"
            f"{_render(result, output)}"
        )
    return "\n\n".join(sections)


def _run_remote(args: list[str], api_url: str, api_token: Optional[str]) -> int:
    parsed = _remote_args(args)
    payload = json.dumps({
        "urls": [parsed["url"]],
        "browser_config": parsed["browser_config"],
        "crawler_config": parsed["crawler_config"],
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    request = Request(
        api_url.rstrip("/") + "/crawl",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            body = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"Error: Crawl4AI API returned HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Error: Cannot connect to Crawl4AI API: {exc.reason}", file=sys.stderr)
        return 1

    if not body.get("success", False):
        print(f"Error: Remote crawl failed: {body.get('msg', 'Unknown error')}", file=sys.stderr)
        return 1
    results = body.get("results", [])
    if not results:
        print("Error: Remote crawl returned no results", file=sys.stderr)
        return 1
    rendered = _render_results(results, parsed["output"])
    if parsed["output_file"]:
        Path(parsed["output_file"]).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "config":
        raise SystemExit(_configure(args[1:]))
    api_url = _api_setting(args, "--api-url", "CRAWL4AI_API_URL")
    if any(arg in ("-h", "--help") for arg in args):
        print(
            "Usage: crwl-remote URL [OPTIONS]\n"
            "       crwl-remote config [--api-url URL --api-token TOKEN]\n\n"
            "Use CRAWL4AI_API_URL and CRAWL4AI_API_TOKEN (or --api-url and\n"
            "--api-token) to crawl through a remote Crawl4AI API. Credentials\n"
            "saved by `crwl-remote config` are used as the fallback.\n\n"
            "Remote options: -B/--browser-config, -C/--crawler-config,\n"
            "-b/--browser, -c/--crawler, -o/--output, -O/--output-file"
        )
        return
    if api_url:
        token = _api_setting(args, "--api-token", "CRAWL4AI_API_TOKEN")
        try:
            raise SystemExit(_run_remote(args, api_url, token))
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(1)

    print(
        "Error: API URL is required; run `crwl-remote config`, set "
        "CRAWL4AI_API_URL, or use --api-url.",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()
