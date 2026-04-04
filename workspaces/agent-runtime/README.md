# agent-runtime workspace

Default workspace for Python development and fast tests.

## Enter shell

```bash
nix develop ./workspaces/agent-runtime
```

## Includes

`python3`, `uv`, `git`, `jq`, `ripgrep`, `curl`

## Typical test

```bash
uv run pytest
```

Use `workspaces/local-llms/` for Ollama runtime workflows.
