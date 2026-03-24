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
