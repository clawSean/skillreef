#!/usr/bin/env python3
"""Create a TinyFish browser session, drive it over CDP, and return extraction JSON.

Examples:
  TINYFISH_API_KEY="$(op read 'op://<vault>/TinyFish API Key/credential')" \
    python3 scripts/tinyfish_browser_extract.py \
    https://camelcamelcamel.com/product/B07XJ8C8F7
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from typing import Any

import requests
import websockets

CREATE_SESSION_URL = "https://api.browser.tinyfish.ai/"
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_WAIT_SECONDS = 12
DEFAULT_SNIPPET_CHARS = 3000


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
        "has_price_history": bool(re.search(r"amazon price history|price history", combined, re.I)),
        "has_product_details": bool(re.search(r"product details", combined, re.I)),
    }


async def evaluate_via_cdp(cdp_url: str, target_url: str, wait_seconds: int, snippet_chars: int) -> dict[str, Any]:
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
          hasPriceHistory: /Amazon Price History|Price History/i.test(document.body ? document.body.innerText : ""),
          hasProductDetails: /Product Details/i.test(document.body ? document.body.innerText : ""),
          hasCloudflare: /Performing security verification|Just a moment|Cloudflare/i.test(document.body ? document.body.innerText : document.title)
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
    parser = argparse.ArgumentParser(description=__doc__)
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

    try:
        response = requests.post(
            CREATE_SESSION_URL,
            headers={"X-API-Key": args.api_key, "Content-Type": "application/json"},
            json={"url": args.url, "timeout_seconds": args.session_timeout_seconds},
            timeout=60,
        )
        response.raise_for_status()
        session = response.json()
        cdp_url = session.get("cdp_url")
        if not cdp_url:
            raise RuntimeError(f"TinyFish response missing cdp_url: {session}")
        page_data = asyncio.run(evaluate_via_cdp(cdp_url, args.url, args.wait_seconds, args.snippet_chars))
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "ok": False,
                    "provider": "tinyfish",
                    "mode": "browser-cdp",
                    "url": args.url,
                    "error": str(exc),
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
        "cdp_url": session.get("cdp_url"),
        "base_url": session.get("base_url"),
        "title": title,
        "href": page_data.get("href"),
        "ready_state": page_data.get("readyState"),
        "body_excerpt": body_excerpt,
        "body_length": len(body_excerpt),
        "has_price_history": bool(page_data.get("hasPriceHistory")),
        "has_product_details": bool(page_data.get("hasProductDetails")),
        "has_cloudflare": bool(page_data.get("hasCloudflare")),
    }
    result.update(signals(title, body_excerpt))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
