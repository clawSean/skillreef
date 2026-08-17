#!/usr/bin/env python3
"""Estimate campaign wall time from source-bound pilots for each exact route."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path


SCHEMA = "clawgauge.campaign-pilot.v2"
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SURFACES = (
    "startup_ms",
    "task_wall_ms",
    "reset_ms",
    "qa_wall_ms",
    "judge_wall_ms",
)


def samples(data: dict, key: str, *, allow_empty: bool = False) -> list[float]:
    values = data.get(key)
    if not isinstance(values, list) or (not values and not allow_empty):
        qualifier = "an array" if allow_empty else "a non-empty array"
        raise ValueError(f"pilot route {key} must be {qualifier}")
    out = []
    for value in values:
        if isinstance(value, bool):
            raise ValueError(f"pilot route {key} contains a non-number")
        parsed = float(value)
        if not math.isfinite(parsed) or parsed < 0:
            raise ValueError(f"pilot route {key} contains an invalid duration")
        out.append(parsed)
    return out


def p90(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.9 * len(ordered)) - 1)]


def artifact_ok(proof: object, root: Path) -> bool:
    if not isinstance(proof, dict):
        return False
    reference, claimed = proof.get("reference"), proof.get("sha256")
    if not isinstance(reference, str) or not isinstance(claimed, str):
        return False
    if not SHA256_PATTERN.fullmatch(claimed):
        return False
    relative = Path(reference)
    if relative.is_absolute():
        return False
    root = root.resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        return False
    try:
        raw = path.read_bytes()
    except OSError:
        return False
    return claimed == "sha256:" + hashlib.sha256(raw).hexdigest()


def exact_route(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("pilot route identity must be an object")
    required = ("provider", "model", "adapter", "reasoning", "fast")
    if any(not isinstance(value.get(key), (str, bool)) or value.get(key) == "" for key in required):
        raise ValueError("pilot exact route identity is incomplete")
    fingerprint = value.get("cache_configuration_fingerprint")
    if not isinstance(fingerprint, str) or not SHA256_PATTERN.fullmatch(fingerprint):
        raise ValueError("pilot route cache configuration fingerprint is invalid")
    return {key: value.get(key) for key in (*required, "cache_configuration_fingerprint")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path)
    parser.add_argument("--cache-profile", required=True)
    parser.add_argument("--tasks", type=int, required=True)
    parser.add_argument("--repetitions", type=int, required=True)
    parser.add_argument("--qa-scenarios", type=int, default=10)
    parser.add_argument("--judge-calls", type=int, default=0)
    parser.add_argument("--execution-mode", choices=("serial", "parallel"), default="serial")
    parser.add_argument("--budget-hours", type=float)
    parser.add_argument("--json", dest="json_out", type=Path)
    args = parser.parse_args()
    try:
        pilot = json.loads(args.pilot.read_text(encoding="utf-8"))
        if pilot.get("schema_version") != SCHEMA:
            raise ValueError(f"pilot schema must be {SCHEMA}")
        if pilot.get("cache_profile") != args.cache_profile:
            raise ValueError("pilot cache profile does not match target campaign")
        raw_routes = pilot.get("routes")
        if not isinstance(raw_routes, list) or not raw_routes:
            raise ValueError("pilot routes must be a non-empty array")
        if min(args.tasks, args.repetitions) < 1:
            raise ValueError("tasks and repetitions must be positive")
        if min(args.qa_scenarios, args.judge_calls) < 0:
            raise ValueError("QA scenarios and judge calls cannot be negative")
        if args.budget_hours is not None and args.budget_hours < 0:
            raise ValueError("budget hours cannot be negative")
        parsed_routes = []
        seen_routes = set()
        for index, raw_route in enumerate(raw_routes):
            if not isinstance(raw_route, dict):
                raise ValueError(f"pilot route {index} must be an object")
            route = exact_route(raw_route.get("route"))
            route_key = json.dumps(route, sort_keys=True, separators=(",", ":"))
            if route_key in seen_routes:
                raise ValueError("pilot exact route identities must be unique")
            seen_routes.add(route_key)
            if raw_route.get("cache_profile") != args.cache_profile:
                raise ValueError(f"pilot route {index} cache profile does not match")
            if not artifact_ok(raw_route.get("cache_trace_proof"), args.pilot.parent):
                raise ValueError(f"pilot route {index} cache trace proof is invalid")
            retry_rate = float(raw_route.get("retry_rate", 0))
            if not 0 <= retry_rate < 1:
                raise ValueError(f"pilot route {index} retry_rate must be in [0,1)")
            surfaces = {
                key: samples(
                    raw_route,
                    key,
                    allow_empty=(key == "judge_wall_ms" and args.judge_calls == 0),
                )
                for key in SURFACES
            }
            parsed_routes.append((route, retry_rate, surfaces))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    task_runs = args.tasks * args.repetitions
    reset_count = task_runs if args.cache_profile == "controlled-cold-then-warm" else 0
    qa_runs = args.qa_scenarios * args.repetitions
    counts = {
        "startup_ms": 1,
        "task_wall_ms": task_runs,
        "reset_ms": reset_count,
        "qa_wall_ms": qa_runs,
        "judge_wall_ms": args.judge_calls,
    }
    route_reports = []
    for route, retry_rate, surfaces in parsed_routes:
        expected_ms = sum(
            (statistics.median(surfaces[key]) if surfaces[key] else 0) * counts[key]
            for key in counts
        )
        p90_ms = sum(
            (p90(surfaces[key]) if surfaces[key] else 0) * counts[key]
            for key in counts
        )
        expected_ms *= 1 + retry_rate
        p90_ms *= 1 + min(0.5, max(retry_rate * 2, retry_rate + 0.05))
        route_reports.append(
            {
                "route": route,
                "retry_rate": retry_rate,
                "counts": counts,
                "expected_ms": round(expected_ms),
                "p90_ms": round(p90_ms),
                "expected_hours": round(expected_ms / 3_600_000, 3),
                "p90_hours": round(p90_ms / 3_600_000, 3),
            }
        )
    if args.execution_mode == "serial":
        expected_ms = sum(item["expected_ms"] for item in route_reports)
        p90_ms = sum(item["p90_ms"] for item in route_reports)
    else:
        expected_ms = max(item["expected_ms"] for item in route_reports)
        p90_ms = max(item["p90_ms"] for item in route_reports)
    budget_ms = args.budget_hours * 3_600_000 if args.budget_hours is not None else None
    within_budget = budget_ms is None or p90_ms <= budget_ms
    report = {
        "schema_version": "clawgauge.campaign-estimate.v2",
        "cache_profile": args.cache_profile,
        "execution_mode": args.execution_mode,
        "route_count": len(route_reports),
        "routes": route_reports,
        "expected_ms": round(expected_ms),
        "p90_ms": round(p90_ms),
        "expected_hours": round(expected_ms / 3_600_000, 3),
        "p90_hours": round(p90_ms / 3_600_000, 3),
        "budget_hours": args.budget_hours,
        "within_budget": within_budget,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if within_budget else 2


if __name__ == "__main__":
    raise SystemExit(main())
