#!/usr/bin/env python3
"""Compare two versioned ClawGauge ShellBench evidence envelopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from cache_trace import ALLOWED_HIT_METRICS, load_trace, validate_trace

SCHEMA = "clawgauge.evidence.v3"
CORE19_TASK_IDS_FINGERPRINT = (
    "sha256:5c19c73824478c6890b46e09fe74530ed393991e0ea02a83fe973fdba24509ea"
)
CORE = (
    "overall_score", "overall_completion", "overall_trajectory",
    "overall_behavior", "overall_reliability", "overall_pass_hat_k",
    "overall_worst_of_n", "overall_ci_lower", "overall_ci_upper",
)
METRICS = (
    ("overall_score", "Overall score", "score"),
    ("overall_ci_lower", "Score CI lower", "score"),
    ("overall_ci_upper", "Score CI upper", "score"),
    ("overall_completion", "Completion", "score"),
    ("overall_trajectory", "Trajectory", "score"),
    ("overall_behavior", "Behavior", "score"),
    ("overall_reliability", "Reliability", "score"),
    ("overall_pass_hat_k", "pass^k", "pct"),
    ("overall_worst_of_n", "Worst-of-n", "score"),
    ("overall_median_latency_ms", "Median latency", "ms"),
    ("overall_p95_latency_ms", "p95 latency", "ms"),
    ("overall_tokens_per_pass", "Tokens/pass", "count"),
    ("overall_cost_usd", "Mean cost USD", "money"),
    ("overall_cost_per_pass", "Cost/pass USD", "money"),
)
OBJECTIVES = {
    "quality": ("overall_score", "high"),
    "reliability": ("overall_reliability", "high"),
    "speed": ("overall_median_latency_ms", "low"),
    "value": ("overall_cost_per_pass", "low"),
}
PAIR_PATHS = (
    ("openclaw", "commit"), ("shellbench", "commit"), ("host", "class"),
    ("campaign", "id"), ("campaign", "window_start"), ("campaign", "window_end"),
    ("campaign", "concurrency"), ("campaign", "model_order"),
    ("campaign", "retry_policy"), ("campaign", "exclusion_policy"),
    ("protocol", "environment_fingerprint"),
    ("protocol", "task_snapshot_fingerprint"), ("protocol", "adapter"),
    ("protocol", "prompt_variant"), ("protocol", "harness_profile"),
    ("protocol", "tool_profile_fingerprint"), ("judge", "requested"),
    ("judge", "observed"), ("judge", "affects_score"),
    ("release", "id"), ("release", "task_ids_fingerprint"),
    ("release", "full_release_task_count"), ("release", "complete"),
)
PRICING_RATE_KEYS = (
    "input_per_million",
    "cached_input_per_million",
    "output_per_million",
    "reasoning_per_million",
)
CACHE_PROFILES = {
    "route-native",
    "controlled-cold-then-warm",
    "cold-only",
}
CACHE_KINDS = {
    "prefix-kv",
    "residency-only",
    "full-response-memoization",
    "embedding-result",
    "opaque-provider-managed",
}
ROUTING_MODES = {"direct", "router", "mixed"}
CLAIM_SCOPES = {"route-operational", "model-isolation", "cache-ablation"}
CACHE_PROTOCOL_FIELDS = (
    "profile",
    "reset_between_task_repetitions",
    "within_task_reuse",
    "cross_task_reuse",
)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return value


def number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def text(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def get(mapping: dict[str, Any], *path: str) -> Any:
    value: Any = mapping
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def proof(value: Any) -> bool:
    return isinstance(value, dict) and bool(text(value.get("kind"))) and bool(text(value.get("reference")))


def sha256_text(value: Any) -> str | None:
    candidate = text(value)
    if not candidate or len(candidate) != 71 or not candidate.startswith("sha256:"):
        return None
    try:
        int(candidate[7:], 16)
    except ValueError:
        return None
    return candidate


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()


def truth_route(prov: dict[str, Any]) -> dict[str, Any]:
    requested = get(prov, "route", "requested")
    observed = get(prov, "route", "observed")
    adapter = get(prov, "protocol", "adapter")
    if not isinstance(requested, dict) or not isinstance(observed, dict):
        return {}
    return {
        "requested": {
            "provider": requested.get("provider"),
            "model": requested.get("model"),
            "adapter": adapter,
            "reasoning": requested.get("reasoning"),
            "fast": requested.get("fast"),
        },
        "observed": {
            "provider": observed.get("provider"),
            "model": observed.get("model"),
            "adapter": adapter,
            "reasoning": observed.get("reasoning"),
            "fast": observed.get("fast"),
        },
        "fallback_used": get(prov, "route", "fallback_used"),
    }


def load_bound_truth_score(
    proof_value: Any,
    artifact_root: Path | None,
    blockers: list[str],
    side: str,
) -> dict[str, Any] | None:
    label = f"{side}: truthfulness score"
    if not isinstance(proof_value, dict):
        blockers.append(f"{label} proof is missing")
        return None
    if proof_value.get("kind") != "clawgauge-truthfulness-score":
        blockers.append(f"{label} proof kind is invalid")
    reference = text(proof_value.get("reference"))
    claimed = sha256_text(proof_value.get("sha256"))
    if not reference or not claimed:
        blockers.append(f"{label} proof reference/hash is incomplete")
        return None
    if artifact_root is None:
        blockers.append(f"{label} artifact root is unavailable")
        return None
    relative = Path(reference)
    if relative.is_absolute() or ".." in relative.parts:
        blockers.append(f"{label} reference must be a safe relative path")
        return None
    root = artifact_root.resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        blockers.append(f"{label} reference escapes its artifact root")
        return None
    try:
        raw = path.read_bytes()
        score = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        blockers.append(f"{label} artifact is unreadable: {exc}")
        return None
    actual = "sha256:" + hashlib.sha256(raw).hexdigest()
    if actual != claimed:
        blockers.append(f"{label} artifact hash mismatch")
        return None
    if not isinstance(score, dict):
        blockers.append(f"{label} artifact is not a JSON object")
        return None
    return score


def validate_truthfulness(
    blockers: list[str],
    side: str,
    prov: dict[str, Any],
    artifact_root: Path | None,
) -> dict[str, Any]:
    attestation = prov.get("truthfulness")
    if attestation is None:
        return {"available": False, "valid": False, "passed": False}
    start = len(blockers)
    if not isinstance(attestation, dict):
        blockers.append(f"{side}: provenance.truthfulness must be an object")
        return {"available": True, "valid": False, "passed": False}
    score = load_bound_truth_score(
        attestation.get("score_proof"), artifact_root, blockers, side
    )
    expected_route = truth_route(prov)
    expected_route_sha = digest(expected_route)
    if score is not None:
        if score.get("schema_version") != "clawgauge.truthfulness-score.v1":
            blockers.append(f"{side}: truthfulness score schema is invalid")
        if score.get("passed") is not True:
            blockers.append(f"{side}: truthfulness deterministic gate did not pass")
        if score.get("execution_attribution_complete") is not True:
            blockers.append(f"{side}: truthfulness execution attribution is incomplete")
        if score.get("route") != expected_route or score.get("route_sha256") != expected_route_sha:
            blockers.append(f"{side}: truthfulness score route differs from envelope route")
        expected_cells = count(score.get("expected_cells"))
        traces = count(score.get("execution_trace_count"))
        if expected_cells is None or traces != expected_cells:
            blockers.append(f"{side}: truthfulness execution trace coverage is incomplete")
        if score.get("blockers") != [] or score.get("deterministic_failures") != []:
            blockers.append(f"{side}: truthfulness score contains blockers or failures")
        if score.get("judge_scores_affect_pass") is not False:
            blockers.append(f"{side}: truthfulness judge policy is not deterministic-only")
        for key in (
            "suite_sha256",
            "route_sha256",
            "plan_sha256",
        ):
            if sha256_text(score.get(key)) is None:
                blockers.append(f"{side}: truthfulness score {key} is invalid")
        for key in ("repetitions", "case_count", "expected_cells"):
            if count(score.get(key)) is None:
                blockers.append(f"{side}: truthfulness score {key} is invalid")
        fields = (
            "passed",
            "suite_sha256",
            "route_sha256",
            "repetitions",
            "case_count",
            "expected_cells",
        )
        for key in fields:
            if attestation.get(key) != score.get(key):
                blockers.append(
                    f"{side}: provenance.truthfulness.{key} differs from its score"
                )
    valid = len(blockers) == start and score is not None
    return {
        "available": True,
        "valid": valid,
        "passed": valid and score.get("passed") is True if score else False,
        "suite_sha256": score.get("suite_sha256") if score else None,
        "route_sha256": score.get("route_sha256") if score else None,
        "repetitions": count(score.get("repetitions")) if score else None,
        "case_count": count(score.get("case_count")) if score else None,
        "expected_cells": count(score.get("expected_cells")) if score else None,
    }


def ids_digest(ids: list[str]) -> str:
    return "sha256:" + hashlib.sha256(("\n".join(sorted(ids)) + "\n").encode()).hexdigest()


def result_of(envelope: dict[str, Any]) -> dict[str, Any]:
    value = envelope.get("benchmark_result")
    return value if isinstance(value, dict) else {}


def provenance_of(envelope: dict[str, Any]) -> dict[str, Any]:
    value = envelope.get("provenance")
    return value if isinstance(value, dict) else {}


def cache_config_payload(cache: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical, proof-free cache configuration identity."""
    runtime = cache.get("runtime") if isinstance(cache.get("runtime"), dict) else {}
    config = cache.get("configuration") if isinstance(cache.get("configuration"), dict) else {}
    capacity = config.get("capacity") if isinstance(config.get("capacity"), dict) else {}
    raw_layers = cache.get("layers") if isinstance(cache.get("layers"), list) else []
    layers = [
        {
            "kind": layer.get("kind"),
            "enabled": layer.get("enabled"),
            "name": layer.get("name"),
            "version": layer.get("version"),
            "engine": layer.get("engine"),
        }
        for layer in raw_layers
        if isinstance(layer, dict)
    ]
    return {
        "runtime": {
            "visibility": runtime.get("visibility"),
            "kind": runtime.get("kind"),
            "name": runtime.get("name"),
            "version": runtime.get("version"),
            "engine": runtime.get("engine"),
        },
        "enabled": config.get("enabled"),
        "persistence": config.get("persistence"),
        "effective_knobs": config.get("effective_knobs"),
        "capacity": {
            "visibility": capacity.get("visibility"),
            "limits": capacity.get("limits"),
        },
        "layers": sorted(layers, key=lambda layer: str(layer.get("kind"))),
    }


