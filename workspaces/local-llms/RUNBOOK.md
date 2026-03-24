# Local LLM Runbook

This workflow keeps Ollama and its model data scoped to the `local-llms` workspace.

## Recommended approach

Use versioned scripts plus flake apps:

- the scripts are easy to inspect and edit
- the flake apps make them reproducible to run from any shell
- the model storage remains under `workspaces/local-llms/.ollama/models`

## One-time setup

From the repository root:

```bash
cd workspaces/local-llms
nix --extra-experimental-features 'nix-command flakes' develop
```

## Reproducible commands

From the repository root:

1. Start Ollama in one terminal:

```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#ollama-serve
```

2. Pull the model in a second terminal:

```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#qwen25-coder-3b-pull
```

3. Start the chat session:

```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#qwen25-coder-3b-chat
```

4. Optionally run the live model-client integration test from the repository root in your runtime shell:

```bash
uv run pytest --run-local-model
```

## Under the hood

- `bin/common-env.sh` derives `LOCAL_LLM_HOME` and defaults `OLLAMA_HOST` and `OLLAMA_MODELS` so model state stays workspace-scoped
- `bin/ollama-serve.sh` starts the server
- `bin/qwen25-coder-3b-pull.sh` downloads the model
- `bin/qwen25-coder-3b-chat.sh` runs the model interactively

## Why this is reproducible

- the commands are stored in Git
- the Nix flake pins package resolution through `flake.lock`
- model storage is local to this workspace instead of your default user profile
