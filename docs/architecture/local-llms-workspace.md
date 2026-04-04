# local-llms workspace architecture

`workspaces/local-llms/` is the local model runtime workspace.

## Responsibilities

- Nix shell for Ollama workflows.
- Scripts/flake apps for serve, pull, chat.
- Workspace-scoped model storage.
- Local debugging path for agent code without paid API calls.

## Boundaries

- Supports agent development and debugging.
- Does not define benchmark-facing agent architecture.
- Is a building block, not the main product surface of the repository.

## References

- [`workspaces/local-llms/README.md`](../../workspaces/local-llms/README.md)
- [`workspaces/local-llms/RUNBOOK.md`](../../workspaces/local-llms/RUNBOOK.md)