def cache_of(prov: dict[str, Any]) -> dict[str, Any]:
    value = prov.get("cache")
    return value if isinstance(value, dict) else {}


def count(value: Any) -> int | None:
    parsed = number(value)
    if parsed is None or parsed < 0 or not parsed.is_integer():
        return None
    return int(parsed)


def valid_effective_knobs(value: Any) -> bool:
    """Require a non-empty, finite, canonical JSON object for effective cache knobs."""
    if not isinstance(value, dict) or not value:
        return False

    def valid(item: Any) -> bool:
        if item is None or isinstance(item, (str, bool, int)):
            return True
        if isinstance(item, float):
            return math.isfinite(item)
        if isinstance(item, list):
            return all(valid(child) for child in item)
        if isinstance(item, dict):
            return all(isinstance(key, str) and bool(key.strip()) and valid(child) for key, child in item.items())
        return False

    return valid(value)


def validate_latency(
    blockers: list[str], side: str, label: str, value: Any, request_count: int | None,
) -> dict[str, float] | None:
    if request_count == 0:
        if value is not None:
            blockers.append(f"{side}: cache {label} latency must be null when there are no {label} requests")
        return None
    if not isinstance(value, dict):
        blockers.append(f"{side}: missing cache {label} latency evidence")
        return None
    p50, p95 = number(value.get("p50")), number(value.get("p95"))
    if p50 is None or p95 is None or p50 < 0 or p95 < p50:
        blockers.append(f"{side}: invalid cache {label} p50/p95 latency evidence")
        return None
    return {"p50": p50, "p95": p95}


