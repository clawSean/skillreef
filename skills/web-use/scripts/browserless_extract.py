#!/usr/bin/env python3
"""Fetch a page through Browserless and return normalized extraction JSON.

Examples:
  BROWSERLESS_TOKEN="<set-at-runtime>" \
    python3 scripts/browserless_extract.py \
    https://example.com/protected-page

  BROWSERLESS_TOKEN="<set-at-runtime>" \
    python3 scripts/browserless_extract.py \
    https://example.com/protected-page \
    --mode unblock
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_HOST = "https://production-sfo.browserless.io"
DEFAULT_TIMEOUT = 120
DEFAULT_SNIPPET_CHARS = 3000
DEFAULT_MAX_RETRIES = 3
DEFAULT_MEDIA_LIMIT = 20
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
BACKOFF_BASE = 1.5
BACKOFF_CAP = 20.0
ERROR_BODY_CHARS = 500
META_KEYS = (
    "og:title",
    "og:description",
    "og:image",
    "og:video",
    "og:video:url",
    "og:video:secure_url",
    "twitter:title",
    "twitter:description",
    "twitter:image",
)
MEDIA_RE = re.compile(
    r"https?:\\?/\\?/[^\"'<>\s]+?\.(?:mp4|m3u8|webm|mov|m4v)(?:[^\"'<>\s]*)?",
    re.I,
)


class BrowserlessRequestError(RuntimeError):
    """Raised when Browserless returns a non-2xx response after retries."""


def redact(text: str, token: str | None) -> str:
    if token and text:
        text = text.replace(token, "<redacted>")
    return re.sub(r"([?&]token=)[^&\s]+", r"\1<redacted>", text or "")


def retry_after(exc: HTTPError) -> float | None:
    raw = exc.headers.get("Retry-After") if exc.headers else None
    if raw and raw.isdigit():
        return float(raw)
    return None


def post_browserless(
    url: str,
    payload: dict[str, Any],
    timeout: int,
    token: str | None,
    max_retries: int,
) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    last_error = "unknown error"

    for attempt in range(max_retries + 1):
        request = Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.status, response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            error_body = redact(exc.read().decode("utf-8", errors="replace"), token)
            last_error = f"HTTP {exc.code}: {error_body[:ERROR_BODY_CHARS]}"
            if exc.code not in RETRYABLE_STATUS or attempt == max_retries:
                raise BrowserlessRequestError(last_error) from None
            delay = retry_after(exc) or min(BACKOFF_BASE * (2**attempt), BACKOFF_CAP)
        except URLError as exc:
            last_error = redact(str(exc.reason), token)
            if attempt == max_retries:
                raise BrowserlessRequestError(last_error) from None
            delay = min(BACKOFF_BASE * (2**attempt), BACKOFF_CAP)
        time.sleep(delay)

    raise BrowserlessRequestError(last_error)


def browserless_url(host: str, path: str, token: str) -> str:
    return f"{host}{path}?{urlencode({'token': token})}"


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


def extract_meta(html: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for key in META_KEYS:
        pattern_a = (
            r"<meta[^>]+(?:property|name)=[\"']%s[\"'][^>]+content=[\"']([^\"']*)[\"']"
            % re.escape(key)
        )
        pattern_b = (
            r"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]+(?:property|name)=[\"']%s[\"']"
            % re.escape(key)
        )
        match = re.search(pattern_a, html, re.I) or re.search(pattern_b, html, re.I)
        if match:
            meta[key] = clean_text(match.group(1))
    return meta


def normalize_media_url(url: str) -> str:
    return unescape(url).replace("\\/", "/")


def extract_media_candidates(html: str, limit: int) -> list[str]:
    seen: list[str] = []
    for match in MEDIA_RE.findall(html):
        media_url = normalize_media_url(match)
        if media_url not in seen:
            seen.append(media_url)
        if len(seen) >= limit:
            break
    return seen


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


def html_result(provider_mode: str, url: str, status: int, html: str, media_limit: int) -> dict[str, Any]:
    title = extract_title_from_html(html)
    body = strip_html(html)
    return {
        "provider": "browserless",
        "mode": provider_mode,
        "url": url,
        "status_code": status,
        "title": title,
        "meta": extract_meta(html),
        "media_candidates": extract_media_candidates(html, media_limit),
        "body": body,
        **signals(title, body),
    }


def request_content(args: argparse.Namespace) -> dict[str, Any]:
    status, html = post_browserless(
        browserless_url(args.host, "/content", args.token),
        {"url": args.url},
        args.timeout,
        args.token,
        args.max_retries,
    )
    return html_result("content", args.url, status, html, args.media_limit)


def request_unblock(args: argparse.Namespace) -> dict[str, Any]:
    status, response_text = post_browserless(
        browserless_url(args.host, "/unblock", args.token),
        {"url": args.url, "browserWSEndpoint": False},
        args.timeout,
        args.token,
        args.max_retries,
    )
    payload = json.loads(response_text)
    html = payload.get("content") or ""
    result = html_result("unblock", args.url, status, html, args.media_limit)
    result["browser_ws_endpoint"] = payload.get("browserWSEndpoint")
    return result


def request_stealth_bql(args: argparse.Namespace) -> dict[str, Any]:
    solve_fragment = "solve(type: cloudflare) { found solved time }" if args.solve else ""
    query = (
        "mutation Extract($url: String!) { "
        "goto(url: $url, waitUntil: networkIdle) { status } "
        f"{solve_fragment} "
        'title: text(selector: "title") { text } '
        'body: text(selector: "body") { text } '
        "}"
    )
    _, response_text = post_browserless(
        browserless_url(args.host, "/stealth/bql", args.token),
        {"query": query, "variables": {"url": args.url}},
        args.timeout,
        args.token,
        args.max_retries,
    )
    payload = json.loads(response_text)
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    data = payload.get("data") or {}
    title = clean_text(((data.get("title") or {}).get("text") or ""))
    body = clean_text(((data.get("body") or {}).get("text") or ""))
    return {
        "provider": "browserless",
        "mode": "stealth-bql",
        "url": args.url,
        "status_code": (data.get("goto") or {}).get("status"),
        "title": title,
        "meta": {},
        "media_candidates": [],
        "body": body,
        "solve": data.get("solve"),
        **signals(title, body),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Target URL")
    parser.add_argument(
        "--mode",
        choices=["stealth-bql", "unblock", "content"],
        default="stealth-bql",
        help="Browserless surface to use",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Browserless host")
    parser.add_argument(
        "--token",
        default=os.environ.get("BROWSERLESS_TOKEN") or os.environ.get("BROWSERLESS_API_KEY"),
        help="Browserless API token",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--media-limit", type=int, default=DEFAULT_MEDIA_LIMIT, help="Maximum media URL candidates to emit")
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
    if not args.token:
        print("Missing Browserless token. Pass --token or set BROWSERLESS_TOKEN.", file=sys.stderr)
        return 2

    try:
        if args.mode == "content":
            result = request_content(args)
        elif args.mode == "unblock":
            result = request_unblock(args)
        else:
            result = request_stealth_bql(args)
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": redact(str(exc), args.token)[:ERROR_BODY_CHARS],
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
