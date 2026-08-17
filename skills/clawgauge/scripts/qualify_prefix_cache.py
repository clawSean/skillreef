#!/usr/bin/env python3
"""Qualify prefix reuse on an already-running loopback OpenAI-compatible API.

The live path sends a cold canary, an append-only continuation, and an exact
replay of that warm prompt. It fails closed on missing cache, anti-memo, or
lifecycle evidence. ``--plan`` validates inputs and emits the exact protocol
without opening a socket.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPORT_SCHEMA = "clawgauge.prefix-cache-qualification.v2"
PLAN_SCHEMA = "clawgauge.prefix-cache-qualification-plan.v2"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
RUN_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
DISK_CONFIGURATION_KEYS = {
    "disk_bytes",
    "disk_max_bytes",
    "disk_evictions",
    "disk_files",
    "disk_blocks_indexed",
    "disk_exact_indexed",
}


class QualificationError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


DIRECT_OPENER = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    NoRedirect(),
)


def canonical_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def normalize_base_url(raw: str) -> Tuple[str, str]:
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme != "http":
        raise ValueError("--base-url must use http on a loopback address")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("--base-url must not contain credentials")
    if parsed.hostname not in {"127.0.0.1", "::1"}:
        raise ValueError("--base-url must use literal loopback 127.0.0.1 or ::1")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"--base-url has an invalid port: {exc}") from exc
    if port is None:
        raise ValueError("--base-url must include an explicit port")
    if parsed.query or parsed.fragment:
        raise ValueError("--base-url must not contain a query or fragment")
    if parsed.path.rstrip("/") != "/v1":
        raise ValueError("--base-url path must be exactly /v1")
    host = f"[{parsed.hostname}]" if ":" in str(parsed.hostname) else parsed.hostname
    origin = f"http://{host}:{port}"
    return origin + "/v1", origin


def validate_text(value: str, label: str, maximum: int = 256) -> str:
    if not value or len(value) > maximum or any(ord(char) < 32 for char in value):
        raise ValueError(f"{label} must be non-empty printable text <= {maximum} chars")
    return value


def request_json(
    url: str,
    *,
    payload: Optional[Dict[str, Any]] = None,
    method: Optional[str] = None,
    timeout: float,
    tenant: Optional[str] = None,
) -> Dict[str, Any]:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if tenant is not None:
        headers["X-APC-Tenant"] = tenant
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with DIRECT_OPENER.open(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise QualificationError(f"request failed for {url}: {exc}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise QualificationError(f"response exceeded {MAX_RESPONSE_BYTES} bytes for {url}")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QualificationError(f"response was not UTF-8 JSON for {url}: {exc}") from exc
    if not isinstance(value, dict):
        raise QualificationError(f"response was not a JSON object for {url}")
    return value


def _tool_path(name: str, fallbacks: List[str]) -> Optional[str]:
    found = shutil.which(name)
    if found:
        return found
    for candidate in fallbacks:
        if Path(candidate).is_file():
            return candidate
    return None


def process_snapshot(base_url: str) -> Dict[str, Any]:
    parsed = urllib.parse.urlsplit(base_url)
    if not parsed.port:
        raise QualificationError("normalized base URL has no port")
    lsof = _tool_path("lsof", ["/usr/sbin/lsof", "/usr/bin/lsof"])
    ps = _tool_path("ps", ["/bin/ps", "/usr/bin/ps"])
    if not lsof or not ps:
        raise QualificationError("lsof and ps are required for lifecycle qualification")
    try:
        completed = subprocess.run(
            [lsof, "-nP", f"-iTCP:{parsed.port}", "-sTCP:LISTEN", "-t"],
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
        if completed.returncode != 0:
            raise QualificationError(
                f"could not identify listener on port {parsed.port}: {completed.stderr.strip()}"
            )
        pids = sorted({int(value) for value in completed.stdout.split()})
        if len(pids) != 1:
            raise QualificationError(
                f"expected one listener process on port {parsed.port}, observed {pids}"
            )
        pid = pids[0]
        start = subprocess.run(
            [ps, "-p", str(pid), "-o", "lstart="],
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
        rss = subprocess.run(
            [ps, "-p", str(pid), "-o", "rss="],
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
        if start.returncode != 0 or rss.returncode != 0:
            raise QualificationError(f"could not inspect listener process {pid}")
        start_time = start.stdout.strip()
        rss_kib = int(rss.stdout.strip())
        if not start_time or rss_kib <= 0:
            raise QualificationError(f"listener process {pid} has incomplete lifecycle evidence")
        return {"pid": pid, "start_time": start_time, "rss_bytes": rss_kib * 1024}
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        if isinstance(exc, QualificationError):
            raise
        raise QualificationError(f"could not inspect loopback listener: {exc}") from exc


def cached_token_observation(response: Dict[str, Any]) -> Tuple[Optional[int], List[str], List[str]]:
    candidates = [
        ("timings.cache_n", ("timings", "cache_n")),
        (
            "usage.prompt_tokens_details.cached_tokens",
            ("usage", "prompt_tokens_details", "cached_tokens"),
        ),
        (
            "usage.input_tokens_details.cached_tokens",
            ("usage", "input_tokens_details", "cached_tokens"),
        ),
        ("usage.prompt_tokens_cached", ("usage", "prompt_tokens_cached")),
    ]
    observations: List[Tuple[str, int]] = []
    errors: List[str] = []
    for label, path in candidates:
        cursor: Any = response
        found = True
        for key in path:
            if not isinstance(cursor, dict) or key not in cursor:
                found = False
                break
            cursor = cursor[key]
        if not found:
            continue
        if not isinstance(cursor, int) or isinstance(cursor, bool) or cursor < 0:
            errors.append(f"{label} is not a non-negative integer")
            continue
        observations.append((label, cursor))
    if not observations:
        errors.append("cached-token telemetry is missing")
        return None, [], errors
    values = {value for _label, value in observations}
    if len(values) != 1:
        errors.append(f"cached-token telemetry disagrees across sources: {observations}")
        return None, [label for label, _value in observations], errors
    return observations[0][1], [label for label, _value in observations], errors


def response_text(response: Dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        return ""
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        return ""
    return message["content"].strip()


def response_id(response: Dict[str, Any]) -> Optional[str]:
    value = response.get("id")
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 256
        or any(ord(char) < 32 for char in value)
    ):
        return None
    return value


def counter(stats: object, key: str) -> Optional[int]:
    if not isinstance(stats, dict) or stats.get("enabled") is not True:
        return None
    value = stats.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return None
    return value


def delta(before: object, after: object, key: str) -> Optional[int]:
    left, right = counter(before, key), counter(after, key)
    if left is None or right is None or right < left:
        return None
    return right - left


def chat_request(
    base_url: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout: float,
    tenant: Optional[str],
) -> Tuple[Dict[str, Any], float]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 24,
        "enable_thinking": False,
    }
    started = time.monotonic()
    response = request_json(
        base_url + "/chat/completions",
        payload=payload,
        timeout=timeout,
        tenant=tenant,
    )
    return response, time.monotonic() - started


def add_check(report: Dict[str, Any], name: str, passed: bool, failure: str) -> None:
    report["checks"][name] = bool(passed)
    if not passed:
        report["blockers"].append(failure)


def protocol_description(args: argparse.Namespace, run_id: str) -> Dict[str, Any]:
    return {
        "profile": "controlled-cold-append-only-warm-then-exact-replay",
        "runtime": args.runtime,
        "prefix_words": args.prefix_words,
        "minimum_reused_tokens": args.minimum_reused_tokens,
        "run_id": run_id,
        "temperature": 0,
        "max_tokens": 24,
        "thinking": False,
        "cross_task_reuse": False,
        "persistence": "process-memory-only",
        "vlm_reset_before_and_after": args.runtime == "mlx-vlm",
    }


def qualification_report(
    args: argparse.Namespace,
    base_url: str,
    origin: str,
    run_id: str,
) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "ok": False,
        "server": {
            "base_url": base_url,
            "model": args.model,
            "runtime": args.runtime,
            "loopback_only": True,
            "health": None,
            "reset_before": None,
            "reset_after": None,
            "lifecycle": {
                "before": None,
                "after_cold": None,
                "after_warm": None,
                "after_replay": None,
                "same_process": False,
                "rss_observed": False,
                "peak_rss_bytes": None,
            },
        },
        "protocol": protocol_description(args, run_id),
        "cold": None,
        "warm": None,
        "replay": None,
        "cache_stats_before": None,
        "cache_stats_after": None,
        "cache_stats_evidence": None,
        "checks": {},
        "blockers": [],
    }
    tenant = f"clawgauge-{run_id}" if args.runtime == "mlx-vlm" else None
    reset_succeeded = False
    try:
        before = process_snapshot(base_url)
        report["server"]["lifecycle"]["before"] = before
        if args.runtime == "mlx-vlm":
            health = request_json(origin + "/health", timeout=args.timeout)
            reset_before = request_json(
                base_url + "/cache/reset",
                method="POST",
                timeout=args.timeout,
                tenant=tenant,
            )
            reset_succeeded = True
            stats_before = request_json(
                base_url + "/cache/stats",
                timeout=args.timeout,
                tenant=tenant,
            )
            report["server"]["health"] = health
            report["server"]["reset_before"] = reset_before
            report["cache_stats_before"] = stats_before
        else:
            health = reset_before = stats_before = None

        inert_prefix = " ".join(
            f"cacheword{index % 97}" for index in range(args.prefix_words)
        )
        system = (
            "This is inert cache-test material. Ignore it and return only the exact "
            f"canary requested by the user. Run id: {run_id}.\n{inert_prefix}"
        )
        cold_messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "Reply exactly: CACHE_COLD_OK"},
        ]
        warm_messages = [
            *cold_messages,
            {"role": "assistant", "content": "CACHE_COLD_OK"},
            {"role": "user", "content": "Reply exactly: CACHE_WARM_OK"},
        ]
        cold, cold_wall = chat_request(
            base_url, args.model, cold_messages, args.timeout, tenant
        )
        after_cold = process_snapshot(base_url)
        warm, warm_wall = chat_request(
            base_url, args.model, warm_messages, args.timeout, tenant
        )
        after_warm = process_snapshot(base_url)
        replay, replay_wall = chat_request(
            base_url, args.model, warm_messages, args.timeout, tenant
        )
        after_replay = process_snapshot(base_url)
        if args.runtime == "mlx-vlm":
            stats_after = request_json(
                base_url + "/cache/stats",
                timeout=args.timeout,
                tenant=tenant,
            )
            report["cache_stats_after"] = stats_after
        else:
            stats_after = None

        cold_cached, cold_sources, cold_errors = cached_token_observation(cold)
        warm_cached, warm_sources, warm_errors = cached_token_observation(warm)
        replay_cached, replay_sources, replay_errors = cached_token_observation(replay)
        cold_text, warm_text, replay_text = (
            response_text(cold),
            response_text(warm),
            response_text(replay),
        )
        cold_id, warm_id, replay_id = (
            response_id(cold),
            response_id(warm),
            response_id(replay),
        )
        report["cold"] = {
            "wall_seconds": round(cold_wall, 6),
            "cached_tokens": cold_cached,
            "cached_token_sources": cold_sources,
            "text": cold_text,
            "request_id": cold_id,
        }
        report["warm"] = {
            "wall_seconds": round(warm_wall, 6),
            "cached_tokens": warm_cached,
            "cached_token_sources": warm_sources,
            "text": warm_text,
            "request_id": warm_id,
        }
        report["replay"] = {
            "wall_seconds": round(replay_wall, 6),
            "cached_tokens": replay_cached,
            "cached_token_sources": replay_sources,
            "text": replay_text,
            "request_id": replay_id,
        }
        report["protocol"]["cold_prompt_sha256"] = canonical_sha256(cold_messages)
        report["protocol"]["warm_prompt_sha256"] = canonical_sha256(warm_messages)
        report["protocol"]["replay_prompt_sha256"] = canonical_sha256(warm_messages)
        report["protocol"]["append_only_verified"] = (
            warm_messages[: len(cold_messages)] == cold_messages
        )
        lifecycle = report["server"]["lifecycle"]
        lifecycle["after_cold"] = after_cold
        lifecycle["after_warm"] = after_warm
        lifecycle["after_replay"] = after_replay
        snapshots = [before, after_cold, after_warm, after_replay]
        identities = {(item["pid"], item["start_time"]) for item in snapshots}
        lifecycle["same_process"] = len(identities) == 1
        lifecycle["rss_observed"] = all(item["rss_bytes"] > 0 for item in snapshots)
        lifecycle["peak_rss_bytes"] = max(item["rss_bytes"] for item in snapshots)

        add_check(
            report,
            "cold_canary_exact",
            cold_text == "CACHE_COLD_OK",
            "cold response did not match its exact canary",
        )
        add_check(
            report,
            "warm_canary_exact",
            warm_text == "CACHE_WARM_OK",
            "warm response did not match its exact canary",
        )
        add_check(
            report,
            "replay_canary_exact",
            replay_text == "CACHE_WARM_OK",
            "exact warm-prompt replay did not match its canary",
        )
        add_check(
            report,
            "replay_prompt_identical",
            report["protocol"]["replay_prompt_sha256"]
            == report["protocol"]["warm_prompt_sha256"],
            "replay prompt was not byte-canonically identical to the warm prompt",
        )
        add_check(
            report,
            "append_only_continuation",
            report["protocol"]["append_only_verified"] is True,
            "warm prompt was not an append-only continuation",
        )
        add_check(
            report,
            "cold_cached_tokens_zero",
            not cold_errors and cold_cached == 0,
            "; ".join(cold_errors) or "cold cached-token count was not zero",
        )
        add_check(
            report,
            "warm_cached_token_floor",
            not warm_errors
            and warm_cached is not None
            and warm_cached >= args.minimum_reused_tokens,
            "; ".join(warm_errors)
            or f"warm cached-token count was below {args.minimum_reused_tokens}",
        )
        add_check(
            report,
            "replay_cached_token_growth",
            not warm_errors
            and not replay_errors
            and warm_cached is not None
            and replay_cached is not None
            and replay_cached > warm_cached,
            "; ".join(replay_errors)
            or "identical warm replay did not cache more input than the original warm request",
        )
        add_check(
            report,
            "response_memoization_disproved",
            warm_text == "CACHE_WARM_OK"
            and replay_text == "CACHE_WARM_OK"
            and warm_id is not None
            and replay_id is not None
            and replay_id != warm_id
            and not warm_errors
            and not replay_errors
            and warm_cached is not None
            and replay_cached is not None
            and replay_cached > warm_cached,
            "full-response memoization remains plausible: require a fresh replay response "
            "ID and cache-token growth beyond the original warm request",
        )
        add_check(
            report,
            "same_server_process",
            lifecycle["same_process"] is True,
            "listener PID/start time changed during qualification",
        )
        add_check(
            report,
            "rss_observed",
            lifecycle["rss_observed"] is True,
            "listener RSS was missing or invalid",
        )
        if args.max_rss_bytes is not None:
            add_check(
                report,
                "rss_below_limit",
                lifecycle["peak_rss_bytes"] <= args.max_rss_bytes,
                f"listener peak RSS exceeded {args.max_rss_bytes} bytes",
            )

        if args.runtime == "mlx-vlm":
            exact_hit_delta = delta(stats_before, stats_after, "exact_hits")
            exact_store_delta = delta(stats_before, stats_after, "exact_stores")
            disk_hits = counter(stats_after, "disk_hits")
            disk_writes = counter(stats_after, "disk_writes")
            disk_configuration_present = sorted(
                DISK_CONFIGURATION_KEYS.intersection(stats_after)
                if isinstance(stats_after, dict)
                else []
            )
            report["cache_stats_evidence"] = {
                "exact_hit_delta": exact_hit_delta,
                "exact_store_delta": exact_store_delta,
                "disk_hits_after": disk_hits,
                "disk_writes_after": disk_writes,
                "disk_configuration_keys_present": disk_configuration_present,
            }
            add_check(
                report,
                "vlm_apc_health",
                isinstance(health, dict) and health.get("apc_enabled") is True,
                "MLX-VLM health did not report apc_enabled=true",
            )
            add_check(
                report,
                "vlm_reset_before",
                isinstance(reset_before, dict)
                and reset_before.get("enabled") is True
                and reset_before.get("status") == "cleared",
                "MLX-VLM pre-run cache reset was not proven",
            )
            add_check(
                report,
                "vlm_stats_enabled",
                isinstance(stats_before, dict)
                and stats_before.get("enabled") is True
                and isinstance(stats_after, dict)
                and stats_after.get("enabled") is True,
                "MLX-VLM cache stats were missing or disabled",
            )
            add_check(
                report,
                "vlm_exact_hit_delta",
                exact_hit_delta is not None and exact_hit_delta > 0,
                "MLX-VLM exact_hits did not increase",
            )
            add_check(
                report,
                "vlm_exact_store_delta",
                exact_store_delta is not None and exact_store_delta > 0,
                "MLX-VLM exact_stores did not increase",
            )
            add_check(
                report,
                "vlm_no_disk_activity",
                disk_hits == 0 and disk_writes == 0,
                "MLX-VLM disk hit/write counters were missing or nonzero",
            )
            add_check(
                report,
                "vlm_no_disk_configuration",
                not disk_configuration_present,
                "MLX-VLM disk-cache configuration keys were present",
            )
    except (QualificationError, ValueError) as exc:
        report["blockers"].append(str(exc))
    finally:
        if args.runtime == "mlx-vlm" and reset_succeeded:
            try:
                cleanup = request_json(
                    base_url + "/cache/reset",
                    method="POST",
                    timeout=args.timeout,
                    tenant=tenant,
                )
                report["server"]["reset_after"] = cleanup
                add_check(
                    report,
                    "vlm_reset_after",
                    cleanup.get("enabled") is True and cleanup.get("status") == "cleared",
                    "MLX-VLM cleanup cache reset was not proven",
                )
            except QualificationError as exc:
                report["checks"]["vlm_reset_after"] = False
                report["blockers"].append(f"cleanup reset failed: {exc}")
    report["blockers"] = list(dict.fromkeys(report["blockers"]))
    report["ok"] = bool(report["checks"]) and not report["blockers"] and all(
        report["checks"].values()
    )
    if report.get("cold") and report.get("warm"):
        warm_wall = report["warm"]["wall_seconds"]
        report["speedup"] = (
            round(report["cold"]["wall_seconds"] / warm_wall, 6) if warm_wall else None
        )
    else:
        report["speedup"] = None
    return report


def write_report(report: Dict[str, Any], out: Optional[Path]) -> None:
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if out is None:
        sys.stdout.write(rendered)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--runtime", choices=("mlx-vlm", "mlx-lm"), required=True)
    parser.add_argument("--prefix-words", type=int, default=8000)
    parser.add_argument("--minimum-reused-tokens", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--max-rss-bytes", type=int)
    parser.add_argument("--run-id")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        base_url, origin = normalize_base_url(args.base_url)
        args.model = validate_text(args.model, "--model")
        if args.prefix_words < 1:
            raise ValueError("--prefix-words must be >= 1")
        if args.minimum_reused_tokens < 1:
            raise ValueError("--minimum-reused-tokens must be >= 1")
        if args.timeout <= 0:
            raise ValueError("--timeout must be > 0")
        if args.max_rss_bytes is not None and args.max_rss_bytes < 1:
            raise ValueError("--max-rss-bytes must be >= 1")
        run_id = args.run_id or uuid.uuid4().hex
        if not RUN_ID_RE.fullmatch(run_id):
            raise ValueError("--run-id must match [A-Za-z0-9._-]{1,64}")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.plan:
        plan = {
            "schema_version": PLAN_SCHEMA,
            "network_calls_performed": 0,
            "server": {
                "base_url": base_url,
                "model": args.model,
                "runtime": args.runtime,
                "loopback_only": True,
            },
            "protocol": protocol_description(args, run_id),
            "requests": (
                [
                    "GET /health",
                    "POST /v1/cache/reset",
                    "GET /v1/cache/stats",
                    "POST /v1/chat/completions (cold)",
                    "POST /v1/chat/completions (append-only warm)",
                    "POST /v1/chat/completions (exact warm replay)",
                    "GET /v1/cache/stats",
                    "POST /v1/cache/reset (cleanup)",
                ]
                if args.runtime == "mlx-vlm"
                else [
                    "POST /v1/chat/completions (cold)",
                    "POST /v1/chat/completions (append-only warm)",
                    "POST /v1/chat/completions (exact warm replay)",
                ]
            ),
            "gates": [
                "exact cold/warm/replay canaries",
                "cold cached tokens equal zero",
                f"warm cached tokens >= {args.minimum_reused_tokens}",
                "exact warm replay has a fresh response ID and greater cached-token count",
                "same listener PID and start time with RSS captured",
            ]
            + (
                [
                    "APC health enabled",
                    "pre/post reset proven",
                    "stats enabled",
                    "exact hit/store deltas positive",
                    "disk counters zero and disk configuration absent",
                ]
                if args.runtime == "mlx-vlm"
                else []
            ),
        }
        try:
            write_report(plan, args.out)
        except OSError as exc:
            print(f"error: could not write report: {exc}", file=sys.stderr)
            return 2
        return 0
    report = qualification_report(args, base_url, origin, run_id)
    try:
        write_report(report, args.out)
    except OSError as exc:
        print(f"error: could not write report: {exc}", file=sys.stderr)
        return 2
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
