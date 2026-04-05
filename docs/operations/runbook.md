# Runbook

## Workflow rules

- New feature -> new branch.
- Do not implement feature work on `main`.
- Decompose large tasks before coding.
- Use the workspace that matches the task.

## Workspaces

1. `workspaces/agent-runtime/`: default workspace for agent-loop development and tests.
2. `workspaces/local-llms/`: Ollama and local-model workflows used when local inference helps debugging or experiments.

## Benchmark run entry point

Use the benchmark runner to launch trials and validate wiring:

- script: `scripts/run_bitgn_agent.py`
- module entry point: `python -m benchmark.bitgn.cli`
- console script (after install): `bitgn-run`

Example:

```bash
uv run --group bitgn-playground bitgn-run --task-id t01
```

Full benchmark task series:

```bash
uv run --group bitgn-playground bitgn-run --all-tasks
```

Debug mode:

```bash
uv run --group bitgn-playground bitgn-run --task-id t01 --debug
```

Current behavior is intentionally minimal:

- initializes model-provider wiring (`local`/`openai`)
- starts real BitGN trials via `StartPlayground` by default
- default agent mode is `dumb`: calls one random valid runtime tool, then submits `Done` with `OUTCOME_OK`
- optional `--agent-mode placeholder` keeps the non-submitting placeholder behavior
- in `--debug` mode, prints detailed run diagnostics (future hook for full LLM traces)
- in `--debug` mode, prints the full available runtime tool list at run start
- in `--debug` mode, prints each agent action and per-tool API call parameters + response payload
- each task output block is wrapped with clear visual separators for scanability

Trial launch mode:

- default: `--trial-launch-mode playground`
- future stub: `--trial-launch-mode run` (reserved for leaderboard-flow wiring)

Benchmark/runtime separation:

- `bitgn/pac1-dev` uses PCM runtime semantics
- `bitgn/sandbox` uses MINI runtime semantics

## Experiment record minimum

- commit SHA
- benchmark score
