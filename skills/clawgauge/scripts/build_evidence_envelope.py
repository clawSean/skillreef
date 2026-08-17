#!/usr/bin/env python3
"""Build or validate a ClawGauge evidence envelope around ShellBench output.

The ShellBench BenchmarkResult remains byte-for-byte data inside
benchmark_result. All route, cache, judge, pricing, campaign, and release
attestations come from the separate --attestation document; they are never
attributed to upstream ShellBench.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from compare_clawbench_results import SCHEMA, digest, validate_envelope


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return value


def build(source: dict[str, Any], attestation: dict[str, Any]) -> dict[str, Any]:
    provenance = attestation.get("provenance", attestation)
    if not isinstance(provenance, dict):
        raise ValueError("attestation must be a provenance object")
    return {
        "schema_version": SCHEMA,
        "source_artifact": {
            "schema": "shellbench.BenchmarkResult",
            "sha256": digest(source),
        },
        "provenance": provenance,
        "benchmark_result": source,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="raw BenchmarkResult or existing envelope")
    parser.add_argument("--attestation", type=Path, help="explicit ClawGauge provenance JSON")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        source = read_object(args.input)
        if "schema_version" in source and source.get("schema_version") != SCHEMA:
            raise ValueError(f"unsupported envelope schema; expected {SCHEMA}")
        if source.get("schema_version") == SCHEMA:
            if args.attestation:
                raise ValueError("--attestation cannot replace provenance in an existing envelope")
            envelope = source
        else:
            if not args.attestation:
                raise ValueError("raw BenchmarkResult requires --attestation")
            envelope = build(source, read_object(args.attestation))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    artifact_root = (
        args.attestation.parent if args.attestation is not None else args.input.parent
    )
    blockers, _facts = validate_envelope(envelope, "evidence", artifact_root)
    if blockers:
        for blocker in blockers:
            print(f"error: {blocker}", file=sys.stderr)
        return 2
    rendered = json.dumps(envelope, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
