#!/usr/bin/env python3
"""Score real OpenClaw QA suite artifacts into an honest model comparison.

Unlike ``summarize_clawbench_result.py`` (which expects ClawBench
``tier_results``/``task_stats`` JSON), this reads the artifacts that
``openclaw qa suite`` actually writes: ``qa-suite-summary.json``
(scenarios/counts/metrics/run) plus optional ``mqb-status.json`` sidecars
written by ``run_model_quality_benchmark.sh`` for runs that stalled or were
blocked before any summary could be produced.

It reports only metrics that exist in the artifacts: per-scenario status,
pass/fail counts, pass_rate, and wall time per model and per scenario. It does
NOT invent ClawBench-style completion/trajectory/behavior scores.

Usage:
  score_qa_suite.py --run-dir <dir> [--out report.md] [--json scorecard.json]
  score_qa_suite.py --summary a.json --summary b.json [--out report.md]

A run-dir is searched recursively for both ``qa-suite-summary.json`` and
``mqb-status.json`` files.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---- status vocabulary -------------------------------------------------------
# Honest, artifact-derived labels. "stalled"/"blocked" only come from sidecars
# (a run that produced no summary). "pass"/"fail"/"skip" come from real summary
# scenario rows.
PASS = "pass"
FAIL = "fail"
SKIP = "skip"
STALLED = "stalled"  # timed out / hung before writing a summary
BLOCKED = "blocked"  # non-zero, non-timeout exit before a summary
MISSING = "missing"  # expected but no artifact at all

STATUS_ICON = {
    PASS: "PASS",
    FAIL: "FAIL",
    SKIP: "skip",
    STALLED: "STALLED",
    BLOCKED: "BLOCKED",
    MISSING: "missing",
}


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report and skip bad files
        print(f"warn: could not parse {path}: {exc}", file=sys.stderr)
        return None


def _norm_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in (PASS, "passed", "ok", "success"):
        return PASS
    if text in (FAIL, "failed", "error"):
        return FAIL
    if text in (SKIP, "skipped"):
        return SKIP
    return text or MISSING


class ModelRecord:
    """Per-model aggregation across one or more summary/sidecar artifacts."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.provider_mode: str | None = None
        self.alt_model: str | None = None
        self.fast_mode: bool | None = None
        # scenario_id -> dict(status, wall_seconds, source)
        self.scenarios: dict[str, dict[str, Any]] = {}
        self.total_wall_seconds: float = 0.0

    def _record(self, scenario_id: str, status: str, wall_seconds: float | None, source: str) -> None:
        # Prefer a real summary result over a sidecar; prefer a terminal status
        # (pass/fail) over a non-terminal one if the same scenario appears twice.
        existing = self.scenarios.get(scenario_id)
        rank = {PASS: 5, FAIL: 5, SKIP: 3, STALLED: 2, BLOCKED: 2, MISSING: 0}
        if existing and rank.get(existing["status"], 0) >= rank.get(status, 0):
            return
        self.scenarios[scenario_id] = {
            "status": status,
            "wall_seconds": wall_seconds,
            "source": source,
        }

    def add_summary(self, summary: dict[str, Any], path: Path) -> None:
        run = summary.get("run") or {}
        if self.provider_mode is None:
            self.provider_mode = run.get("providerMode")
        if self.alt_model is None:
            self.alt_model = run.get("alternateModel")
        if self.fast_mode is None:
            self.fast_mode = run.get("fastMode")
        metrics = summary.get("metrics") or {}
        wall_ms = metrics.get("wallMs")
        wall_s = (float(wall_ms) / 1000.0) if isinstance(wall_ms, (int, float)) else None
        scenarios = summary.get("scenarios") or []
        scenario_ids = run.get("scenarioIds")
        for idx, sc in enumerate(scenarios):
            status = _norm_status(sc.get("status"))
            if isinstance(scenario_ids, list) and idx < len(scenario_ids):
                sid = str(scenario_ids[idx])
            else:
                sid = str(sc.get("name") or f"scenario-{idx}")
            # Attribute the whole summary wall time to its (usually single) scenario.
            per = wall_s if len(scenarios) == 1 else None
            self._record(sid, status, per, source=str(path))
        if wall_s is not None:
            self.total_wall_seconds += wall_s

    def add_sidecar(self, sidecar: dict[str, Any], path: Path) -> None:
        sid = str(sidecar.get("scenario") or sidecar.get("scenario_id") or path.parent.name)
        status = _norm_status(sidecar.get("status_label") or sidecar.get("status"))
        if status not in (PASS, FAIL, SKIP, STALLED, BLOCKED):
            status = BLOCKED
        wall = sidecar.get("wall_seconds")
        wall = float(wall) if isinstance(wall, (int, float)) else None
        if self.provider_mode is None:
            self.provider_mode = sidecar.get("provider_mode")
        if self.alt_model is None:
            self.alt_model = sidecar.get("alt_model")
        self._record(sid, status, wall, source=str(path))
        if wall is not None:
            self.total_wall_seconds += wall

    # ---- derived metrics ----
    @property
    def attempted(self) -> int:
        return len(self.scenarios)

    def count(self, status: str) -> int:
        return sum(1 for v in self.scenarios.values() if v["status"] == status)

    @property
    def passed(self) -> int:
        return self.count(PASS)

    @property
    def completed(self) -> int:
        return self.count(PASS) + self.count(FAIL)

    @property
    def pass_rate(self) -> float | None:
        return (self.passed / self.attempted) if self.attempted else None

    @property
    def completed_pass_rate(self) -> float | None:
        return (self.passed / self.completed) if self.completed else None

    @property
    def fallback_enabled(self) -> bool | None:
        if self.alt_model is None:
            return None
        return self.alt_model != self.model


