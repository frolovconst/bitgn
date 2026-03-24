# local-llms

This folder is the isolated workspace for local LLM experimentation inside Columbarium.

## What lives here

- Nix-based development shell for agent and local-LLM work
- local configuration files such as `.env`
- future helper scripts for Ollama-based development

## Enter the environment

If you use flakes:

```bash
nix develop ./local-llms
```

Or from inside this directory:

```bash
cd local-llms
nix develop
```

## Included tools

- `python3`
- `uv`
- `git`
- `jq`
- `ripgrep`
- `curl`

## Notes

- Keep secrets in `local-llms/.env`.
- This environment is intentionally focused on development tooling; Ollama itself can still be run natively on macOS and pointed to from the agent code.
