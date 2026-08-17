#!/usr/bin/env python3
"""Validate source-bound per-request cache telemetry for ClawGauge."""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from pathlib import Path
from typing import Any


SCHEMA = "clawgauge.cache-events.v2"
ALLOWED_HIT_METRICS = {
    "cache_n",
    "cached_input_tokens",
    "prompt_tokens_cached",
    "prompt_tokens_details.cached_tokens",
}
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _integer(value: Any, *, minimum: int = 0) -> int | None:
    parsed = _number(value)
    if parsed is None or not parsed.is_integer() or parsed < minimum:
        return None
    return int(parsed)


def _text(value: Any) -> str | None:
    value = str(value).strip() if value is not None else ""
    return value or None


def _sha256(value: Any) -> str | None:
    value = _text(value)
    return value if value and SHA256_PATTERN.fullmatch(value) else None


def _sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _latency(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"p50": float(statistics.median(values)), "p95": float(_p95(values))}


def _same_number(left: Any, right: Any) -> bool:
    a, b = _number(left), _number(right)
    return a is not None and b is not None and abs(a - b) <= 1e-6


def _bound_artifact(
    proof: Any,
    artifact_root: Path,
    blockers: list[str],
    label: str,
    *,
    require_identity: bool = False,
) -> bool:
    if not isinstance(proof, dict):
        blockers.append(f"{label} provenance is missing")
        return False
    if require_identity and (not _text(proof.get("name")) or not _text(proof.get("version"))):
        blockers.append(f"{label} parser name/version is missing")
        return False
    reference, claimed = _text(proof.get("reference")), _sha256(proof.get("sha256"))
    if not reference or not claimed:
        blockers.append(f"{label} reference/hash is incomplete")
        return False
    relative = Path(reference)
    if relative.is_absolute():
        blockers.append(f"{label} reference must be relative")
        return False
    root = artifact_root.resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        blockers.append(f"{label} reference escapes its artifact root")
        return False
    try:
        raw = path.read_bytes()
    except OSError as exc:
        blockers.append(f"{label} artifact is unreadable: {exc}")
        return False
    if _sha256_bytes(raw) != claimed:
        blockers.append(f"{label} artifact hash mismatch")
        return False
    return True


def load_trace(
    proof: Any, artifact_root: Path | None, blockers: list[str], side: str
) -> dict[str, Any] | None:
    if not isinstance(proof, dict):
        blockers.append(f"{side}: cache trace proof is missing")
        return None
    if proof.get("kind") != "clawgauge-cache-events":
        blockers.append(f"{side}: cache trace proof kind is invalid")
        return None
    reference, claimed = _text(proof.get("reference")), _sha256(proof.get("sha256"))
    if not reference or not claimed:
        blockers.append(f"{side}: cache trace reference/hash is incomplete")
        return None
    if artifact_root is None:
        blockers.append(f"{side}: cache trace artifact root is unavailable")
        return None
    relative = Path(reference)
    if relative.is_absolute():
        blockers.append(f"{side}: cache trace reference must be relative")
        return None
    root = artifact_root.resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        blockers.append(f"{side}: cache trace reference escapes its artifact root")
        return None
    try:
        raw = path.read_bytes()
        trace = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        blockers.append(f"{side}: cache trace artifact is unreadable: {exc}")
        return None
    if _sha256_bytes(raw) != claimed:
        blockers.append(f"{side}: cache trace artifact hash mismatch")
        return None
    if not isinstance(trace, dict) or trace.get("schema_version") != SCHEMA:
        blockers.append(f"{side}: cache trace schema is invalid")
        return None
    source = trace.get("source")
    if not isinstance(source, dict):
        blockers.append(f"{side}: cache trace source provenance is missing")
        return None
    source_ok = all(
        (
            _bound_artifact(
                source.get("runtime_log"), root, blockers, f"{side}: cache runtime log"
            ),
            _bound_artifact(
                source.get("openclaw_trace"), root, blockers, f"{side}: OpenClaw trace"
            ),
            _bound_artifact(
                source.get("parser"),
                root,
                blockers,
                f"{side}: cache parser",
                require_identity=True,
            ),
        )
    )
    if not source_ok:
        return None
    return trace


