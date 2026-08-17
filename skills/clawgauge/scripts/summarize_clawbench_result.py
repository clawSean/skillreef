#!/usr/bin/env python3
"""Summarize one versioned ClawGauge ShellBench evidence envelope."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from compare_clawbench_results import (
    SCHEMA,
    get,
    number,
    pricing_valid,
    provenance_of,
    result_of,
    task_rows,
    validate_envelope,
)


def read_result(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("result root must be a JSON object")
    return value


def fmt(value: Any, digits: int = 3) -> str:
    value = number(value)
    return "n/a" if value is None else f"{value:.{digits}f}"


def pct(value: Any) -> str:
    value = number(value)
    return "n/a" if value is None else f"{value * 100:.0f}%"


def failure_evidence(result: dict[str, Any]) -> dict[str, Any] | None:
    value = result.get("overall_failure_mode_counts")
    return value if "overall_failure_mode_counts" in result and isinstance(value, dict) else None


def summary_object(envelope: dict[str, Any], source: Path) -> dict[str, Any]:
    result, prov = result_of(envelope), provenance_of(envelope)
    blockers, facts = validate_envelope(envelope, "evidence", source.parent)
    rows = task_rows(result)
    priced = pricing_valid(prov)
    metric_keys = (
        "overall_score", "overall_ci_lower", "overall_ci_upper",
        "overall_completion", "overall_trajectory", "overall_behavior",
        "overall_reliability", "overall_pass_hat_k", "overall_worst_of_n",
        "overall_median_latency_ms", "overall_p95_latency_ms",
        "overall_input_tokens", "overall_output_tokens",
        "overall_reasoning_tokens", "overall_total_tokens",
        "overall_tokens_per_pass", "overall_cost_usd", "overall_cost_per_pass",
    )
    metrics = {key: number(result.get(key)) for key in metric_keys}
    if not priced:
        metrics["overall_cost_usd"] = None
        metrics["overall_cost_per_pass"] = None
    tasks = []
    for task_id, item in sorted(rows.items()):
        tasks.append({
            "task_id": task_id,
            "runs": item.get("runs"),
            "score": number(item.get("mean_task_score")),
            "completion": number(item.get("mean_completion_score")),
            "trajectory": number(item.get("mean_trajectory_score")),
            "behavior": number(item.get("mean_behavior_score")),
            "reliability": number(item.get("reliability_score")),
            "pass_hat_k": item.get("pass_hat_k"),
            "worst_of_n": number(item.get("worst_of_n")),
            "cost_per_pass": number(item.get("cost_per_pass")) if priced else None,
            "capabilities": item.get("capabilities") or [],
            "failure_modes": item.get("failure_mode_counts")
            if isinstance(item.get("failure_mode_counts"), dict) else None,
        })
    return {
        "source": source.name,
        "schema_version": envelope.get("schema_version"),
        "artifact_status": "incomplete" if blockers else "complete",
        "missing_or_invalid_evidence": blockers,
        "model": result.get("model"),
        "provider": result.get("provider"),
        "benchmark_version": result.get("benchmark_version"),
        "openclaw_version": result.get("openclaw_version"),
        "openclaw_commit": get(prov, "openclaw", "commit"),
        "shellbench_commit": get(prov, "shellbench", "commit"),
        "host_class": get(prov, "host", "class"),
        "campaign_id": get(prov, "campaign", "id"),
        "route_requested": get(prov, "route", "requested"),
        "route_observed": get(prov, "route", "observed"),
        "route_attribution": facts.get("route", {}),
        "judge_requested": get(prov, "judge", "requested"),
        "judge_observed": get(prov, "judge", "observed"),
        "release_id": get(prov, "release", "id"),
        "task_ids_fingerprint": get(prov, "release", "task_ids_fingerprint"),
        "pricing_source": get(prov, "pricing", "source") if priced else None,
        "pricing_as_of": get(prov, "pricing", "as_of") if priced else None,
        "pricing_currency": get(prov, "pricing", "currency") if priced else None,
        "cache": facts.get("cache", {}),
        "task_count": len(tasks),
        "min_runs_per_task": min([int(number(item["runs"]) or 0) for item in tasks] or [0]),
        "metrics": metrics,
        "failure_modes": failure_evidence(result),
        "tasks": tasks,
    }


def render(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    lines = [
        f"# ShellBench Summary: {summary['model'] or 'unknown'}", "",
        f"- Artifact: **{summary['artifact_status']}**",
        f"- Source label: {summary['source']}",
        f"- Envelope: {summary['schema_version'] or 'n/a'}",
        f"- Provider / model: {summary['provider'] or 'n/a'} / {summary['model'] or 'n/a'}",
        f"- Benchmark: {summary['benchmark_version'] or 'n/a'}",
        f"- OpenClaw: {summary['openclaw_version'] or 'n/a'} at {summary['openclaw_commit'] or 'n/a'}",
        f"- ShellBench commit: {summary['shellbench_commit'] or 'n/a'}",
        f"- Host / campaign: {summary['host_class'] or 'n/a'} / {summary['campaign_id'] or 'n/a'}",
        f"- Routing / downstream evidence: {summary['route_attribution'].get('routing_mode') or 'n/a'} / {summary['route_attribution'].get('downstream_count', 0)} observations / {summary['route_attribution'].get('downstream_fingerprint') or 'n/a'}",
        f"- Release / fingerprint: {summary['release_id'] or 'n/a'} / {summary['task_ids_fingerprint'] or 'n/a'}",
        f"- Tasks / minimum runs: {summary['task_count']} / {summary['min_runs_per_task']}", "",
    ]
    if summary["missing_or_invalid_evidence"]:
        lines.extend(["## Missing Or Invalid Evidence", ""])
        lines.extend(f"- {item}" for item in summary["missing_or_invalid_evidence"])
        lines.append("")
    lines.extend([
        "## Score Surfaces", "",
        f"- Overall: {fmt(metrics['overall_score'])} (CI {fmt(metrics['overall_ci_lower'])}–{fmt(metrics['overall_ci_upper'])})",
        f"- Completion / trajectory / behavior: {fmt(metrics['overall_completion'])} / {fmt(metrics['overall_trajectory'])} / {fmt(metrics['overall_behavior'])}",
        f"- Reliability / pass^k / worst-of-n: {fmt(metrics['overall_reliability'])} / {pct(metrics['overall_pass_hat_k'])} / {fmt(metrics['overall_worst_of_n'])}",
        f"- Latency p50 / p95: {fmt(metrics['overall_median_latency_ms'], 0)}ms / {fmt(metrics['overall_p95_latency_ms'], 0)}ms",
        f"- Tokens/pass: {fmt(metrics['overall_tokens_per_pass'], 0)}",
        f"- Cost/pass: {'n/a' if metrics['overall_cost_per_pass'] is None else 'USD ' + format(metrics['overall_cost_per_pass'], '.4f')}",
        f"- Pricing: {summary['pricing_source'] or 'n/a'} / {summary['pricing_as_of'] or 'n/a'} / {summary['pricing_currency'] or 'n/a'}", "",
        "## Cache Evidence", "",
    ])
    cache = summary["cache"]
    runtime, capacity, protocol, lifecycle, observed = (
        cache.get("runtime", {}), cache.get("capacity", {}),
        cache.get("protocol", {}), cache.get("lifecycle", {}), cache.get("observed", {}),
    )
    cold, warm = observed.get("cold_latency_ms"), observed.get("warm_latency_ms")
    ttft = observed.get("ttft_latency_ms")
    layers = cache.get("layers", [])
    layer_text = ", ".join(
        f"{layer.get('kind')}={'on' if layer.get('enabled') else 'off'}"
        for layer in layers
    ) or "n/a"
    rss = observed.get("peak_process_rss_bytes")
    accelerator = observed.get("peak_accelerator_bytes")
    lines.extend([
        f"- Kind / runtime / engine: {runtime.get('kind') or 'n/a'} / {runtime.get('name') or 'n/a'} {runtime.get('version') or 'opaque'} / {runtime.get('engine') or 'n/a'}",
        f"- Cache layers: {layer_text}",
        f"- Capacity: {capacity.get('visibility') or 'n/a'} / {json.dumps(capacity.get('limits', {}), sort_keys=True)}",
        f"- Effective knobs: {json.dumps(cache.get('effective_knobs', {}), sort_keys=True)}",
        f"- Configuration fingerprint: {cache.get('configuration_fingerprint') or 'n/a'}",
        f"- Protocol: {protocol.get('profile') or 'n/a'}; reset repetitions={protocol.get('reset_between_task_repetitions')}; within-task={protocol.get('within_task_reuse')}; cross-task={protocol.get('cross_task_reuse')}",
        f"- Lifecycle: {lifecycle.get('server_scope') or 'n/a'} / {lifecycle.get('reset_mechanism') or 'n/a'} / {lifecycle.get('reuse_scope') or 'n/a'}",
        f"- Requests cold / warm / hits: {observed.get('cold_request_count')} / {observed.get('warm_request_count')} / {observed.get('hit_request_count') if observed.get('hit_request_count') is not None else 'n/a'}",
        f"- Full-response memo hits: {observed.get('response_memo_hit_count') if observed.get('response_memo_hit_count') is not None else 'n/a'}",
        f"- Reused input / metric: {observed.get('reused_input_tokens') if observed.get('reused_input_tokens') is not None else 'n/a'} / {observed.get('hit_metric') or 'n/a'}",
        f"- Cold p50/p95: {'n/a' if not cold else format(cold['p50'], '.0f') + '/' + format(cold['p95'], '.0f') + 'ms'}",
        f"- Warm p50/p95: {'n/a' if not warm else format(warm['p50'], '.0f') + '/' + format(warm['p95'], '.0f') + 'ms'}",
        f"- TTFT p50/p95: {'n/a' if not isinstance(ttft, dict) else format(ttft['p50'], '.0f') + '/' + format(ttft['p95'], '.0f') + 'ms'}",
        f"- Peak RSS / accelerator: {'n/a' if rss is None else format(rss / 1048576, '.0f') + 'MiB'} / {'n/a' if accelerator is None else format(accelerator / 1048576, '.0f') + 'MiB'}",
        f"- Cache resident bytes/tokens / evictions: {observed.get('peak_cache_resident_bytes') if observed.get('peak_cache_resident_bytes') is not None else 'n/a'} / {observed.get('peak_cache_resident_tokens') if observed.get('peak_cache_resident_tokens') is not None else 'n/a'} / {observed.get('cache_evictions') if observed.get('cache_evictions') is not None else 'n/a'}",
        f"- Speed evidence usable: {'yes' if cache.get('speed_usable') else 'no'}", "",
        "## Tasks", "",
        "| Task | Runs | Score | Reliability | pass^k | Worst | Cost/pass |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for item in summary["tasks"]:
        cost = "n/a" if item["cost_per_pass"] is None else "USD " + format(item["cost_per_pass"], ".4f")
        lines.append(
            f"| {item['task_id']} | {item['runs'] or 'n/a'} | {fmt(item['score'])} | "
            f"{fmt(item['reliability'])} | {item['pass_hat_k'] if item['pass_hat_k'] is not None else 'n/a'} | "
            f"{fmt(item['worst_of_n'])} | {cost} |"
        )
    lines.extend(["", "## Failure Modes", ""])
    failures = summary["failure_modes"]
    if failures is None:
        lines.append("- n/a (failure evidence absent)")
    elif failures:
        lines.extend(f"- {key}: {value}" for key, value in sorted(failures.items()) if value)
    else:
        lines.append("- none (explicit empty count map)")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", dest="json_out", type=Path)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    try:
        envelope = read_result(args.result)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    summary = summary_object(envelope, args.result)
    report = render(summary) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 2 if summary["artifact_status"] == "incomplete" and not args.allow_incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())
