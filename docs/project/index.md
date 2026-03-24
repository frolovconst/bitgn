# Project Index

This section defines what the repository is for and how to reason about it.

## Current understanding

`columbarium` is a repository for building and iterating on an AI agent for BitGN benchmark challenges.

The repository exists to support a tight benchmark loop:

- build or improve the agent
- run it against the BitGN challenge environment
- study failures and score changes
- evolve the system toward stronger leaderboard performance

The `workspaces/local-llms/` workspace is supporting infrastructure for that goal. It is not the goal by itself.

## Documents in this section

- [`vision.md`](./vision.md): why this repository exists and what it is trying to enable
- [`scope.md`](./scope.md): current scope, non-goals, and likely expansion areas
- [`glossary.md`](./glossary.md): project-specific terminology
- [`../references/bitgn-platform.md`](../references/bitgn-platform.md): verified external benchmark assumptions

## Questions this section should answer

- What problem space does this repository serve?
- What counts as success for the project?
- What are the current boundaries of the work?
- Which words have precise meanings in this repository?
