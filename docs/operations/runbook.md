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

Use the placeholder benchmark runner to validate wiring and configuration:

- script: `scripts/run_bitgn_agent.py`
- module entry point: `python -m benchmark.bitgn.cli`
- console script (after install): `bitgn-run`

Example:

```bash
bitgn-run --task-id t01
```

Debug mode:

```bash
bitgn-run --task-id t01 --debug
```

Current behavior is intentionally placeholder-only:

- initializes model-provider wiring (`local`/`openai`)
- executes a mock platform + mock agent-loop flow
- does not yet call the real BitGN API or solve tasks
- in `--debug` mode, prints detailed run diagnostics (future hook for full LLM traces)

## Experiment record minimum

- commit SHA
- benchmark score
