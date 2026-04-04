# Repository Structure

Target structure for modular experimentation.

```text
columbarium/
├─ AGENTS.md
├─ README.md
├─ ARCHITECTURE.md
├─ docs/
├─ src/
│  ├─ agent/
│  ├─ benchmark/
│  ├─ model_clients/
│  └─ config/
├─ tests/
├─ scripts/
├─ runs/
└─ workspaces/
   ├─ agent-runtime/
   └─ local-llms/
```

## Rules

- Keep platform and agent concerns separated.
- Prefer replaceable modules over monolithic logic.
- Keep workspace-specific state inside each workspace.
- Keep durable knowledge in `docs/`.
