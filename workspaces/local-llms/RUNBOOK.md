# Local LLM Runbook

From repo root:

1. Start server:
```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#ollama-serve
```

2. Pull a model:
```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#<model-app>-pull
```

3. Run a model:
```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#<model-app>-chat
```

Naming template:

- `<model-app>` uses the script/app stem in `workspaces/local-llms/bin/` and `workspaces/local-llms/flake.nix`.

Optional test:
```bash
uv run pytest --run-local-model
```