def _string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    out = [_text(item) for item in value]
    if any(item is None for item in out):
        return None
    return [str(item) for item in out]


def _sha256_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    out = [_sha256(item) for item in value]
    if any(item is None for item in out):
        return None
    return [str(item) for item in out]


def validate_trace(
    trace: dict[str, Any],
    result: dict[str, Any],
    provenance: dict[str, Any],
    cache_fingerprint: str,
    blockers: list[str],
    side: str,
) -> dict[str, Any] | None:
    raw_events = trace.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        blockers.append(f"{side}: cache trace has no events")
        return None
    hit_metric = _text(trace.get("hit_metric"))
    if hit_metric not in ALLOWED_HIT_METRICS:
        blockers.append(f"{side}: cache trace hit_metric is unsupported")
        return None
    route = provenance.get("route", {}).get("observed", {})
    provider, model = route.get("provider"), route.get("model")
    cache = provenance.get("cache", {})
    protocol = cache.get("protocol", {})
    expected_pairs: set[tuple[str, int]] = set()
    for row in result.get("task_results") or []:
        if not isinstance(row, dict) or not _text(row.get("task_id")):
            continue
        runs = _integer(row.get("runs"), minimum=1)
        if runs:
            expected_pairs.update((str(row["task_id"]), rep) for rep in range(1, runs + 1))

    events: list[dict[str, Any]] = []
    seen_requests: set[str] = set()
    seen_turns: set[tuple[str, int, int]] = set()
    seen_openclaw_events: set[str] = set()
    seen_tool_calls: set[str] = set()
    timing_fields = (
        "startup_ms",
        "readiness_ms",
        "ttft_ms",
        "prefill_ms",
        "decode_ms",
        "request_wall_ms",
        "tool_wall_ms",
        "task_wall_ms",
        "task_started_at_ms",
        "request_started_at_ms",
        "first_token_at_ms",
        "request_completed_at_ms",
        "tool_completed_at_ms",
        "task_completed_at_ms",
    )
    memory_fields = (
        "process_rss_bytes",
        "accelerator_active_bytes",
        "accelerator_peak_bytes",
        "cache_resident_bytes",
        "cache_resident_tokens",
        "cache_evictions",
    )
    for index, event in enumerate(raw_events):
        label = f"{side}: cache event {index}"
        if not isinstance(event, dict):
            blockers.append(f"{label} is not an object")
            continue
        task_id = _text(event.get("task_id"))
        repetition = _integer(event.get("repetition"), minimum=1)
        turn_index = _integer(event.get("turn_index"))
        request_id = _text(event.get("request_id"))
        phase = event.get("phase")
        gross = _integer(event.get("gross_input_tokens"))
        cached = _integer(event.get("cached_input_tokens"))
        uncached = _integer(event.get("uncached_input_tokens"))
        written = _integer(event.get("written_input_tokens"))
        lifecycle = (
            _integer(event.get("backend_pid"), minimum=1),
            _text(event.get("backend_started_at")),
            _text(event.get("runtime_id")),
            _text(event.get("cache_epoch")),
        )
        prompt = _sha256(event.get("prompt_fingerprint"))
        prefix = _sha256(event.get("prefix_fingerprint"))
        next_prefix = _sha256(event.get("next_prefix_fingerprint"))
        openclaw_event = _sha256(event.get("openclaw_event_fingerprint"))
        parent_request = _text(event.get("parent_request_id"))
        parent_prompt = _sha256(event.get("parent_prompt_fingerprint"))
        tool_calls = _string_list(event.get("tool_call_ids"))
        tool_results = _sha256_list(event.get("tool_result_fingerprints"))
        timings = {key: _number(event.get(key)) for key in timing_fields}
        memory = {key: _integer(event.get(key), minimum=1 if key == "process_rss_bytes" else 0) for key in memory_fields}
        valid = True
        if None in (task_id, repetition, turn_index, request_id):
            blockers.append(f"{label} identity is incomplete")
            valid = False
        if phase not in {"cold", "warm"}:
            blockers.append(f"{label} phase is invalid")
            valid = False
        if phase == "cold" and cached != 0:
            blockers.append(f"{label} cold request must have zero cached input tokens")
            valid = False
        if None in (gross, cached, uncached, written) or (
            gross is not None
            and cached is not None
            and uncached is not None
            and (cached + uncached != gross or written > gross)
        ):
            blockers.append(f"{label} token accounting is impossible")
            valid = False
        if any(value is None or value < 0 for value in timings.values()):
            blockers.append(f"{label} timing is incomplete or invalid")
            valid = False
        else:
            ts = [
                timings["task_started_at_ms"],
                timings["request_started_at_ms"],
                timings["first_token_at_ms"],
                timings["request_completed_at_ms"],
                timings["tool_completed_at_ms"],
                timings["task_completed_at_ms"],
            ]
            if ts != sorted(ts):
                blockers.append(f"{label} timing timestamps are not monotonic")
                valid = False
            expected_timing = {
                "ttft_ms": timings["first_token_at_ms"] - timings["request_started_at_ms"],
                "decode_ms": timings["request_completed_at_ms"] - timings["first_token_at_ms"],
                "request_wall_ms": timings["request_completed_at_ms"] - timings["request_started_at_ms"],
                "tool_wall_ms": timings["tool_completed_at_ms"] - timings["request_completed_at_ms"],
                "task_wall_ms": timings["task_completed_at_ms"] - timings["task_started_at_ms"],
            }
            if any(not _same_number(timings[key], value) for key, value in expected_timing.items()):
                blockers.append(f"{label} timing durations do not match timestamps")
                valid = False
            if timings["prefill_ms"] > timings["ttft_ms"]:
                blockers.append(f"{label} prefill time exceeds TTFT")
                valid = False
        if any(value is None for value in memory.values()):
            blockers.append(f"{label} memory telemetry is incomplete")
            valid = False
        elif memory["accelerator_active_bytes"] > memory["accelerator_peak_bytes"]:
            blockers.append(f"{label} active accelerator memory exceeds peak")
            valid = False
        if any(item is None for item in lifecycle):
            blockers.append(f"{label} lifecycle identity is incomplete")
            valid = False
        if None in (prompt, prefix, next_prefix, openclaw_event):
            blockers.append(f"{label} content fingerprint is invalid")
            valid = False
        if phase == "cold":
            if parent_request is not None or event.get("parent_prompt_fingerprint") is not None:
                blockers.append(f"{label} cold request cannot claim a parent")
                valid = False
            if event.get("append_only") is not False:
                blockers.append(f"{label} cold request append_only must be false")
                valid = False
        elif phase == "warm":
            if not parent_request or not parent_prompt:
                blockers.append(f"{label} warm request lineage is incomplete")
                valid = False
            if event.get("append_only") is not True:
                blockers.append(f"{label} warm request append_only must be true")
                valid = False
        if tool_calls is None or tool_results is None or len(tool_calls) != len(tool_results):
            blockers.append(f"{label} tool call/result linkage is invalid")
            valid = False
        elif len(set(tool_calls)) != len(tool_calls):
            blockers.append(f"{label} tool call IDs are duplicated")
            valid = False
        if event.get("response_memo_hit") is not False:
            blockers.append(f"{label} full-response memoization hit invalidates the trial")
            valid = False
        if event.get("provider") != provider or event.get("model") != model:
            blockers.append(f"{label} route identity does not match BenchmarkResult")
            valid = False
        if event.get("fallback_used") is not False:
            blockers.append(f"{label} reports fallback use")
            valid = False
        if event.get("cache_configuration_fingerprint") != cache_fingerprint:
            blockers.append(f"{label} cache configuration fingerprint differs")
            valid = False
        if request_id in seen_requests:
            blockers.append(f"{label} request_id is duplicated")
            valid = False
        if openclaw_event in seen_openclaw_events:
            blockers.append(f"{label} OpenClaw event fingerprint is duplicated")
            valid = False
        if task_id is not None and repetition is not None and turn_index is not None:
            turn_key = (task_id, repetition, turn_index)
            if turn_key in seen_turns:
                blockers.append(f"{label} turn identity is duplicated")
                valid = False
            seen_turns.add(turn_key)
        duplicate_tool_calls = set(tool_calls or []) & seen_tool_calls
        if duplicate_tool_calls:
            blockers.append(f"{label} tool call IDs repeat across events")
            valid = False
        seen_tool_calls.update(tool_calls or [])
        if request_id:
            seen_requests.add(request_id)
        if openclaw_event:
            seen_openclaw_events.add(openclaw_event)
        if valid:
            events.append(
                {
                    **event,
                    "task_id": task_id,
                    "repetition": repetition,
                    "turn_index": turn_index,
                    "request_id": request_id,
                    "parent_request_id": parent_request,
                    "parent_prompt_fingerprint": parent_prompt,
                    "prompt_fingerprint": prompt,
                    "prefix_fingerprint": prefix,
                    "next_prefix_fingerprint": next_prefix,
                    "gross_input_tokens": gross,
                    "cached_input_tokens": cached,
                    "uncached_input_tokens": uncached,
                    "written_input_tokens": written,
                    "tool_call_ids": tool_calls,
                    "tool_result_fingerprints": tool_results,
                    "timings": timings,
                    "memory": memory,
                    "lifecycle": lifecycle,
                }
            )
    if len(events) != len(raw_events):
        return None

    observed_pairs = {(e["task_id"], e["repetition"]) for e in events}
    if observed_pairs != expected_pairs:
        blockers.append(f"{side}: cache trace task/repetition coverage differs from BenchmarkResult")
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for event in events:
        grouped.setdefault((event["task_id"], event["repetition"]), []).append(event)
    epochs: list[str] = []
    task_walls: list[float] = []
    for pair, group in grouped.items():
        group.sort(key=lambda item: item["turn_index"])
        turns = [item["turn_index"] for item in group]
        if turns != list(range(len(group))):
            blockers.append(f"{side}: cache trace turns are not contiguous for {pair}")
        phases = [item["phase"] for item in group]
        if phases[0] != "cold" or phases.count("cold") != 1:
            blockers.append(f"{side}: cache trace must have one leading cold event for {pair}")
        if protocol.get("profile") == "controlled-cold-then-warm" and len(group) < 2:
            blockers.append(f"{side}: controlled cache trace lacks a warm event for {pair}")
        lifecycles = {item["lifecycle"] for item in group}
        if len(lifecycles) != 1:
            blockers.append(f"{side}: backend process/cache epoch changed within {pair}")
        else:
            epochs.append(str(group[0]["lifecycle"][3]))
        task_spans = {
            (
                item["timings"]["task_started_at_ms"],
                item["timings"]["task_completed_at_ms"],
                item["timings"]["task_wall_ms"],
            )
            for item in group
        }
        if len(task_spans) != 1:
            blockers.append(f"{side}: task timing changed across turns for {pair}")
        else:
            task_walls.append(float(next(iter(task_spans))[2]))
        prompts = [item["prompt_fingerprint"] for item in group]
        if len(set(prompts)) != len(prompts):
            blockers.append(f"{side}: prompt fingerprint repeats within {pair}")
        for current_index in range(1, len(group)):
            previous, current = group[current_index - 1], group[current_index]
            if current["timings"]["request_started_at_ms"] < previous["timings"]["tool_completed_at_ms"]:
                blockers.append(f"{side}: model/tool turn timing overlaps for {pair}")
            if current["parent_request_id"] != previous["request_id"]:
                blockers.append(f"{side}: warm parent request lineage differs for {pair}")
            if current["parent_prompt_fingerprint"] != previous["prompt_fingerprint"]:
                blockers.append(f"{side}: warm parent prompt lineage differs for {pair}")
            if current["prefix_fingerprint"] != previous["next_prefix_fingerprint"]:
                blockers.append(f"{side}: append-only prefix lineage differs for {pair}")
            if not previous["tool_call_ids"]:
                blockers.append(f"{side}: warm continuation lacks a preceding tool result for {pair}")
        if (
            protocol.get("profile") == "controlled-cold-then-warm"
            and cache.get("runtime", {}).get("kind") == "prefix-kv"
            and cache.get("configuration", {}).get("enabled") is True
            and any(item["cached_input_tokens"] <= 0 for item in group[1:])
        ):
            blockers.append(f"{side}: post-cold cache miss observed for {pair}")
    if protocol.get("reset_between_task_repetitions") is True and len(set(epochs)) != len(epochs):
        blockers.append(f"{side}: cache epoch was reused across reset boundaries")

    cold = [e for e in events if e["phase"] == "cold"]
    warm = [e for e in events if e["phase"] == "warm"]
    hits = [e for e in warm if e["cached_input_tokens"] > 0]
    derived = {
        "request_count": len(events),
        "cold_request_count": len(cold),
        "warm_request_count": len(warm),
        "hit_request_count": len(hits),
        "reused_input_tokens": sum(e["cached_input_tokens"] for e in events),
        "gross_input_tokens": sum(e["gross_input_tokens"] for e in events),
        "response_memo_hit_count": sum(1 for e in events if e["response_memo_hit"] is True),
        "hit_status": "observed" if hits else "none-observed",
        "hit_metric": hit_metric,
        "cold_latency_ms": _latency([e["timings"]["request_wall_ms"] for e in cold]),
        "warm_latency_ms": _latency([e["timings"]["request_wall_ms"] for e in warm]),
        "startup_latency_ms": _latency([e["timings"]["startup_ms"] for e in cold]),
        "readiness_latency_ms": _latency([e["timings"]["readiness_ms"] for e in cold]),
        "ttft_latency_ms": _latency([e["timings"]["ttft_ms"] for e in events]),
        "prefill_latency_ms": _latency([e["timings"]["prefill_ms"] for e in events]),
        "decode_latency_ms": _latency([e["timings"]["decode_ms"] for e in events]),
        "task_latency_ms": _latency(task_walls),
        "hit_rate": len(hits) / len(warm) if warm else 0.0,
        "peak_process_rss_bytes": max(e["memory"]["process_rss_bytes"] for e in events),
        "peak_accelerator_bytes": max(e["memory"]["accelerator_peak_bytes"] for e in events),
        "peak_cache_resident_bytes": max(e["memory"]["cache_resident_bytes"] for e in events),
        "peak_cache_resident_tokens": max(e["memory"]["cache_resident_tokens"] for e in events),
        "cache_evictions": max(e["memory"]["cache_evictions"] for e in events),
    }
    observed = cache.get("observed", {})
    for key in (
        "request_count",
        "cold_request_count",
        "warm_request_count",
        "hit_request_count",
        "reused_input_tokens",
        "gross_input_tokens",
        "response_memo_hit_count",
        "hit_status",
        "hit_metric",
        "peak_process_rss_bytes",
        "peak_accelerator_bytes",
        "peak_cache_resident_bytes",
        "peak_cache_resident_tokens",
        "cache_evictions",
    ):
        if observed.get(key) != derived[key]:
            blockers.append(f"{side}: cache observed.{key} differs from raw trace")
    for key in (
        "cold_latency_ms",
        "warm_latency_ms",
        "startup_latency_ms",
        "readiness_latency_ms",
        "ttft_latency_ms",
        "prefill_latency_ms",
        "decode_latency_ms",
    ):
        claimed, actual = observed.get(key), derived[key]
        if not isinstance(claimed, dict) or actual is None or not all(
            _same_number(claimed.get(metric), actual.get(metric)) for metric in ("p50", "p95")
        ):
            blockers.append(f"{side}: cache observed.{key} differs from raw trace")
    if not _same_number(observed.get("hit_rate"), derived["hit_rate"]):
        blockers.append(f"{side}: cache observed.hit_rate differs from raw trace")
    task_latency = derived["task_latency_ms"] or {}
    if not _same_number(result.get("overall_median_latency_ms"), task_latency.get("p50")):
        blockers.append(f"{side}: BenchmarkResult median latency is not bound to cache trace task walls")
    if not _same_number(result.get("overall_p95_latency_ms"), task_latency.get("p95")):
        blockers.append(f"{side}: BenchmarkResult p95 latency is not bound to cache trace task walls")
    return derived
