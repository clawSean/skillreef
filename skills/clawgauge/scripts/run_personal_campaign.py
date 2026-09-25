#!/usr/bin/env python3
"""Plan and supervise a bounded, fail-closed two-route ClawGauge campaign."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from process_cleanup import terminate_process_tree

SCHEMA = "clawgauge.personal-campaign.v5"
TASKS = ["t1-bugfix-discount", "t2-add-tests-normalizer", "t2-config-loader"]
REQUIRED_CONTROLS = [
    "effective_provider_model",
    "auth_account",
    "reasoning",
    "fast",
    "fallback",
]
WORKER = Path(__file__).with_name("personal_campaign_worker.py")
EVIDENCE_TIERS = {"requested-route-screening", "strict-decision-grade"}
AUTH_KINDS = {"provider-free-mock", "isolated-api-config", "subscription-handoff"}
PRODUCTION_TOKEN_ENV_DENYLIST = {
    "OPENCLAW_GATEWAY_TOKEN",
    "OPENCLAW_GATEWAY_PASSWORD",
    "OPENCLAW_AUTH_TOKEN",
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.chmod(path, 0o600)


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if data.get("schema") != SCHEMA:
        raise ValueError(f"expected schema {SCHEMA}")
    pass_env = data.get("pass_env", [])
    if not isinstance(pass_env, list) or not all(isinstance(name, str) for name in pass_env):
        raise ValueError("pass_env must be a list of environment variable names")
    denied = sorted(set(pass_env) & PRODUCTION_TOKEN_ENV_DENYLIST)
    if denied:
        raise ValueError("production token names are forbidden in pass_env: " + ", ".join(denied))
    if pass_env:
        raise ValueError("generic pass_env is unsupported; use the isolated auth preparation contract")
    data["pass_env"] = []

    gateway = data.get("gateway", {})
    if gateway.get("token_env") not in (None, ""):
        raise ValueError("gateway.token_env is unsupported; production Gateway tokens may not be inherited")

    routes = data.get("routes", [])
    if len(routes) != 2 or len({route.get("id") for route in routes}) != 2:
        raise ValueError("routes must contain exactly two distinct entries")
    required = ("id", "provider", "model", "adapter", "reasoning", "fast", "fallback", "auth_account")
    for route in routes:
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}", str(route.get("id", ""))):
            raise ValueError("route id must be a safe nonempty directory label")
        if any(key not in route for key in required):
            raise ValueError("each route needs a complete requested-route contract")
        if route["adapter"] != "openclaw":
            raise ValueError("only the pinned executable openclaw adapter is supported")
        if route["fallback"] is not False:
            raise ValueError("fallback must be requested false")
        if not isinstance(route["fast"], bool):
            raise ValueError("fast must be an explicit boolean")
        tools_profile = route.get("tools_profile", "default")
        if not isinstance(tools_profile, str) or not tools_profile:
            raise ValueError("tools_profile must be a non-empty stable label")
        route["tools_profile"] = tools_profile
        if not re.fullmatch(r"[a-zA-Z0-9._-]+", str(route["auth_account"])):
            raise ValueError("auth_account must be a non-secret stable label")
        controls = route.get("required_observed_controls", REQUIRED_CONTROLS)
        if sorted(controls) != sorted(REQUIRED_CONTROLS):
            raise ValueError("all exact-route controls must remain required")
        route["required_observed_controls"] = list(REQUIRED_CONTROLS)
        tier = route.get("evidence_tier", "requested-route-screening")
        if tier not in EVIDENCE_TIERS:
            raise ValueError(f"unsupported evidence_tier: {tier}")
        route["evidence_tier"] = tier
        observed = route.get("independently_observed_controls", [])
        if not isinstance(observed, list) or not set(observed).issubset(REQUIRED_CONTROLS):
            raise ValueError("independently_observed_controls contains an unknown control")
        if observed:
            raise ValueError(
                "independently observed controls cannot be self-declared; no observer is configured"
            )
        route["independently_observed_controls"] = []
        preparation = route.get("auth_preparation", {})
        if preparation.get("kind") not in AUTH_KINDS:
            raise ValueError("auth_preparation.kind must name a supported preparation")
        endpoint = str(preparation.get("provider_endpoint", ""))
        if not endpoint.startswith(("http://127.0.0.1:", "https://")):
            raise ValueError(
                "auth_preparation.provider_endpoint must be explicit loopback HTTP or HTTPS"
            )
        credential_env = preparation.get("credential_env")
        if preparation["kind"] == "isolated-api-config":
            if credential_env != "CLAWGAUGE_ISOLATED_API_KEY":
                raise ValueError("isolated API config must use CLAWGAUGE_ISOLATED_API_KEY")
        elif credential_env not in (None, ""):
            raise ValueError("only isolated-api-config may name a credential env")
        config_sha256 = str(preparation.get("config_sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", config_sha256):
            raise ValueError("auth_preparation.config_sha256 must be a SHA-256 hex digest")

    data["repetitions"] = int(data.get("repetitions", 3))
    data["tasks"] = data.get("tasks") or list(TASKS)
    if data["repetitions"] != 3 or data["tasks"] != TASKS:
        raise ValueError("lean campaign is frozen at three tasks x three repetitions")
    bounds = data.get("bounds", {})
    if int(bounds.get("cell_timeout_seconds", 0)) not in range(1, 181):
        raise ValueError("cell_timeout_seconds must be 1..180")
    if int(bounds.get("campaign_timeout_seconds", 0)) not in range(1, 4201):
        raise ValueError("campaign_timeout_seconds must be 1..4200")
    if int(bounds.get("kill_grace_seconds", 0)) not in range(1, 11):
        raise ValueError("kill_grace_seconds must be 1..10")
    if data.get("automatic_retries", 0) != 0:
        raise ValueError("automatic_retries must be zero")
    soft = data.get("soft_accounting", {})
    if "maximum_usd" in soft:
        raise ValueError("hard dollar admission is not part of this campaign")
    if soft.get("estimated_usd") is not None and not isinstance(soft["estimated_usd"], (int, float)):
        raise ValueError("soft_accounting.estimated_usd must be numeric or null")
    return data


def schedule(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    route_ids = [route["id"] for route in manifest["routes"]]
    cells: list[dict[str, Any]] = []
    sequence = 0
    for repetition in range(1, 4):
        for task_index, task in enumerate(TASKS):
            order = route_ids if (repetition + task_index) % 2 else list(reversed(route_ids))
            for position, route_id in enumerate(order, 1):
                sequence += 1
                cells.append(
                    {
                        "sequence": sequence,
                        "task": task,
                        "repetition": repetition,
                        "position": position,
                        "route": route_id,
                    }
                )
    if len(cells) != 18:
        raise AssertionError("internal schedule must contain exactly 18 cells")
    return cells


def route_for(manifest: dict[str, Any], route_id: str) -> dict[str, Any]:
    return next(route for route in manifest["routes"] if route["id"] == route_id)


def cell_contract(
    manifest: dict[str, Any], cell: dict[str, Any], task_fingerprint: str
) -> dict[str, Any]:
    """Identity frozen for one attempted cell, including every requested route control."""
    route = route_for(manifest, cell["route"])
    return {
        "schedule": cell,
        "task_fingerprint": task_fingerprint,
        "route": {
            key: route[key]
            for key in (
                "provider",
                "model",
                "adapter",
                "reasoning",
                "fast",
                "fallback",
                "auth_account",
                "tools_profile",
            )
        },
    }


def verify_shellbench(manifest: dict[str, Any]) -> tuple[Path, str]:
    shellbench = manifest["shellbench"]
    root = Path(shellbench["root"]).expanduser().resolve()
    python = str(Path(shellbench["python"]).expanduser().resolve())
    if not (root / ".git").is_dir():
        raise RuntimeError(f"ShellBench checkout missing: {root}")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    if head != shellbench["commit"]:
        raise RuntimeError("ShellBench commit drift")
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True
    ).stdout
    if dirty:
        raise RuntimeError("ShellBench checkout must be clean")
    probe_env = dict(os.environ)
    probe_env["PYTHONDONTWRITEBYTECODE"] = "1"
    probe = subprocess.run(
        [python, "-c", "import sys, clawbench; assert sys.version_info >= (3, 11)"],
        cwd=root,
        env=probe_env,
        capture_output=True,
        text=True,
    )
    if probe.returncode:
        raise RuntimeError("pinned ShellBench Python is unavailable or unusable: " + probe.stderr.strip())
    return root, python


def transitive(manifest: dict[str, Any], cells: list[dict[str, Any]]) -> dict[str, Any]:
    shellbench_root, python = verify_shellbench(manifest)
    tasks = []
    for task in TASKS:
        found = sorted(
            list(shellbench_root.glob(f"**/{task}.yaml"))
            + list(shellbench_root.glob(f"**/{task}.yml"))
            + list(shellbench_root.glob(f"**/{task}.json"))
        )
        if not found:
            raise RuntimeError(f"ShellBench task missing: {task}")
        tasks.append({"id": task, "path": str(found[0]), "sha256": file_digest(found[0])})
    references = {}
    for path in (
        Path(__file__).resolve(),
        WORKER.resolve(),
        Path(__file__).with_name("personal_campaign_config.py").resolve(),
        Path(__file__).with_name("analyze_personal_campaign.py").resolve(),
        Path(__file__).with_name("process_cleanup.py").resolve(),
    ):
        references[str(path)] = file_digest(path)
    return {
        "manifest_sha256": digest(manifest),
        "schedule_sha256": digest(cells),
        "shellbench_commit": manifest["shellbench"]["commit"],
        "shellbench_root": str(shellbench_root),
        "shellbench_python": python,
        "tasks": tasks,
        "references": references,
    }


def freeze(manifest: dict[str, Any], run_dir: Path, cells: list[dict[str, Any]]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(run_dir, 0o700)
    proof = transitive(manifest, cells)
    for name, value in (("manifest.json", manifest), ("schedule.json", cells), ("freeze.json", proof)):
        path = run_dir / name
        if path.exists() and digest(json.loads(path.read_text())) != digest(value):
            raise RuntimeError(f"{name} drift: start a new run directory")
        if not path.exists():
            write_json(path, value)


def verify_frozen(manifest: dict[str, Any], run_dir: Path, cells: list[dict[str, Any]]) -> None:
    frozen_manifest = json.loads((run_dir / "manifest.json").read_text())
    frozen_schedule = json.loads((run_dir / "schedule.json").read_text())
    proof = json.loads((run_dir / "freeze.json").read_text())
    if digest(frozen_manifest) != digest(manifest) or digest(frozen_schedule) != digest(cells):
        raise RuntimeError("frozen manifest or schedule drift")
    if proof.get("manifest_sha256") != digest(manifest) or proof.get("schedule_sha256") != digest(cells):
        raise RuntimeError("freeze receipt drift")
    for raw_path, expected in proof.get("references", {}).items():
        path = Path(raw_path)
        if not path.is_file() or file_digest(path) != expected:
            raise RuntimeError(f"frozen implementation drift: {path}")
    shellbench_root = Path(proof.get("shellbench_root", manifest["shellbench"]["root"])).resolve()
    for task in proof.get("tasks", []):
        path = Path(task["path"])
        if not path.is_file() or file_digest(path) != task.get("sha256"):
            raise RuntimeError(f"frozen task bytes drift: {path}")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=shellbench_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if head != proof.get("shellbench_commit"):
        raise RuntimeError("frozen ShellBench commit drift")
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=shellbench_root, check=True,
        capture_output=True, text=True,
    ).stdout
    if dirty:
        raise RuntimeError("frozen ShellBench checkout is no longer clean")


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def execution_blockers(manifest: dict[str, Any], run_dir: Path | None = None) -> list[str]:
    """Return only factual, route-specific unmet execution prerequisites."""
    blockers: list[str] = []
    source_value = manifest.get("gateway", {}).get("config_source")
    config_source = Path(source_value).expanduser().resolve() if source_value else None
    if config_source is None or not config_source.is_file():
        blockers.append("gateway: run-local config_source is missing")
        config_digest = None
        config_text = ""
    else:
        config_digest = file_digest(config_source)
        config_text = config_source.read_text(errors="replace")
        if run_dir is not None and not is_within(config_source, run_dir.resolve()):
            blockers.append("gateway: config_source must be inside the evidence run directory")
    for route in manifest["routes"]:
        preparation = route["auth_preparation"]
        if config_digest is not None and preparation["config_sha256"] != config_digest:
            blockers.append(f"{route['id']}: prepared config SHA-256 does not match config_source")
        if config_digest is not None and preparation["provider_endpoint"] not in config_text:
            blockers.append(f"{route['id']}: explicit provider endpoint is absent from config_source")
        if preparation["kind"] == "subscription-handoff":
            blockers.append(
                f"{route['id']}: exact subscription handoff into the disposable Gateway is unsupported"
            )
        if (
            preparation["kind"] == "isolated-api-config"
            and not os.environ.get("CLAWGAUGE_ISOLATED_API_KEY")
        ):
            blockers.append(f"{route['id']}: CLAWGAUGE_ISOLATED_API_KEY is not prepared")
        if route["evidence_tier"] == "strict-decision-grade":
            missing = sorted(
                set(REQUIRED_CONTROLS) - set(route["independently_observed_controls"])
            )
            if missing:
                blockers.append(
                    f"{route['id']}: strict decision-grade observation missing: {', '.join(missing)}"
                )
    return blockers


def terminate_group(process: subprocess.Popen[str], grace_seconds: int) -> None:
    terminate_process_tree(process, grace_seconds)

def execute_process_group(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    log_path: Path,
    timeout_seconds: float,
    grace_seconds: int,
) -> tuple[int, bool, float]:
    started = time.monotonic()
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
        timed_out = False
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            if timed_out or process.poll() is None:
                terminate_group(process, grace_seconds)
        return (124 if timed_out else int(process.returncode), timed_out, time.monotonic() - started)


def prepare_cell(
    manifest: dict[str, Any],
    run_dir: Path,
    runtime_root: Path,
    cell: dict[str, Any],
    shellbench_python: str,
) -> tuple[Path, Path]:
    route = route_for(manifest, cell["route"])
    cell_name = f"{cell['sequence']:02d}-{cell['route']}-{cell['task']}-r{cell['repetition']}"
    evidence_root = run_dir / "cells" / cell_name
    cell_root = runtime_root / "cells" / cell_name
    if cell_root.exists() or evidence_root.exists():
        raise RuntimeError(f"cell already attempted; zero-retry policy requires a new run: {cell_name}")
    cell_root.mkdir(parents=True)
    evidence_root.mkdir(parents=True)
    config_source = Path(manifest["gateway"]["config_source"]).expanduser().resolve()
    if not config_source.is_file() or not str(config_source).startswith(str(run_dir.resolve()) + os.sep):
        raise RuntimeError("gateway.config_source must be an operator-staged file inside run_dir")
    config_path = cell_root / "openclaw.json"
    shutil.copyfile(config_source, config_path)
    gateway_url = manifest["gateway"]["url"]
    port = int(gateway_url.rsplit(":", 1)[1])
    frozen = json.loads((run_dir / "freeze.json").read_text())
    task_fingerprint = next(
        item["sha256"] for item in frozen["tasks"] if item["id"] == cell["task"]
    )
    contract = cell_contract(manifest, cell, task_fingerprint)
    spec = {
        **cell,
        "run_root": str(run_dir.resolve()),
        "runtime_root": str(runtime_root.resolve()),
        "cell_root": str(cell_root.resolve()),
        "evidence_root": str(evidence_root.resolve()),
        "home": str((cell_root / "home").resolve()),
        "state_dir": str((cell_root / "state").resolve()),
        "config_path": str(config_path.resolve()),
        "workspace_root": str((cell_root / "state" / "workspace-clawbench").resolve()),
        "output_path": str((evidence_root / "native-result.json").resolve()),
        "gateway_url": gateway_url,
        "gateway_command": [
            manifest["gateway"]["executable"],
            "gateway",
            "run",
            "--bind",
            "loopback",
            "--port",
            str(port),
        ],
        "gateway_token_env": manifest["gateway"].get("token_env", ""),
        "provider": route["provider"],
        "model": route["model"],
        "adapter": route["adapter"],
        "reasoning": route["reasoning"],
        "fast": route["fast"],
        "fallback": route["fallback"],
        "auth_account": route["auth_account"],
        "tools_profile": route["tools_profile"],
        "task_fingerprint": task_fingerprint,
        "cell_contract": contract,
        "cell_sha256": digest(contract),
        "required_observed_controls": route["required_observed_controls"],
        "independently_observed_controls": route["independently_observed_controls"],
        "evidence_tier": route["evidence_tier"],
        "auth_preparation": route["auth_preparation"],
    }
    spec_path = evidence_root / "cell.json"
    write_json(spec_path, spec)
    return evidence_root, spec_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--armed", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    cells = schedule(manifest)
    run_dir = args.run_dir.expanduser().resolve()
    freeze(manifest, run_dir, cells)
    blockers = execution_blockers(manifest, run_dir)
    plan = {
        "mode": "execute" if args.execute else "plan",
        "cells": len(cells),
        "automatic_retries": 0,
        "hard_dollar_gate": False,
        "soft_estimated_usd": manifest.get("soft_accounting", {}).get("estimated_usd"),
        "observed_cost_usd": None,
        "execution_blockers": blockers,
    }
    write_json(run_dir / "plan.json", plan)
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return 0
    if not args.armed:
        raise SystemExit("--execute requires --armed")
    if blockers:
        write_json(run_dir / "execution-blocked.json", plan)
        print("BLOCKED before Gateway/provider contact: " + "; ".join(blockers), file=sys.stderr)
        return 78

    shellbench_root, shellbench_python = verify_shellbench(manifest)
    bounds = manifest["bounds"]
    campaign_started = time.monotonic()
    failures = 0
    timed_out_campaign = False
    with tempfile.TemporaryDirectory(prefix="clawgauge-runtime-") as raw_runtime:
        runtime_root = Path(raw_runtime).resolve()
        for cell in cells:
            verify_frozen(manifest, run_dir, cells)
            elapsed = time.monotonic() - campaign_started
            remaining = bounds["campaign_timeout_seconds"] - elapsed
            if remaining <= 0:
                timed_out_campaign = True
                write_json(run_dir / "campaign-timeout.json", {"elapsed_seconds": elapsed})
                break
            if elapsed >= 2700:
                print("WARNING: campaign elapsed time exceeded 45 minutes", file=sys.stderr)
            evidence_root, spec_path = prepare_cell(
                manifest, run_dir, runtime_root, cell, shellbench_python
            )
            spec = json.loads(spec_path.read_text())
            env = {
                "PATH": os.environ.get("PATH", os.defpath),
                "LANG": os.environ.get("LANG", "C.UTF-8"),
                "PYTHONPATH": str(shellbench_root),
            }
            credential_env = spec["auth_preparation"].get("credential_env")
            if credential_env:
                env[credential_env] = os.environ[credential_env]
            code, timed_out, duration = execute_process_group(
                [shellbench_python, str(WORKER), "--cell", str(spec_path)],
                cwd=Path(spec["cell_root"]),
                env=env,
                log_path=evidence_root / "worker.log",
                timeout_seconds=min(bounds["cell_timeout_seconds"], remaining),
                grace_seconds=bounds["kill_grace_seconds"],
            )
            write_json(
                evidence_root / "supervisor-receipt.json",
                {
                    "cell_sha256": spec["cell_sha256"],
                    "duration_seconds": round(duration, 3),
                    "exit_code": code,
                    "timed_out": timed_out,
                    "retry": 0,
                    "observed_cost_usd": None,
                },
            )
            failures += int(code != 0)
    write_json(
        run_dir / "campaign-receipt.json",
        {
            "attempted_cells": len(list((run_dir / "cells").glob("*/supervisor-receipt.json"))),
            "failed_cells": failures,
            "campaign_timed_out": timed_out_campaign,
            "runtime_root_removed": True,
        },
    )
    if timed_out_campaign:
        return 124
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
