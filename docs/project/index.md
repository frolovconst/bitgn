# Project

## Core priorities (equal weight)

1. Maximize BitGN benchmark score.
2. Keep architecture modular and replaceable (LLM, agent loop, strategies).
3. Implement each new feature in a new branch.
4. Keep an experiment platform where agent implementations can be swapped and tested through the benchmark interface.

## Current state

The central deliverable is the benchmark-facing agent loop.
That loop is not implemented yet.

`workspaces/local-llms/` is a supporting environment for local-model debugging and development, not the product itself.

## Audience

Primary: coding agents.
Secondary: human maintainers.

## Documents

- [`vision.md`](./vision.md)
- [`scope.md`](./scope.md)
- [`glossary.md`](./glossary.md)
- [`../references/bitgn-platform.md`](../references/bitgn-platform.md)
