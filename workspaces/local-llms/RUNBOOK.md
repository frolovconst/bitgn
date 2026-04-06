# Local LLM Runbook

Use reproducible flake apps from repo root.

1. Serve:
```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#ollama-serve
```

2. Pull model:
```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#qwen35-4b-pull
```

3. Chat:
```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#qwen35-4b-chat
```

Alternative model (9B):
```bash
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#qwen35-9b-pull
nix --extra-experimental-features 'nix-command flakes' run ./workspaces/local-llms#qwen35-9b-chat
```

Optional integration test:
```bash
uv run pytest --run-local-model
```
