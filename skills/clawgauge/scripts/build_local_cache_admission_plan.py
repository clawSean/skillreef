#!/usr/bin/env python3
"""Build a provider-free, architecture-aware local cache admission plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


FEATURES = {
    "standard-kv",
    "hybrid-recurrent",
    "rotating-or-conv",
    "multimodal",
    "shared-service",
}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
REVISION_RE = re.compile(r"^[A-Za-z0-9._-]{7,128}$")


def parse_version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("--runtime-version must be major.minor.patch")
    return tuple(int(part) for part in match.groups())


def add_case(cases: list[dict], case_id: str, purpose: str, evidence: list[str]) -> None:
    cases.append({"id": case_id, "purpose": purpose, "required_evidence": evidence})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=("mlx-vlm", "mlx-lm"), required=True)
    parser.add_argument("--runtime-version", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--openclaw-commit", required=True)
    parser.add_argument("--cache-layout-fingerprint", required=True)
    parser.add_argument("--feature", action="append", choices=sorted(FEATURES), default=[])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    try:
        runtime_version = parse_version(args.runtime_version)
        if not REVISION_RE.fullmatch(args.model_revision):
            raise ValueError("--model-revision must identify an immutable revision")
        if not REVISION_RE.fullmatch(args.openclaw_commit):
            raise ValueError("--openclaw-commit must identify an immutable revision")
        if not SHA256_RE.fullmatch(args.cache_layout_fingerprint):
            raise ValueError("--cache-layout-fingerprint must be sha256:<64 lowercase hex>")
        if not args.model or len(args.model) > 256 or any(ord(c) < 32 for c in args.model):
            raise ValueError("--model must be printable text <= 256 characters")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    features = sorted(set(args.feature) or {"standard-kv"})
    cases: list[dict] = []
    blockers: list[str] = []
    warnings: list[str] = []

    add_case(cases, "declaration-provenance", "Bind exact route and cache identity.", [
        "requested/observed route", "fallback=false", "runtime/OpenClaw commit",
        "model revision", "template/tool/reasoning settings", "cache layout",
    ])
    add_case(cases, "cold-warm-replay", "Disprove cold reuse and response memoization.", [
        "cold=0", "warm reuse", "replay growth", "fresh replay id",
        "same pid/start/cache epoch", "RSS",
    ])
    add_case(cases, "mutation-matrix", "Prove semantic invalidation.", [
        "system", "tools/order", "reasoning", "template", "revision", "media", "tenant",
    ])
    add_case(cases, "current-openclaw-tool-loop", "Prove realistic continuation.", [
        "2-3 tools", "reasoning history", "no raw tool text", "fallback=false",
    ])
    add_case(cases, "truthfulness-n3", "Block fast but untrustworthy promotion.", [
        "frozen truthfulness", "realistic lane", "n>=3", "worst-of-n",
    ])
    add_case(cases, "memory-lifecycle", "Bound operational risk.", [
        "RSS/pressure/swap", "saturation/eviction", "idle/exit", "route handoff",
    ])

    if {"hybrid-recurrent", "rotating-or-conv"} & set(features):
        add_case(cases, "stateful-branch-replay", "Prove auxiliary-state restoration.", [
            "cold A", "warm A", "branch B", "return A", "fresh cold-A reference",
        ])
    if "multimodal" in features:
        add_case(cases, "media-key-isolation", "Prove media reuse without collision.", [
            "media-A cold/warm", "media-B no collision", "cold-B parity", "media hashes",
        ])
    if "shared-service" in features:
        add_case(cases, "tenant-and-eviction-isolation", "Prove shared boundaries.", [
            "tenant salts", "concurrent prefixes", "no cross-tenant hit", "eviction parity",
        ])

    if args.runtime == "mlx-vlm" and runtime_version < (0, 6, 14):
        blockers.append("mlx-vlm <0.6.14 predates the accepted cache-fix floor")
    if args.runtime == "mlx-lm" and runtime_version <= (0, 31, 3):
        warnings.extend([
            "prompt-cache-bytes is a trim target, not a universal hard cap",
            "nearest-cache reuse may transiently copy cached state",
        ])

    provenance = {
        "runtime": args.runtime,
        "runtime_version": args.runtime_version,
        "model": args.model,
        "model_revision": args.model_revision,
        "openclaw_commit": args.openclaw_commit,
        "cache_layout_fingerprint": args.cache_layout_fingerprint,
        "features": features,
    }
    fingerprint = "sha256:" + hashlib.sha256(
        json.dumps(provenance, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    report = {
        "schema_version": "clawgauge.local-cache-admission-plan.v1",
        "ok_to_execute": not blockers,
        "network_calls_performed": 0,
        "provenance": provenance,
        "plan_fingerprint": fingerprint,
        "cases": cases,
        "blockers": blockers,
        "warnings": warnings,
        "claim_if_all_pass": "cache-qualified",
        "claim_not_granted": ["operator-qualified", "promoted"],
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
