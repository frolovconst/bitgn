# Local LLM Workspace

## Summary

The `local-llms/` directory is the current primary implementation workspace in this repository.

Its role is to provide an isolated, reproducible environment for local LLM development and experimentation.

## Responsibilities

- define the Nix development shell for local LLM work
- host helper scripts for Ollama workflows
- keep model storage scoped to the workspace
- provide reproducible commands for serving, pulling, and chatting with local models

## Key files

- [`local-llms/README.md`](../../local-llms/README.md)
- [`local-llms/RUNBOOK.md`](../../local-llms/RUNBOOK.md)
- [`local-llms/flake.nix`](../../local-llms/flake.nix)
- [`local-llms/bin/`](../../local-llms/bin)

## Operational model

- development environment is created through Nix
- Ollama commands are wrapped in versioned scripts and flake apps
- model data is intentionally stored under `local-llms/.ollama/models`

## Invariants

- local model state should remain workspace-scoped unless a deliberate change is made
- reproducible commands should be documented and runnable from versioned definitions
- secrets should not be committed and should stay in local configuration such as `.env`

## Open questions

- What additional models should be standardized?
- Should evaluation and benchmarking live in this workspace or in a sibling workspace?
- What interfaces should future agents rely on here?
