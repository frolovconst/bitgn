# agent-runtime workspace architecture

`workspaces/agent-runtime/` is the default Python dev/test workspace.

## Purpose

- Default workspace for building and testing the agent loop.
- Fast tests.
- Runtime development without Ollama dependency.
- Optional notebook-based API exploration via the `notebook` dependency group.

Use `workspaces/local-llms/` when local model serving is required.
