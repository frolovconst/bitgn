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

Current behavior:

- initializes model-provider wiring (`local`/`openai`)
- starts real BitGN trials via `StartPlayground` by default
- default agent mode is `llm`: iterative tool-using loop with `report_completion`
- optional `--agent-mode dumb` keeps connectivity-check behavior
- optional `--agent-mode placeholder` keeps non-solving placeholder behavior
- in `--debug` mode, prints run-level settings once, available tools, per-task actions, LLM step output, and final run score summary
- each task output block is wrapped with visual separators for scanability

Trial launch mode:

- default: `--trial-launch-mode playground`
- future stub: `--trial-launch-mode run` (reserved for leaderboard-flow wiring)

Benchmark/runtime separation:

- `bitgn/pac1-dev` uses PCM runtime semantics
- `bitgn/sandbox` uses MINI runtime semantics

## CLI options reference

- `--benchmark-host <url>`: BitGN API host. Default: `https://api.bitgn.com`.
- `--benchmark-id <id>`: benchmark id. Default from `BENCHMARK_ID` env or project default.
- `--task-id <id>`: run a single task (for example `t01`).
- `--all-tasks`: run all tasks returned by `GetBenchmark` (mutually exclusive with `--task-id`).
- `--allow-submit`: submit agent answer and call `EndTrial`; without this flag, run is dry and unsubmitted.
- `--agent-mode <llm|dumb|placeholder>`: choose agent implementation mode. Default: `llm`.
- `--trial-launch-mode <playground|run>`: trial launch strategy. Default: `playground` (`run` is reserved stub).
- `--debug`: enable verbose diagnostics and formatted run/task summaries.
- `--model-provider <local|openai>`: LLM provider backend. Default: `local`.
- `--model-name <name>`: model id/name. Default depends on provider (local default: `qwen3.5:4b`).
- `--model-base-url <url>`: provider API base URL. Default depends on provider.
- `--model-api-key-env <env_var>`: OpenAI API key env var name. Used only when provider is `openai`. Default: `OPENAI_API_KEY`.
- `--model-timeout-seconds <float>`: per-request model API timeout. Default: `60.0`.

## Full command examples

All options in single-task mode:

```bash
uv run --group bitgn-playground bitgn-run \
  --benchmark-host https://api.bitgn.com \
  --benchmark-id bitgn/sandbox \
  --task-id t01 \
  --allow-submit \
  --agent-mode llm \
  --trial-launch-mode playground \
  --debug \
  --model-provider local \
  --model-name qwen3.5:4b \
  --model-base-url http://127.0.0.1:11434 \
  --model-timeout-seconds 60
```

All options in all-tasks mode (replace `--task-id` with `--all-tasks`):

```bash
uv run --group bitgn-playground bitgn-run \
  --benchmark-host https://api.bitgn.com \
  --benchmark-id bitgn/sandbox \
  --all-tasks \
  --allow-submit \
  --agent-mode llm \
  --trial-launch-mode playground \
  --debug \
  --model-provider local \
  --model-name qwen3.5:4b \
  --model-base-url http://127.0.0.1:11434 \
  --model-timeout-seconds 60
```

OpenAI provider variant (shows `--model-api-key-env` usage):

```bash
uv run --group bitgn-playground bitgn-run \
  --benchmark-host https://api.bitgn.com \
  --benchmark-id bitgn/pac1-dev \
  --task-id t01 \
  --allow-submit \
  --agent-mode llm \
  --trial-launch-mode playground \
  --debug \
  --model-provider openai \
  --model-name gpt-4.1-mini \
  --model-base-url https://api.openai.com \
  --model-api-key-env OPENAI_API_KEY \
  --model-timeout-seconds 60
```

## Experiment record minimum

- commit SHA
- benchmark score
