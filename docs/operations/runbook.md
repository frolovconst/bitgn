# Repository Runbook

## Current operator workflows

### 1) Fast Python runtime + tests

Use `workspaces/agent-runtime/` for quick local development and unit tests.

Primary references:

- [`workspaces/agent-runtime/README.md`](../../workspaces/agent-runtime/README.md)

This workspace now also contains the BitGN benchmark baseline runner. Use it to:

- run the repository's benchmark-facing Python agent
- connect to the BitGN API and score the agent against a benchmark
- iterate on agent logic while keeping model access behind the current model-client abstraction

Current versioned entrypoints:

- `./scripts/run-bitgn-sandbox` for the mini-runtime sandbox benchmark
- `./scripts/run-bitgn-pac1` for the PCM-runtime PAC1 benchmark

### 2) Local LLM hosting and experimentation

Use `workspaces/local-llms/` for Ollama serving, model pulls, and local model chat.

Primary references:

- [`workspaces/local-llms/README.md`](../../workspaces/local-llms/README.md)
- [`workspaces/local-llms/RUNBOOK.md`](../../workspaces/local-llms/RUNBOOK.md)

## Repository-level operating conventions

- start all new feature work on a new branch before making code changes
- do not implement feature work directly on `main`
- enter the correct workspace before running workspace-specific tooling
- prefer versioned scripts and flake apps over ad hoc local commands
- keep environment-specific state isolated where possible
- document any repeated operational procedure in this section or in the relevant workspace runbook

## Add new runbooks here when needed

Examples:

- benchmark execution
- experiment result capture
- environment reset procedures
- dependency update routines
