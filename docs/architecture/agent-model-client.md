# Agent Model Client

Goal: switch model providers without changing agent logic.

## Interface

- `ModelClient.generate(messages, settings, tools) -> ModelResponse`

Core agent code depends only on this interface.

## Current adapters

- local Ollama adapter
- OpenAI adapter

## Constraints

- Keep provider branching out of agent decision code.
- Normalize request/response types.
- Use config to switch providers.
- Preserve tool-calling parity across providers.
