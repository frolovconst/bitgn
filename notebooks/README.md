# Notebooks

Exploratory notebooks for API probing and experiment support.

Current starter:

- `bitgn_api_playground.ipynb`: manual BitGN Harness + PCM request flow.

## Run

1. Enter runtime shell:

```bash
nix develop ./workspaces/agent-runtime
```

If `nix` is not available in the current shell, run:

```bash
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
```

2. Install optional notebook dependencies:

```bash
uv sync --group notebook --group bitgn-playground
```

3. Start JupyterLab:

```bash
uv run jupyter lab
```

If you see `ModuleNotFoundError: No module named 'connectrpc'`, rerun:

```bash
uv sync --group notebook --group bitgn-playground
```
