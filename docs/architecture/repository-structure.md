# Repository Structure

## Summary

This document proposes a repository structure for `columbarium` that separates benchmark-facing code, supporting workspaces, run artifacts, and durable documentation.

This structure is a recommended direction, not a fixed constraint. It should be changed if needed to better support benchmark performance, reproducibility, or maintainability.

## Goals

- keep benchmark-facing code easy to find and evolve
- separate core agent logic from provider-specific model integrations
- preserve isolated supporting workspaces such as local LLM development
- give run artifacts and evaluation outputs a predictable home
- keep durable project knowledge in `docs/`

## Suggested layout

```text
columbarium/
├─ README.md
├─ AGENTS.md
├─ ARCHITECTURE.md
├─ docs/
│  ├─ project/
│  ├─ architecture/
│  ├─ operations/
│  ├─ exec-plans/
│  ├─ experiments/
│  ├─ decisions/
│  ├─ references/
│  ├─ templates/
│  └─ generated/
├─ src/
│  ├─ agent/
│  │  ├─ core/
│  │  ├─ prompts/
│  │  ├─ strategies/
│  │  └─ tasks/
│  ├─ model_clients/
│  ├─ benchmark/
│  │  ├─ runner/
│  │  ├─ submit/
│  │  └─ artifacts/
│  ├─ config/
│  │  ├─ schema/
│  │  └─ presets/
│  └─ utils/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ fixtures/
├─ scripts/
│  ├─ dev/
│  ├─ run-benchmark
│  ├─ submit-score
│  └─ collect-artifacts
├─ runs/
│  ├─ local/
│  └─ scored/
├─ workspaces/
│  └─ local-llms/
└─ third_party/
```

## Ownership boundaries

- `docs/`: durable repository knowledge and navigation
- `src/agent/`: benchmark agent behavior and task-solving logic
- `src/model_clients/`: provider adapters behind a common model-client boundary
- `src/benchmark/`: evaluation, submission, and artifact collection flow
- `src/config/`: validated runtime configuration and reusable presets
- `tests/`: verification for core logic, integrations, and fixtures
- `scripts/`: operator-oriented entry points and development helpers
- `runs/`: generated run outputs, logs, and scored artifacts
- `workspaces/`: isolated support environments such as local model experimentation

## Notes on evolution

- `local-llms/` is currently the main active workspace and could later move under `workspaces/` if that improves clarity
- not every directory needs to exist immediately; this layout can be adopted incrementally as benchmark-facing code lands
- if future work shows a better split between evaluation, agent logic, and tooling, this structure should be revised rather than preserved for its own sake
