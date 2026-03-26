# columbarium

Repository for building an AI agent to compete on BitGN benchmark challenges and climb the leaderboard.

## Project Areas

- `src/model_clients/` - provider-agnostic model client boundary with local (Ollama) and OpenAI adapters.
- `workspaces/agent-runtime/` - Nix workspace for Python runtime development and fast tests.
- `workspaces/local-llms/` - isolated workspace for local model runtime and Ollama-focused experimentation.

## Repository Knowledge

- `AGENTS.md` - short agent-facing map for navigating the repository
- `docs/` - system of record for durable project knowledge
- `ARCHITECTURE.md` - high-level architecture entry point

## Current Objective

Develop an agent that performs as strongly as possible on the BitGN benchmark platform.