def validate_cache(
    blockers: list[str],
    side: str,
    prov: dict[str, Any],
    result: dict[str, Any],
    artifact_root: Path | None,
    claim_scope: str | None,
) -> dict[str, Any]:
    """Validate route-specific cache identity and normalized cache treatment."""
    start = len(blockers)
    cache = cache_of(prov)
    if not cache:
        blockers.append(f"{side}: missing provenance.cache")
        return {"valid": False, "speed_usable": False}

    runtime = cache.get("runtime")
    if not isinstance(runtime, dict):
        blockers.append(f"{side}: missing provenance.cache.runtime")
        runtime = {}
    runtime_visibility = runtime.get("visibility")
    runtime_kind = runtime.get("kind")
    if runtime_visibility not in {"known", "opaque"}:
        blockers.append(f"{side}: cache runtime visibility must be known or opaque")
    if runtime_kind not in CACHE_KINDS:
        blockers.append(f"{side}: cache runtime kind must be one of {sorted(CACHE_KINDS)}")
    if runtime_visibility == "opaque" and runtime_kind != "opaque-provider-managed":
        blockers.append(f"{side}: opaque cache runtime must use kind opaque-provider-managed")
    if runtime_kind == "opaque-provider-managed" and runtime_visibility != "opaque":
        blockers.append(f"{side}: opaque-provider-managed cache kind requires opaque runtime visibility")
    for key in ("name", "engine"):
        if not text(runtime.get(key)):
            blockers.append(f"{side}: missing provenance.cache.runtime.{key}")
    if runtime_visibility == "known" and not text(runtime.get("version")):
        blockers.append(f"{side}: known cache runtime requires a version")
    if runtime_visibility == "opaque":
        if runtime.get("version") is not None:
            blockers.append(f"{side}: opaque cache runtime version must be null")
        if not proof(runtime.get("proof")):
            blockers.append(f"{side}: opaque cache runtime requires a proof")

    raw_layers = cache.get("layers")
    layers: list[dict[str, Any]] = []
    if not isinstance(raw_layers, list) or not raw_layers:
        blockers.append(f"{side}: cache layers are missing")
        raw_layers = []
    seen_layer_kinds: set[str] = set()
    for index, layer in enumerate(raw_layers):
        label = f"{side}: cache layer {index}"
        if not isinstance(layer, dict):
            blockers.append(f"{label} is not an object")
            continue
        kind = layer.get("kind")
        if kind not in CACHE_KINDS:
            blockers.append(f"{label} kind is invalid")
        elif kind in seen_layer_kinds:
            blockers.append(f"{label} kind is duplicated")
        else:
            seen_layer_kinds.add(kind)
        if not isinstance(layer.get("enabled"), bool):
            blockers.append(f"{label} enabled state must be boolean")
        for key in ("name", "version", "engine"):
            if not text(layer.get(key)):
                blockers.append(f"{label} {key} is missing")
        layers.append({
            "kind": kind,
            "enabled": layer.get("enabled"),
            "name": layer.get("name"),
            "version": layer.get("version"),
            "engine": layer.get("engine"),
        })
    memo_layers = [layer for layer in layers if layer.get("kind") == "full-response-memoization"]
    if len(memo_layers) != 1:
        blockers.append(f"{side}: exactly one explicit full-response memoization layer is required")
    memo_enabled = bool(memo_layers and memo_layers[0].get("enabled") is True)

    config = cache.get("configuration")
    if not isinstance(config, dict):
        blockers.append(f"{side}: missing provenance.cache.configuration")
        config = {}
    enabled = config.get("enabled")
    if not isinstance(enabled, bool):
        blockers.append(f"{side}: cache enabled state must be boolean")
    if not text(config.get("persistence")):
        blockers.append(f"{side}: missing cache persistence scope")
    if not proof(config.get("proof")):
        blockers.append(f"{side}: cache configuration proof is missing")
    if not valid_effective_knobs(config.get("effective_knobs")):
        blockers.append(f"{side}: effective cache knobs must be a non-empty canonical JSON object")

    capacity = config.get("capacity")
    if not isinstance(capacity, dict):
        blockers.append(f"{side}: missing cache capacity")
        capacity = {}
    capacity_visibility = capacity.get("visibility")
    limits = capacity.get("limits")
    if capacity_visibility not in {"known", "opaque", "not-applicable"}:
        blockers.append(f"{side}: invalid cache capacity visibility")
    if not isinstance(limits, dict):
        blockers.append(f"{side}: cache capacity limits must be an object")
        limits = {}
    bad_limits = [
        str(key) for key, value in limits.items()
        if not text(key) or count(value) is None
    ]
    if bad_limits:
        blockers.append(f"{side}: invalid cache capacity limits: {sorted(bad_limits)}")
    if enabled is True and capacity_visibility == "known" and not limits:
        blockers.append(f"{side}: enabled known cache requires at least one capacity limit")
    if capacity_visibility == "opaque":
        if limits:
            blockers.append(f"{side}: opaque cache capacity cannot claim numeric limits")
        if not proof(capacity.get("proof")):
            blockers.append(f"{side}: opaque cache capacity requires a proof")
    if capacity_visibility == "not-applicable" and (enabled is not False or limits):
        blockers.append(f"{side}: not-applicable cache capacity is valid only when cache is disabled")
    if enabled is False and capacity_visibility != "not-applicable":
        blockers.append(f"{side}: disabled cache must use not-applicable capacity")
    primary_layers = [layer for layer in layers if layer.get("kind") == runtime_kind]
    if len(primary_layers) != 1:
        blockers.append(f"{side}: cache runtime kind must match exactly one declared layer")
    elif primary_layers[0].get("enabled") is not enabled:
        blockers.append(f"{side}: primary cache layer enabled state differs from configuration")

    claimed_fingerprint = text(config.get("fingerprint"))
    actual_fingerprint = digest(cache_config_payload(cache))
    if claimed_fingerprint != actual_fingerprint:
        blockers.append(f"{side}: cache configuration fingerprint mismatch")

    protocol = cache.get("protocol")
    if not isinstance(protocol, dict):
        blockers.append(f"{side}: missing provenance.cache.protocol")
        protocol = {}
    profile = protocol.get("profile")
    if profile not in CACHE_PROFILES:
        blockers.append(f"{side}: unsupported cache protocol profile")
    for key in CACHE_PROTOCOL_FIELDS[1:]:
        if not isinstance(protocol.get(key), bool):
            blockers.append(f"{side}: cache protocol {key} must be boolean")
    reset = protocol.get("reset_between_task_repetitions")
    within = protocol.get("within_task_reuse")
    cross = protocol.get("cross_task_reuse")
    if profile == "controlled-cold-then-warm" and (reset is not True or within is not True or cross is not False):
        blockers.append(f"{side}: controlled-cold-then-warm cache protocol is inconsistent")
    if profile == "cold-only" and (reset is not True or within is not False or cross is not False):
        blockers.append(f"{side}: cold-only cache protocol is inconsistent")

    lifecycle = cache.get("lifecycle")
    if not isinstance(lifecycle, dict):
        blockers.append(f"{side}: missing provenance.cache.lifecycle")
        lifecycle = {}
    for key in ("server_scope", "reset_mechanism", "reuse_scope"):
        if not text(lifecycle.get(key)):
            blockers.append(f"{side}: missing provenance.cache.lifecycle.{key}")
    reuse_scope = lifecycle.get("reuse_scope")
    if reuse_scope not in {"none", "within-task", "campaign", "provider-managed"}:
        blockers.append(f"{side}: invalid cache lifecycle reuse_scope")
    if lifecycle.get("stability_verified") is not True or not proof(lifecycle.get("stability_proof")):
        blockers.append(f"{side}: cache lifecycle stability is not proven")
    if reset is True and lifecycle.get("reset_mechanism") == "none":
        blockers.append(f"{side}: cache reset policy contradicts lifecycle reset mechanism")
    if within is True and reuse_scope not in {"within-task", "campaign", "provider-managed"}:
        blockers.append(f"{side}: within-task cache reuse contradicts lifecycle reuse_scope")
    if within is False and reuse_scope == "within-task":
        blockers.append(f"{side}: disabled within-task reuse contradicts lifecycle reuse_scope")
    if cross is False and reuse_scope == "campaign":
        blockers.append(f"{side}: disabled cross-task reuse contradicts lifecycle reuse_scope")

    observed = cache.get("observed")
    if not isinstance(observed, dict):
        blockers.append(f"{side}: missing provenance.cache.observed")
        observed = {}
    if observed.get("configuration_fingerprint") != actual_fingerprint:
        blockers.append(f"{side}: observed cache configuration fingerprint mismatch")
    request_count = count(observed.get("request_count"))
    cold_count = count(observed.get("cold_request_count"))
    warm_count = count(observed.get("warm_request_count"))
    for label, value in (("request", request_count), ("cold request", cold_count), ("warm request", warm_count)):
        if value is None:
            blockers.append(f"{side}: invalid cache {label} count")
    if request_count == 0:
        blockers.append(f"{side}: cache request_count must be positive")
    if None not in (request_count, cold_count, warm_count) and cold_count + warm_count != request_count:
        blockers.append(f"{side}: cold and warm cache request counts do not equal request_count")

    hit_status = observed.get("hit_status")
    if hit_status not in {"observed", "none-observed", "unavailable"}:
        blockers.append(f"{side}: invalid cache hit evidence status")
    hit_count, reused_tokens = count(observed.get("hit_request_count")), count(observed.get("reused_input_tokens"))
    if hit_status == "unavailable":
        if observed.get("hit_request_count") is not None or observed.get("reused_input_tokens") is not None or observed.get("hit_metric") is not None:
            blockers.append(f"{side}: unavailable cache hit evidence cannot claim counters")
    else:
        if hit_count is None or reused_tokens is None or observed.get("hit_metric") not in ALLOWED_HIT_METRICS:
            blockers.append(f"{side}: cache hit counters and metric are incomplete")
        if hit_count is not None and warm_count is not None and hit_count > warm_count:
            blockers.append(f"{side}: cache hit count exceeds warm request count")
        if hit_status == "observed" and hit_count == 0:
            blockers.append(f"{side}: observed cache hits require a nonzero hit count")
        if hit_status == "observed" and runtime_kind == "prefix-kv" and reused_tokens == 0:
            blockers.append(f"{side}: observed prefix/KV cache hits require nonzero reused input tokens")
        if hit_status == "none-observed" and (hit_count != 0 or reused_tokens != 0):
            blockers.append(f"{side}: none-observed cache evidence requires zero hit counters")
    if not proof(observed.get("hit_proof")):
        blockers.append(f"{side}: cache hit evidence proof is missing")
    if enabled is False and hit_status != "none-observed":
        blockers.append(f"{side}: disabled cache cannot report observed or unavailable hits")
    response_memo_hits = count(observed.get("response_memo_hit_count"))
    if response_memo_hits is None:
        blockers.append(f"{side}: response memoization hit count is missing or invalid")
    elif response_memo_hits != 0:
        blockers.append(f"{side}: full-response memoization hit invalidates repeated agent quality/trust evidence")
    if runtime_kind == "residency-only" and (
        hit_status != "none-observed" or hit_count != 0 or reused_tokens != 0
    ):
        blockers.append(f"{side}: residency-only cache cannot claim request hits or reused input tokens")
    if runtime_kind == "embedding-result" and reused_tokens not in {0, None}:
        blockers.append(f"{side}: embedding-result cache cannot claim reused model input tokens")

    cold_latency = validate_latency(blockers, side, "cold", observed.get("cold_latency_ms"), cold_count)
    warm_latency = validate_latency(blockers, side, "warm", observed.get("warm_latency_ms"), warm_count)
    if profile == "controlled-cold-then-warm" and (not cold_count or not warm_count):
        blockers.append(f"{side}: controlled-cold-then-warm requires cold and warm requests")
    if profile == "cold-only" and (not cold_count or warm_count != 0):
        blockers.append(f"{side}: cold-only profile requires only cold requests")

    trace_errors: list[str] = []
    trace = load_trace(
        observed.get("trace_proof"), artifact_root, trace_errors, side
    )
    trace_derived = None
    if trace is not None:
        trace_derived = validate_trace(
            trace,
            result,
            prov,
            actual_fingerprint,
            trace_errors,
            side,
        )
    trace_valid = trace_derived is not None and not trace_errors
    if claim_scope == "cache-ablation" and not trace_valid:
        blockers.extend(trace_errors or [f"{side}: cache-ablation requires a valid raw cache trace"])
    if memo_enabled and not trace_valid:
        blockers.extend(trace_errors)
        blockers.append(f"{side}: enabled response memoization requires valid per-request no-hit proof")

    valid = len(blockers) == start
    speed_usable = valid and trace_valid and hit_status != "unavailable" and (
        (cold_count == 0 or cold_latency is not None)
        and (warm_count == 0 or warm_latency is not None)
    )
    return {
        "valid": valid,
        "runtime": {
            "visibility": runtime.get("visibility"),
            "kind": runtime.get("kind"),
            "name": runtime.get("name"),
            "version": runtime.get("version"),
            "engine": runtime.get("engine"),
        },
        "layers": layers,
        "configuration_fingerprint": actual_fingerprint,
        "effective_knobs": config.get("effective_knobs"),
        "capacity": {
            "visibility": capacity_visibility,
            "limits": limits,
        },
        "protocol": {key: protocol.get(key) for key in CACHE_PROTOCOL_FIELDS},
        "lifecycle": {
            "server_scope": lifecycle.get("server_scope"),
            "reset_mechanism": lifecycle.get("reset_mechanism"),
            "reuse_scope": lifecycle.get("reuse_scope"),
        },
        "observed": {
            "request_count": request_count,
            "cold_request_count": cold_count,
            "warm_request_count": warm_count,
            "hit_status": hit_status,
            "hit_request_count": hit_count,
            "reused_input_tokens": reused_tokens,
            "response_memo_hit_count": response_memo_hits,
            "hit_metric": observed.get("hit_metric"),
            "cold_latency_ms": cold_latency,
            "warm_latency_ms": warm_latency,
            "startup_latency_ms": observed.get("startup_latency_ms"),
            "readiness_latency_ms": observed.get("readiness_latency_ms"),
            "ttft_latency_ms": observed.get("ttft_latency_ms"),
            "prefill_latency_ms": observed.get("prefill_latency_ms"),
            "decode_latency_ms": observed.get("decode_latency_ms"),
            "peak_process_rss_bytes": count(observed.get("peak_process_rss_bytes")),
            "peak_accelerator_bytes": count(observed.get("peak_accelerator_bytes")),
            "peak_cache_resident_bytes": count(observed.get("peak_cache_resident_bytes")),
            "peak_cache_resident_tokens": count(observed.get("peak_cache_resident_tokens")),
            "cache_evictions": count(observed.get("cache_evictions")),
        },
        "speed_usable": speed_usable,
        "trace_valid": trace_valid,
        "trace_errors": trace_errors,
        "trace_derived": trace_derived,
    }


