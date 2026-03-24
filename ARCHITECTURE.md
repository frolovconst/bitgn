# Architecture

This file is the high-level architecture map for the repository.
Detailed source-of-truth documents live in [`docs/architecture/`](./docs/architecture/index.md).

## Current state

The repository currently acts as a benchmark-agent project with supporting experimentation infrastructure.

The central product goal is to build an AI agent that performs strongly on BitGN benchmark challenges.

The first established technical workstream is [`workspaces/local-llms/`](./workspaces/local-llms/README.md), which provides:

- an isolated Nix development environment
- local Ollama-based model workflows
- helper scripts for serving, pulling, and chatting with models
- workspace-local model storage under `workspaces/local-llms/.ollama/models`

## Architectural intent

The repo is organized to support a fast, reproducible benchmark-improvement loop.

That means:

- infrastructure and workflows should be versioned
- local state should stay scoped to the relevant workspace where possible
- helper scripts should remain easy to inspect
- evolving project knowledge should live in docs alongside the code
- benchmark-facing learnings should be captured as durable project knowledge

## Architecture index

- Overview and boundaries: [`docs/architecture/index.md`](./docs/architecture/index.md)
- Local LLM workspace details: [`docs/architecture/local-llms-workspace.md`](./docs/architecture/local-llms-workspace.md)
- Operational runbooks: [`docs/operations/index.md`](./docs/operations/index.md)

## Open areas to document

- the benchmark-facing agent architecture itself
- run and score tracking workflows
- challenge-specific strategy or adaptation layers
- interfaces between local tooling and the BitGN evaluation environment
