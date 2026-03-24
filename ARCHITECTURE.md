# Architecture

This file is the high-level architecture map for the repository.
Detailed source-of-truth documents live in [`docs/architecture/`](./docs/architecture/index.md).

## Current state

The repository currently acts as a container for experimental workstreams.

The first established workstream is [`local-llms/`](./local-llms/README.md), which provides:

- an isolated Nix development environment
- local Ollama-based model workflows
- helper scripts for serving, pulling, and chatting with models
- workspace-local model storage under `local-llms/.ollama/models`

## Architectural intent

The repo is organized to keep experimentation reproducible, inspectable, and compartmentalized.

That means:

- infrastructure and workflows should be versioned
- local state should stay scoped to the relevant workspace where possible
- helper scripts should remain easy to inspect
- evolving project knowledge should live in docs alongside the code

## Architecture index

- Overview and boundaries: [`docs/architecture/index.md`](./docs/architecture/index.md)
- Local LLM workspace details: [`docs/architecture/local-llms-workspace.md`](./docs/architecture/local-llms-workspace.md)
- Operational runbooks: [`docs/operations/index.md`](./docs/operations/index.md)

## Open areas to document

- future subprojects beyond `local-llms/`
- shared conventions across experimental workspaces
- deployment or service topology, if the repo grows into running systems
- interfaces between experiments, tooling, and any product-facing surfaces
