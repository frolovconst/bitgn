# local-llms workspace

Isolated workspace for local model runtime experiments.

## Enter shell

```bash
nix develop ./workspaces/local-llms
```

## Includes

`ollama`, `python3`, `uv`, `git`, `jq`, `ripgrep`, `curl`

## Notes

- Keep secrets in `.env`.
- Keep model state under `.ollama/models`.
- See [`RUNBOOK.md`](./RUNBOOK.md) for commands.
