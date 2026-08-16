#!/usr/bin/env python3
"""Run isolated OpenClaw Personal Agent QA gates on macOS or Linux.

The default is the complete ten-scenario ``personal-agent`` profile. A much
smaller mock-provider bootstrap check is available only with ``--preflight``;
that signal is harness-only and never counts as model evidence.

No ambient credentials or real OpenClaw state are inherited. Provider auth
must be named explicitly with repeatable ``--pass-env NAME`` arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SUMMARY_NAME = "qa-suite-summary.json"
EVIDENCE_NAME = "qa-evidence.json"
STATUS_NAME = "mqb-status.json"
PERSONAL_AGENT_SCENARIOS = (
    "personal-reminder-roundtrip",
    "personal-channel-thread-reply",
    "personal-memory-preference-recall",
    "personal-redaction-no-secret-leak",
    "agent-tool-safety-approvals",
    "personal-approval-denial-stop",
    "personal-task-followthrough-status",
    "personal-share-safe-diagnostics-artifact",
    "personal-no-fake-progress",
    "personal-failure-recovery",
)
PREFLIGHT_SCENARIOS = ("approval-turn-tool-followthrough",)
ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PROTECTED_ENV_NAMES = {
    "HOME",
    "PATH",
    "TMPDIR",
    "NODE_OPTIONS",
    "BASH_ENV",
    "ENV",
    "NPM_CONFIG_USERCONFIG",
    "PNPM_HOME",
    "COREPACK_HOME",
    "COREPACK_ENABLE_NETWORK",
}
PROTECTED_ENV_PREFIXES = ("OPENCLAW_", "XDG_", "DYLD_", "LD_", "PYTHON")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def env_first(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    return None


def split_env(*names: str) -> list[str]:
    raw = env_first(*names)
    if not raw:
        return []
    return [part for part in shlex.split(raw.replace(",", " ")) if part]


def safe_part(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value)
    return cleaned.strip(".-_") or "unknown"


def slug(value: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", value.lower()))


def read_package_version(repo_root: Path) -> str | None:
    try:
        data = json.loads((repo_root / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("version")
    return str(value) if value else None


def git_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            text=True,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def summary_scenarios(summary: dict[str, Any]) -> dict[str, str]:
    run = summary.get("run") if isinstance(summary.get("run"), dict) else {}
    ids = run.get("scenarioIds") if isinstance(run.get("scenarioIds"), list) else []
    scenarios = summary.get("scenarios") if isinstance(summary.get("scenarios"), list) else []
    out: dict[str, str] = {}
    for index, item in enumerate(scenarios):
        if not isinstance(item, dict):
            continue
        scenario_id = str(ids[index]).strip() if index < len(ids) else slug(str(item.get("name") or ""))
        if not scenario_id:
            continue
        status = str(item.get("status") or "missing").strip().lower()
        out[scenario_id] = status
    return out


def evidence_scenarios(evidence: dict[str, Any], key: str) -> set[str]:
    plan = evidence.get("profilePlan") if isinstance(evidence.get("profilePlan"), dict) else {}
    cells = plan.get(key) if isinstance(plan.get(key), list) else []
    return {
        str(cell.get("scenarioId")).strip()
        for cell in cells
        if isinstance(cell, dict) and str(cell.get("scenarioId") or "").strip()
    }


def validate_profile_evidence(evidence: dict[str, Any] | None, expected: set[str]) -> str | None:
    if evidence is None:
        return "qa-evidence.json missing or invalid"
    if str(evidence.get("profile") or "") != "personal-agent":
        return "qa-evidence profile is not personal-agent"
    expected_cells = evidence_scenarios(evidence, "expectedCells")
    observed_cells = evidence_scenarios(evidence, "observedCells")
    if expected_cells != expected:
        return "qa-evidence expected scenario set does not match the pinned profile"
    if observed_cells != expected:
        return "qa-evidence observed scenario set is incomplete or unexpected"
    plan = evidence.get("profilePlan") if isinstance(evidence.get("profilePlan"), dict) else {}
    counts = plan.get("counts") if isinstance(plan.get("counts"), dict) else {}
    if counts.get("missingCells") not in (None, 0):
        return "qa-evidence reports missing execution cells"
    return None


def terminate_process_group(process: subprocess.Popen[Any], grace_seconds: int = 10) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait()


def execute(
    command: list[str], cwd: Path, env: dict[str, str], log_path: Path, timeout: int
) -> tuple[int, bool, float]:
    started = time.monotonic()
    timed_out = False
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            terminate_process_group(process)
            code = 124
    return code, timed_out, time.monotonic() - started


def build_command(
    pnpm: str,
    repo_root: Path,
    output_dir: Path,
    model: str,
    alternate: str,
    provider_mode: str,
    concurrency: int,
    scenarios: tuple[str, ...],
    preflight: bool,
    fast_requested: str,
) -> list[str]:
    if preflight:
        command = [
            pnpm,
            "openclaw",
            "qa",
            "suite",
            "--repo-root",
            str(repo_root),
            "--provider-mode",
            "mock-openai",
            "--concurrency",
            "1",
            "--allow-failures",
            "--preflight",
        ]
    else:
        command = [
            pnpm,
            "openclaw",
            "qa",
            "run",
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--qa-profile",
            "personal-agent",
            "--provider-mode",
            provider_mode,
            "--model",
            model,
            "--alt-model",
            alternate,
            "--concurrency",
            str(concurrency),
            "--allow-failures",
        ]
        if set(scenarios) != set(PERSONAL_AGENT_SCENARIOS):
            for scenario in scenarios:
                command.extend(["--scenario", scenario])
    if fast_requested == "on":
        command.append("--fast")
    return command


def command_for_manifest(command: list[str], repo_root: Path, output_dir: Path) -> list[str]:
    replacements = {
        str(repo_root): "<repo-root>",
        str(output_dir): "<entry-output>",
        command[0]: "pnpm",
    }
    return [replacements.get(part, part) for part in command]


def validate_pass_env(names: list[str]) -> tuple[list[str], list[str]]:
    accepted: list[str] = []
    errors: list[str] = []
    for name in names:
        if not ENV_NAME_RE.fullmatch(name):
            errors.append(f"invalid environment variable name: {name!r}")
            continue
        if name in PROTECTED_ENV_NAMES or name.startswith(PROTECTED_ENV_PREFIXES):
            errors.append(f"{name} is controlled by the isolation boundary and cannot be passed")
            continue
        if name not in os.environ:
            errors.append(f"explicit --pass-env variable is not set: {name}")
            continue
        if name not in accepted:
            accepted.append(name)
    return accepted, errors


def isolated_env(state_root: Path, pass_env: list[str]) -> dict[str, str]:
    corepack_home = Path.home() / ".cache" / "node" / "corepack"
    paths = {
        "HOME": state_root / "home",
        "TMPDIR": state_root / "tmp",
        "OPENCLAW_HOME": state_root / "openclaw-home",
        "OPENCLAW_STATE_DIR": state_root / "state",
        "OPENCLAW_CONFIG_PATH": state_root / "openclaw.json",
        "OPENCLAW_OAUTH_DIR": state_root / "state" / "credentials",
        "XDG_CONFIG_HOME": state_root / "xdg-config",
        "XDG_DATA_HOME": state_root / "xdg-data",
        "XDG_CACHE_HOME": state_root / "xdg-cache",
    }
    for key, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if key != "OPENCLAW_CONFIG_PATH":
            path.mkdir(parents=True, exist_ok=True)
    env: dict[str, str] = {
        "PATH": os.environ.get("PATH") or os.defpath,
        **{key: str(value) for key, value in paths.items()},
        "OPENCLAW_ENABLE_PRIVATE_QA_CLI": "1",
        "OPENCLAW_SKIP_BROWSER_CONTROL_SERVER": "1",
        "OPENCLAW_SKIP_GMAIL_WATCHER": "1",
        "OPENCLAW_SKIP_CANVAS_HOST": "1",
        "OPENCLAW_NO_RESPAWN": "1",
        "COREPACK_ENABLE_NETWORK": "0",
    }
    if corepack_home.is_dir():
        env["COREPACK_HOME"] = str(corepack_home)
    for name in ("LANG", "LC_ALL", "LC_CTYPE", "TZ"):
        if os.environ.get(name):
            env[name] = os.environ[name]
    for name in pass_env:
        env[name] = os.environ[name]
    return env


def parse_preflight_summary(log_path: Path, repo_root: Path) -> Path | None:
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    prefix = "QA parity preflight summary:"
    values = [line[len(prefix) :].strip() for line in lines if line.startswith(prefix)]
    if len(values) != 1:
        return None
    candidate = Path(values[0]).expanduser().resolve()
    allowed = (repo_root / ".artifacts" / "qa-e2e" / "preflight").resolve()
    try:
        candidate.relative_to(allowed)
    except ValueError:
        return None
    return candidate if candidate.name == SUMMARY_NAME and candidate.is_file() else None


def copy_preflight_artifacts(summary: Path, destination: Path) -> None:
    for name in (SUMMARY_NAME, "qa-suite-report.md", EVIDENCE_NAME):
        source = summary.parent / name
        if source.is_file():
            shutil.copy2(source, destination / name)


def copy_profile_artifacts(source: Path, destination: Path) -> None:
    if not source.is_dir():
        return
    for item in source.rglob("*"):
        if item.is_symlink() or not item.is_file():
            continue
        relative = item.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def remove_repo_artifact(path: Path, allowed_root: Path) -> None:
    resolved = path.resolve()
    root = allowed_root.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"refusing repo artifact cleanup outside {root}") from exc
    if not relative.parts:
        raise RuntimeError("refusing to remove the repo artifact root itself")
    if resolved.exists():
        shutil.rmtree(resolved)


def classify_failure(log_path: Path, timed_out: bool, summary_found: bool) -> str:
    if timed_out:
        return "transport-timeout"
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")[-1_000_000:].lower()
    except OSError:
        text = ""
    if any(marker in text for marker in ("rate limit", "rate-limit", "quota", "429", "insufficient credit")):
        return "quota"
    if any(marker in text for marker in ("unauthorized", "authentication", "api key", "api-key", "401", "forbidden", "403")):
        return "auth"
    if any(
        marker in text
        for marker in (
            "econnreset",
            "econnrefused",
            "etimedout",
            "enotfound",
            "fetch failed",
            "socket hang up",
            "connection reset",
            "network error",
        )
    ):
        return "transport"
    return "infra" if summary_found else "artifact-missing"


def parse_args() -> argparse.Namespace:
    default_repo = env_first("CLAWGAUGE_REPO_ROOT", "MQB_REPO_ROOT") or str(
        Path.home() / "projects" / "openclaw"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(default_repo))
    parser.add_argument("--model", action="append", default=[], help="Exact provider/model ref; repeatable")
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Narrow the personal-agent profile to a pinned scenario ID; repeatable",
    )
    parser.add_argument("--provider-mode", default=env_first("CLAWGAUGE_PROVIDER_MODE", "MQB_PROVIDER_MODE") or "live-frontier")
    parser.add_argument("--fast", action="store_true", help="Explicitly request provider fast mode; omission remains unset")
    parser.add_argument("--concurrency", type=int, default=int(env_first("CLAWGAUGE_CONCURRENCY", "MQB_CONCURRENCY") or "1"))
    parser.add_argument("--timeout", type=int, default=int(env_first("CLAWGAUGE_TIMEOUT", "MQB_TIMEOUT") or "240"))
    parser.add_argument("--repetitions", type=int, default=1, help="Independent attempts per model")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pass-env", action="append", default=[], metavar="NAME", help="Explicitly pass one existing environment variable; repeatable")
    parser.add_argument("--preflight", action="store_true", help="Run only the mock bootstrap sentinel; harness-only")
    parser.add_argument("--allow-cross-fallback", action="store_true", help="Use another compared model as fallback; invalid for clean model attribution")
    parser.add_argument("--keep-state", action="store_true", help="Keep isolated temp roots for local audit")
    parser.add_argument("--plan", action="store_true", help="Print the sanitized plan; make no provider calls or files")
    return parser.parse_args()


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    models = args.model or split_env("CLAWGAUGE_MODELS", "MQB_MODELS")
    if args.preflight and not models:
        models = ["harness/mock-openai"]
    if not models:
        print("error: provide at least one --model (or CLAWGAUGE_MODELS)", file=sys.stderr)
        return 2
    if len(set(models)) != len(models):
        print("error: duplicate model refs are not allowed", file=sys.stderr)
        return 2
    if args.allow_cross_fallback and len(models) < 2:
        print("error: --allow-cross-fallback needs at least two distinct models", file=sys.stderr)
        return 2
    if min(args.timeout, args.concurrency, args.repetitions) < 1:
        print("error: --timeout, --concurrency, and --repetitions must be positive", file=sys.stderr)
        return 2
    if args.preflight and args.provider_mode not in {"mock-openai", "aimock", "live-frontier"}:
        print("error: --preflight is fixed to mock-openai; omit --provider-mode", file=sys.stderr)
        return 2
    if args.preflight and args.scenario:
        print("error: --scenario cannot be combined with --preflight", file=sys.stderr)
        return 2

    pass_env, env_errors = validate_pass_env(args.pass_env)
    if env_errors:
        for error in env_errors:
            print(f"error: {error}", file=sys.stderr)
        return 2

    selected = tuple(args.scenario) if args.scenario else PERSONAL_AGENT_SCENARIOS
    unknown = sorted(set(selected) - set(PERSONAL_AGENT_SCENARIOS))
    if unknown:
        print(f"error: scenario(s) are not in the pinned personal-agent profile: {unknown}", file=sys.stderr)
        return 2
    if len(set(selected)) != len(selected):
        print("error: duplicate scenario IDs are not allowed", file=sys.stderr)
        return 2
    expected = PREFLIGHT_SCENARIOS if args.preflight else selected
    provider_mode = "mock-openai" if args.preflight else args.provider_mode
    fast_requested = "on" if args.fast else "unset"

    repo_root = args.repo_root.expanduser().resolve()
    if not (repo_root / "package.json").is_file() or not (repo_root / "openclaw.mjs").is_file():
        print(f"error: not an OpenClaw source checkout: {repo_root}", file=sys.stderr)
        return 2
    pnpm = shutil.which("pnpm")
    if not pnpm:
        print("error: pnpm is not available; ClawGauge will not install it", file=sys.stderr)
        return 2

    current_run_id = new_run_id()
    output = args.output.expanduser().resolve() if args.output else (SKILL_ROOT / "runs" / f"qa-gate-{current_run_id}").resolve()
    repo_artifact_root = (
        repo_root / ".artifacts" / "qa-e2e" / f"clawgauge-{current_run_id}"
    )
    runtime_entries: list[dict[str, Any]] = []
    manifest_entries: list[dict[str, Any]] = []
    ordinal = 0
    for repetition in range(1, args.repetitions + 1):
        for model in models:
            ordinal += 1
            alternate = (
                next(other for other in models if other != model)
                if args.allow_cross_fallback
                else model
            )
            entry_id = f"e{ordinal:03d}-{safe_part(model)}-{uuid.uuid4().hex[:8]}"
            output_rel = Path("entries") / entry_id
            entry_output = output / output_rel
            repo_output = repo_artifact_root / entry_id
            repo_output_rel = repo_output.relative_to(repo_root)
            command = build_command(
                pnpm,
                repo_root,
                repo_output_rel,
                model,
                alternate,
                provider_mode,
                args.concurrency,
                expected,
                args.preflight,
                fast_requested,
            )
            runtime_entries.append(
                {
                    "entry_id": entry_id,
                    "output": entry_output,
                    "repo_output": repo_output,
                    "command": command,
                }
            )
            manifest_entries.append(
                {
                    "entry_id": entry_id,
                    "attempt": repetition,
                    "model": model,
                    "alternate_model": alternate,
                    "fallback_enabled": alternate != model,
                    "mode": "preflight-harness" if args.preflight else "personal-agent-profile",
                    "profile": None if args.preflight else "personal-agent",
                    "provider_mode": provider_mode,
                    "expected_scenarios": list(expected),
                    "fast_mode_requested": fast_requested,
                    "output_rel": output_rel.as_posix(),
                    "command": command_for_manifest(command, repo_root, repo_output_rel),
                }
            )

    manifest: dict[str, Any] = {
        "schema_version": 3,
        "run_id": current_run_id,
        "created_at": utc_now(),
        "host": {"system": platform.system(), "machine": platform.machine()},
        "openclaw": {
            "checkout_name": repo_root.name,
            "version": read_package_version(repo_root),
            "commit": git_commit(repo_root),
        },
        "provider_mode": provider_mode,
        "fast_mode_requested": fast_requested,
        "concurrency": 1 if args.preflight else args.concurrency,
        "timeout_seconds": args.timeout,
        "repetitions": args.repetitions,
        "strict_single_model": not args.allow_cross_fallback,
        "models": models,
        "expected_scenarios": list(expected),
        "passed_env_names": sorted(pass_env),
        "entries": manifest_entries,
        "status": "planned",
    }
    if args.plan:
        print(json.dumps(manifest, indent=2))
        return 0

    output.mkdir(parents=True, exist_ok=False)
    manifest_path = output / "run-manifest.json"
    manifest["status"] = "running"
    write_manifest(manifest_path, manifest)
    incomplete = False
    results: list[dict[str, Any]] = []

    for runtime, declared in zip(runtime_entries, manifest_entries):
        entry_id = str(runtime["entry_id"])
        destination = Path(runtime["output"])
        repo_output = Path(runtime["repo_output"])
        destination.mkdir(parents=True, exist_ok=False)
        log_path = destination / "run.log"
        state_root = Path(tempfile.mkdtemp(prefix="openclaw-clawgauge-qa-"))
        print(f">>> entry={entry_id} model={declared['model']} attempt={declared['attempt']}")
        try:
            code, timed_out, wall_seconds = execute(
                list(runtime["command"]),
                repo_root,
                isolated_env(state_root, pass_env),
                log_path,
                args.timeout,
            )
            if args.preflight:
                source_summary = parse_preflight_summary(log_path, repo_root)
                if source_summary:
                    copy_preflight_artifacts(source_summary, destination)
            else:
                copy_profile_artifacts(repo_output, destination)
            summary_path = destination / SUMMARY_NAME
            evidence_path = destination / EVIDENCE_NAME
            summary = read_json(summary_path)
            observed = summary_scenarios(summary) if summary else {}
            expected_set = set(expected)
            evidence_error = None
            if not args.preflight:
                evidence_error = validate_profile_evidence(read_json(evidence_path), expected_set)

            non_pass = {name: status for name, status in observed.items() if status != "pass"}
            scenario_set_ok = set(observed) == expected_set
            if timed_out:
                status = "stalled"
                failure_class = "transport-timeout"
            elif code != 0:
                status = "blocked"
                failure_class = classify_failure(log_path, False, summary is not None)
            elif summary is None:
                status = "blocked"
                failure_class = "artifact-missing"
            elif not scenario_set_ok:
                status = "blocked"
                failure_class = "scenario-set"
            elif evidence_error:
                status = "blocked"
                failure_class = "profile-evidence"
            elif non_pass:
                status = "fail" if set(non_pass.values()) <= {"fail", "failed"} else "blocked"
                failure_class = "scenario"
            else:
                status = "complete"
                failure_class = None

            summary_run = summary.get("run") if summary and isinstance(summary.get("run"), dict) else {}
            effective_fast = summary_run.get("fastMode") if isinstance(summary_run.get("fastMode"), bool) else None
            if fast_requested == "on" and effective_fast is not True:
                status = "blocked"
                failure_class = "fast-mode"

            if status != "complete":
                incomplete = True
                sidecar = {
                    "schema_version": 2,
                    "entry_id": entry_id,
                    "model": declared["model"],
                    "status_label": status,
                    "failure_class": failure_class,
                    "exit_code": code,
                    "timed_out": timed_out,
                    "summary_found": summary is not None,
                    "evidence_found": evidence_path.is_file(),
                    "evidence_error": evidence_error,
                    "wall_seconds": round(wall_seconds, 3),
                    "provider_mode": provider_mode,
                    "alternate_model": declared["alternate_model"],
                    "fast_mode_requested": fast_requested,
                    "fast_mode_effective": effective_fast,
                }
                (destination / STATUS_NAME).write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")

            result = {
                "entry_id": entry_id,
                "status": status,
                "failure_class": failure_class,
                "exit_code": code,
                "timed_out": timed_out,
                "wall_seconds": round(wall_seconds, 3),
                "summary_found": summary is not None,
                "evidence_found": evidence_path.is_file(),
                "fast_mode_effective": effective_fast,
                "artifacts": sorted(
                    path.name
                    for path in destination.iterdir()
                    if path.is_file()
                ),
            }
            results.append(result)
            manifest["results"] = results
            write_manifest(manifest_path, manifest)
            print(f"    -> {status} ({wall_seconds:.1f}s)")
            if args.keep_state:
                print(f"CLAWGAUGE_RETAINED_STATE[{entry_id}]={state_root}")
                if repo_output.exists():
                    print(f"CLAWGAUGE_RETAINED_REPO_ARTIFACT[{entry_id}]={repo_output}")
        finally:
            if not args.keep_state:
                shutil.rmtree(state_root)
                if not args.preflight:
                    remove_repo_artifact(repo_output, repo_artifact_root)

    if not args.keep_state and repo_artifact_root.is_dir():
        try:
            repo_artifact_root.rmdir()
        except OSError:
            pass

    manifest["completed_at"] = utc_now()
    manifest["results"] = results
    manifest["status"] = "incomplete" if incomplete else "artifacts-written"
    write_manifest(manifest_path, manifest)
    print(f"CLAWGAUGE_QA_RUN_DIR={output}")
    print(
        "Next: python3 "
        f"{SCRIPT_DIR / 'score_qa_suite.py'} --run-dir {output} "
        f"--out {output / 'qa-gate.md'} --json {output / 'qa-gate.json'}"
    )
    return 1 if incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())