def _fmt_rate(rate: float | None) -> str:
    return "n/a" if rate is None else f"{rate * 100:.0f}%"


def _fmt_secs(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f}s"


def collect(run_dir: Path | None, summary_paths: list[Path]) -> dict[str, ModelRecord]:
    records: dict[str, ModelRecord] = {}

    def model_record(model: str) -> ModelRecord:
        return records.setdefault(model, ModelRecord(model))

    paths: list[tuple[str, Path]] = []
    if run_dir is not None:
        for p in sorted(run_dir.rglob("qa-suite-summary.json")):
            paths.append(("summary", p))
        for p in sorted(run_dir.rglob("mqb-status.json")):
            paths.append(("sidecar", p))
    for p in summary_paths:
        paths.append(("summary", p))

    for kind, path in paths:
        data = _read_json(path)
        if not isinstance(data, dict):
            continue
        if kind == "summary":
            model = (data.get("run") or {}).get("primaryModel") or "unknown-model"
            model_record(str(model)).add_summary(data, path)
        else:
            model = data.get("model") or "unknown-model"
            model_record(str(model)).add_sidecar(data, path)
    return records


def render_markdown(records: dict[str, ModelRecord]) -> str:
    models = sorted(records.values(), key=lambda r: r.model)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    provider_modes = sorted({r.provider_mode for r in models if r.provider_mode})

    lines: list[str] = []
    lines.append("# ClawGauge — QA Suite Score")
    lines.append("")
    lines.append(f"- Generated: `{now}`")
    if provider_modes:
        lines.append(f"- Provider mode(s): {', '.join(provider_modes)}")
    lines.append(f"- Models scored: {len(models)}")
    lines.append("- Scores are derived only from real QA artifacts "
                 "(`qa-suite-summary.json`) and run-status sidecars. "
                 "No synthetic/judge scores.")
    lines.append("")

    # Per-model summary table.
    lines.append("## Per-Model Summary")
    lines.append("")
    lines.append("| Model | Attempted | Pass | Fail | Stalled | Blocked | Skip | "
                 "Pass rate | Completed pass rate | Wall time | Fallback |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in models:
        fb = r.fallback_enabled
        fb_text = "n/a" if fb is None else (f"ENABLED→{r.alt_model}" if fb else "disabled")
        lines.append(
            f"| `{r.model}` | {r.attempted} | {r.passed} | {r.count(FAIL)} | "
            f"{r.count(STALLED)} | {r.count(BLOCKED)} | {r.count(SKIP)} | "
            f"{_fmt_rate(r.pass_rate)} | {_fmt_rate(r.completed_pass_rate)} "
            f"({r.passed}/{r.completed}) | {_fmt_secs(r.total_wall_seconds)} | {fb_text} |"
        )
    lines.append("")

    # Per-scenario grid.
    all_scenarios = sorted({s for r in models for s in r.scenarios})
    if all_scenarios:
        lines.append("## Per-Scenario Status")
        lines.append("")
        header = "| Scenario | " + " | ".join(f"`{r.model}`" for r in models) + " |"
        sep = "|---|" + "|".join(["---"] * len(models)) + "|"
        lines.append(header)
        lines.append(sep)
        for sid in all_scenarios:
            cells = []
            for r in models:
                rec = r.scenarios.get(sid)
                if rec is None:
                    cells.append(STATUS_ICON[MISSING])
                else:
                    icon = STATUS_ICON.get(rec["status"], rec["status"])
                    secs = rec.get("wall_seconds")
                    cells.append(icon + (f" ({secs:.0f}s)" if isinstance(secs, (int, float)) else ""))
            lines.append(f"| `{sid}` | " + " | ".join(cells) + " |")
        lines.append("")

    # Concerns: anything not a pass.
    concerns: list[str] = []
    for r in models:
        for sid, rec in sorted(r.scenarios.items()):
            if rec["status"] != PASS:
                concerns.append(f"- `{r.model}` / `{sid}`: **{rec['status']}** "
                                f"(source: `{rec['source']}`)")
    lines.append("## Failures / Stalls / Blocks")
    lines.append("")
    lines.extend(concerns if concerns else ["- None. Every attempted scenario passed."])
    lines.append("")

    lines.append("## Honesty Notes")
    lines.append("")
    lines.append("- `pass_rate` = passed / attempted (stalled & blocked count as not passed).")
    lines.append("- `completed pass rate` = passed / (pass+fail); excludes stalled/blocked.")
    lines.append("- `Fallback ENABLED` means the alternate model differs from the primary, so a "
                 "primary-model failure can be silently rescued by the alternate. Prefer "
                 "`disabled` (alt == primary) for a clean single-model verdict.")
    lines.append("- `stalled` = the run exceeded its per-scenario timeout before writing a "
                 "summary. `blocked` = the run exited non-zero (infra/auth) before a summary.")
    return "\n".join(lines) + "\n"


def build_scorecard(records: dict[str, ModelRecord]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "models": [
            {
                "model": r.model,
                "provider_mode": r.provider_mode,
                "alt_model": r.alt_model,
                "fallback_enabled": r.fallback_enabled,
                "fast_mode": r.fast_mode,
                "attempted": r.attempted,
                "passed": r.passed,
                "failed": r.count(FAIL),
                "stalled": r.count(STALLED),
                "blocked": r.count(BLOCKED),
                "skipped": r.count(SKIP),
                "pass_rate": r.pass_rate,
                "completed_pass_rate": r.completed_pass_rate,
                "total_wall_seconds": round(r.total_wall_seconds, 3),
                "scenarios": {
                    sid: {"status": rec["status"], "wall_seconds": rec["wall_seconds"]}
                    for sid, rec in sorted(r.scenarios.items())
                },
            }
            for r in sorted(records.values(), key=lambda r: r.model)
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, help="Directory to search recursively for artifacts")
    ap.add_argument("--summary", type=Path, action="append", default=[],
                    help="Explicit qa-suite-summary.json path (repeatable)")
    ap.add_argument("--out", type=Path, help="Write Markdown report here (also prints to stdout)")
    ap.add_argument("--json", dest="json_out", type=Path, help="Write JSON scorecard here")
    args = ap.parse_args()

    if not args.run_dir and not args.summary:
        ap.error("provide --run-dir and/or one or more --summary paths")

    records = collect(args.run_dir, args.summary)
    if not records:
        print("error: no qa-suite-summary.json or mqb-status.json artifacts found", file=sys.stderr)
        return 2

    report = render_markdown(records)
    sys.stdout.write(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"\n[wrote report] {args.out}", file=sys.stderr)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(build_scorecard(records), indent=2) + "\n", encoding="utf-8")
        print(f"[wrote scorecard] {args.json_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
