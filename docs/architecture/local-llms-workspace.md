# Local LLM Workspace

## Summary

The `workspaces/local-llms/` directory is the current primary supporting workspace in this repository.

Its role is to provide an isolated, reproducible environment for agent development in support of BitGN benchmark work.

## Responsibilities

- define the Nix development shell for local LLM work
- host helper scripts for Ollama workflows
- keep model storage scoped to the workspace
- provide reproducible commands for serving, pulling, and chatting with local models
- support fast local iteration on agent behavior before or alongside benchmark runs

## Key files

- [`workspaces/local-llms/README.md`](../../workspaces/local-llms/README.md)
- [`workspaces/local-llms/RUNBOOK.md`](../../workspaces/local-llms/RUNBOOK.md)
- [`workspaces/local-llms/flake.nix`](../../workspaces/local-llms/flake.nix)
- [`workspaces/local-llms/bin/`](../../workspaces/local-llms/bin)

## Operational model

- development environment is created through Nix
- Ollama commands are wrapped in versioned scripts and flake apps
- model data is intentionally stored under `workspaces/local-llms/.ollama/models`

## Invariants

- local model state should remain workspace-scoped unless a deliberate change is made
- reproducible commands should be documented and runnable from versioned definitions
- secrets should not be committed and should stay in local configuration such as `.env`

## Open questions

- What additional models should be standardized?
- Should evaluation and benchmarking live in this workspace or in a sibling workspace?
- What interfaces should future agents rely on here?
- Which parts of the BitGN-facing agent loop should be testable locally?
