# local-llms workspace

This folder is the isolated workspace for local LLM experimentation inside Columbarium.

## What lives here

- Nix-based development shell for agent and local-LLM work
- local configuration files such as `.env`
- helper scripts and flake apps for Ollama-based development

## Enter the environment

If you use flakes:

```bash
nix develop ./workspaces/local-llms
```

Or from inside this directory:

```bash
cd workspaces/local-llms
nix develop
```

## Included tools

- `ollama`
- `python3`
- `uv`
- `git`
- `jq`
- `ripgrep`
- `curl`

## Notes

- Keep secrets in `workspaces/local-llms/.env`.
- Ollama model data is stored under `workspaces/local-llms/.ollama/models` to keep this workspace self-contained.
- Scripts under `workspaces/local-llms/bin/` default `LOCAL_LLM_HOME`, `OLLAMA_HOST`, and `OLLAMA_MODELS` to workspace-scoped values.
- See [`RUNBOOK.md`](./RUNBOOK.md) for the reproducible workflow.
- The main flake apps are:

```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#ollama-serve
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#qwen25-coder-3b-pull
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#qwen25-coder-3b-chat
```
