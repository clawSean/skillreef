#!/usr/bin/env python3
"""Fetch a page through Browserless and return normalized extraction JSON.

Examples:
  BROWSERLESS_TOKEN="<your token>" \
    python3 skills/web-use/scripts/browserless_extract.py \
    https://example.com/protected-page

  BROWSERLESS_TOKEN="<your token>" \
    python3 skills/web-use/scripts/browserless_extract.py \
    https://example.com/protected-page \
    --mode unblock
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from html import unescape
from typing import Any
from urllib.parse import urlparse

import _http as requests

DEFAULT_HOST = "https://production-sfo.browserless.io"
DEFAULT_TIMEOUT = 120
DEFAULT_SNIPPET_CHARS = 3000


def configured_host() -> str:
    host = os.environ.get("BROWSERLESS_HOST", DEFAULT_HOST).rstrip("/")
    parsed = urlparse(host)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("BROWSERLESS_HOST must be a bare trusted HTTPS origin")
    allowed = {urlparse(DEFAULT_HOST).netloc}
    allowed.update(item.strip() for item in os.environ.get("BROWSERLESS_ALLOWED_HOSTS", "").split(",") if item.strip())
    if parsed.netloc not in allowed:
        raise ValueError("BROWSERLESS_HOST is not in BROWSERLESS_ALLOWED_HOSTS")
    return host


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def strip_html(html: str) -> str:
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", html)
    match = re.search(r"(?is)<body[^>]*>(.*?)</body>", html)
    body = match.group(1) if match else html
    text = re.sub(r"(?is)<[^>]+>", " ", body)
    return clean_text(text)


def extract_title_from_html(html: str) -> str:
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    return clean_text(match.group(1)) if match else ""


def signals(title: str, body: str) -> dict[str, bool]:
    combined = f"{title}\n{body}"
    return {
        "has_cloudflare": bool(
            re.search(
                r"just a moment|performing security verification|cloudflare|cf-browser-verification",
                combined,
                re.I,
            )
        ),
        "has_security_challenge": bool(
            re.search(
                r"captcha|verify you are human|security check|access denied",
                combined,
                re.I,
            )
        ),
        "has_meaningful_text": len(clean_text(body)) >= 200,
    }


def sanitize_error(error: Exception, token: str | None) -> str:
    message = str(error)
    if token:
        message = message.replace(token, "<redacted>")
    message = re.sub(r"([?&]token=)[^&\s]+", r"\1<redacted>", message)
    return message


def request_content(token: str, url: str, host: str, timeout: int) -> dict[str, Any]:
    response = requests.post(
        f"{host}/content",
        params={"token": token},
        json={"url": url},
        timeout=timeout,
    )
    response.raise_for_status()
    html = response.text
    title = extract_title_from_html(html)
    body = strip_html(html)
    return {
        "provider": "browserless",
        "mode": "content",
        "url": url,
        "status_code": response.status_code,
        "title": title,
        "body": body,
        **signals(title, body),
    }


def request_unblock(token: str, url: str, host: str, timeout: int) -> dict[str, Any]:
    response = requests.post(
        f"{host}/unblock",
        params={"token": token},
        json={"url": url, "browserWSEndpoint": False},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    html = payload.get("content") or ""
    title = extract_title_from_html(html)
    body = strip_html(html)
    return {
        "provider": "browserless",
        "mode": "unblock",
        "url": url,
        "status_code": response.status_code,
        "title": title,
        "body": body,
        "browser_ws_endpoint": payload.get("browserWSEndpoint"),
        **signals(title, body),
    }


def request_stealth_bql(token: str, url: str, host: str, timeout: int, solve: bool) -> dict[str, Any]:
    solve_fragment = "solve(type: cloudflare) { found solved time }" if solve else ""
    query = (
        "mutation Extract($url: String!) { "
        "goto(url: $url, waitUntil: networkIdle) { status } "
        f"{solve_fragment} "
        'title: text(selector: "title") { text } '
        'body: text(selector: "body") { text } '
        "}"
    )
    response = requests.post(
        f"{host}/stealth/bql",
        params={"token": token},
        json={"query": query, "variables": {"url": url}},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    data = payload.get("data") or {}
    title = clean_text(((data.get("title") or {}).get("text") or ""))
    body = clean_text(((data.get("body") or {}).get("text") or ""))
    return {
        "provider": "browserless",
        "mode": "stealth-bql",
        "url": url,
        "status_code": (data.get("goto") or {}).get("status"),
        "title": title,
        "body": body,
        "solve": data.get("solve"),
        **signals(title, body),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="Target URL")
    parser.add_argument(
        "--mode",
        choices=["stealth-bql", "unblock", "content"],
        default="stealth-bql",
        help="Browserless surface to use",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument(
        "--snippet-chars",
        type=int,
        default=DEFAULT_SNIPPET_CHARS,
        help="Maximum body characters to emit",
    )
    parser.add_argument(
        "--solve",
        action="store_true",
        help="For stealth-bql mode, include Browserless solve(type: cloudflare)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.environ.get("BROWSERLESS_TOKEN")
    if not token:
        print("Missing Browserless token. Set BROWSERLESS_TOKEN through secure runtime injection.", file=sys.stderr)
        return 2

    try:
        host = configured_host()
        if args.mode == "content":
            result = request_content(token, args.url, host, args.timeout)
        elif args.mode == "unblock":
            result = request_unblock(token, args.url, host, args.timeout)
        else:
            result = request_stealth_bql(token, args.url, host, args.timeout, args.solve)
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": sanitize_error(exc, token),
                    "provider": "browserless",
                    "mode": args.mode,
                    "url": args.url,
                },
                indent=2,
            )
        )
        return 1

    body = result.get("body") or ""
    result["body_excerpt"] = body[: args.snippet_chars]
    result["body_length"] = len(body)
    result.pop("body", None)
    result["ok"] = True
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
