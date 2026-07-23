#!/usr/bin/env python3
"""Compare two ClawBench result JSON files.

This is for real ClawBench outputs, not OpenClaw QA suite summaries.
It reads the ClawBench BenchmarkResult shape and reports the score surfaces
that make model comparisons useful: overall score, completion, trajectory,
behavior, reliability/pass^k, worst-of-n, latency, tokens, cost, and failure
modes.

Usage:
  compare_clawbench_results.py --baseline baseline.json --candidate candidate.json --out comparison.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_num(data: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = data.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def fmt_delta(value: float, digits: int = 3) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{digits}f}"


def pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def label(data: dict[str, Any], fallback: str) -> str:
    return str(data.get("model") or fallback)


METRICS = [
    ("overall_score", "Overall score", "score"),
    ("overall_completion", "Completion", "score"),
    ("overall_trajectory", "Trajectory", "score"),
    ("overall_behavior", "Behavior", "score"),
    ("overall_reliability", "Reliability", "score"),
    ("overall_pass_hat_k", "pass^k rate", "pct"),
    ("overall_worst_of_n", "Worst-of-n", "score"),
    ("overall_median_latency_ms", "Median latency", "ms"),
    ("overall_p95_latency_ms", "p95 latency", "ms"),
    ("overall_total_tokens", "Total tokens", "count"),
    ("overall_tokens_per_pass", "Tokens/pass", "count"),
    ("overall_cost_usd", "Total cost USD", "money"),
    ("overall_cost_per_pass", "Cost/pass USD", "money"),
]


def format_metric(value: float, kind: str) -> str:
    if kind == "pct":
        return pct(value)
    if kind == "ms":
        return f"{value:.0f}ms"
    if kind == "count":
        return f"{value:.0f}"
    if kind == "money":
        return "$" + f"{value:.4f}"
    return fmt(value)


def task_rows(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in data.get("task_results") or []:
        if isinstance(row, dict) and row.get("task_id"):
            rows[str(row["task_id"])] = row
    return rows


def failure_modes(data: dict[str, Any]) -> dict[str, int]:
    raw = data.get("overall_failure_mode_counts") or {}
    if isinstance(raw, dict):
        return {str(k): int(v) for k, v in raw.items() if v}
    return {}


def render(baseline: dict[str, Any], candidate: dict[str, Any]) -> str:
    base_name = label(baseline, "baseline")
    cand_name = label(candidate, "candidate")

    lines: list[str] = []
    lines.append("# ClawBench Model Comparison")
    lines.append("")
    lines.append(f"- Baseline: {base_name}")
    lines.append(f"- Candidate: {cand_name}")
    lines.append(f"- Benchmark versions: baseline {baseline.get('benchmark_version', 'unknown')}, candidate {candidate.get('benchmark_version', 'unknown')}")
    lines.append(f"- OpenClaw versions: baseline {baseline.get('openclaw_version', 'unknown')}, candidate {candidate.get('openclaw_version', 'unknown')}")
    lines.append("- Scores come from ClawBench result JSONs. Do not use this for QA-suite pass/fail summaries.")
    lines.append("")

    lines.append("## Score Surfaces")
    lines.append("")
    lines.append("| Metric | Baseline | Candidate | Delta |")
    lines.append("|---|---:|---:|---:|")
    for key, title, kind in METRICS:
        b = get_num(baseline, key)
        c = get_num(candidate, key)
        lines.append(f"| {title} | {format_metric(b, kind)} | {format_metric(c, kind)} | {fmt_delta(c - b)} |")
    lines.append("")

    base_tasks = task_rows(baseline)
    cand_tasks = task_rows(candidate)
    task_ids = sorted(set(base_tasks) | set(cand_tasks))
    if task_ids:
        lines.append("## Per-Task Deltas")
        lines.append("")
        lines.append("| Task | Baseline | Candidate | Delta | Candidate pass^k | Candidate worst |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for tid in task_ids:
            b = get_num(base_tasks.get(tid, {}), "mean_task_score")
            c = get_num(cand_tasks.get(tid, {}), "mean_task_score")
            passk = cand_tasks.get(tid, {}).get("pass_hat_k", "")
            worst = get_num(cand_tasks.get(tid, {}), "worst_of_n")
            lines.append(f"| {tid} | {fmt(b)} | {fmt(c)} | {fmt_delta(c - b)} | {passk} | {fmt(worst)} |")
        lines.append("")

    failures = failure_modes(candidate)
    lines.append("## Candidate Failure Modes")
    lines.append("")
    if failures:
        for mode, count in sorted(failures.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {mode}: {count}")
    else:
        lines.append("- None reported in overall_failure_mode_counts.")
    lines.append("")

    b_score = get_num(baseline, "overall_score")
    c_score = get_num(candidate, "overall_score")
    b_passk = get_num(baseline, "overall_pass_hat_k")
    c_passk = get_num(candidate, "overall_pass_hat_k")
    if c_score >= b_score - 0.02 and c_passk >= b_passk:
        verdict = "usable"
    elif c_score >= b_score - 0.08:
        verdict = "promising-but-risky"
    else:
        verdict = "not-ready"
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"- {verdict} based on overall score delta and pass^k reliability.")
    lines.append("- Treat this as decisive only when both runs use the same ClawBench commit, OpenClaw version, task set, run count, profile/tool surface, and provider routing.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = render(read_json(args.baseline), read_json(args.candidate))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report + "\n", encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
