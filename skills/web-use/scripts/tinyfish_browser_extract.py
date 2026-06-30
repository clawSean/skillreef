#!/usr/bin/env python3
"""Create a TinyFish browser session, drive it over CDP, and return extraction JSON.

Examples:
  TINYFISH_API_KEY="<your key>" \
    python3 skills/web-use/scripts/tinyfish_browser_extract.py \
    https://example.com/protected-page
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CREATE_SESSION_URL = "https://api.browser.tinyfish.ai/"
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_WAIT_SECONDS = 12
DEFAULT_SNIPPET_CHARS = 3000


class TinyFishRequestError(RuntimeError):
    """Raised when TinyFish returns a failed HTTP response."""


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> tuple[int, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
            try:
                return response.status, json.loads(text) if text else {}
            except json.JSONDecodeError:
                return response.status, {"raw": text}
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise TinyFishRequestError(f"HTTP {exc.code}: {error_body[:1000]}") from exc
    except URLError as exc:
        raise TinyFishRequestError(str(exc.reason)) from exc


def sanitize_error(error: Exception, api_key: str | None, session: dict[str, Any] | None = None) -> str:
    message = str(error)
    secrets = [api_key]
    if session:
        secrets.extend(
            value
            for key in ("cdp_url", "base_url")
            if isinstance((value := session.get(key)), str)
        )
    for secret in sorted((item for item in secrets if item), key=len, reverse=True):
        message = message.replace(secret, "<redacted>")
    return message


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
        "has_meaningful_text": len(body.strip()) >= 200,
    }


async def evaluate_via_cdp(cdp_url: str, target_url: str, wait_seconds: int, snippet_chars: int) -> dict[str, Any]:
    try:
        import websockets
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "TinyFish CDP extraction requires the optional Python package `websockets`."
        ) from exc

    async with websockets.connect(cdp_url, max_size=20_000_000) as ws:
        next_id = 0

        async def send(method: str, params: dict[str, Any] | None = None, session_id: str | None = None) -> dict[str, Any]:
            nonlocal next_id
            next_id += 1
            message: dict[str, Any] = {"id": next_id, "method": method}
            if params is not None:
                message["params"] = params
            if session_id is not None:
                message["sessionId"] = session_id
            await ws.send(json.dumps(message))
            while True:
                raw = await ws.recv()
                payload = json.loads(raw)
                if payload.get("id") == next_id:
                    return payload

        targets = await send("Target.getTargets")
        target_infos = (targets.get("result") or {}).get("targetInfos") or []
        page = next((item for item in target_infos if item.get("type") == "page"), None)
        if page is None:
            created = await send("Target.createTarget", {"url": target_url})
            target_id = (created.get("result") or {}).get("targetId")
        else:
            target_id = page.get("targetId")

        if not target_id:
            raise RuntimeError("Unable to find or create a page target")

        attached = await send("Target.attachToTarget", {"targetId": target_id, "flatten": True})
        session_id = (attached.get("result") or {}).get("sessionId")
        if not session_id:
            raise RuntimeError("Unable to attach to page target")

        await send("Page.enable", session_id=session_id)
        await send("Runtime.enable", session_id=session_id)
        await send("Page.navigate", {"url": target_url}, session_id=session_id)
        await asyncio.sleep(wait_seconds)

        expression = f'''JSON.stringify({{
          title: document.title,
          href: location.href,
          readyState: document.readyState,
          body: document.body ? document.body.innerText.slice(0, {snippet_chars}) : "",
          hasCloudflare: /Performing security verification|Just a moment|Cloudflare/i.test(document.body ? document.body.innerText : document.title),
          hasSecurityChallenge: /captcha|verify you are human|security check|access denied/i.test(document.body ? document.body.innerText : document.title)
        }})'''
        evaluated = await send(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
            session_id=session_id,
        )
        value = (((evaluated.get("result") or {}).get("result") or {}).get("value"))
        if not value:
            raise RuntimeError(f"Missing evaluation result: {evaluated}")
        return json.loads(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="Target URL")
    parser.add_argument("--api-key", default=os.environ.get("TINYFISH_API_KEY"), help="TinyFish API key")
    parser.add_argument(
        "--session-timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Requested TinyFish browser-session timeout",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=DEFAULT_WAIT_SECONDS,
        help="Seconds to wait after navigation before reading page content",
    )
    parser.add_argument(
        "--snippet-chars",
        type=int,
        default=DEFAULT_SNIPPET_CHARS,
        help="Maximum body characters to extract from the page",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.api_key:
        print("Missing TinyFish API key. Pass --api-key or set TINYFISH_API_KEY.", file=sys.stderr)
        return 2

    session: dict[str, Any] | None = None
    try:
        status_code, session = post_json(
            CREATE_SESSION_URL,
            {"url": args.url, "timeout_seconds": args.session_timeout_seconds},
            {"X-API-Key": args.api_key},
            60,
        )
        if not (200 <= status_code < 300):
            raise TinyFishRequestError(f"HTTP {status_code}: {session}")
        if not isinstance(session, dict):
            raise TinyFishRequestError("TinyFish response was not a JSON object")
        cdp_url = session.get("cdp_url")
        if not cdp_url:
            raise RuntimeError("TinyFish response missing cdp_url")
        page_data = asyncio.run(evaluate_via_cdp(cdp_url, args.url, args.wait_seconds, args.snippet_chars))
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "ok": False,
                    "provider": "tinyfish",
                    "mode": "browser-cdp",
                    "url": args.url,
                    "error": sanitize_error(exc, args.api_key, session),
                },
                indent=2,
            )
        )
        return 1

    title = page_data.get("title") or ""
    body_excerpt = page_data.get("body") or ""
    result = {
        "ok": True,
        "provider": "tinyfish",
        "mode": "browser-cdp",
        "url": args.url,
        "session_id": session.get("session_id"),
        "has_cdp_url": bool(session.get("cdp_url")),
        "has_base_url": bool(session.get("base_url")),
        "title": title,
        "href": page_data.get("href"),
        "ready_state": page_data.get("readyState"),
        "body_excerpt": body_excerpt,
        "body_length": len(body_excerpt),
        "has_cloudflare": bool(page_data.get("hasCloudflare")),
        "has_security_challenge": bool(page_data.get("hasSecurityChallenge")),
        "has_meaningful_text": len(body_excerpt.strip()) >= 200,
    }
    result.update(signals(title, body_excerpt))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
