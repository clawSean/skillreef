#!/usr/bin/env python3
"""Discover media network requests from a rendered page via Browserless /function.

This is intentionally generic web-use plumbing. It does not decide what kind of
social/video workflow should happen next; callers such as the video skill consume
the normalized JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_HOST = "https://production-sfo.browserless.io"
DEFAULT_TIMEOUT = 120
DEFAULT_WAIT_MS = 6000
DEFAULT_GOTO_TIMEOUT_MS = 90000


def post_json(url: str, payload: dict[str, Any], timeout: int) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
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
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Browserless HTTP {exc.code}: {error_body[:1000]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Browserless request failed: {exc.reason}") from exc


def browserless_url(host: str, path: str, token: str) -> str:
    return f"{host}{path}?{urlencode({'token': token})}"


FUNCTION_CODE = r"""
export default async function({ page, context }) {
  const seen = new Map();
  const mediaTypes = /video|audio|mpegurl|mp4|webm|m3u8/i;
  const mediaUrl = /\.(mp4|m4v|webm|mov|m3u8|mp3|m4a)(\?|$)/i;
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

  const remember = (url, source, headers = {}) => {
    if (!url || seen.has(url)) return;
    const contentType = headers['content-type'] || headers['Content-Type'] || '';
    if (!mediaTypes.test(contentType) && !mediaUrl.test(url)) return;
    seen.set(url, { url, source, content_type: contentType || null });
  };

  page.on('response', async response => {
    try {
      remember(response.url(), 'response', response.headers());
    } catch (err) {}
  });

  await page.goto(context.url, { waitUntil: 'networkidle2', timeout: context.gotoTimeoutMs || 90000 });

  if (context.play) {
    await page.evaluate(async () => {
      for (const video of Array.from(document.querySelectorAll('video'))) {
        try { video.muted = true; await video.play(); } catch (err) {}
      }
      for (const button of Array.from(document.querySelectorAll('button, [role="button"]')).slice(0, 20)) {
        const label = `${button.ariaLabel || ''} ${button.textContent || ''}`.toLowerCase();
        if (/play|watch|reel|video/.test(label)) {
          try { button.click(); } catch (err) {}
        }
      }
    });
  }

  await sleep(context.waitMs || 6000);

  const domMedia = await page.evaluate(() => Array.from(document.querySelectorAll('video, audio, source'))
    .map(el => el.currentSrc || el.src)
    .filter(Boolean));
  for (const url of domMedia) remember(url, 'dom');

  const title = await page.title().catch(() => '');
  return {
    ok: true,
    url: context.url,
    title,
    candidates: Array.from(seen.values()),
    candidate_count: seen.size
  };
}
"""


def parse_browserless_function_response(text: str) -> dict[str, Any]:
    payload = json.loads(text)
    if isinstance(payload, dict) and "data" in payload and isinstance(payload["data"], dict):
        return payload["data"]
    if isinstance(payload, dict):
        return payload
    raise RuntimeError("Unexpected Browserless /function response shape")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Target page URL")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Browserless host")
    parser.add_argument(
        "--token",
        default=os.environ.get("BROWSERLESS_TOKEN") or os.environ.get("BROWSERLESS_API_KEY"),
        help="Browserless token; defaults to BROWSERLESS_TOKEN or BROWSERLESS_API_KEY",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout in seconds")
    parser.add_argument("--wait-ms", type=int, default=DEFAULT_WAIT_MS, help="Post-load wait time in ms")
    parser.add_argument("--goto-timeout-ms", type=int, default=DEFAULT_GOTO_TIMEOUT_MS, help="Browser goto timeout in ms")
    parser.add_argument("--play", action="store_true", help="Try muted playback/clicks before collecting media")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.token:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Missing Browserless token. Set BROWSERLESS_TOKEN or BROWSERLESS_API_KEY.",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    try:
        _, response_text = post_json(
            browserless_url(args.host, "/function", args.token),
            {
                "code": FUNCTION_CODE,
                "context": {
                    "url": args.url,
                    "waitMs": args.wait_ms,
                    "gotoTimeoutMs": args.goto_timeout_ms,
                    "play": args.play,
                },
            },
            args.timeout,
        )
        result = parse_browserless_function_response(response_text)
        result.setdefault("ok", True)
        result.setdefault("provider", "browserless")
        result.setdefault("mode", "function-media-requests")
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc), "provider": "browserless", "mode": "function-media-requests", "url": args.url}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
