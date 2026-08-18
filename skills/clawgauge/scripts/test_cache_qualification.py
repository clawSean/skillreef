#!/usr/bin/env python3
"""Provider-free loopback tests for prefix-cache qualification."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Iterator, Tuple


ROOT = Path(__file__).resolve().parent.parent
QUALIFIER = ROOT / "scripts" / "qualify_prefix_cache.py"


class State:
    def __init__(self, **overrides: object) -> None:
        self.calls = 0
        self.exact_hits = 0
        self.exact_stores = 0
        self.cold_cached = 0
        self.warm_cached = 5000
        self.replay_cached = 6000
        self.warm_text = "CACHE_WARM_OK"
        self.omit_cache_telemetry = False
        self.increment_exact_hit = True
        self.increment_exact_store = True
        self.disk_writes = 0
        self.chat_calls = 0
        self.hybrid_prompt_memo = False
        self.response_model = "mock-model"
        self.response_models = None
        self.prompt_memo: Dict[str, dict] = {}
        for key, value in overrides.items():
            setattr(self, key, value)


def handler_for(state: State) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def send_json(self, value: dict, status: int = 200) -> None:
            raw = json.dumps(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            state.calls += 1
            if self.path == "/health":
                self.send_json({"status": "ok", "apc_enabled": True})
                return
            if self.path == "/v1/cache/stats":
                self.send_json(
                    {
                        "enabled": True,
                        "exact_hits": state.exact_hits,
                        "exact_stores": state.exact_stores,
                        "disk_hits": 0,
                        "disk_writes": state.disk_writes,
                    }
                )
                return
            self.send_json({"error": "not found"}, 404)

        def do_POST(self) -> None:
            state.calls += 1
            if self.path == "/v1/cache/reset":
                state.exact_hits = 0
                state.exact_stores = 0
                self.send_json({"enabled": True, "status": "cleared"})
                return
            if self.path != "/v1/chat/completions":
                self.send_json({"error": "not found"}, 404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            messages = payload.get("messages", [])
            prompt_key = json.dumps(messages, sort_keys=True, separators=(",", ":"))
            warm = any(
                isinstance(message, dict)
                and message.get("content") == "Reply exactly: CACHE_WARM_OK"
                for message in messages
            )
            state.chat_calls += 1
            if state.increment_exact_store:
                state.exact_stores += 1
            if warm and state.increment_exact_hit:
                state.exact_hits += 1
            if state.hybrid_prompt_memo and prompt_key in state.prompt_memo:
                self.send_json(copy.deepcopy(state.prompt_memo[prompt_key]))
                return
            replay = warm and prompt_key in state.prompt_memo
            cached = (
                state.replay_cached
                if replay
                else state.warm_cached
                if warm
                else state.cold_cached
            )
            text = state.warm_text if warm else "CACHE_COLD_OK"
            response = {
                "id": f"mock-{'warm' if warm else 'cold'}-{state.chat_calls}",
                "choices": [{"message": {"role": "assistant", "content": text}}],
                "usage": {"prompt_tokens": 6000},
            }
            observed_model = (
                state.response_models[state.chat_calls - 1]
                if isinstance(state.response_models, list)
                and state.chat_calls <= len(state.response_models)
                else state.response_model
            )
            if observed_model is not None:
                response["model"] = observed_model
            if not state.omit_cache_telemetry:
                response["usage"]["prompt_tokens_details"] = {"cached_tokens": cached}
            state.prompt_memo[prompt_key] = copy.deepcopy(response)
            self.send_json(response)

    return Handler


@contextmanager
def mock_server(**overrides: object) -> Iterator[Tuple[str, State]]:
    state = State(**overrides)
    server = HTTPServer(("127.0.0.1", 0), handler_for(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/v1", state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def run_qualifier(
    root: Path,
    label: str,
    base_url: str,
    runtime: str,
    expected: int,
    *extra: str,
) -> Dict[str, object]:
    out = root / f"{label}.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(QUALIFIER),
            "--base-url",
            base_url,
            "--model",
            "mock-model",
            "--runtime",
            runtime,
            "--runtime-version",
            "0.31.3" if runtime == "mlx-lm" else "0.6.15",
            "--mlx-version",
            "0.32.1",
            "--model-revision",
            "a" * 40,
            "--cache-epoch",
            f"epoch-{label}",
            "--prefix-words",
            "100",
            "--minimum-reused-tokens",
            "1000",
            "--timeout",
            "5",
            "--run-id",
            f"test-{label}",
            "--out",
            str(out),
            *extra,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != expected:
        raise AssertionError(
            f"{label}: expected {expected}, got {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return json.loads(out.read_text(encoding="utf-8"))


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="clawgauge-cache-qualification-") as raw:
        root = Path(raw)

        with mock_server() as (base_url, state):
            before = state.calls
            plan = run_qualifier(root, "plan", base_url, "mlx-vlm", 0, "--plan")
            assert state.calls == before
            assert plan["network_calls_performed"] == 0
            assert plan["schema_version"] == "clawgauge.prefix-cache-qualification-plan.v3"
            assert "POST /v1/chat/completions (exact warm replay)" in plan["requests"]
            checks += 4

        with mock_server() as (base_url, _state):
            report = run_qualifier(root, "vlm-pass", base_url, "mlx-vlm", 0)
            assert report["ok"] is True
            assert report["checks"]["vlm_exact_hit_delta"] is True
            assert report["checks"]["vlm_reset_after"] is True
            assert report["checks"]["response_memoization_disproved"] is True
            assert report["server"]["lifecycle"]["same_process"] is True
            assert report["checks"]["response_model_exact"] is True
            assert report["claim_granted"] == "direct-service-prefix-reuse"
            assert report["server"]["fallback_proven_off"] is False
            checks += 8

        with mock_server() as (base_url, state):
            report = run_qualifier(root, "lm-pass", base_url, "mlx-lm", 0)
            assert report["ok"] is True
            assert state.calls == 3
            assert report["warm"]["cached_tokens"] == 5000
            assert report["replay"]["cached_tokens"] == 6000
            assert report["warm"]["request_id"] != report["replay"]["request_id"]
            checks += 5

        with mock_server(warm_cached=10) as (base_url, _state):
            report = run_qualifier(root, "warm-floor", base_url, "mlx-lm", 2)
            assert report["checks"]["warm_cached_token_floor"] is False
            checks += 1

        with mock_server(warm_text="CACHE_COLD_OK") as (base_url, _state):
            report = run_qualifier(root, "memoized", base_url, "mlx-lm", 2)
            assert report["checks"]["response_memoization_disproved"] is False
            checks += 1

        # This hybrid passed the old two-request protocol: cold and warm were
        # distinct, while exact prompt repeats were served from a response
        # memo with fabricated prefix-cache counters. The replay gate must
        # reject its repeated response ID and unchanged cached-token usage.
        with mock_server(hybrid_prompt_memo=True) as (base_url, _state):
            report = run_qualifier(root, "hybrid-prompt-memo", base_url, "mlx-lm", 2)
            assert report["checks"]["replay_canary_exact"] is True
            assert report["checks"]["replay_cached_token_growth"] is False
            assert report["checks"]["response_memoization_disproved"] is False
            assert any("full-response memoization" in item for item in report["blockers"])
            checks += 4

        with mock_server(omit_cache_telemetry=True) as (base_url, _state):
            report = run_qualifier(root, "missing-telemetry", base_url, "mlx-lm", 2)
            assert report["checks"]["cold_cached_tokens_zero"] is False
            assert any("telemetry is missing" in item for item in report["blockers"])
            checks += 2

        with mock_server(disk_writes=1) as (base_url, _state):
            report = run_qualifier(root, "disk-write", base_url, "mlx-vlm", 2)
            assert report["checks"]["vlm_no_disk_activity"] is False
            checks += 1

        with mock_server(increment_exact_hit=False) as (base_url, _state):
            report = run_qualifier(root, "no-exact-hit", base_url, "mlx-vlm", 2)
            assert report["checks"]["vlm_exact_hit_delta"] is False
            checks += 1

        with mock_server(response_model=None) as (base_url, _state):
            report = run_qualifier(root, "missing-model", base_url, "mlx-lm", 2)
            assert report["checks"]["response_model_exact"] is False
            assert report["claim_granted"] is None
            checks += 2

        with mock_server(response_model="wrong-model") as (base_url, _state):
            report = run_qualifier(root, "wrong-model", base_url, "mlx-lm", 2)
            assert report["checks"]["response_model_exact"] is False
            checks += 1

        with mock_server(response_models=["mock-model", "other-model", "mock-model"]) as (base_url, _state):
            report = run_qualifier(root, "changing-model", base_url, "mlx-lm", 2)
            assert report["checks"]["response_model_exact"] is False
            checks += 1

        external = subprocess.run(
            [
                sys.executable,
                str(QUALIFIER),
                "--base-url",
                "https://example.com/v1",
                "--model",
                "mock-model",
                "--runtime",
                "mlx-lm",
                "--runtime-version",
                "0.31.3",
                "--mlx-version",
                "0.32.1",
                "--model-revision",
                "a" * 40,
                "--cache-epoch",
                "epoch-external",
                "--plan",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert external.returncode == 2
        assert "loopback" in external.stderr
        checks += 2

        for label, flag, value, expected_message in (
            ("mutable-revision", "--model-revision", "main", "immutable"),
            ("bad-runtime-version", "--runtime-version", "latest", "major.minor.patch"),
            ("bad-mlx-version", "--mlx-version", "0.32", "major.minor.patch"),
        ):
            args = [
                sys.executable, str(QUALIFIER), "--base-url", "http://127.0.0.1:9/v1",
                "--model", "mock-model", "--runtime", "mlx-lm",
                "--runtime-version", "0.31.3", "--mlx-version", "0.32.1",
                "--model-revision", "a" * 40, "--cache-epoch", f"epoch-{label}",
                "--plan",
            ]
            args[args.index(flag) + 1] = value
            completed = subprocess.run(args, text=True, capture_output=True, check=False)
            assert completed.returncode == 2 and expected_message in completed.stderr
            checks += 1

    print(f"ClawGauge cache qualification tests: PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
