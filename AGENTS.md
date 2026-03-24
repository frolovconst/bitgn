# AGENTS.md

This file is the entry point for agents working in this repository.

Do not treat this file as the full project manual. Treat it as the map.
The system of record for project knowledge lives under [`docs/`](./docs/README.md).

## What this repository is

`columbarium` is a repository for building and improving an AI agent for BitGN benchmark challenges.

The main objective is to maximize benchmark performance and leaderboard standing on BitGN.

Right now, the main active area is [`local-llms/`](./local-llms/README.md), an isolated supporting workspace for:

- local model experimentation
- Ollama-based development workflows
- Nix-based reproducibility
- agent-development tooling

## How to navigate the knowledge base

Start here depending on the task:

- Project intent and scope: [`docs/project/index.md`](./docs/project/index.md)
- Architecture and technical boundaries: [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Local LLM workspace details: [`docs/architecture/local-llms-workspace.md`](./docs/architecture/local-llms-workspace.md)
- Operational workflows: [`docs/operations/index.md`](./docs/operations/index.md)
- Current and historical execution plans: [`docs/exec-plans/README.md`](./docs/exec-plans/README.md)
- Research notes and experiments: [`docs/experiments/index.md`](./docs/experiments/index.md)
- Decisions and tradeoffs: [`docs/decisions/index.md`](./docs/decisions/index.md)
- External references and vendor docs: [`docs/references/index.md`](./docs/references/index.md)
- Verified BitGN context: [`docs/references/bitgn-platform.md`](./docs/references/bitgn-platform.md)

## Working rules for agents

- Prefer repo docs over assumptions.
- Optimize for measurable benchmark progress rather than generic experimentation.
- If you discover something important that is durable, add or update the relevant doc in `docs/`.
- If you make a significant architectural or workflow change, update the matching system-of-record file in the same change.
- Keep top-level docs short and navigational. Move depth into the relevant folder under `docs/`.
- When documentation is missing, create the smallest correct record instead of stuffing context into ad hoc notes.

## Current repo shape

- [`README.md`](./README.md): brief repository entry point
- [`local-llms/README.md`](./local-llms/README.md): local LLM workspace overview
- [`local-llms/RUNBOOK.md`](./local-llms/RUNBOOK.md): reproducible workflow for Ollama and model usage
- [`docs/`](./docs/README.md): system of record for durable repository knowledge

## Documentation hygiene

When adding or updating docs:

- favor concise, high-signal writing
- record facts, not aspirations, unless the file is explicitly a plan
- date time-sensitive notes
- link related documents instead of duplicating content
- mark placeholders clearly so they can be filled in later

## If you are unsure where to write something

- Enduring technical truth: `docs/architecture/`
- Workflow or operator instructions: `docs/operations/`
- Product or project intent: `docs/project/`
- Proposed or active work: `docs/exec-plans/`
- Experimental findings: `docs/experiments/`
- Decision rationale: `docs/decisions/`
- Third-party references: `docs/references/`
