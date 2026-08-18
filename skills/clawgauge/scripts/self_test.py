#!/usr/bin/env python3
"""Run deterministic, provider-free ClawGauge regression and adversarial checks."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
import statistics
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
    layers = [
        {
            "kind": layer.get("kind"),
            "enabled": layer.get("enabled"),
            "name": layer.get("name"),
            "version": layer.get("version"),
            "engine": layer.get("engine"),
        }
        for layer in cache["layers"]
    ]
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
        "effective_knobs": config.get("effective_knobs"),
        "capacity": {
            "visibility": capacity.get("visibility"),
            "limits": capacity.get("limits"),
        },
        "layers": sorted(layers, key=lambda layer: str(layer.get("kind"))),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    fingerprint = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    config["fingerprint"] = fingerprint
    cache["observed"]["configuration_fingerprint"] = fingerprint
    return fingerprint


def attach_cache_trace(tmp: Path, label: str, envelope: dict) -> Path:
    result = envelope["benchmark_result"]
    cache = envelope["provenance"]["cache"]
    observed = cache["observed"]
    route = envelope["provenance"]["route"]["observed"]
    pairs = [
        (row["task_id"], repetition)
        for row in result["task_results"]
        for repetition in range(1, int(row["runs"]) + 1)
    ]
    cold_p50, cold_p95 = (
        observed["cold_latency_ms"]["p50"],
        observed["cold_latency_ms"]["p95"],
    )
    warm_p50, warm_p95 = (
        observed["warm_latency_ms"]["p50"],
        observed["warm_latency_ms"]["p95"],
    )
    cold_walls = [cold_p50] * len(pairs)
    cold_walls[-1] = cold_p95
    warm_walls = [warm_p50] * (len(pairs) * 2)
    warm_walls[-1] = warm_p95
    task_walls = [result["overall_median_latency_ms"]] * len(pairs)
    task_walls[-1] = result["overall_p95_latency_ms"]
    total_reused = int(observed["reused_input_tokens"])
    warm_count = len(warm_walls)
    per_hit, remainder = divmod(total_reused, warm_count)
    events = []
    warm_index = 0
    for pair_index, ((task_id, repetition), task_wall) in enumerate(zip(pairs, task_walls)):
        task_started = float(pair_index * 100_000)
        task_completed = task_started + task_wall
        request_started = task_started + 50
        previous_request_id = None
        previous_prompt = None
        previous_next_prefix = None
        for turn_index in range(3):
            phase = "cold" if turn_index == 0 else "warm"
            if phase == "cold":
                cached, request_wall = 0, cold_walls[pair_index]
            else:
                cached = per_hit + (1 if warm_index < remainder else 0)
                request_wall = warm_walls[warm_index]
                warm_index += 1
            uncached = 6000 + turn_index
            request_id = f"{label}-{task_id}-{repetition}-{turn_index}"
            prompt = "sha256:" + hashlib.sha256(
                f"prompt:{label}:{task_id}:{repetition}:{turn_index}".encode()
            ).hexdigest()
            prefix = previous_next_prefix or "sha256:" + hashlib.sha256(b"").hexdigest()
            next_prefix = "sha256:" + hashlib.sha256(
                f"next-prefix:{label}:{task_id}:{repetition}:{turn_index}".encode()
            ).hexdigest()
            ttft = max(1.0, round(request_wall * 0.35, 3))
            prefill = round(ttft * 0.8, 3)
            first_token = request_started + ttft
            request_completed = request_started + request_wall
            has_tool = turn_index < 2
            tool_wall = 75.0 if has_tool else 0.0
            tool_completed = request_completed + tool_wall
            tool_calls = [f"tool-{label}-{task_id}-{repetition}-{turn_index}"] if has_tool else []
            tool_results = [
                "sha256:" + hashlib.sha256(
                    f"tool-result:{label}:{task_id}:{repetition}:{turn_index}".encode()
                ).hexdigest()
            ] if has_tool else []
            assert tool_completed <= task_completed
            events.append(
                {
                    "task_id": task_id,
                    "repetition": repetition,
                    "turn_index": turn_index,
                    "request_id": request_id,
                    "phase": phase,
                    "provider": route["provider"],
                    "model": route["model"],
                    "fallback_used": False,
                    "backend_pid": 10000 + pair_index,
                    "backend_started_at": f"synthetic-start-{pair_index}",
                    "runtime_id": f"synthetic-runtime-{pair_index}",
                    "cache_epoch": f"synthetic-epoch-{pair_index}",
                    "prompt_fingerprint": prompt,
                    "prefix_fingerprint": prefix,
                    "next_prefix_fingerprint": next_prefix,
                    "parent_request_id": previous_request_id,
                    "parent_prompt_fingerprint": previous_prompt,
                    "append_only": phase == "warm",
                    "openclaw_event_fingerprint": "sha256:" + hashlib.sha256(
                        f"openclaw-event:{label}:{task_id}:{repetition}:{turn_index}".encode()
                    ).hexdigest(),
                    "cache_configuration_fingerprint": observed[
                        "configuration_fingerprint"
                    ],
                    "gross_input_tokens": cached + uncached,
                    "cached_input_tokens": cached,
                    "uncached_input_tokens": uncached,
                    "written_input_tokens": cached + uncached,
                    "response_memo_hit": False,
                    "tool_call_ids": tool_calls,
                    "tool_result_fingerprints": tool_results,
                    "startup_ms": 900.0 if phase == "cold" else 0.0,
                    "readiness_ms": 700.0 if phase == "cold" else 0.0,
                    "ttft_ms": ttft,
                    "prefill_ms": prefill,
                    "decode_ms": request_completed - first_token,
                    "request_wall_ms": request_wall,
                    "tool_wall_ms": tool_wall,
                    "task_wall_ms": task_wall,
                    "task_started_at_ms": task_started,
                    "request_started_at_ms": request_started,
                    "first_token_at_ms": first_token,
                    "request_completed_at_ms": request_completed,
                    "tool_completed_at_ms": tool_completed,
                    "task_completed_at_ms": task_completed,
                    "process_rss_bytes": 2_000_000_000 + pair_index * 10_000_000,
                    "accelerator_active_bytes": 1_000_000_000 + turn_index * 1_000_000,
                    "accelerator_peak_bytes": 1_100_000_000 + turn_index * 1_000_000,
                    "cache_resident_bytes": 10_000_000 + turn_index * 1_000_000,
                    "cache_resident_tokens": 6000 + turn_index * 1000,
                    "cache_evictions": 0,
                }
            )
            previous_request_id = request_id
            previous_prompt = prompt
            previous_next_prefix = next_prefix
            request_started = tool_completed + 25
    def latency(values: list[float]) -> dict[str, float]:
        ordered = sorted(values)
        return {
            "p50": float(statistics.median(values)),
            "p95": float(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]),
        }
    runtime_log = tmp / f"{label}-runtime.log"
    openclaw_trace = tmp / f"{label}-openclaw-trace.jsonl"
    parser_artifact = tmp / f"{label}-parser.py"
    runtime_log.write_text(f"synthetic runtime log for {label}\n", encoding="utf-8")
    openclaw_trace.write_text(
        "\n".join(json.dumps({"event": event["openclaw_event_fingerprint"]}) for event in events) + "\n",
        encoding="utf-8",
    )
    parser_artifact.write_text("# synthetic cache parser\n", encoding="utf-8")
    def artifact_proof(path: Path, **extra: str) -> dict:
        proof = {
            "reference": path.name,
            "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        proof.update(extra)
        return proof
    trace = {
        "schema_version": "clawgauge.cache-events.v2",
        "hit_metric": observed["hit_metric"],
        "source": {
            "runtime_log": artifact_proof(runtime_log),
            "openclaw_trace": artifact_proof(openclaw_trace),
            "parser": artifact_proof(
                parser_artifact, name="synthetic-cache-parser", version="1.0.0"
            ),
        },
        "events": events,
    }
    path = tmp / f"{label}-cache-events.json"
    raw = json.dumps(trace, indent=2) + "\n"
    path.write_text(raw, encoding="utf-8")
    observed.update(
        {
            "gross_input_tokens": sum(e["gross_input_tokens"] for e in events),
            "response_memo_hit_count": 0,
            "hit_rate": 1.0,
            "startup_latency_ms": latency([e["startup_ms"] for e in events if e["phase"] == "cold"]),
            "readiness_latency_ms": latency([e["readiness_ms"] for e in events if e["phase"] == "cold"]),
            "ttft_latency_ms": latency([e["ttft_ms"] for e in events]),
            "prefill_latency_ms": latency([e["prefill_ms"] for e in events]),
            "decode_latency_ms": latency([e["decode_ms"] for e in events]),
            "peak_process_rss_bytes": max(e["process_rss_bytes"] for e in events),
            "peak_accelerator_bytes": max(e["accelerator_peak_bytes"] for e in events),
            "peak_cache_resident_bytes": max(e["cache_resident_bytes"] for e in events),
            "peak_cache_resident_tokens": max(e["cache_resident_tokens"] for e in events),
            "cache_evictions": max(e["cache_evictions"] for e in events),
            "trace_proof": {
                "kind": "clawgauge-cache-events",
                "reference": path.name,
                "sha256": "sha256:" + hashlib.sha256(raw.encode()).hexdigest(),
            },
        }
    )
    return path


def rehash_trace(path: Path, envelope: dict) -> None:
    raw = path.read_bytes()
    envelope["provenance"]["cache"]["observed"]["trace_proof"]["sha256"] = (
        "sha256:" + hashlib.sha256(raw).hexdigest()
    )


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
        assert summary["schema_version"] == "clawgauge.evidence.v3"
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
        assert comparison["facts"]["cache_speed_comparable"] is False
        checks += 2

        traced_baseline, traced_candidate = copy.deepcopy(baseline), copy.deepcopy(candidate)
        baseline_trace = attach_cache_trace(tmp, "bound-baseline", traced_baseline)
        candidate_trace = attach_cache_trace(tmp, "bound-candidate", traced_candidate)
        traced_result = compare_case(
            tmp,
            "content-bound-cache",
            traced_baseline,
            traced_candidate,
            objective="speed",
        )
        assert traced_result["facts"]["cache_speed_comparable"] is True
        assert traced_result["objective_read"]["leader"] == "baseline"
        assert traced_result["facts"]["baseline_cache"]["trace_valid"] is True
        checks += 3

        bad_digest = copy.deepcopy(traced_candidate)
        bad_digest["provenance"]["cache"]["observed"]["trace_proof"]["sha256"] = "sha256:" + "0" * 64
        bad_digest_result = compare_case(
            tmp, "cache-trace-bad-digest", traced_baseline, bad_digest, objective="speed"
        )
        assert bad_digest_result["facts"]["cache_speed_comparable"] is False
        assert bad_digest_result["objective_read"]["leader"] == "unavailable-cache-evidence"
        checks += 2

        restarted = copy.deepcopy(traced_candidate)
        restarted_trace = json.loads(candidate_trace.read_text())
        restarted_trace["events"][1]["backend_pid"] += 1
        candidate_trace.write_text(json.dumps(restarted_trace, indent=2) + "\n")
        rehash_trace(candidate_trace, restarted)
        restarted_result = compare_case(
            tmp, "cache-trace-process-restart", traced_baseline, restarted, objective="speed"
        )
        assert restarted_result["facts"]["cache_speed_comparable"] is False
        assert any(
            "process/cache epoch changed" in item
            for item in restarted_result["facts"]["candidate_cache"]["trace_errors"]
        )
        checks += 2

        # Restore the fixture for later trace mutations.
        candidate_trace = attach_cache_trace(tmp, "bound-candidate", traced_candidate)

        reused_epoch = copy.deepcopy(traced_candidate)
        reused_epoch_trace = json.loads(candidate_trace.read_text())
        first_epoch = reused_epoch_trace["events"][0]["cache_epoch"]
        for event in reused_epoch_trace["events"][3:6]:
            event["cache_epoch"] = first_epoch
        candidate_trace.write_text(json.dumps(reused_epoch_trace, indent=2) + "\n")
        rehash_trace(candidate_trace, reused_epoch)
        reused_epoch_result = compare_case(
            tmp, "cache-trace-reused-epoch", traced_baseline, reused_epoch, objective="speed"
        )
        assert any(
            "cache epoch was reused" in item
            for item in reused_epoch_result["facts"]["candidate_cache"]["trace_errors"]
        )
        checks += 1

        candidate_trace = attach_cache_trace(tmp, "bound-candidate", traced_candidate)
        impossible_tokens = copy.deepcopy(traced_candidate)
        impossible_trace = json.loads(candidate_trace.read_text())
        impossible_trace["events"][1]["gross_input_tokens"] += 1
        candidate_trace.write_text(json.dumps(impossible_trace, indent=2) + "\n")
        rehash_trace(candidate_trace, impossible_tokens)
        impossible_trace_result = compare_case(
            tmp, "cache-trace-impossible-tokens", traced_baseline, impossible_tokens, objective="speed"
        )
        assert any(
            "token accounting is impossible" in item
            for item in impossible_trace_result["facts"]["candidate_cache"]["trace_errors"]
        )
        checks += 1

        candidate_trace = attach_cache_trace(tmp, "bound-candidate", traced_candidate)
        warm_miss = copy.deepcopy(traced_candidate)
        warm_miss_trace = json.loads(candidate_trace.read_text())
        missed = warm_miss_trace["events"][1]
        missed["uncached_input_tokens"] += missed["cached_input_tokens"]
        missed["cached_input_tokens"] = 0
        candidate_trace.write_text(json.dumps(warm_miss_trace, indent=2) + "\n")
        rehash_trace(candidate_trace, warm_miss)
        warm_miss_result = compare_case(
            tmp, "cache-trace-post-warm-miss", traced_baseline, warm_miss, objective="speed"
        )
        assert any(
            "post-cold cache miss" in item
            for item in warm_miss_result["facts"]["candidate_cache"]["trace_errors"]
        )
        checks += 1

        # Cache-events v2 adversarial coverage: hashes, cold/warm semantics,
        # metric identity, source binding, lineage, tools, timing, and memory.
        malformed_hash = copy.deepcopy(candidate)
        malformed_hash_trace = attach_cache_trace(tmp, "malformed-prefix", malformed_hash)
        malformed_hash_data = json.loads(malformed_hash_trace.read_text())
        malformed_hash_data["events"][1]["prefix_fingerprint"] = "sha256:x"
        malformed_hash_trace.write_text(json.dumps(malformed_hash_data, indent=2) + "\n")
        rehash_trace(malformed_hash_trace, malformed_hash)
        malformed_hash_result = compare_case(
            tmp, "cache-trace-malformed-prefix", traced_baseline, malformed_hash, objective="speed"
        )
        assert malformed_hash_result["facts"]["cache_speed_comparable"] is False
        assert any("content fingerprint is invalid" in item for item in malformed_hash_result["facts"]["candidate_cache"]["trace_errors"])

        cold_hit = copy.deepcopy(candidate)
        cold_hit_trace = attach_cache_trace(tmp, "cold-hit", cold_hit)
        cold_hit_data = json.loads(cold_hit_trace.read_text())
        cold_event = cold_hit_data["events"][0]
        cold_event["cached_input_tokens"] = 1
        cold_event["uncached_input_tokens"] -= 1
        cold_hit["provenance"]["cache"]["observed"]["reused_input_tokens"] += 1
        cold_hit_trace.write_text(json.dumps(cold_hit_data, indent=2) + "\n")
        rehash_trace(cold_hit_trace, cold_hit)
        cold_hit_result = compare_case(
            tmp, "cache-trace-cold-hit", traced_baseline, cold_hit, objective="speed"
        )
        assert any("cold request must have zero cached" in item for item in cold_hit_result["facts"]["candidate_cache"]["trace_errors"])

        fake_metric = copy.deepcopy(candidate)
        fake_metric_trace = attach_cache_trace(tmp, "fake-metric", fake_metric)
        fake_metric_data = json.loads(fake_metric_trace.read_text())
        fake_metric_data["hit_metric"] = "unicorns"
        fake_metric["provenance"]["cache"]["observed"]["hit_metric"] = "unicorns"
        fake_metric_trace.write_text(json.dumps(fake_metric_data, indent=2) + "\n")
        rehash_trace(fake_metric_trace, fake_metric)
        fake_metric_result = compare_case(
            tmp, "cache-trace-fake-metric", traced_baseline, fake_metric, objective="speed", expected=2
        )
        assert any("hit counters and metric are incomplete" in item for item in fake_metric_result["blockers"])

        bad_lineage = copy.deepcopy(candidate)
        bad_lineage_trace = attach_cache_trace(tmp, "bad-lineage", bad_lineage)
        bad_lineage_data = json.loads(bad_lineage_trace.read_text())
        bad_lineage_data["events"][1]["prefix_fingerprint"] = "sha256:" + "1" * 64
        bad_lineage_trace.write_text(json.dumps(bad_lineage_data, indent=2) + "\n")
        rehash_trace(bad_lineage_trace, bad_lineage)
        bad_lineage_result = compare_case(
            tmp, "cache-trace-bad-lineage", traced_baseline, bad_lineage, objective="speed"
        )
        assert any("append-only prefix lineage differs" in item for item in bad_lineage_result["facts"]["candidate_cache"]["trace_errors"])

        no_tools = copy.deepcopy(candidate)
        no_tools_trace = attach_cache_trace(tmp, "no-tools", no_tools)
        no_tools_data = json.loads(no_tools_trace.read_text())
        no_tools_data["events"][0]["tool_call_ids"] = []
        no_tools_data["events"][0]["tool_result_fingerprints"] = []
        no_tools_trace.write_text(json.dumps(no_tools_data, indent=2) + "\n")
        rehash_trace(no_tools_trace, no_tools)
        no_tools_result = compare_case(
            tmp, "cache-trace-no-tools", traced_baseline, no_tools, objective="speed"
        )
        assert any("warm continuation lacks a preceding tool result" in item for item in no_tools_result["facts"]["candidate_cache"]["trace_errors"])

        bad_timing = copy.deepcopy(candidate)
        bad_timing_trace = attach_cache_trace(tmp, "bad-timing", bad_timing)
        bad_timing_data = json.loads(bad_timing_trace.read_text())
        bad_timing_data["events"][1]["first_token_at_ms"] += 1
        bad_timing_trace.write_text(json.dumps(bad_timing_data, indent=2) + "\n")
        rehash_trace(bad_timing_trace, bad_timing)
        bad_timing_result = compare_case(
            tmp, "cache-trace-bad-timing", traced_baseline, bad_timing, objective="speed"
        )
        assert any("timing durations do not match" in item for item in bad_timing_result["facts"]["candidate_cache"]["trace_errors"])

        bad_memory = copy.deepcopy(candidate)
        bad_memory_trace = attach_cache_trace(tmp, "bad-memory", bad_memory)
        bad_memory_data = json.loads(bad_memory_trace.read_text())
        bad_memory_data["events"][1]["accelerator_active_bytes"] = bad_memory_data["events"][1]["accelerator_peak_bytes"] + 1
        bad_memory_trace.write_text(json.dumps(bad_memory_data, indent=2) + "\n")
        rehash_trace(bad_memory_trace, bad_memory)
        bad_memory_result = compare_case(
            tmp, "cache-trace-bad-memory", traced_baseline, bad_memory, objective="speed"
        )
        assert any("active accelerator memory exceeds peak" in item for item in bad_memory_result["facts"]["candidate_cache"]["trace_errors"])

        bad_source = copy.deepcopy(candidate)
        bad_source_trace = attach_cache_trace(tmp, "bad-source", bad_source)
        bad_source_data = json.loads(bad_source_trace.read_text())
        bad_source_runtime = tmp / bad_source_data["source"]["runtime_log"]["reference"]
        bad_source_runtime.write_text("tampered runtime source\n", encoding="utf-8")
        bad_source_result = compare_case(
            tmp, "cache-trace-bad-source", traced_baseline, bad_source, objective="speed"
        )
        assert any("runtime log artifact hash mismatch" in item for item in bad_source_result["facts"]["candidate_cache"]["trace_errors"])

        invalid_events = tmp / "invalid-cache-events.json"
        invalid_events.write_text('[{}]\n', encoding="utf-8")
        builder_source = tmp / "builder-source.log"
        builder_trace = tmp / "builder-openclaw.jsonl"
        builder_parser = tmp / "builder-parser.py"
        for path in (builder_source, builder_trace, builder_parser):
            path.write_text("synthetic\n", encoding="utf-8")
        invalid_build = run(
            str(SCRIPTS / "build_cache_trace.py"),
            str(invalid_events),
            "--out", str(tmp / "invalid-built-trace.json"),
            "--runtime-log", str(builder_source),
            "--openclaw-trace", str(builder_trace),
            "--parser-artifact", str(builder_parser),
            "--parser-name", "synthetic-parser",
            "--parser-version", "1.0.0",
            expected=2,
        )
        assert "missing required fields" in invalid_build.stderr
        checks += 11

        route_adapter = copy.deepcopy(candidate)
        route_adapter["provenance"]["protocol"]["adapter"] = "candidate-native-adapter"
        route_adapter_result = compare_case(
            tmp, "route-operational-adapter", baseline, route_adapter
        )
        assert route_adapter_result["protocol_status"] == "comparable"
        checks += 1

        ablation_base, ablation_candidate = copy.deepcopy(traced_baseline), copy.deepcopy(traced_candidate)
        ablation_base["provenance"]["claim_scope"] = "cache-ablation"
        ablation_candidate["provenance"]["claim_scope"] = "cache-ablation"
        ablation_result = compare_case(
            tmp, "cache-ablation-route-mismatch", ablation_base, ablation_candidate, expected=2
        )
        assert any("same exact route" in item for item in ablation_result["blockers"])
        checks += 1

        legacy = copy.deepcopy(baseline)
        legacy["schema_version"] = "clawgauge.evidence.v1"
        legacy_result = compare_case(tmp, "legacy-cache-schema", legacy, candidate, expected=2)
        assert any("clawgauge.evidence.v3" in item for item in legacy_result["blockers"])
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

        missing_memo_layer = copy.deepcopy(candidate)
        missing_memo_layer["provenance"]["cache"]["layers"] = [
            layer for layer in missing_memo_layer["provenance"]["cache"]["layers"]
            if layer["kind"] != "full-response-memoization"
        ]
        rehash_cache(missing_memo_layer)
        missing_memo_result = compare_case(tmp, "missing-response-memo-layer", baseline, missing_memo_layer, expected=2)
        assert any("explicit full-response memoization layer is required" in item for item in missing_memo_result["blockers"])
        checks += 1

        bad_fingerprint = copy.deepcopy(candidate)
        bad_fingerprint["provenance"]["cache"]["configuration"]["fingerprint"] = "sha256:bad"
        bad_fingerprint_result = compare_case(tmp, "bad-cache-fingerprint", baseline, bad_fingerprint, expected=2)
        assert any("cache configuration fingerprint mismatch" in item for item in bad_fingerprint_result["blockers"])
        checks += 1

        knob_unhashed = copy.deepcopy(candidate)
        knob_unhashed["provenance"]["cache"]["configuration"]["effective_knobs"]["eviction_policy"] = "aggressive-lru"
        knob_unhashed_result = compare_case(tmp, "cache-knob-unhashed", baseline, knob_unhashed, expected=2)
        assert any("cache configuration fingerprint mismatch" in item for item in knob_unhashed_result["blockers"])

        knob_rehashed = copy.deepcopy(baseline)
        knob_rehashed["provenance"]["cache"]["configuration"]["effective_knobs"]["eviction_policy"] = "aggressive-lru"
        rehash_cache(knob_rehashed)
        knob_rehashed_result = compare_case(tmp, "cache-knob-rehashed", baseline, knob_rehashed, expected=2)
        assert any("same exact route has different cache configuration" in item for item in knob_rehashed_result["blockers"])
        checks += 2

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
            primary = next(layer for layer in cache["layers"] if layer["kind"] == "prefix-kv")
            primary.update(
                kind="opaque-provider-managed",
                name=cache["runtime"]["name"],
                version="opaque",
                engine=cache["runtime"]["engine"],
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
        memo_layer = next(
            layer for layer in memo_enabled["provenance"]["cache"]["layers"]
            if layer["kind"] == "full-response-memoization"
        )
        memo_layer["enabled"] = True
        rehash_cache(memo_enabled)
        memo_enabled_result = compare_case(tmp, "cache-full-response-enabled-no-trace", baseline, memo_enabled, expected=2)
        assert any("enabled response memoization requires valid per-request no-hit proof" in item for item in memo_enabled_result["blockers"])
        checks += 1

        memo_hit = copy.deepcopy(candidate)
        memo_hit_trace = attach_cache_trace(tmp, "memo-hit", memo_hit)
        memo_hit_events = json.loads(memo_hit_trace.read_text())
        memo_hit_events["events"][1]["response_memo_hit"] = True
        memo_hit_trace.write_text(json.dumps(memo_hit_events, indent=2) + "\n")
        memo_hit["provenance"]["cache"]["observed"]["response_memo_hit_count"] = 1
        rehash_trace(memo_hit_trace, memo_hit)
        memo_hit_result = compare_case(tmp, "cache-full-response-hit", baseline, memo_hit, expected=2)
        assert any("full-response memoization hit invalidates" in item for item in memo_hit_result["blockers"])
        checks += 1

        memo_enabled_proven = copy.deepcopy(candidate)
        memo_layer = next(
            layer for layer in memo_enabled_proven["provenance"]["cache"]["layers"]
            if layer["kind"] == "full-response-memoization"
        )
        memo_layer["enabled"] = True
        rehash_cache(memo_enabled_proven)
        attach_cache_trace(tmp, "memo-enabled-proven", memo_enabled_proven)
        memo_enabled_proven_result = compare_case(
            tmp, "cache-full-response-enabled-proven-no-hit", baseline, memo_enabled_proven
        )
        assert memo_enabled_proven_result["protocol_status"] == "comparable"
        checks += 1

        residency_hits = copy.deepcopy(candidate)
        residency_cache = residency_hits["provenance"]["cache"]
        residency_cache["runtime"]["kind"] = "residency-only"
        next(layer for layer in residency_cache["layers"] if layer["kind"] == "prefix-kv")["kind"] = "residency-only"
        rehash_cache(residency_hits)
        residency_result = compare_case(tmp, "cache-residency-hits", baseline, residency_hits, expected=2)
        assert any("residency-only cache cannot claim" in item for item in residency_result["blockers"])
        checks += 1

        embedding_tokens = copy.deepcopy(candidate)
        embedding_tokens_cache = embedding_tokens["provenance"]["cache"]
        embedding_tokens_cache["runtime"]["kind"] = "embedding-result"
        next(layer for layer in embedding_tokens_cache["layers"] if layer["kind"] == "prefix-kv")["kind"] = "embedding-result"
        rehash_cache(embedding_tokens)
        embedding_result = compare_case(tmp, "cache-embedding-input-tokens", baseline, embedding_tokens, expected=2)
        assert any("embedding-result cache cannot claim reused model input" in item for item in embedding_result["blockers"])
        checks += 1

        embedding_valid = copy.deepcopy(candidate)
        embedding_valid_cache = embedding_valid["provenance"]["cache"]
        embedding_valid_cache["runtime"]["kind"] = "embedding-result"
        next(layer for layer in embedding_valid_cache["layers"] if layer["kind"] == "prefix-kv")["kind"] = "embedding-result"
        embedding_valid_cache["observed"]["reused_input_tokens"] = 0
        embedding_valid_cache["observed"]["hit_metric"] = "cached_input_tokens"
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

        pilot_path = tmp / "campaign-pilot.json"
        pilot_trace_a = tmp / "campaign-pilot-route-a-cache.json"
        pilot_trace_b = tmp / "campaign-pilot-route-b-cache.json"
        pilot_trace_a.write_text('{"route":"a"}\n', encoding="utf-8")
        pilot_trace_b.write_text('{"route":"b"}\n', encoding="utf-8")
        def pilot_proof(path: Path) -> dict:
            return {
                "reference": path.name,
                "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        def pilot_route(envelope: dict, trace: Path, multiplier: int) -> dict:
            route = envelope["provenance"]["route"]["observed"]
            return {
                "route": {
                    "provider": route["provider"],
                    "model": route["model"],
                    "adapter": envelope["provenance"]["protocol"]["adapter"],
                    "reasoning": route["reasoning"],
                    "fast": route["fast"],
                    "cache_configuration_fingerprint": envelope["provenance"]["cache"]["configuration"]["fingerprint"],
                },
                "cache_profile": "controlled-cold-then-warm",
                "cache_trace_proof": pilot_proof(trace),
                "retry_rate": 0.05,
                "startup_ms": [1000 * multiplier, 1200 * multiplier, 1500 * multiplier],
                "task_wall_ms": [10000 * multiplier, 12000 * multiplier, 16000 * multiplier],
                "reset_ms": [100 * multiplier, 120 * multiplier, 150 * multiplier],
                "qa_wall_ms": [2000 * multiplier, 2200 * multiplier, 2600 * multiplier],
                "judge_wall_ms": [],
            }
        write(
            pilot_path,
            {
                "schema_version": "clawgauge.campaign-pilot.v2",
                "cache_profile": "controlled-cold-then-warm",
                "routes": [
                    pilot_route(baseline, pilot_trace_a, 1),
                    pilot_route(candidate, pilot_trace_b, 8),
                ],
            },
        )
        estimate_path = tmp / "campaign-estimate.json"
        run(
            str(SCRIPTS / "estimate_campaign.py"),
            str(pilot_path),
            "--cache-profile",
            "controlled-cold-then-warm",
            "--tasks",
            "9",
            "--repetitions",
            "3",
            "--budget-hours",
            "5",
            "--json",
            str(estimate_path),
        )
        estimate = load(estimate_path)
        assert estimate["route_count"] == 2
        assert estimate["routes"][0]["counts"]["task_wall_ms"] == 27
        assert estimate["routes"][1]["expected_ms"] > estimate["routes"][0]["expected_ms"] * 7
        assert estimate["expected_ms"] == sum(route["expected_ms"] for route in estimate["routes"])
        assert estimate["within_budget"] is True
        mismatch = run(
            str(SCRIPTS / "estimate_campaign.py"),
            str(pilot_path),
            "--cache-profile",
            "route-native",
            "--tasks",
            "9",
            "--repetitions",
            "3",
            expected=2,
        )
        assert "does not match" in mismatch.stderr
        unbound_pilot = load(pilot_path)
        unbound_pilot["routes"][1]["cache_trace_proof"]["sha256"] = "sha256:" + "0" * 64
        write(pilot_path, unbound_pilot)
        unbound = run(
            str(SCRIPTS / "estimate_campaign.py"),
            str(pilot_path),
            "--cache-profile",
            "controlled-cold-then-warm",
            "--tasks",
            "9",
            "--repetitions",
            "3",
            expected=2,
        )
        assert "cache trace proof is invalid" in unbound.stderr
        checks += 7

        truth_test = run(str(SCRIPTS / "test_truthfulness.py"))
        assert "ClawGauge truthfulness tests: PASS" in truth_test.stdout
        checks += 1

        cache_qualification_test = run(str(SCRIPTS / "test_cache_qualification.py"))
        assert "ClawGauge cache qualification tests: PASS" in cache_qualification_test.stdout
        checks += 1

        local_admission_test = run(str(SCRIPTS / "test_local_cache_admission_plan.py"))
        assert "ClawGauge local cache admission tests: PASS" in local_admission_test.stdout
        checks += 1

        decision_grade_test = run(str(SCRIPTS / "test_decision_grade.py"))
        assert "ClawGauge decision-grade tests: PASS" in decision_grade_test.stdout
        checks += 1

        assert comparison["decision_grade"] is False
        assert comparison["decision_grade_requirements"]["core_19_coverage"] is False
        checks += 2

    print(f"ClawGauge self-test: PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
