# Agent Runtime Workspace

## Purpose

Define a Nix shell for day-to-day Python development and fast test execution without Ollama runtime dependencies.

This keeps the agent runtime/test loop separate from `workspaces/local-llms/`, which is optimized for local model hosting.

## Location

- `workspaces/agent-runtime/flake.nix`
- `workspaces/agent-runtime/README.md`

## Included tools

- `python3`
- `uv`
- `git`
- `jq`
- `ripgrep`
- `curl`

## Intended usage

Use this workspace when you need to:

- run unit tests quickly
- develop benchmark-agent Python code
- install and run package dependencies without bringing Ollama into the environment

Use `workspaces/local-llms/` when you need to run local model serving workflows.
