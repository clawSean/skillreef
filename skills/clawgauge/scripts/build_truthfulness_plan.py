#!/usr/bin/env python3
"""Build a content-bound execution plan for the frozen truthfulness suite.

This provider-free planner does not invoke a model.  A harness should execute
each cell exactly as emitted, capture the raw model response and only the actual
fixture-backed events, then write the evidence path declared by the cell.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from score_truthfulness import (
    ATTEMPT_SCHEMA,
    EXECUTION_SCHEMA,
    PLAN_SCHEMA,
    RESULT_SCHEMA,
    cell_digest,
    prepare_suite,
    read_json_object,
    route_digest,
    validate_route,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        type=Path,
        default=Path(__file__).resolve().parent.parent
        / "references"
        / "truthfulness-suite-v1.json",
    )
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument(
        "--route",
        type=Path,
        required=True,
        help="exact requested/observed route JSON with fallback_used=false",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        suite = read_json_object(args.suite)
        route = read_json_object(args.route)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    meta, errors = prepare_suite(suite)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2
    route_errors = validate_route(route)
    if route_errors:
        for error in route_errors:
            print(f"error: {error}", file=sys.stderr)
        return 2
    route_sha256 = route_digest(route)
    minimum = meta["minimum_repetitions"]
    if args.repetitions < minimum:
        print(
            f"error: --repetitions must be >= suite minimum {minimum}",
            file=sys.stderr,
        )
        return 2
    cells = []
    for case in suite["cases"]:
        case_meta = meta["case_map"][case["id"]]
        for repetition in range(1, args.repetitions + 1):
            cells.append(
                {
                    "cell_id": f"{case['id']}/{repetition}",
                    "case_id": case["id"],
                    "repetition": repetition,
                    "cell_sha256": cell_digest(
                        case_meta, repetition, route_sha256
                    ),
                    "case_sha256": case_meta["case_sha256"],
                    "prompt": case["prompt"],
                    "prompt_sha256": case_meta["prompt_sha256"],
                    "fixtures": case["fixtures"],
                    "fixtures_sha256": case_meta["fixtures_sha256"],
                    "route_sha256": route_sha256,
                    "evidence_output": (
                        f"attempts/{case['id']}/{repetition}/evidence.json"
                    ),
                }
            )
    plan = {
        "schema_version": PLAN_SCHEMA,
        "results_schema": RESULT_SCHEMA,
        "attempt_evidence_schema": ATTEMPT_SCHEMA,
        "execution_trace_schema": EXECUTION_SCHEMA,
        "suite_sha256": meta["suite_sha256"],
        "route": route,
        "route_sha256": route_sha256,
        "fallback_proof_required": True,
        "repetitions": args.repetitions,
        "case_count": len(suite["cases"]),
        "expected_cells": len(cells),
        "cells": cells,
    }
    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"error: could not write {args.out}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
