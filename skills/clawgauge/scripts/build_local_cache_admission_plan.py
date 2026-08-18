#!/usr/bin/env python3
"""Build an exact-route, architecture-aware local cache admission plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


PLAN_SCHEMA = "clawgauge.local-cache-admission-plan.v2"
RESULTS_SCHEMA = "clawgauge.local-cache-admission-results.v1"
SCORE_SCHEMA = "clawgauge.local-cache-admission-score.v1"
FEATURES = {
    "standard-kv",
    "hybrid-recurrent",
    "rotating-or-conv",
    "text-only",
    "multimodal",
    "isolated-service",
    "shared-service",
    "serial-service",
    "batched-service",
}
STRUCTURAL_FEATURES = {"standard-kv", "hybrid-recurrent", "rotating-or-conv"}
MODALITY_FEATURES = {"text-only", "multimodal"}
SERVICE_FEATURES = {"isolated-service", "shared-service"}
BATCHING_FEATURES = {"serial-service", "batched-service"}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
REVISION_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


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
    parser.add_argument("--mlx-version", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--loaded-model", required=True)
    parser.add_argument("--model-revision", required=True)
    parser.add_argument("--openclaw-version", required=True)
    parser.add_argument("--openclaw-commit", required=True)
    parser.add_argument("--architecture-fingerprint", required=True)
    parser.add_argument("--template-fingerprint", required=True)
    parser.add_argument("--parser-fingerprint", required=True)
    parser.add_argument("--cache-policy-fingerprint", required=True)
    parser.add_argument("--cache-layout-fingerprint", required=True)
    parser.add_argument("--feature", action="append", choices=sorted(FEATURES), default=[])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    try:
        runtime_version = parse_version(args.runtime_version)
        mlx_version = parse_version(args.mlx_version)
        if not REVISION_RE.fullmatch(args.model_revision):
            raise ValueError("--model-revision must identify an immutable revision")
        if not REVISION_RE.fullmatch(args.openclaw_commit):
            raise ValueError("--openclaw-commit must identify an immutable revision")
        for name in (
            "architecture_fingerprint", "template_fingerprint", "parser_fingerprint",
            "cache_policy_fingerprint", "cache_layout_fingerprint",
        ):
            if not SHA256_RE.fullmatch(getattr(args, name)):
                raise ValueError(f"--{name.replace('_', '-')} must be sha256:<64 lowercase hex>")
        for name in ("provider", "model", "loaded_model", "openclaw_version"):
            value = getattr(args, name)
            if not value or len(value) > 512 or any(ord(c) < 32 for c in value):
                raise ValueError(
                    f"--{name.replace('_', '-')} must be printable text <= 512 characters"
                )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    features = sorted(set(args.feature))
    cases: list[dict] = []
    blockers: list[str] = []
    warnings: list[str] = []

    structural = STRUCTURAL_FEATURES & set(features)
    if len(structural) != 1:
        blockers.append(
            "declare exactly one structural cache feature: standard-kv, "
            "hybrid-recurrent, or rotating-or-conv"
        )
    for label, choices in (
        ("modality", MODALITY_FEATURES),
        ("service scope", SERVICE_FEATURES),
        ("batching mode", BATCHING_FEATURES),
    ):
        if len(choices & set(features)) != 1:
            blockers.append(
                f"declare exactly one {label} feature: {', '.join(sorted(choices))}"
            )

    add_case(cases, "declaration-provenance", "Bind exact service and cache identity.", [
        "requested/observed route", "fallback=false", "runtime/OpenClaw commit",
        "MLX version", "model revision", "architecture manifest",
        "template/parser/cache-policy fingerprints", "cache layout", "runtime epoch",
    ])
    add_case(cases, "cold-warm-replay", "Disprove cold reuse and response memoization.", [
        "cold=0", "warm reuse", "replay growth", "fresh replay id",
        "same pid/start/cache epoch", "RSS",
    ])
    add_case(cases, "mutation-matrix", "Prove semantic invalidation.", [
        "system", "tools/order", "reasoning", "template", "revision", "media", "tenant",
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
            "media-A cold/warm", "media-B no collision", "cold-B parity",
            "same-path changed-content invalidation", "media hashes",
        ])
    if "shared-service" in features:
        add_case(cases, "tenant-and-eviction-isolation", "Prove shared boundaries.", [
            "tenant salts", "concurrent prefixes", "no cross-tenant hit", "eviction parity",
        ])
    if "batched-service" in features:
        add_case(cases, "batch-parity", "Prove row isolation under batched serving.", [
            "single request reference", "short peer batch", "long peer batch",
            "identical target output", "no cross-row state contamination",
        ])

    if mlx_version < (0, 32, 0):
        blockers.append("MLX <0.32.0 is below the supported runtime floor")
    if args.runtime == "mlx-vlm" and runtime_version < (0, 6, 15):
        blockers.append("mlx-vlm <0.6.15 predates the accepted cache-correctness floor")
    if args.runtime == "mlx-vlm" and mlx_version < (0, 32, 1):
        warnings.append(
            "mlx-vlm 0.6.15 was repaired and tested against MLX 0.32.1; "
            "qualify the exact older core pair before promotion"
        )
    if args.runtime == "mlx-lm" and runtime_version <= (0, 31, 3):
        warnings.extend([
            "prompt-cache-bytes is a trim target, not a universal hard cap",
            "nearest-cache reuse may transiently copy cached state",
        ])

    provenance = {
        "runtime": args.runtime,
        "runtime_version": args.runtime_version,
        "mlx_version": args.mlx_version,
        "provider": args.provider,
        "model": args.model,
        "loaded_model": args.loaded_model,
        "model_revision": args.model_revision,
        "openclaw_version": args.openclaw_version,
        "openclaw_commit": args.openclaw_commit,
        "architecture_fingerprint": args.architecture_fingerprint,
        "template_fingerprint": args.template_fingerprint,
        "parser_fingerprint": args.parser_fingerprint,
        "cache_policy_fingerprint": args.cache_policy_fingerprint,
        "cache_layout_fingerprint": args.cache_layout_fingerprint,
        "features": features,
    }
    fingerprint = "sha256:" + hashlib.sha256(
        json.dumps(provenance, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    report = {
        "schema_version": PLAN_SCHEMA,
        "ok_to_execute": not blockers,
        "network_calls_performed": 0,
        "provenance": provenance,
        "plan_fingerprint": fingerprint,
        "cases": cases,
        "blockers": blockers,
        "warnings": warnings,
        "results_schema": RESULTS_SCHEMA,
        "score_schema": SCORE_SCHEMA,
        "claim_if_validated_score_passes": "cache-qualified",
        "claim_not_granted": ["cache-qualified", "operator-qualified", "promoted"],
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
