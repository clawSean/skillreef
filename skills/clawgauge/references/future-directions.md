# Future Directions

These are useful later, but out of scope until the basic model-quality benchmark is proven.

## SeanBench Scenario Pack

A fake-but-representative scenario pack modeled after Sean/JPop workflows:

- Telegram mention-gating and reply-context behavior
- fake preference recall from temporary QA memory
- fake secret no-echo and safe diagnostics
- proof-backed contribution status reporting
- code review with source reads and tests
- source-backed research memo
- usage-log summarization
- denial of sensitive local read requests
- failure recovery after a bad tool call
- Bottom Feeder-style knowledge extraction

All scenarios should use fake data and deterministic verifiers first.

## Operational Usage Telemetry

A separate lane for real-world usage visibility:

- OpenClaw `/usage`, `/status`, and `/usage cost`
- transcript-backed usage entries
- provider quota windows from `openclaw status --usage`
- token and cache counters by provider/model/runtime
- fallback frequency and retry spend
- sanitized Partner Trace JSONL exports for process analysis

This is not the first benchmark. It answers "what are we spending and where are tokens going?" rather than "is the new model capable?"

## External Benchmark Adapter: Agents' Last Exam

A later adapter/inspiration lane for evaluating full agent harnesses beyond ClawBench.

Agents' Last Exam (ALE) from Berkeley RDI is relevant because it evaluates frontier agent systems on long-horizon, economically valuable tasks across many industries. Its shape maps well to the eventual mature version of this skill:

- real OS sandboxes instead of simplified prompt-only tasks
- hidden references staged only after the agent finishes
- deterministic graders and verifiable outcomes
- captured trajectories, raw logs, and task artifacts
- full harness comparison rather than model-only answer comparison
- existing harness paths for OpenClaw-style, Codex, Grok, Claude/Cursor-style agents

Do not make ALE the immediate path. Treat it as a v4/v5 external benchmark adapter after Sean/JPop have clean local ClawBench comparisons and Personal Agent QA gates. ALE setup is heavier: GCP or Docker sandbox setup, cloud/project configuration, secrets, longer runs, and broader infra cleanup. The near-term job remains ClawBench-first scored comparisons plus OpenClaw Personal Agent QA gates.

Useful future work:

- capture ALE repo commit, task list, environment, provider routing, run count, and cost in model-quality reports
- add an `ale` result-ingest/summarizer path only after ClawBench JSON comparison is stable
- compare OpenClaw harness behavior against Codex/Grok/Claude-style harnesses when the question is about agent-system design, not only model choice
- borrow ALE's hidden-reference and trajectory/artifact discipline for any future SeanBench scenarios

## Decision Layer

Later, benchmark outputs could drive a model-routing guide:

- best model by task class
- cheapest acceptable model by task class
- models to avoid for tool-heavy work
- models that need narrower tool surfaces
- when to escalate to premium models
- when local/open-weight models are acceptable

Do not build this until ClawBench and the personal-agent pack have produced credible local results.
