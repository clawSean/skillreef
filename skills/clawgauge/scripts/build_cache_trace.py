#!/usr/bin/env python3
"""Build a source-bound ClawGauge cache-event artifact from normalized events."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from cache_trace import ALLOWED_HIT_METRICS, SCHEMA, SHA256_PATTERN


REQUIRED_EVENT_FIELDS = {
    "task_id",
    "repetition",
    "turn_index",
    "request_id",
    "phase",
    "provider",
    "model",
    "fallback_used",
    "backend_pid",
    "backend_started_at",
    "runtime_id",
    "cache_epoch",
    "prompt_fingerprint",
    "prefix_fingerprint",
    "next_prefix_fingerprint",
    "openclaw_event_fingerprint",
    "cache_configuration_fingerprint",
    "gross_input_tokens",
    "cached_input_tokens",
    "uncached_input_tokens",
    "written_input_tokens",
    "response_memo_hit",
    "append_only",
    "tool_call_ids",
    "tool_result_fingerprints",
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
    "process_rss_bytes",
    "accelerator_active_bytes",
    "accelerator_peak_bytes",
    "cache_resident_bytes",
    "cache_resident_tokens",
    "cache_evictions",
}


def source_proof(path: Path, root: Path, *, name: str | None = None, version: str | None = None) -> dict:
    resolved = path.resolve()
    try:
        reference = resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"source artifact must be inside {root}") from exc
    raw = resolved.read_bytes()
    proof = {
        "reference": reference,
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
    }
    if name is not None:
        proof["name"] = name
    if version is not None:
        proof["version"] = version
    return proof


def validate_events(events: list[object]) -> None:
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f"event {index} must be an object")
        missing = sorted(REQUIRED_EVENT_FIELDS - set(event))
        if missing:
            raise ValueError(f"event {index} missing required fields: {missing}")
        for field in (
            "prompt_fingerprint",
            "prefix_fingerprint",
            "next_prefix_fingerprint",
            "openclaw_event_fingerprint",
            "cache_configuration_fingerprint",
        ):
            if not isinstance(event.get(field), str) or not SHA256_PATTERN.fullmatch(event[field]):
                raise ValueError(f"event {index} has invalid {field}")
        if event.get("response_memo_hit") is not False:
            raise ValueError(f"event {index} reports or omits a false response_memo_hit")
        calls, results = event.get("tool_call_ids"), event.get("tool_result_fingerprints")
        if not isinstance(calls, list) or not isinstance(results, list) or len(calls) != len(results):
            raise ValueError(f"event {index} has invalid tool call/result linkage")
        if not all(isinstance(value, str) and value for value in calls):
            raise ValueError(f"event {index} has invalid tool call IDs")
        if not all(isinstance(value, str) and SHA256_PATTERN.fullmatch(value) for value in results):
            raise ValueError(f"event {index} has invalid tool result fingerprints")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="JSON array of per-request events")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--proof-out", type=Path)
    parser.add_argument("--hit-metric", default="cached_input_tokens")
    parser.add_argument("--runtime-log", required=True, type=Path)
    parser.add_argument("--openclaw-trace", required=True, type=Path)
    parser.add_argument("--parser-artifact", required=True, type=Path)
    parser.add_argument("--parser-name", required=True)
    parser.add_argument("--parser-version", required=True)
    args = parser.parse_args()
    try:
        events = json.loads(args.events.read_text(encoding="utf-8"))
        if not isinstance(events, list) or not events:
            raise ValueError("events input must be a non-empty JSON array")
        if args.hit_metric not in ALLOWED_HIT_METRICS:
            raise ValueError(f"unsupported hit metric: {args.hit_metric}")
        validate_events(events)
        artifact_root = args.out.parent.resolve()
        source = {
            "runtime_log": source_proof(args.runtime_log, artifact_root),
            "openclaw_trace": source_proof(args.openclaw_trace, artifact_root),
            "parser": source_proof(
                args.parser_artifact,
                artifact_root,
                name=args.parser_name,
                version=args.parser_version,
            ),
        }
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    artifact = {
        "schema_version": SCHEMA,
        "hit_metric": args.hit_metric,
        "source": source,
        "events": events,
    }
    raw = (json.dumps(artifact, indent=2) + "\n").encode()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(raw)
    proof = {
        "kind": "clawgauge-cache-events",
        "reference": args.out.name,
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
    }
    rendered = json.dumps(proof, indent=2) + "\n"
    if args.proof_out:
        args.proof_out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
