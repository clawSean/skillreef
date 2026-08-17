#!/usr/bin/env python3
"""Run deterministic, provider-free ClawGauge regression and adversarial checks."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
EXAMPLES = ROOT / "examples"


def run(*args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != expected:
        raise AssertionError(
            f"expected exit {expected}, got {result.returncode}: {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def import_script(name: str) -> ModuleType:
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"clawgauge_test_{name}", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rehash(envelope: dict) -> None:
    raw = json.dumps(
        envelope["benchmark_result"],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    envelope["source_artifact"]["sha256"] = (
        "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    )


def rehash_cache(envelope: dict) -> str:
    cache = envelope["provenance"]["cache"]
    runtime = cache["runtime"]
    config = cache["configuration"]
    capacity = config["capacity"]
    payload = {
        "runtime": {
            "visibility": runtime.get("visibility"),
            "kind": runtime.get("kind"),
            "name": runtime.get("name"),
            "version": runtime.get("version"),
            "engine": runtime.get("engine"),
        },
        "enabled": config.get("enabled"),
        "persistence": config.get("persistence"),
        "capacity": {
            "visibility": capacity.get("visibility"),
            "limits": capacity.get("limits"),
        },
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    fingerprint = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    config["fingerprint"] = fingerprint
    cache["observed"]["configuration_fingerprint"] = fingerprint
    return fingerprint


def downstream_observation(provider: str, model: str, cache_fingerprint: str, label: str) -> dict:
    return {
        "provider": provider,
        "model": model,
        "cache_configuration_fingerprint": cache_fingerprint,
        "fallback_used": False,
        "identity_proof": {"kind": "synthetic-trace", "reference": f"fixture://downstream/{label}/identity"},
        "cache_proof": {"kind": "synthetic-trace", "reference": f"fixture://downstream/{label}/cache"},
        "fallback_proof": {"kind": "synthetic-trace", "reference": f"fixture://downstream/{label}/fallback"},
    }


def set_router(envelope: dict, mode: str, observations: list[dict]) -> None:
    route = envelope["provenance"]["route"]
    route["routing_mode"] = mode
    route["downstream"] = {
        "complete": True,
        "coverage_proof": {"kind": "synthetic-trace", "reference": f"fixture://downstream/{mode}/coverage"},
        "observations": observations,
    }


def qa_candidate(summary: dict, model: str, status: str = "pass") -> dict:
    out = copy.deepcopy(summary)
    run_data = out["run"]
    run_data.update(
        {
            "primaryModel": model,
            "primaryModelName": model.rsplit("/", 1)[-1],
            "alternateModel": model,
            "alternateModelName": model.rsplit("/", 1)[-1],
        }
    )
    out["scenarios"][0]["status"] = status
    out["counts"]["passed"] = 10 if status == "pass" else 9
    out["counts"]["failed"] = 0 if status == "pass" else 1
    return out


def profile_evidence(scenario: str) -> dict:
    cell = {"scenarioId": scenario}
    return {
        "profile": "personal-agent",
        "profilePlan": {
            "expectedCells": [cell],
            "observedCells": [cell],
            "counts": {"missingCells": 0},
        },
    }


def profile_summary(model: str, scenario: str) -> dict:
    return {
        "scenarios": [{"name": scenario, "status": "pass", "steps": []}],
        "metrics": {"wallMs": 100},
        "run": {
            "providerMode": "live-frontier",
            "primaryModel": model,
            "alternateModel": model,
            "fastMode": False,
            "scenarioIds": [scenario],
        },
    }


def compare_case(
    tmp: Path, name: str, baseline: dict, candidate: dict, *,
    objective: str = "quality", expected: int = 0,
) -> dict:
    baseline_path = tmp / f"{name}-baseline.json"
    candidate_path = tmp / f"{name}-candidate.json"
    output_path = tmp / f"{name}-comparison.json"
    write(baseline_path, baseline)
    write(candidate_path, candidate)
    run(
        str(SCRIPTS / "compare_clawbench_results.py"),
        "--baseline", str(baseline_path),
        "--candidate", str(candidate_path),
        "--objective", objective,
        "--json", str(output_path),
        expected=expected,
    )
    return load(output_path)


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="clawgauge-self-test-") as raw_tmp:
        tmp = Path(raw_tmp)
        baseline_path = EXAMPLES / "sample-clawbench-result.json"
        candidate_path = EXAMPLES / "sample-clawbench-candidate.json"
        baseline, candidate = load(baseline_path), load(candidate_path)

        summary_json = tmp / "summary.json"
        run(
            str(SCRIPTS / "summarize_clawbench_result.py"),
            str(baseline_path),
            "--json",
            str(summary_json),
        )
        summary = load(summary_json)
        assert summary["artifact_status"] == "complete"
        assert summary["schema_version"] == "clawgauge.evidence.v2"
        assert summary["source"] == baseline_path.name
        checks += 3

        raw_result, attestation = tmp / "raw.json", tmp / "attestation.json"
        imported = tmp / "imported.json"
        write(raw_result, baseline["benchmark_result"])
        write(attestation, {"provenance": baseline["provenance"]})
        run(
            str(SCRIPTS / "build_evidence_envelope.py"),
            str(raw_result),
            "--attestation",
            str(attestation),
            "--out",
            str(imported),
        )
        assert load(imported)["benchmark_result"] == baseline["benchmark_result"]
        checks += 1

        compare_json = tmp / "compare.json"
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(candidate_path),
            "--json",
            str(compare_json),
        )
        comparison = load(compare_json)
        assert comparison["protocol_status"] == "comparable"
        assert comparison["confidence"] == "directional"
        assert comparison["objective_read"]["leader"] == "no-clear-leader"
        checks += 3

        # Cache engines and capacities are route identity, not pair-equality
        # requirements. The normalized cache treatment must still match.
        assert baseline["provenance"]["cache"]["runtime"]["engine"] != candidate["provenance"]["cache"]["runtime"]["engine"]
        assert comparison["facts"]["cache_speed_comparable"] is True
        checks += 2

        legacy = copy.deepcopy(baseline)
        legacy["schema_version"] = "clawgauge.evidence.v1"
        legacy_result = compare_case(tmp, "legacy-cache-schema", legacy, candidate, expected=2)
        assert any("clawgauge.evidence.v2" in item for item in legacy_result["blockers"])
        legacy_path = tmp / "legacy-envelope.json"
        write(legacy_path, legacy)
        legacy_build = run(
            str(SCRIPTS / "build_evidence_envelope.py"), str(legacy_path), expected=2,
        )
        assert "unsupported envelope schema" in legacy_build.stderr
        checks += 2

        missing_cache = copy.deepcopy(candidate)
        missing_cache["provenance"].pop("cache")
        missing_cache_result = compare_case(tmp, "missing-cache", baseline, missing_cache, expected=2)
        assert any("missing provenance.cache" in item for item in missing_cache_result["blockers"])
        checks += 1

        bad_fingerprint = copy.deepcopy(candidate)
        bad_fingerprint["provenance"]["cache"]["configuration"]["fingerprint"] = "sha256:bad"
        bad_fingerprint_result = compare_case(tmp, "bad-cache-fingerprint", baseline, bad_fingerprint, expected=2)
        assert any("cache configuration fingerprint mismatch" in item for item in bad_fingerprint_result["blockers"])
        checks += 1

        fractional_capacity = copy.deepcopy(candidate)
        fractional_capacity["provenance"]["cache"]["configuration"]["capacity"]["limits"]["blocks"] = 1.5
        rehash_cache(fractional_capacity)
        fractional_result = compare_case(tmp, "fractional-cache-capacity", baseline, fractional_capacity, expected=2)
        assert any("invalid cache capacity limits" in item for item in fractional_result["blockers"])
        checks += 1

        protocol_cases = (
            ("profile", "route-native"),
            ("reset_between_task_repetitions", False),
            ("within_task_reuse", False),
            ("cross_task_reuse", True),
        )
        for field, value in protocol_cases:
            drift = copy.deepcopy(candidate)
            drift["provenance"]["cache"]["protocol"][field] = value
            drift_result = compare_case(tmp, f"cache-protocol-{field}", baseline, drift, expected=2)
            assert any(f"provenance.cache.protocol.{field}" in item for item in drift_result["blockers"])
            checks += 1

        lifecycle_drift = copy.deepcopy(candidate)
        lifecycle_drift["provenance"]["cache"]["lifecycle"]["reuse_scope"] = "campaign"
        lifecycle_result = compare_case(tmp, "cache-lifecycle-drift", baseline, lifecycle_drift, expected=2)
        assert any("cross-task reuse contradicts" in item for item in lifecycle_result["blockers"])
        checks += 1

        no_hit_proof = copy.deepcopy(candidate)
        no_hit_proof["provenance"]["cache"]["observed"].pop("hit_proof")
        no_hit_result = compare_case(tmp, "cache-no-hit-proof", baseline, no_hit_proof, expected=2)
        assert any("cache hit evidence proof is missing" in item for item in no_hit_result["blockers"])
        checks += 1

        fake_disabled = copy.deepcopy(candidate)
        disabled_cache = fake_disabled["provenance"]["cache"]
        disabled_cache["configuration"]["enabled"] = False
        disabled_cache["configuration"]["persistence"] = "none"
        disabled_cache["configuration"]["capacity"] = {"visibility": "not-applicable", "limits": {}}
        rehash_cache(fake_disabled)
        disabled_result = compare_case(tmp, "cache-disabled-with-hits", baseline, fake_disabled, expected=2)
        assert any("disabled cache cannot report" in item for item in disabled_result["blockers"])
        checks += 1

        impossible_counts = copy.deepcopy(candidate)
        impossible_counts["provenance"]["cache"]["observed"]["request_count"] = 17
        impossible_result = compare_case(tmp, "cache-impossible-counts", baseline, impossible_counts, expected=2)
        assert any("do not equal request_count" in item for item in impossible_result["blockers"])
        checks += 1

        zero_requests = copy.deepcopy(candidate)
        zero_observed = zero_requests["provenance"]["cache"]["observed"]
        zero_observed.update(
            request_count=0,
            cold_request_count=0,
            warm_request_count=0,
            hit_status="none-observed",
            hit_request_count=0,
            reused_input_tokens=0,
            cold_latency_ms=None,
            warm_latency_ms=None,
        )
        zero_result = compare_case(tmp, "cache-zero-requests", baseline, zero_requests, expected=2)
        assert any("request_count must be positive" in item for item in zero_result["blockers"])
        checks += 1

        # Cached-input pricing is not cache-hit evidence.
        pricing_only = copy.deepcopy(candidate)
        pricing_only["provenance"]["cache"]["observed"].pop("hit_proof")
        pricing_only_result = compare_case(tmp, "cache-pricing-is-not-proof", baseline, pricing_only, expected=2)
        assert pricing_only["provenance"]["pricing"]["rates"]["cached_input_per_million"] >= 0
        assert any("cache hit evidence proof is missing" in item for item in pricing_only_result["blockers"])
        checks += 2

        unavailable_base, unavailable_candidate = copy.deepcopy(baseline), copy.deepcopy(candidate)
        for envelope in (unavailable_base, unavailable_candidate):
            observed = envelope["provenance"]["cache"]["observed"]
            observed.update(
                hit_status="unavailable",
                hit_request_count=None,
                reused_input_tokens=None,
                hit_metric=None,
            )
        unavailable_quality = compare_case(tmp, "cache-unavailable-quality", unavailable_base, unavailable_candidate)
        unavailable_speed = compare_case(
            tmp, "cache-unavailable-speed", unavailable_base, unavailable_candidate, objective="speed",
        )
        assert unavailable_quality["protocol_status"] == "comparable"
        assert unavailable_quality["facts"]["cache_speed_comparable"] is False
        assert unavailable_speed["objective_read"]["leader"] == "unavailable-cache-evidence"
        checks += 3

        same_route = copy.deepcopy(candidate)
        same_route["benchmark_result"]["model"] = baseline["benchmark_result"]["model"]
        same_route["benchmark_result"]["provider"] = baseline["benchmark_result"]["provider"]
        same_route["provenance"]["route"] = copy.deepcopy(baseline["provenance"]["route"])
        rehash(same_route)
        same_route_result = compare_case(tmp, "same-route-cache-drift", baseline, same_route, expected=2)
        assert any("same exact route has different cache configuration" in item for item in same_route_result["blockers"])
        checks += 1

        opaque_base, opaque_candidate = copy.deepcopy(baseline), copy.deepcopy(candidate)
        for envelope in (opaque_base, opaque_candidate):
            cache = envelope["provenance"]["cache"]
            cache["runtime"].update(
                visibility="opaque",
                kind="opaque-provider-managed",
                version=None,
                proof={"kind": "synthetic-provider-doc", "reference": "fixture://cache/runtime/opaque"},
            )
            cache["configuration"]["capacity"] = {
                "visibility": "opaque",
                "limits": {},
                "proof": {"kind": "synthetic-provider-doc", "reference": "fixture://cache/capacity/opaque"},
            }
            rehash_cache(envelope)
        opaque_result = compare_case(tmp, "opaque-provider-cache", opaque_base, opaque_candidate)
        assert opaque_result["protocol_status"] == "comparable"
        checks += 1

        assert baseline["provenance"]["cache"]["runtime"]["kind"] == "prefix-kv"
        assert baseline["provenance"]["route"]["routing_mode"] == "direct"
        checks += 2

        missing_kind = copy.deepcopy(candidate)
        missing_kind["provenance"]["cache"]["runtime"].pop("kind")
        rehash_cache(missing_kind)
        missing_kind_result = compare_case(tmp, "cache-missing-kind", baseline, missing_kind, expected=2)
        assert any("cache runtime kind" in item for item in missing_kind_result["blockers"])
        checks += 1

        memo_enabled = copy.deepcopy(candidate)
        memo_enabled["provenance"]["cache"]["runtime"]["kind"] = "full-response-memoization"
        rehash_cache(memo_enabled)
        memo_enabled_result = compare_case(tmp, "cache-full-response-enabled", baseline, memo_enabled, expected=2)
        assert any("full-response memoization enabled or hit" in item for item in memo_enabled_result["blockers"])
        checks += 1

        memo_hit = copy.deepcopy(candidate)
        memo_hit_cache = memo_hit["provenance"]["cache"]
        memo_hit_cache["runtime"]["kind"] = "full-response-memoization"
        memo_hit_cache["configuration"].update(
            enabled=False,
            persistence="none",
            capacity={"visibility": "not-applicable", "limits": {}},
        )
        rehash_cache(memo_hit)
        memo_hit_result = compare_case(tmp, "cache-full-response-hit", baseline, memo_hit, expected=2)
        assert any("full-response memoization enabled or hit" in item for item in memo_hit_result["blockers"])
        checks += 1

        memo_off = copy.deepcopy(candidate)
        memo_off_cache = memo_off["provenance"]["cache"]
        memo_off_cache["runtime"]["kind"] = "full-response-memoization"
        memo_off_cache["configuration"].update(
            enabled=False,
            persistence="none",
            capacity={"visibility": "not-applicable", "limits": {}},
        )
        memo_off_cache["protocol"].update(
            profile="cold-only",
            reset_between_task_repetitions=True,
            within_task_reuse=False,
            cross_task_reuse=False,
        )
        memo_off_cache["lifecycle"].update(reuse_scope="none")
        memo_off_cache["observed"].update(
            request_count=6,
            cold_request_count=6,
            warm_request_count=0,
            hit_status="none-observed",
            hit_request_count=0,
            reused_input_tokens=0,
            hit_metric="full_response_cache_hit",
            warm_latency_ms=None,
        )
        rehash_cache(memo_off)
        memo_off_path, memo_off_summary = tmp / "memo-off.json", tmp / "memo-off-summary.json"
        write(memo_off_path, memo_off)
        run(
            str(SCRIPTS / "summarize_clawbench_result.py"), str(memo_off_path),
            "--json", str(memo_off_summary),
        )
        assert load(memo_off_summary)["artifact_status"] == "complete"
        checks += 1

        residency_hits = copy.deepcopy(candidate)
        residency_hits["provenance"]["cache"]["runtime"]["kind"] = "residency-only"
        rehash_cache(residency_hits)
        residency_result = compare_case(tmp, "cache-residency-hits", baseline, residency_hits, expected=2)
        assert any("residency-only cache cannot claim" in item for item in residency_result["blockers"])
        checks += 1

        embedding_tokens = copy.deepcopy(candidate)
        embedding_tokens["provenance"]["cache"]["runtime"]["kind"] = "embedding-result"
        rehash_cache(embedding_tokens)
        embedding_result = compare_case(tmp, "cache-embedding-input-tokens", baseline, embedding_tokens, expected=2)
        assert any("embedding-result cache cannot claim reused model input" in item for item in embedding_result["blockers"])
        checks += 1

        embedding_valid = copy.deepcopy(candidate)
        embedding_valid_cache = embedding_valid["provenance"]["cache"]
        embedding_valid_cache["runtime"]["kind"] = "embedding-result"
        embedding_valid_cache["observed"]["reused_input_tokens"] = 0
        embedding_valid_cache["observed"]["hit_metric"] = "embedding_cache_hit"
        rehash_cache(embedding_valid)
        embedding_valid_path = tmp / "embedding-valid.json"
        embedding_valid_summary = tmp / "embedding-valid-summary.json"
        write(embedding_valid_path, embedding_valid)
        run(
            str(SCRIPTS / "summarize_clawbench_result.py"), str(embedding_valid_path),
            "--json", str(embedding_valid_summary),
        )
        assert load(embedding_valid_summary)["artifact_status"] == "complete"
        checks += 1

        missing_mode = copy.deepcopy(candidate)
        missing_mode["provenance"]["route"].pop("routing_mode")
        missing_mode_result = compare_case(tmp, "route-missing-mode", baseline, missing_mode, expected=2)
        assert any("route routing_mode" in item for item in missing_mode_result["blockers"])
        checks += 1

        missing_downstream = copy.deepcopy(candidate)
        missing_downstream["provenance"]["route"]["routing_mode"] = "router"
        missing_downstream_result = compare_case(tmp, "route-missing-downstream", baseline, missing_downstream, expected=2)
        assert any("requires downstream routing attestation" in item for item in missing_downstream_result["blockers"])
        checks += 1

        router_base, router_candidate = copy.deepcopy(baseline), copy.deepcopy(candidate)
        set_router(router_base, "router", [downstream_observation(
            "local", "downstream-a", rehash_cache(router_base), "router-a",
        )])
        set_router(router_candidate, "router", [downstream_observation(
            "cloud", "downstream-b", rehash_cache(router_candidate), "router-b",
        )])
        router_result = compare_case(tmp, "route-valid-router", router_base, router_candidate)
        assert router_result["protocol_status"] == "comparable"
        assert router_result["facts"]["baseline_route"]["downstream_count"] == 1
        checks += 2

        router_no_cache_proof = copy.deepcopy(router_candidate)
        router_no_cache_proof["provenance"]["route"]["downstream"]["observations"][0].pop("cache_proof")
        router_no_proof_result = compare_case(tmp, "route-no-cache-proof", router_base, router_no_cache_proof, expected=2)
        assert any("cache proof is missing" in item for item in router_no_proof_result["blockers"])
        checks += 1

        router_fallback = copy.deepcopy(router_candidate)
        router_fallback["provenance"]["route"]["downstream"]["observations"][0]["fallback_used"] = True
        router_fallback_result = compare_case(tmp, "route-downstream-fallback", router_base, router_fallback, expected=2)
        assert any("reports fallback use" in item for item in router_fallback_result["blockers"])
        checks += 1

        mixed_single = copy.deepcopy(router_candidate)
        mixed_single["provenance"]["route"]["routing_mode"] = "mixed"
        mixed_single_result = compare_case(tmp, "route-mixed-single", router_base, mixed_single, expected=2)
        assert any("mixed route requires at least two distinct" in item for item in mixed_single_result["blockers"])
        checks += 1

        mixed_base, mixed_candidate = copy.deepcopy(baseline), copy.deepcopy(candidate)
        mixed_observations = [
            downstream_observation("local", "downstream-a", rehash_cache(mixed_base), "mixed-a"),
            downstream_observation("cloud", "downstream-b", rehash_cache(mixed_candidate), "mixed-b"),
        ]
        set_router(mixed_base, "mixed", copy.deepcopy(mixed_observations))
        set_router(mixed_candidate, "mixed", copy.deepcopy(mixed_observations))
        mixed_result = compare_case(tmp, "route-valid-mixed", mixed_base, mixed_candidate)
        assert mixed_result["protocol_status"] == "comparable"
        assert mixed_result["facts"]["candidate_route"]["downstream_count"] == 2
        checks += 2

        drift_base, drift_candidate = copy.deepcopy(baseline), copy.deepcopy(baseline)
        set_router(drift_base, "router", [downstream_observation(
            "local", "downstream-a", rehash_cache(drift_base), "drift-a",
        )])
        set_router(drift_candidate, "router", [downstream_observation(
            "local", "downstream-c", rehash_cache(drift_candidate), "drift-c",
        )])
        downstream_drift_result = compare_case(tmp, "route-downstream-drift", drift_base, drift_candidate, expected=2)
        assert any("different downstream routing identity/cache/fallback attribution" in item for item in downstream_drift_result["blockers"])
        checks += 1

        # Fast mode has a tri-state request and a boolean effective state.
        # An omitted request may resolve either way, but the compared routes
        # must share both the requested state and the observed effective state.
        unset_base, unset_candidate = copy.deepcopy(baseline), copy.deepcopy(candidate)
        for envelope in (unset_base, unset_candidate):
            envelope["provenance"]["route"]["requested"]["fast"] = "unset"
            envelope["provenance"]["route"]["observed"]["fast"] = False
        unset_base_path, unset_candidate_path = tmp / "unset-b.json", tmp / "unset-c.json"
        write(unset_base_path, unset_base)
        write(unset_candidate_path, unset_candidate)
        unset_json = tmp / "unset.json"
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline", str(unset_base_path),
            "--candidate", str(unset_candidate_path),
            "--json", str(unset_json),
        )
        assert load(unset_json)["protocol_status"] == "comparable"

        for envelope in (unset_base, unset_candidate):
            envelope["provenance"]["route"]["observed"]["fast"] = True
        write(unset_base_path, unset_base)
        write(unset_candidate_path, unset_candidate)
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline", str(unset_base_path),
            "--candidate", str(unset_candidate_path),
            "--json", str(unset_json),
        )
        assert load(unset_json)["protocol_status"] == "comparable"

        explicit_mismatch = copy.deepcopy(candidate)
        explicit_mismatch["provenance"]["route"]["requested"]["fast"] = "on"
        explicit_mismatch["provenance"]["route"]["observed"]["fast"] = False
        explicit_path, explicit_json = tmp / "explicit-fast.json", tmp / "explicit-fast-out.json"
        write(explicit_path, explicit_mismatch)
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline", str(baseline_path),
            "--candidate", str(explicit_path),
            "--json", str(explicit_json),
            expected=2,
        )
        assert any(
            "explicit fast=on" in item for item in load(explicit_json)["blockers"]
        )

        observed_mismatch_base = copy.deepcopy(baseline)
        observed_mismatch_candidate = copy.deepcopy(candidate)
        for envelope in (observed_mismatch_base, observed_mismatch_candidate):
            envelope["provenance"]["route"]["requested"]["fast"] = "unset"
        observed_mismatch_base["provenance"]["route"]["observed"]["fast"] = False
        observed_mismatch_candidate["provenance"]["route"]["observed"]["fast"] = True
        observed_base_path = tmp / "observed-fast-b.json"
        observed_candidate_path = tmp / "observed-fast-c.json"
        observed_json = tmp / "observed-fast-out.json"
        write(observed_base_path, observed_mismatch_base)
        write(observed_candidate_path, observed_mismatch_candidate)
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline", str(observed_base_path),
            "--candidate", str(observed_candidate_path),
            "--json", str(observed_json),
            expected=2,
        )
        assert any(
            "observed effective fast state" in item
            for item in load(observed_json)["blockers"]
        )
        checks += 4

        mismatch = copy.deepcopy(candidate)
        mismatch["provenance"]["campaign"]["concurrency"] = 99
        mismatch_path, mismatch_json = tmp / "mismatch.json", tmp / "mismatch-out.json"
        write(mismatch_path, mismatch)
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(mismatch_path),
            "--json",
            str(mismatch_json),
            expected=2,
        )
        assert any("campaign.concurrency" in item for item in load(mismatch_json)["blockers"])
        checks += 1

        twice_base, twice_cand = copy.deepcopy(baseline), copy.deepcopy(candidate)
        for envelope in (twice_base, twice_cand):
            for row in envelope["benchmark_result"]["task_results"]:
                row["runs"] = 2
            rehash(envelope)
        twice_base_path, twice_cand_path = tmp / "twice-b.json", tmp / "twice-c.json"
        write(twice_base_path, twice_base)
        write(twice_cand_path, twice_cand)
        twice_json = tmp / "twice.json"
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline",
            str(twice_base_path),
            "--candidate",
            str(twice_cand_path),
            "--json",
            str(twice_json),
        )
        assert load(twice_json)["confidence"] == "insufficient-repeats"
        checks += 1

        value_none = tmp / "value-none.json"
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(candidate_path),
            "--objective",
            "value",
            "--json",
            str(value_none),
        )
        assert load(value_none)["objective_read"]["leader"] == "unavailable-floor"
        checks += 1

        cheap = copy.deepcopy(candidate)
        result = cheap["benchmark_result"]
        result.update(
            {
                "overall_score": 0.10,
                "overall_ci_lower": 0.05,
                "overall_ci_upper": 0.15,
                "overall_reliability": 0.10,
                "overall_worst_of_n": 0.10,
                "overall_cost_per_pass": 0.01,
            }
        )
        rehash(cheap)
        cheap_path, value_json = tmp / "cheap.json", tmp / "value.json"
        write(cheap_path, cheap)
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(cheap_path),
            "--objective",
            "value",
            "--min-score",
            "0.60",
            "--min-reliability",
            "0.60",
            "--min-worst-of-n",
            "0.40",
            "--json",
            str(value_json),
        )
        value = load(value_json)["objective_read"]
        assert value["leader"] == "baseline"
        assert value["eligibility"]["candidate"]["eligible"] is False
        checks += 2

        no_price_b, no_price_c = copy.deepcopy(baseline), copy.deepcopy(candidate)
        no_price_b["provenance"].pop("pricing")
        no_price_c["provenance"].pop("pricing")
        no_price_b_path, no_price_c_path = tmp / "no-price-b.json", tmp / "no-price-c.json"
        write(no_price_b_path, no_price_b)
        write(no_price_c_path, no_price_c)
        no_price_json = tmp / "no-price.json"
        run(
            str(SCRIPTS / "compare_clawbench_results.py"),
            "--baseline",
            str(no_price_b_path),
            "--candidate",
            str(no_price_c_path),
            "--json",
            str(no_price_json),
        )
        no_price = load(no_price_json)
        assert no_price["protocol_status"] == "comparable"
        assert no_price["metrics"]["overall_cost_per_pass"]["baseline"] is None
        checks += 2

        character_json = tmp / "character.json"
        run(
            str(SCRIPTS / "summarize_character_eval.py"),
            str(EXAMPLES / "sample-character-eval-summary.json"),
            "--json",
            str(character_json),
        )
        character = load(character_json)
        assert character["evidence_status"] == "usable"
        assert character["judge_agreement"] == "split"
        assert character["leader"] == "tie"
        checks += 3

        no_attestation = copy.deepcopy(load(EXAMPLES / "sample-character-eval-summary.json"))
        no_attestation.pop("clawgaugeAttestation")
        no_attestation_path, blocked_character = tmp / "no-attestation.json", tmp / "blocked-character.json"
        write(no_attestation_path, no_attestation)
        run(
            str(SCRIPTS / "summarize_character_eval.py"),
            str(no_attestation_path),
            "--json",
            str(blocked_character),
            expected=2,
        )
        assert load(blocked_character)["evidence_status"] == "blocked"
        checks += 1

        character_fixture = load(EXAMPLES / "sample-character-eval-summary.json")
        candidate_cases = [
            (
                "misattributed-route",
                lambda value: value["clawgaugeAttestation"]["candidates"][1].update(
                    observedModel="other"
                ),
                "misattributed",
            ),
            (
                "fallback-used",
                lambda value: value["clawgaugeAttestation"]["candidates"][1].update(
                    fallbackUsed=True
                ),
                "fallback was used",
            ),
            (
                "missing-thinking",
                lambda value: value["runs"][1].pop("thinkingDefault"),
                "thinking states are required",
            ),
            (
                "fast-mismatch",
                lambda value: value["clawgaugeAttestation"]["candidates"][1].update(
                    observedFastMode=True
                ),
                "fast state does not match",
            ),
            (
                "missing-reasoning-proof",
                lambda value: value["clawgaugeAttestation"]["candidates"][1].pop(
                    "reasoningProofSha256"
                ),
                "reasoning proof is missing",
            ),
        ]
        for name, mutate, expected_blocker in candidate_cases:
            case = copy.deepcopy(character_fixture)
            mutate(case)
            case_path = tmp / f"character-{name}.json"
            result_path = tmp / f"character-{name}-out.json"
            write(case_path, case)
            run(
                str(SCRIPTS / "summarize_character_eval.py"),
                str(case_path),
                "--json",
                str(result_path),
                expected=2,
            )
            result = load(result_path)
            assert result["evidence_status"] == "blocked"
            assert any(expected_blocker in item for item in result["blockers"])
            checks += 2

        qa_base = load(EXAMPLES / "sample-qa-suite-summary.json")
        qa_candidate_summary = qa_candidate(qa_base, "test/candidate")
        qa_base_path, qa_candidate_path = tmp / "qa-base.json", tmp / "qa-candidate.json"
        write(qa_base_path, qa_base)
        write(qa_candidate_path, qa_candidate_summary)
        qa_json = tmp / "qa.json"
        run(
            str(SCRIPTS / "score_qa_suite.py"),
            "--summary",
            str(qa_base_path),
            "--summary",
            str(qa_candidate_path),
            "--json",
            str(qa_json),
        )
        qa = load(qa_json)
        assert qa["comparison_status"] == "comparable"
        assert {item["gate_status"] for item in qa["models"]} == {"pass"}
        checks += 2

        qa_fail_path = tmp / "qa-fail.json"
        write(qa_fail_path, qa_candidate(qa_base, "test/candidate", "fail"))
        qa_fail_json = tmp / "qa-fail-out.json"
        run(
            str(SCRIPTS / "score_qa_suite.py"),
            "--summary",
            str(qa_base_path),
            "--summary",
            str(qa_fail_path),
            "--json",
            str(qa_fail_json),
            expected=1,
        )
        assert next(
            item for item in load(qa_fail_json)["models"] if item["model"] == "test/candidate"
        )["gate_status"] == "fail"
        checks += 1

        repeated_json = tmp / "repeated.json"
        run(
            str(SCRIPTS / "score_qa_suite.py"),
            "--summary",
            str(qa_base_path),
            "--summary",
            str(qa_base_path),
            "--summary",
            str(qa_fail_path),
            "--summary",
            str(qa_candidate_path),
            "--json",
            str(repeated_json),
            expected=1,
        )
        repeated = next(
            item for item in load(repeated_json)["models"] if item["model"] == "test/candidate"
        )
        assert repeated["attempt_count"] == 2
        assert repeated["gate_status"] == "fail"
        checks += 2

        run_root = tmp / "manifest-qa"
        scenario = "personal-approval-denial-stop"
        entries = []
        for index, model in enumerate(("test/baseline", "test/candidate"), 1):
            entry_id = f"e{index}"
            rel = f"entries/{entry_id}"
            entries.append(
                {
                    "entry_id": entry_id,
                    "attempt": 1,
                    "model": model,
                    "alternate_model": model,
                    "mode": "personal-agent-profile",
                    "profile": "personal-agent",
                    "provider_mode": "live-frontier",
                    "expected_scenarios": [scenario],
                    "fast_mode_requested": "unset",
                    "output_rel": rel,
                }
            )
            write(run_root / rel / "qa-suite-summary.json", profile_summary(model, scenario))
            write(run_root / rel / "qa-evidence.json", profile_evidence(scenario))
        write(
            run_root / "entries/e2/mqb-status.json",
            {
                "status_label": "stalled",
                "failure_class": "transport-timeout",
                "wall_seconds": 1.0,
            },
        )
        write(
            run_root / "run-manifest.json",
            {
                "schema_version": 3,
                "provider_mode": "live-frontier",
                "fast_mode_requested": "unset",
                "entries": entries,
                "results": [
                    {
                        "entry_id": "e1",
                        "status": "complete",
                        "failure_class": None,
                        "wall_seconds": 2.5,
                        "exit_code": 0,
                        "timed_out": False,
                        "fast_mode_effective": False,
                    },
                    {
                        "entry_id": "e2",
                        "status": "complete",
                        "failure_class": None,
                        "wall_seconds": 3.5,
                        "exit_code": 0,
                        "timed_out": False,
                        "fast_mode_effective": False,
                    },
                ],
            },
        )
        sidecar_json = tmp / "sidecar.json"
        run(
            str(SCRIPTS / "score_qa_suite.py"),
            "--run-dir",
            str(run_root),
            "--json",
            str(sidecar_json),
            expected=1,
        )
        sidecar_candidate = next(
            item for item in load(sidecar_json)["models"] if item["model"] == "test/candidate"
        )
        sidecar_baseline = next(
            item for item in load(sidecar_json)["models"] if item["model"] == "test/baseline"
        )
        assert sidecar_candidate["gate_status"] == "blocked"
        assert "transport-timeout" in sidecar_candidate["failure_classes"]
        assert sidecar_baseline["wall_seconds"] == 2.5
        assert sidecar_candidate["wall_seconds"] == 3.5
        assert sidecar_candidate["attempts"][0]["runner_result"]["status"] == "complete"
        assert sidecar_candidate["attempts"][0]["status"] == "stalled"
        checks += 6

        canonical_manifest = load(run_root / "run-manifest.json")
        result_contract_cases = [
            (
                "missing-result",
                lambda value: value["results"].pop(0),
                "manifest result missing for declared entry",
                "blocked",
            ),
            (
                "unknown-status",
                lambda value: value["results"][0].update(status="mystery"),
                "manifest result status is missing or invalid",
                "blocked",
            ),
            (
                "complete-exit-one",
                lambda value: value["results"][0].update(exit_code=1),
                "manifest result exit_code is nonzero",
                "blocked",
            ),
            (
                "complete-timed-out",
                lambda value: value["results"][0].update(timed_out=True),
                "manifest result timed_out is true",
                "stalled",
            ),
            (
                "contradictory-failure-class",
                lambda value: value["results"][0].update(failure_class="auth"),
                "manifest result failure_class contradicts complete status",
                "blocked",
            ),
        ]
        for name, mutate, expected_blocker, expected_status in result_contract_cases:
            case = copy.deepcopy(canonical_manifest)
            mutate(case)
            write(run_root / "run-manifest.json", case)
            case_json = tmp / f"manifest-result-{name}.json"
            run(
                str(SCRIPTS / "score_qa_suite.py"),
                "--run-dir",
                str(run_root),
                "--json",
                str(case_json),
                expected=2,
            )
            result = load(case_json)
            assert any(expected_blocker in item for item in result["comparison_blockers"])
            baseline_attempt = next(
                item for item in result["models"] if item["model"] == "test/baseline"
            )["attempts"][0]
            assert baseline_attempt["status"] == expected_status
            checks += 2
        write(run_root / "run-manifest.json", canonical_manifest)

        no_wall_manifest = load(run_root / "run-manifest.json")
        for result in no_wall_manifest["results"]:
            result.pop("wall_seconds")
        write(run_root / "run-manifest.json", no_wall_manifest)
        for entry in entries:
            summary_path = run_root / entry["output_rel"] / "qa-suite-summary.json"
            summary = load(summary_path)
            summary.pop("metrics")
            write(summary_path, summary)
        stalled_sidecar_path = run_root / "entries/e2/mqb-status.json"
        stalled_sidecar = load(stalled_sidecar_path)
        stalled_sidecar.pop("wall_seconds")
        write(stalled_sidecar_path, stalled_sidecar)
        no_wall_json, no_wall_report = tmp / "no-wall.json", tmp / "no-wall.md"
        run(
            str(SCRIPTS / "score_qa_suite.py"),
            "--run-dir",
            str(run_root),
            "--json",
            str(no_wall_json),
            "--out",
            str(no_wall_report),
            expected=1,
        )
        no_wall = load(no_wall_json)
        assert all(item["wall_seconds"] is None for item in no_wall["models"])
        assert "| n/a |" in no_wall_report.read_text(encoding="utf-8")
        checks += 2

        single_json = tmp / "single.json"
        run(
            str(SCRIPTS / "score_qa_suite.py"),
            "--summary",
            str(qa_base_path),
            "--json",
            str(single_json),
            expected=2,
        )
        assert load(single_json)["comparison_status"] == "blocked"
        checks += 1

        runner = import_script("run_openclaw_qa_gate")
        os.environ["CLAWGAUGE_TEST_SENTINEL"] = "must-not-leak"
        with tempfile.TemporaryDirectory(prefix="clawgauge-env-") as env_tmp:
            clean = runner.isolated_env(Path(env_tmp), [])
            passed = runner.isolated_env(Path(env_tmp) / "passed", ["CLAWGAUGE_TEST_SENTINEL"])
        assert "CLAWGAUGE_TEST_SENTINEL" not in clean
        assert passed["CLAWGAUGE_TEST_SENTINEL"] == "must-not-leak"
        accepted, errors = runner.validate_pass_env(["HOME"])
        assert accepted == [] and errors
        command = runner.build_command(
            "pnpm",
            Path("/repo"),
            Path("/out"),
            "test/model",
            "test/model",
            "live-frontier",
            1,
            runner.PERSONAL_AGENT_SCENARIOS,
            False,
            "unset",
        )
        assert command[2:6] == ["qa", "run", "--repo-root", "/repo"]
        assert "--qa-profile" in command and "personal-agent" in command
        assert "--thinking" not in command and "--fast" not in command
        assert "agent-tool-safety-approvals" in runner.PERSONAL_AGENT_SCENARIOS
        assert "personal-tool-safety-followthrough" not in runner.PERSONAL_AGENT_SCENARIOS
        assert "strict=True" not in (SCRIPTS / "run_openclaw_qa_gate.py").read_text()
        checks += 9

    print(f"ClawGauge self-test: PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
