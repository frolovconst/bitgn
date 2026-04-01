# agent-runtime workspace

This workspace provides a Nix development shell focused on:

- running the main Python code for the benchmark agent
- running fast local tests without Ollama-specific tooling

## Enter the environment

From repository root:

```bash
nix develop ./workspaces/agent-runtime
```

From inside this directory:

```bash
cd workspaces/agent-runtime
nix develop
```

## Included tools

- python3
- uv
- git
- jq
- ripgrep
- curl

## Typical setup and test flow

```bash
uv run pytest
```

To include the real local-model integration test:

```bash
uv run pytest --run-local-model
```

Use this shell for model-client unit tests and general Python development.
Use `workspaces/local-llms/` when you need an Ollama runtime.

## BitGN benchmark baseline

This workspace also hosts the benchmark-facing Python runtime that mirrors the
core functionality of the sibling `sample-agents` repository while using
Columbarium's current model-client abstraction.

Run the sandbox benchmark with:

```bash
BITGN_MODEL=gpt-4.1-mini ./scripts/run-bitgn-sandbox
```

Run selected tasks only:

```bash
BITGN_MODEL=gpt-4.1-mini ./scripts/run-bitgn-sandbox t01 t03
```

Required environment:

- `BITGN_MODEL`: model id used by the current model client

Common optional environment:

- `BITGN_MODEL_PROVIDER`: `openai` or `local` (default: `openai`)
- `BITGN_MODEL_BASE_URL`: override model endpoint
- `BITGN_MODEL_API_KEY_ENV`: API key env var for OpenAI-compatible providers
- `BENCHMARK_HOST`: BitGN API host (default: `https://api.bitgn.com`)
- `BITGN_BENCHMARK_ID`: benchmark id (default: `bitgn/sandbox`)
- `BITGN_AGENT_MAX_STEPS`: max reasoning steps per task (default: `30`)

For local-model runs, start the Ollama workspace separately and point
`BITGN_MODEL_PROVIDER=local`.