def task_rows(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = result.get("task_results")
    if not isinstance(rows, list):
        return {}
    return {
        str(row["task_id"]): row for row in rows
        if isinstance(row, dict) and text(row.get("task_id"))
    }


def pricing_valid(prov: dict[str, Any]) -> bool:
    value = get(prov, "pricing")
    rates = value.get("rates") if isinstance(value, dict) else None
    return (
        isinstance(value, dict)
        and bool(text(value.get("as_of")))
        and bool(text(value.get("currency")))
        and bool(text(value.get("source")))
        and isinstance(rates, dict)
        and all(
            number(rates.get(key)) is not None and number(rates.get(key)) >= 0
            for key in PRICING_RATE_KEYS
        )
    )


def requested_fast_state(value: Any) -> bool:
    """Requested CLI state is tri-state; omission is not equivalent to off."""
    return value in {"unset", "on", "off"}


def observed_fast_state(value: Any) -> bool:
    """Observed state is the effective boolean reported by the completed run."""
    return isinstance(value, bool)


def validate_route(blockers: list[str], side: str, result: dict[str, Any], prov: dict[str, Any]) -> dict[str, Any]:
    route = get(prov, "route")
    if not isinstance(route, dict):
        blockers.append(f"{side}: missing provenance.route")
        return {"routing_mode": None, "downstream_fingerprint": None, "downstream_count": 0}
    requested, observed = route.get("requested"), route.get("observed")
    for label, value in (("requested", requested), ("observed", observed)):
        if not isinstance(value, dict):
            blockers.append(f"{side}: missing provenance.route.{label}")
            continue
        for key in ("provider", "model", "reasoning"):
            if not text(value.get(key)):
                blockers.append(f"{side}: missing provenance.route.{label}.{key}")
        valid_fast = (
            requested_fast_state(value.get("fast"))
            if label == "requested"
            else observed_fast_state(value.get("fast"))
        )
        if "fast" not in value or not valid_fast:
            blockers.append(f"{side}: missing/invalid provenance.route.{label}.fast")
    if isinstance(requested, dict) and isinstance(observed, dict):
        for key in ("provider", "model", "reasoning"):
            if requested.get(key) != observed.get(key):
                blockers.append(f"{side}: requested and observed route {key} differ")
        requested_fast = requested.get("fast")
        observed_fast = observed.get("fast")
        if requested_fast == "on" and observed_fast is not True:
            blockers.append(f"{side}: explicit fast=on did not resolve to observed true")
        elif requested_fast == "off" and observed_fast is not False:
            blockers.append(f"{side}: explicit fast=off did not resolve to observed false")
        if result.get("model") != observed.get("model") or result.get("provider") != observed.get("provider"):
            blockers.append(f"{side}: observed route does not match BenchmarkResult identity")
    if route.get("identity_verified") is not True or not proof(route.get("identity_proof")):
        blockers.append(f"{side}: route identity proof is missing or unverified")
    if route.get("reasoning_verified") is not True or not proof(route.get("reasoning_proof")):
        blockers.append(f"{side}: route reasoning proof is missing or unverified")
    if route.get("fallback_used") is not False or not proof(route.get("fallback_proof")):
        blockers.append(f"{side}: fallback absence is not explicitly proven")

    routing_mode = route.get("routing_mode")
    downstream = route.get("downstream")
    normalized: list[dict[str, Any]] = []
    if routing_mode not in ROUTING_MODES:
        blockers.append(f"{side}: route routing_mode must be direct, router, or mixed")
    elif routing_mode == "direct":
        if downstream is not None:
            blockers.append(f"{side}: direct route must not include downstream routing attestation")
    else:
        if not isinstance(downstream, dict):
            blockers.append(f"{side}: {routing_mode} route requires downstream routing attestation")
        else:
            if downstream.get("complete") is not True:
                blockers.append(f"{side}: downstream route coverage is not complete")
            if not proof(downstream.get("coverage_proof")):
                blockers.append(f"{side}: downstream route coverage proof is missing")
            observations = downstream.get("observations")
            if not isinstance(observations, list) or not observations:
                blockers.append(f"{side}: downstream route observations are missing")
                observations = []
            for index, item in enumerate(observations):
                label = f"{side}: downstream observation {index}"
                if not isinstance(item, dict):
                    blockers.append(f"{label} is not an object")
                    continue
                provider, model = text(item.get("provider")), text(item.get("model"))
                cache_fingerprint = text(item.get("cache_configuration_fingerprint"))
                if not provider or not model:
                    blockers.append(f"{label} identity is missing")
                if not cache_fingerprint or len(cache_fingerprint) != 71 or not cache_fingerprint.startswith("sha256:"):
                    blockers.append(f"{label} cache configuration fingerprint is missing or invalid")
                else:
                    try:
                        int(cache_fingerprint[7:], 16)
                    except ValueError:
                        blockers.append(f"{label} cache configuration fingerprint is missing or invalid")
                if item.get("fallback_used") is not False:
                    blockers.append(f"{label} reports fallback use or lacks a false fallback state")
                for proof_name in ("identity_proof", "cache_proof", "fallback_proof"):
                    if not proof(item.get(proof_name)):
                        blockers.append(f"{label} {proof_name.replace('_', ' ')} is missing")
                normalized.append({
                    "provider": provider,
                    "model": model,
                    "cache_configuration_fingerprint": cache_fingerprint,
                    "fallback_used": item.get("fallback_used"),
                })
            identities = {
                (item.get("provider"), item.get("model"), item.get("cache_configuration_fingerprint"))
                for item in normalized
            }
            if routing_mode == "mixed" and len(identities) < 2:
                blockers.append(f"{side}: mixed route requires at least two distinct downstream identities/cache configurations")
    downstream_fingerprint = digest({
        "routing_mode": routing_mode,
        "observations": sorted(
            normalized,
            key=lambda item: (
                str(item.get("provider")), str(item.get("model")),
                str(item.get("cache_configuration_fingerprint")),
            ),
        ),
    }) if routing_mode in ROUTING_MODES else None
    return {
        "routing_mode": routing_mode,
        "downstream_fingerprint": downstream_fingerprint,
        "downstream_count": len(normalized),
    }


def validate_judge(blockers: list[str], side: str, prov: dict[str, Any]) -> None:
    judge = get(prov, "judge")
    if not isinstance(judge, dict):
        blockers.append(f"{side}: missing provenance.judge")
        return
    requested, observed = judge.get("requested"), judge.get("observed")
    for label, value in (("requested", requested), ("observed", observed)):
        if not isinstance(value, dict):
            blockers.append(f"{side}: missing provenance.judge.{label}")
            continue
        for key in ("provider", "model", "reasoning"):
            if not text(value.get(key)):
                blockers.append(f"{side}: missing provenance.judge.{label}.{key}")
    if isinstance(requested, dict) and isinstance(observed, dict):
        if any(requested.get(key) != observed.get(key) for key in ("provider", "model", "reasoning")):
            blockers.append(f"{side}: requested and observed judge route differ")
    if judge.get("identity_verified") is not True or not proof(judge.get("identity_proof")):
        blockers.append(f"{side}: judge identity proof is missing or unverified")
    if judge.get("reasoning_verified") is not True or not proof(judge.get("reasoning_proof")):
        blockers.append(f"{side}: judge reasoning proof is missing or unverified")
    if not isinstance(judge.get("affects_score"), bool):
        blockers.append(f"{side}: judge affects_score policy is missing")


def validate_envelope(
    envelope: dict[str, Any], side: str, artifact_root: Path | None = None
) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    if envelope.get("schema_version") != SCHEMA:
        blockers.append(f"{side}: expected schema_version {SCHEMA}")
    source, result, prov = envelope.get("source_artifact"), result_of(envelope), provenance_of(envelope)
    if not result:
        return blockers + [f"{side}: missing benchmark_result"], {}
    claim_scope = prov.get("claim_scope")
    if claim_scope not in CLAIM_SCOPES:
        blockers.append(f"{side}: provenance.claim_scope must be one of {sorted(CLAIM_SCOPES)}")
    if not isinstance(source, dict) or source.get("schema") != "shellbench.BenchmarkResult":
        blockers.append(f"{side}: missing source_artifact schema")
    elif source.get("sha256") != digest(result):
        blockers.append(f"{side}: source_artifact hash mismatch")
    for key in ("model", "provider", "benchmark_version", "openclaw_version"):
        if not text(result.get(key)):
            blockers.append(f"{side}: missing BenchmarkResult.{key}")
    for key in CORE:
        if number(result.get(key)) is None:
            blockers.append(f"{side}: missing/non-numeric BenchmarkResult.{key}")
    rows = task_rows(result)
    if not rows:
        blockers.append(f"{side}: no BenchmarkResult.task_results")
    for task_id, row in rows.items():
        runs = number(row.get("runs"))
        if runs is None or runs < 1 or not runs.is_integer():
            blockers.append(f"{side}/{task_id}: invalid runs")
        if number(row.get("mean_task_score")) is None:
            blockers.append(f"{side}/{task_id}: missing mean_task_score")
    low, score, high = (number(result.get("overall_ci_lower")), number(result.get("overall_score")), number(result.get("overall_ci_upper")))
    if None not in (low, score, high) and not low <= score <= high:
        blockers.append(f"{side}: invalid overall confidence interval")
    for path in PAIR_PATHS:
        if path in (("campaign", "concurrency"), ("campaign", "model_order"), ("release", "full_release_task_count"), ("release", "complete"), ("judge", "requested"), ("judge", "observed")):
            continue
        if not text(get(prov, *path)):
            blockers.append(f"{side}: missing provenance.{'.'.join(path)}")
    concurrency = number(get(prov, "campaign", "concurrency"))
    if concurrency is None or concurrency < 1 or not concurrency.is_integer():
        blockers.append(f"{side}: invalid provenance.campaign.concurrency")
    order = get(prov, "campaign", "model_order")
    if not isinstance(order, list) or not order or not all(text(item) for item in order):
        blockers.append(f"{side}: invalid provenance.campaign.model_order")
    elif result.get("model") not in order:
        blockers.append(f"{side}: model absent from campaign model order")
    expected = number(get(prov, "release", "full_release_task_count"))
    complete = get(prov, "release", "complete")
    claimed, actual = text(get(prov, "release", "task_ids_fingerprint")), ids_digest(list(rows))
    if expected is None or expected < 1 or not expected.is_integer():
        blockers.append(f"{side}: invalid release task count")
    if not isinstance(complete, bool):
        blockers.append(f"{side}: release completeness flag is missing")
    elif expected is not None and complete is True and int(expected) != len(rows):
        blockers.append(f"{side}: complete release count differs from observed count")
    elif expected is not None and complete is False and int(expected) <= len(rows):
        blockers.append(f"{side}: subset release count is inconsistent with observed count")
    if claimed and claimed != actual:
        blockers.append(f"{side}: release task fingerprint mismatch")
    route_facts = validate_route(blockers, side, result, prov)
    validate_judge(blockers, side, prov)
    cache_facts = validate_cache(
        blockers, side, prov, result, artifact_root, claim_scope
    )
    truthfulness_facts = validate_truthfulness(
        blockers, side, prov, artifact_root
    )
    return blockers, {
        "fingerprint": actual,
        "pricing": pricing_valid(prov),
        "route": route_facts,
        "cache": cache_facts,
        "truthfulness": truthfulness_facts,
        "claim_scope": claim_scope,
    }


def protocol_audit(
    baseline_env: dict[str, Any],
    candidate_env: dict[str, Any],
    baseline_root: Path | None = None,
    candidate_root: Path | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    blockers, base_facts = validate_envelope(baseline_env, "baseline", baseline_root)
    more, cand_facts = validate_envelope(candidate_env, "candidate", candidate_root)
    blockers.extend(more)
    baseline, candidate = result_of(baseline_env), result_of(candidate_env)
    base_prov, cand_prov = provenance_of(baseline_env), provenance_of(candidate_env)
    base_tasks, cand_tasks = task_rows(baseline), task_rows(candidate)
    for key in ("benchmark_version", "openclaw_version"):
        if baseline.get(key) != candidate.get(key):
            blockers.append(f"protocol mismatch: BenchmarkResult.{key}")
    base_scope, cand_scope = base_facts.get("claim_scope"), cand_facts.get("claim_scope")
    if base_scope != cand_scope:
        blockers.append("protocol mismatch: provenance.claim_scope")
    for path in PAIR_PATHS:
        if path == ("protocol", "adapter") and base_scope == "route-operational":
            continue
        if get(base_prov, *path) != get(cand_prov, *path):
            blockers.append(f"protocol mismatch: provenance.{'.'.join(path)}")
    if get(base_prov, "route", "requested", "fast") != get(cand_prov, "route", "requested", "fast"):
        blockers.append("protocol mismatch: requested fast state")
    if get(base_prov, "route", "observed", "fast") != get(cand_prov, "route", "observed", "fast"):
        blockers.append("protocol mismatch: observed effective fast state")
    base_cache, cand_cache = base_facts.get("cache", {}), cand_facts.get("cache", {})
    base_cache_protocol = base_cache.get("protocol", {})
    cand_cache_protocol = cand_cache.get("protocol", {})
    for field in CACHE_PROTOCOL_FIELDS:
        if base_cache_protocol.get(field) != cand_cache_protocol.get(field):
            blockers.append(f"protocol mismatch: provenance.cache.protocol.{field}")
    base_route, cand_route = get(base_prov, "route", "observed"), get(cand_prov, "route", "observed")
    if isinstance(base_route, dict) and isinstance(cand_route, dict):
        route_keys = ("provider", "model", "reasoning", "fast")
        if base_scope == "cache-ablation" and any(
            base_route.get(key) != cand_route.get(key) for key in route_keys
        ):
            blockers.append("protocol mismatch: cache-ablation requires the same exact route")
        if all(base_route.get(key) == cand_route.get(key) for key in route_keys):
            if (
                base_scope != "cache-ablation"
                and base_cache.get("configuration_fingerprint")
                != cand_cache.get("configuration_fingerprint")
            ):
                blockers.append("protocol mismatch: same exact route has different cache configuration fingerprint")
            if base_facts.get("route", {}).get("downstream_fingerprint") != cand_facts.get("route", {}).get("downstream_fingerprint"):
                blockers.append("protocol mismatch: same exact route has different downstream routing identity/cache/fallback attribution")
    if set(base_tasks) != set(cand_tasks):
        blockers.append("protocol mismatch: task IDs differ")
    for task_id in set(base_tasks) & set(cand_tasks):
        if base_tasks[task_id].get("runs") != cand_tasks[task_id].get("runs"):
            blockers.append(f"protocol mismatch: run count differs for {task_id}")
    min_runs = min([int(number(row.get("runs")) or 0) for row in list(base_tasks.values()) + list(cand_tasks.values())] or [0])
    task_count = min(len(base_tasks), len(cand_tasks))
    release_id = text(get(base_prov, "release", "id"))
    count = number(get(base_prov, "release", "full_release_task_count"))
    fingerprints_match = bool(base_facts.get("fingerprint") and base_facts.get("fingerprint") == cand_facts.get("fingerprint") == get(base_prov, "release", "task_ids_fingerprint"))
    if (
        release_id == "clawbench-core-v1"
        and count == 19
        and task_count == 19
        and fingerprints_match
        and base_facts.get("fingerprint") == CORE19_TASK_IDS_FINGERPRINT
    ):
        coverage = "core-19"
    elif release_id and get(base_prov, "release", "complete") is True and fingerprints_match:
        coverage = f"pinned-release:{release_id}"
    elif release_id and get(base_prov, "release", "complete") is False and fingerprints_match:
        coverage = f"subset:{release_id}"
    else:
        coverage = "subset/unverified"
    warnings: list[str] = []
    base_pricing = pricing_valid(base_prov)
    cand_pricing = pricing_valid(cand_prov)
    pricing_comparable = base_pricing and cand_pricing
    if not pricing_comparable:
        warnings.append("pricing provenance is incomplete; cost metrics are unavailable")
    elif any(
        get(base_prov, "pricing", key) != get(cand_prov, "pricing", key)
        for key in ("as_of", "currency", "source")
    ):
        pricing_comparable = False
        warnings.append("pricing date, currency, or source differs; value comparison is unavailable")
    cache_speed_comparable = bool(
        base_cache.get("speed_usable") and cand_cache.get("speed_usable")
    )
    if not cache_speed_comparable:
        warnings.append("content-bound cache events or cold/warm latency evidence are unavailable; speed comparison is unavailable")
    base_truth = base_facts.get("truthfulness", {})
    cand_truth = cand_facts.get("truthfulness", {})
    truthfulness_comparable = bool(
        base_truth.get("valid")
        and cand_truth.get("valid")
        and base_truth.get("passed")
        and cand_truth.get("passed")
        and base_truth.get("suite_sha256") == cand_truth.get("suite_sha256")
        and base_truth.get("repetitions") == cand_truth.get("repetitions")
        and base_truth.get("case_count") == cand_truth.get("case_count")
        and base_truth.get("expected_cells") == cand_truth.get("expected_cells")
    )
    if not truthfulness_comparable:
        warnings.append(
            "route-bound deterministic truthfulness evidence is absent or mismatched; trust/decision-grade claims are unavailable"
        )
    facts = {
        "min_runs_per_task": min_runs, "task_count": task_count,
        "shellbench_coverage": coverage,
        "identity_proven": not any("identity proof" in item for item in blockers),
        "reasoning_proven": not any("reasoning proof" in item for item in blockers),
        "fallback_proven_off": not any("fallback absence" in item for item in blockers),
        "pricing_proven": base_pricing and cand_pricing,
        "pricing_comparable": pricing_comparable,
        "cache_protocol_profile": base_cache_protocol.get("profile"),
        "cache_speed_comparable": cache_speed_comparable,
        "baseline_cache": base_cache,
        "candidate_cache": cand_cache,
        "baseline_route": base_facts.get("route", {}),
        "candidate_route": cand_facts.get("route", {}),
        "baseline_truthfulness": base_truth,
        "candidate_truthfulness": cand_truth,
        "truthfulness_comparable": truthfulness_comparable,
        "claim_scope": base_scope,
    }
    return sorted(set(blockers)), sorted(set(warnings)), facts


def ci_relation(baseline: dict[str, Any], candidate: dict[str, Any]) -> str:
    b_low, b_high, c_low, c_high = (
        number(baseline.get("overall_ci_lower")), number(baseline.get("overall_ci_upper")),
        number(candidate.get("overall_ci_lower")), number(candidate.get("overall_ci_upper")),
    )
    if None in (b_low, b_high, c_low, c_high):
        return "unavailable"
    if c_low > b_high:
        return "candidate interval is above baseline"
    if b_low > c_high:
        return "baseline interval is above candidate"
    return "intervals overlap"


def eligible(data: dict[str, Any], floors: dict[str, Any]) -> tuple[bool, list[str]]:
    misses = []
    for metric, floor_name in (("overall_score", "min_score"), ("overall_reliability", "min_reliability"), ("overall_worst_of_n", "min_worst_of_n")):
        value, floor = number(data.get(metric)), floors[floor_name]
        if value is None or value < floor:
            misses.append(f"{metric}<{floor:.3f}")
    if floors["require_pass_hat_k"] and (number(data.get("overall_pass_hat_k")) or 0) < 1:
        misses.append("overall_pass_hat_k<1")
    return not misses, misses


def objective_read(objective: str, baseline: dict[str, Any], candidate: dict[str, Any], blocked: bool, floors: dict[str, Any]) -> dict[str, Any]:
    metric, direction = OBJECTIVES[objective]
    left, right = number(baseline.get(metric)), number(candidate.get(metric))
    out: dict[str, Any] = {"objective": objective, "metric": metric, "baseline": left, "candidate": right, "leader": "unavailable"}
    if blocked or left is None or right is None:
        return out
    if objective == "value":
        if any(floors.get(name) is None for name in ("min_score", "min_reliability", "min_worst_of_n")):
            out["leader"] = "unavailable-floor"
            return out
        base_ok, base_miss = eligible(baseline, floors)
        cand_ok, cand_miss = eligible(candidate, floors)
        out["eligibility"] = {"baseline": {"eligible": base_ok, "misses": base_miss}, "candidate": {"eligible": cand_ok, "misses": cand_miss}}
        if not base_ok and not cand_ok:
            out["leader"] = "no-eligible-route"
        elif base_ok != cand_ok:
            out["leader"] = "baseline" if base_ok else "candidate"
        elif left == right:
            out["leader"] = "tie"
        else:
            out["leader"] = "candidate" if right < left else "baseline"
        return out
    if objective == "quality" and ci_relation(baseline, candidate) == "intervals overlap":
        out["leader"] = "no-clear-leader"
    elif left == right:
        out["leader"] = "tie"
    else:
        out["leader"] = "candidate" if (right > left) == (direction == "high") else "baseline"
    return out


def failure_modes(data: dict[str, Any]) -> dict[str, int] | None:
    if "overall_failure_mode_counts" not in data or not isinstance(data.get("overall_failure_mode_counts"), dict):
        return None
    out = {}
    for key, value in data["overall_failure_mode_counts"].items():
        parsed = number(value)
        if parsed is not None and parsed > 0:
            out[str(key)] = int(parsed)
    return out


def build_result(
    baseline_env: dict[str, Any], candidate_env: dict[str, Any], objective: str,
    *, min_score: float | None = None, min_reliability: float | None = None,
    min_worst_of_n: float | None = None, require_pass_hat_k: bool = False,
    baseline_root: Path | None = None, candidate_root: Path | None = None,
) -> dict[str, Any]:
    blockers, warnings, facts = protocol_audit(
        baseline_env, candidate_env, baseline_root, candidate_root
    )
    baseline, candidate = result_of(baseline_env), result_of(candidate_env)
    metrics = {}
    for key, _label, _kind in METRICS:
        left, right = number(baseline.get(key)), number(candidate.get(key))
        if key.startswith("overall_cost") and not pricing_valid(provenance_of(baseline_env)):
            left = None
        if key.startswith("overall_cost") and not pricing_valid(provenance_of(candidate_env)):
            right = None
        metrics[key] = {"baseline": left, "candidate": right, "delta": right - left if left is not None and right is not None else None}
    base_tasks, cand_tasks = task_rows(baseline), task_rows(candidate)
    tasks = []
    for task_id in sorted(set(base_tasks) | set(cand_tasks)):
        left, right = number(base_tasks.get(task_id, {}).get("mean_task_score")), number(cand_tasks.get(task_id, {}).get("mean_task_score"))
        tasks.append({"task_id": task_id, "baseline": left, "candidate": right, "delta": right - left if left is not None and right is not None else None})
    floors = {"min_score": min_score, "min_reliability": min_reliability, "min_worst_of_n": min_worst_of_n, "require_pass_hat_k": require_pass_hat_k}
    min_runs = facts["min_runs_per_task"]
    confidence = "blocked" if blockers else "routing-smoke" if min_runs <= 1 else "insufficient-repeats" if min_runs < 3 else "directional"
    decision_grade = bool(
        not blockers
        and min_runs >= 3
        and facts.get("truthfulness_comparable") is True
    )
    result = {
        "protocol_status": "blocked" if blockers else "comparable", "confidence": confidence,
        "decision_grade": decision_grade,
        "decision_grade_reason": (
            "route-bound truthfulness and repeated capability evidence are complete"
            if decision_grade
            else "requires unblocked n>=3 capability evidence and comparable route-bound truthfulness scores"
        ),
        "blockers": blockers, "warnings": warnings, "facts": facts,
        "baseline": baseline.get("model"), "candidate": candidate.get("model"),
        "ci_relation": ci_relation(baseline, candidate),
        "objective_read": objective_read(objective, baseline, candidate, bool(blockers), floors),
        "metrics": metrics, "tasks": tasks,
        "baseline_failure_modes": failure_modes(baseline),
        "candidate_failure_modes": failure_modes(candidate),
    }
    if objective == "value" and not facts["pricing_comparable"] and not blockers:
        result["objective_read"]["leader"] = "unavailable-pricing-protocol"
    if objective == "speed" and not facts["cache_speed_comparable"] and not blockers:
        result["objective_read"]["leader"] = "unavailable-cache-evidence"
    return result


def fmt(value: float | None, kind: str = "score") -> str:
    if value is None:
        return "n/a"
    if kind == "pct":
        return f"{value * 100:.0f}%"
    if kind == "ms":
        return f"{value:.0f}ms"
    if kind == "count":
        return f"{value:.0f}"
    if kind == "money":
        return f"USD {value:.4f}"
    return f"{value:.3f}"


def render(out: dict[str, Any], baseline_env: dict[str, Any], candidate_env: dict[str, Any]) -> str:
    baseline, candidate = result_of(baseline_env), result_of(candidate_env)
    lines = [
        "# ClawGauge — ShellBench Comparison", "",
        f"- Baseline: {out['baseline'] or 'unknown'}", f"- Candidate: {out['candidate'] or 'unknown'}",
        f"- Protocol: **{out['protocol_status']}**", f"- Confidence: **{out['confidence']}**",
        f"- Decision-grade: **{'yes' if out['decision_grade'] else 'no'}**",
        f"- CI read: {out['ci_relation']}",
        f"- Claim scope: **{out['facts'].get('claim_scope') or 'n/a'}**",
        f"- Objective ({out['objective_read']['objective']}): **{out['objective_read']['leader']}**", "",
    ]
    if out["blockers"]:
        lines.extend(["## Comparison Blockers", ""] + [f"- {item}" for item in out["blockers"]] + [""])
    if out["objective_read"].get("eligibility"):
        lines.extend(["## Value Eligibility", ""])
        for side, item in out["objective_read"]["eligibility"].items():
            lines.append(f"- {side}: {'eligible' if item['eligible'] else ', '.join(item['misses'])}")
        lines.append("")
    lines.extend(["## Score Surfaces", "", "| Metric | Baseline | Candidate |", "|---|---:|---:|"])
    for key, label, kind in METRICS:
        item = out["metrics"][key]
        lines.append(f"| {label} | {fmt(item['baseline'], kind)} | {fmt(item['candidate'], kind)} |")
    lines.extend(["", "## Truthfulness Evidence", ""])
    lines.append(
        f"- Route-bound scores comparable: {'yes' if out['facts']['truthfulness_comparable'] else 'no'}"
    )
    for label, item in (
        ("Baseline", out["facts"]["baseline_truthfulness"]),
        ("Candidate", out["facts"]["candidate_truthfulness"]),
    ):
        lines.append(
            f"- {label}: {'passed' if item.get('passed') else 'unavailable/failed'}; "
            f"n={item.get('repetitions') or 'n/a'}; cells={item.get('expected_cells') or 'n/a'}"
        )
    lines.extend(["", "## Cache Evidence", ""])
    lines.append(f"- Protocol profile: {out['facts']['cache_protocol_profile'] or 'n/a'}")
    lines.append(f"- Speed evidence comparable: {'yes' if out['facts']['cache_speed_comparable'] else 'no'}")
    lines.extend([
        "",
        "| Route | Cache layers | Runtime / engine | Capacity | Cold / warm / hits / memo | Reused input | Cold p50/p95 | Warm p50/p95 | TTFT p50/p95 | Peak RSS / accelerator / cache |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    knob_lines = []
    for label, cache in (("Baseline", out["facts"]["baseline_cache"]), ("Candidate", out["facts"]["candidate_cache"])):
        runtime = cache.get("runtime", {})
        capacity = cache.get("capacity", {})
        observed = cache.get("observed", {})
        layers = cache.get("layers", [])
        cold, warm = observed.get("cold_latency_ms"), observed.get("warm_latency_ms")
        ttft = observed.get("ttft_latency_ms")
        cold_text = "n/a" if not cold else f"{cold['p50']:.0f}/{cold['p95']:.0f}ms"
        warm_text = "n/a" if not warm else f"{warm['p50']:.0f}/{warm['p95']:.0f}ms"
        ttft_text = "n/a" if not ttft else f"{ttft['p50']:.0f}/{ttft['p95']:.0f}ms"
        capacity_text = "opaque" if capacity.get("visibility") == "opaque" else json.dumps(capacity.get("limits", {}), sort_keys=True)
        counts = (
            f"{observed.get('cold_request_count')}/{observed.get('warm_request_count')}/"
            f"{observed.get('hit_request_count') if observed.get('hit_request_count') is not None else 'n/a'}/"
            f"{observed.get('response_memo_hit_count') if observed.get('response_memo_hit_count') is not None else 'n/a'}"
        )
        layers_text = ", ".join(
            f"{item.get('kind')}={'on' if item.get('enabled') else 'off'}"
            for item in layers
        ) or "n/a"
        memory_text = "/".join(
            str(observed.get(key)) if observed.get(key) is not None else "n/a"
            for key in ("peak_process_rss_bytes", "peak_accelerator_bytes", "peak_cache_resident_bytes")
        )
        reused = observed.get("reused_input_tokens")
        lines.append(
            f"| {label} | {layers_text} | {runtime.get('name') or 'n/a'} {runtime.get('version') or 'opaque'} / {runtime.get('engine') or 'n/a'} | "
            f"{capacity_text} | {counts} | {reused if reused is not None else 'n/a'} | {cold_text} | {warm_text} | {ttft_text} | {memory_text} |"
        )
        knob_lines.append(f"- {label} effective cache knobs: `{json.dumps(cache.get('effective_knobs'), sort_keys=True)}`")
    lines.extend(["", *knob_lines])
    lines.extend(["", "## Route Attribution", ""])
    for label, route in (("Baseline", out["facts"]["baseline_route"]), ("Candidate", out["facts"]["candidate_route"])):
        lines.append(
            f"- {label}: {route.get('routing_mode') or 'n/a'}; downstream observations={route.get('downstream_count', 0)}; "
            f"fingerprint={route.get('downstream_fingerprint') or 'n/a'}"
        )
    lines.extend(["", "## Failure Modes", ""])
    for label, failures in (("Baseline", out["baseline_failure_modes"]), ("Candidate", out["candidate_failure_modes"])):
        detail = "n/a (failure evidence absent)" if failures is None else "none (explicit empty count map)" if not failures else ", ".join(f"{key}={value}" for key, value in sorted(failures.items()))
        lines.append(f"- {label}: {detail}")
    lines.extend([
        "", "## Artifact Identity", "", f"- Envelope: {SCHEMA}",
        f"- Benchmark: {baseline.get('benchmark_version') or 'n/a'} / {candidate.get('benchmark_version') or 'n/a'}",
        f"- OpenClaw: {baseline.get('openclaw_version') or 'n/a'} / {candidate.get('openclaw_version') or 'n/a'}",
        f"- Minimum runs/task: {out['facts']['min_runs_per_task']}",
        f"- Tasks: {out['facts']['task_count']}",
        f"- Coverage: {out['facts']['shellbench_coverage']}", "",
    ])
    return "\n".join(lines)


def fraction(value: str) -> float:
    value = float(value)
    if not 0 <= value <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--objective", choices=tuple(OBJECTIVES), default="quality")
    parser.add_argument("--min-score", type=fraction)
    parser.add_argument("--min-reliability", type=fraction)
    parser.add_argument("--min-worst-of-n", type=fraction)
    parser.add_argument("--require-pass-hat-k", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", dest="json_out", type=Path)
    parser.add_argument("--allow-mismatch", action="store_true")
    args = parser.parse_args()
    try:
        baseline, candidate = read_json(args.baseline), read_json(args.candidate)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out = build_result(
        baseline, candidate, args.objective, min_score=args.min_score,
        min_reliability=args.min_reliability, min_worst_of_n=args.min_worst_of_n,
        require_pass_hat_k=args.require_pass_hat_k,
        baseline_root=args.baseline.parent, candidate_root=args.candidate.parent,
    )
    report = render(out, baseline, candidate) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return 2 if out["protocol_status"] == "blocked" and not args.allow_mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
