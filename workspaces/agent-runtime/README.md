# agent-runtime workspace

Default workspace for Python development and fast tests.

## Enter shell

```bash
nix develop ./workspaces/agent-runtime
```

If `nix` is not available in the current shell, load the daemon profile first:

```bash
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
```

## Includes

`python3`, `uv`, `git`, `jq`, `ripgrep`, `curl`

## Typical test

```bash
uv run pytest
```

Use `workspaces/local-llms/` for Ollama runtime workflows.
