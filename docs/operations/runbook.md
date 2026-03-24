# Repository Runbook

## Current operator workflow

The main documented operational flow today is the local LLM workflow under `local-llms/`.

Primary references:

- [`local-llms/README.md`](../../local-llms/README.md)
- [`local-llms/RUNBOOK.md`](../../local-llms/RUNBOOK.md)

## Repository-level operating conventions

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
