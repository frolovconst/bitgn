# Repository Knowledge Base

This `docs/` directory is the system of record for durable repository knowledge.

`AGENTS.md` is intentionally short. It points here.

## Principles

- Keep navigational docs short and link outward.
- Keep source-of-truth docs close to the topic they describe.
- Avoid one giant manual.
- Update docs in the same change when behavior, architecture, or workflows materially change.
- Prefer one canonical document per topic instead of repeating the same guidance in many places.

## Directory map

- [`project/`](./project/index.md): project purpose, scope, vocabulary, and success criteria
- [`architecture/`](./architecture/index.md): system boundaries, technical structure, and component relationships
- [`operations/`](./operations/index.md): how to run, debug, and maintain working environments
- [`experiments/`](./experiments/index.md): active research and findings
- [`exec-plans/`](./exec-plans/README.md): implementation plans, active work, and completed work records
- [`decisions/`](./decisions/index.md): major decisions and tradeoffs
- [`references/`](./references/index.md): curated external references and local copies of critical vendor material
- [`generated/`](./generated/README.md): generated artifacts that are useful for agents and humans
- [`templates/`](./templates/README.md): reusable templates for new documents

## Maintenance expectations

- If a document becomes large, add an index page and split it.
- If a document contains temporary planning, move closed outcomes into `exec-plans/completed/`.
- If something becomes stale, either update it or mark it as historical.
- When uncertain, add a short note with explicit placeholders instead of inventing detail.
