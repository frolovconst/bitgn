# Repository Runbook

## Current operator workflows

### 1) Fast Python runtime + tests

Use `workspaces/agent-runtime/` for quick local development and unit tests.

Primary references:

- [`workspaces/agent-runtime/README.md`](../../workspaces/agent-runtime/README.md)

### 2) Local LLM hosting and experimentation

Use `workspaces/local-llms/` for Ollama serving, model pulls, and local model chat.

Primary references:

- [`workspaces/local-llms/README.md`](../../workspaces/local-llms/README.md)
- [`workspaces/local-llms/RUNBOOK.md`](../../workspaces/local-llms/RUNBOOK.md)

## Repository-level operating conventions

- implement new features on a new branch by default; avoid developing feature work directly on `main`
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
