#!/usr/bin/env python3
"""Manage an opt-in Browserless persistent session and run BQL against it.

This is NOT the default browser route. Use stateless one-off extraction
(`skills/web-use/scripts/browserless_extract.py`) for single reads. Reach for a persistent
session only when a workflow repeatedly touches the same protected site and
genuinely benefits from cookies, localStorage, sessionStorage, or cache
persisting across BQL calls. Use it sparingly until token-bearing URL handling
is proven safe.

Browserless `/session` responses contain token-bearing `connect`, `browserQL`,
and `stop` URLs. They act as bearer credentials. This tool stores them only in a
local session file with 0600 permissions and never prints them; normal output is
redacted. Always `stop` the session when finished instead of relying on TTL
expiry.

Examples:
  # Create a stealth BQL session (writes a 0600 token-bearing file):
  BROWSERLESS_TOKEN="<your token>" \
    python3 skills/web-use/scripts/browserless_session.py create \
    --session-file /tmp/bl-session.json --ttl-ms 1800000

  # Run a BQL mutation against the persisted session:
  python3 skills/web-use/scripts/browserless_session.py query \
    --session-file /tmp/bl-session.json \
    --query 'mutation Go($url: String!) { goto(url: $url, waitUntil: domContentLoaded) { status } body: text(selector: "body") { text } }' \
    --variables-json '{"url": "TARGET_URL"}'

  # Inspect redacted metadata only (no URLs/token):
  python3 skills/web-use/scripts/browserless_session.py inspect --session-file /tmp/bl-session.json

  # Stop the session and delete the local file:
  python3 skills/web-use/scripts/browserless_session.py stop --session-file /tmp/bl-session.json --delete-file
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_HOST = "https://production-sfo.browserless.io"
DEFAULT_TIMEOUT = 120
SESSION_URL_KEYS = ("browserQL", "connect", "stop")
STD_STREAMS = {"-", "/dev/stdout", "/dev/stderr", "/dev/fd/1", "/dev/fd/2"}


class BrowserlessRequestError(RuntimeError):
    """Raised when Browserless returns a failed HTTP response."""


def with_query(url: str, params: dict[str, str] | None = None) -> str:
    if not params:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode(params)}"


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    timeout: int,
) -> tuple[int, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"} if body is not None else {},
        method=method,
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
        raise BrowserlessRequestError(f"HTTP {exc.code}: {error_body[:1000]}") from exc
    except URLError as exc:
        raise BrowserlessRequestError(str(exc.reason)) from exc


def token_from_url(url: Any) -> str | None:
    if not isinstance(url, str):
        return None
    match = re.search(r"[?&]token=([^&\s]+)", url)
    return match.group(1) if match else None


def collect_secrets(token: str | None, session: dict[str, Any] | None) -> set[str]:
    """Gather every string that must never reach stdout/stderr."""
    secrets: set[str] = set()
    if token:
        secrets.add(token)
    for key in SESSION_URL_KEYS:
        url = (session or {}).get(key)
        if isinstance(url, str) and url:
            secrets.add(url)
            embedded = token_from_url(url)
            if embedded:
                secrets.add(embedded)
    return {secret for secret in secrets if secret}


def sanitize(text: Any, secrets: set[str]) -> str:
    out = text if isinstance(text, str) else str(text)
    # Longest first so full token-bearing URLs are redacted before bare tokens.
    for secret in sorted(secrets, key=len, reverse=True):
        out = out.replace(secret, "<redacted>")
    out = re.sub(r"([?&]token=)[^&\s]+", r"\1<redacted>", out)
    return out


def sanitize_error(exc: Exception, secrets: set[str]) -> str:
    return sanitize(str(exc), secrets)


def emit(payload: dict[str, Any], secrets: set[str]) -> None:
    """Serialize, redact, then print. Redaction is the last line of defense."""
    print(sanitize(json.dumps(payload, indent=2), secrets))


def reject_std_stream(path: str) -> None:
    if path in STD_STREAMS:
        raise ValueError(
            "Refusing to write a token-bearing session to a standard stream; "
            "pass a real --session-file path."
        )


def file_mode(path: str) -> int:
    return os.stat(path).st_mode & 0o777


def warn_if_insecure(path: str) -> None:
    try:
        mode = file_mode(path)
    except OSError:
        return
    if mode & 0o077:
        print(
            f"warning: session file {path} mode is {oct(mode)}; expected 0o600 "
            "(it holds token-bearing URLs).",
            file=sys.stderr,
        )


def write_session_file(path: str, data: dict[str, Any], overwrite: bool) -> None:
    reject_std_stream(path)
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(
            f"Session file already exists: {path} (pass --overwrite to replace)."
        )
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, mode=0o700, exist_ok=True)
        try:
            os.chmod(parent, 0o700)
        except OSError:
            pass
    # O_CREAT mode is masked by umask, so chmod afterwards to guarantee 0600.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    os.chmod(path, 0o600)


def load_session_file(path: str) -> dict[str, Any]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Session file not found: {path}")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Session file does not contain a JSON object.")
    return data


def normalize_query_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def resolve_query(value: str) -> str:
    if os.path.isfile(value):
        with open(value, encoding="utf-8") as handle:
            return handle.read()
    return value


def cmd_create(args: argparse.Namespace) -> int:
    token = args.token
    if not token:
        print(
            "Missing Browserless token. Pass --token or set BROWSERLESS_TOKEN.",
            file=sys.stderr,
        )
        return 2
    try:
        # Fail before creating a remote session if we cannot save it locally.
        reject_std_stream(args.session_file)
        if os.path.exists(args.session_file) and not args.overwrite:
            raise FileExistsError(
                f"Session file already exists: {args.session_file} "
                "(pass --overwrite to replace)."
            )

        params: dict[str, str] = {"token": token}
        body: dict[str, Any] = {"ttl": args.ttl_ms, "stealth": args.stealth}
        if args.proxy_json:
            proxy = json.loads(args.proxy_json)
            if not isinstance(proxy, dict):
                raise ValueError("--proxy-json must be a JSON object.")
            body["proxy"] = proxy
        if args.process_keep_alive_ms is not None:
            if args.process_keep_alive_ms < 0:
                raise ValueError("--process-keep-alive-ms must be >= 0.")
            if args.process_keep_alive_ms > args.ttl_ms:
                raise ValueError("--process-keep-alive-ms must be <= --ttl-ms.")
            body["processKeepAlive"] = args.process_keep_alive_ms

        _, session = request_json(
            "POST",
            with_query(f"{args.host}/session", params),
            body,
            args.timeout,
        )
        if not isinstance(session, dict):
            raise ValueError("Browserless /session did not return a JSON object.")

        try:
            write_session_file(args.session_file, session, args.overwrite)
        except Exception as write_exc:  # noqa: BLE001
            # Don't leak an orphan remote session we couldn't persist.
            stop_url = session.get("stop")
            cleanup = "not attempted"
            if stop_url:
                try:
                    request_json("DELETE", stop_url, None, args.timeout)
                    cleanup = "stopped"
                except Exception:  # noqa: BLE001
                    cleanup = "stop failed"
            detail = sanitize(str(write_exc), collect_secrets(token, session))
            raise RuntimeError(
                f"Created remote session but failed to save it ({detail}); "
                f"remote cleanup: {cleanup}."
            ) from None

        secrets = collect_secrets(token, session)
        emit(
            {
                "ok": True,
                "action": "create",
                "session_file": args.session_file,
                "session_id": session.get("id"),
                "stealth": args.stealth,
                "ttl_ms": args.ttl_ms,
                "has_browserql": bool(session.get("browserQL")),
                "has_connect": bool(session.get("connect")),
                "has_stop": bool(session.get("stop")),
                "note": "Token-bearing URLs stored at 0600; run `stop` when finished.",
            },
            secrets,
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        secrets = collect_secrets(token, None)
        emit(
            {
                "ok": False,
                "action": "create",
                "session_file": args.session_file,
                "error": sanitize_error(exc, secrets),
            },
            secrets,
        )
        return 1


def cmd_query(args: argparse.Namespace) -> int:
    session: dict[str, Any] | None = None
    secrets: set[str] = set()
    try:
        session = load_session_file(args.session_file)
        warn_if_insecure(args.session_file)
        secrets = collect_secrets(args.token, session)

        browserql = session.get("browserQL")
        if not browserql:
            raise ValueError(
                "Session file has no browserQL URL; cannot run a BQL query."
            )

        query_text = resolve_query(args.query)
        variables: dict[str, Any] = {}
        if args.variables_json:
            variables = json.loads(args.variables_json)
            if not isinstance(variables, dict):
                raise ValueError("--variables-json must be a JSON object.")

        status_code, payload = request_json(
            "POST",
            browserql,
            {"query": query_text, "variables": variables},
            args.timeout,
        )

        errors = payload.get("errors") if isinstance(payload, dict) else None
        ok = 200 <= status_code < 300 and not errors
        emit(
            {
                "ok": ok,
                "action": "query",
                "session_file": args.session_file,
                "session_id": session.get("id"),
                "status_code": status_code,
                "response": payload,
            },
            secrets,
        )
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001
        secrets = secrets or collect_secrets(args.token, session)
        emit(
            {
                "ok": False,
                "action": "query",
                "session_file": args.session_file,
                "session_id": (session or {}).get("id"),
                "error": sanitize_error(exc, secrets),
            },
            secrets,
        )
        return 1


def cmd_stop(args: argparse.Namespace) -> int:
    session: dict[str, Any] | None = None
    secrets: set[str] = set()
    try:
        session = load_session_file(args.session_file)
        secrets = collect_secrets(args.token, session)

        stop_url = session.get("stop")
        if not stop_url:
            raise ValueError(
                "Session file has no stop URL; nothing to delete remotely."
            )

        try:
            status_code, _ = request_json("DELETE", stop_url, None, args.timeout)
            stopped = 200 <= status_code < 300
        except BrowserlessRequestError as exc:
            status_match = re.search(r"HTTP (\d+):", str(exc))
            status_code = int(status_match.group(1)) if status_match else None
            stopped = False
        # A 404 means the session is already gone, so the local file is moot too.
        removable = stopped or status_code == 404

        file_deleted = False
        retained_reason = None
        if args.delete_file:
            if removable:
                try:
                    os.remove(args.session_file)
                    file_deleted = True
                except OSError as remove_exc:
                    retained_reason = sanitize_error(remove_exc, secrets)
            else:
                retained_reason = "remote stop failed; retry stop before deleting"

        result = {
            "ok": stopped,
            "action": "stop",
            "session_file": args.session_file,
            "session_id": session.get("id"),
            "status_code": status_code,
            "stopped": stopped,
            "file_deleted": file_deleted,
        }
        if retained_reason:
            result["file_retained_reason"] = retained_reason
        emit(result, secrets)
        return 0 if stopped else 1
    except Exception as exc:  # noqa: BLE001
        secrets = secrets or collect_secrets(args.token, session)
        emit(
            {
                "ok": False,
                "action": "stop",
                "session_file": args.session_file,
                "session_id": (session or {}).get("id"),
                "error": sanitize_error(exc, secrets),
            },
            secrets,
        )
        return 1


def cmd_inspect(args: argparse.Namespace) -> int:
    session: dict[str, Any] | None = None
    secrets: set[str] = set()
    try:
        session = load_session_file(args.session_file)
        secrets = collect_secrets(args.token, session)
        mode = file_mode(args.session_file)
        emit(
            {
                "ok": True,
                "action": "inspect",
                "session_file": args.session_file,
                "session_id": session.get("id"),
                "has_browserql": bool(session.get("browserQL")),
                "has_connect": bool(session.get("connect")),
                "has_stop": bool(session.get("stop")),
                "file_mode": oct(mode),
                "insecure_permissions": bool(mode & 0o077),
            },
            secrets,
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        secrets = secrets or collect_secrets(args.token, session)
        emit(
            {
                "ok": False,
                "action": "inspect",
                "session_file": args.session_file,
                "error": sanitize_error(exc, secrets),
            },
            secrets,
        )
        return 1


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--session-file",
        required=True,
        help="Path to the local 0600 session file (required; no global default).",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("BROWSERLESS_TOKEN") or os.environ.get("BROWSERLESS_API_KEY"),
        help=(
            "Browserless API token (env BROWSERLESS_TOKEN or BROWSERLESS_API_KEY). Required for create; "
            "query/stop read the token-bearing URL from the session file."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Request timeout in seconds.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser(
        "create", help="Create a persistent Browserless session; store it at 0600."
    )
    add_common(create)
    create.add_argument(
        "--ttl-ms",
        type=int,
        required=True,
        help="Session time-to-live in milliseconds.",
    )
    create.add_argument(
        "--no-stealth",
        dest="stealth",
        action="store_false",
        default=True,
        help="Disable stealth (default: stealth on, required for BQL sessions).",
    )
    create.add_argument(
        "--proxy-json",
        help=(
            "JSON object for the Browserless session proxy config, e.g. "
            '\'{"proxy":"residential","proxySticky":true,"proxyCountry":"us"}\'.'
        ),
    )
    create.add_argument(
        "--process-keep-alive-ms",
        type=int,
        help=(
            "Milliseconds to keep the browser process alive after disconnect. "
            "Must be <= --ttl-ms. Omit unless live in-memory state matters."
        ),
    )
    create.add_argument("--host", default=DEFAULT_HOST, help="Browserless host.")
    create.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing session file (otherwise refuse to clobber).",
    )
    create.set_defaults(func=cmd_create)

    query = sub.add_parser(
        "query", help="Run a BQL query/mutation against the stored session."
    )
    add_common(query)
    query.add_argument(
        "--query",
        required=True,
        help="BQL query string, or a path to a file containing it.",
    )
    query.add_argument(
        "--variables-json",
        help="JSON object of BQL variables.",
    )
    query.set_defaults(func=cmd_query)

    stop = sub.add_parser(
        "stop", help="DELETE the session via its stored stop URL."
    )
    add_common(stop)
    stop.add_argument(
        "--delete-file",
        action="store_true",
        help="Also delete the local session file after a successful stop.",
    )
    stop.set_defaults(func=cmd_stop)

    inspect = sub.add_parser(
        "inspect", help="Print redacted session metadata only (no URLs/token)."
    )
    add_common(inspect)
    inspect.set_defaults(func=cmd_inspect)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
