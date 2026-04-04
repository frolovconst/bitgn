# Architecture

Keep architecture simple and replaceable.

## Core boundary

- Platform layer: benchmark API integration and run plumbing.
- Agent layer: the benchmark-facing loop, strategy, planning, memory, and tool-use behavior.

Use adapters where needed; avoid coupling core agent logic to one provider or loop design.

## Current emphasis

The main architectural concern is the agent loop.
Workspace docs exist to support development around that core.

## Docs

- [`repository-structure.md`](./repository-structure.md)
- [`agent-model-client.md`](./agent-model-client.md)
- [`agent-runtime-workspace.md`](./agent-runtime-workspace.md)
- [`local-llms-workspace.md`](./local-llms-workspace.md)
