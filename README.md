# columbarium

Build and evaluate personal AI agents for BitGN benchmark tasks.

## Goal

Maximize BitGN score with fast, measurable iteration.

## Current focus

The main target is the benchmark-facing agent loop.
That core implementation is still in progress.

## Main areas

- `src/`: agent logic and supporting code for the benchmark-facing loop.
- `src/model_clients/`: provider adapters behind one model-client interface.
- `notebooks/`: exploratory notebooks for API probing and agent-development experiments.
- `workspaces/agent-runtime/`: Python dev and test shell.
- `workspaces/local-llms/`: local model runtime and Ollama workflows used to debug agent code without paid API usage.
- `docs/`: source-of-truth project docs.

## Start here

- `AGENTS.md`
- `docs/README.md`
- `docs/project/index.md`
