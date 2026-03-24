# Agent Model Client Architecture

## Purpose

Define a minimal, extensible architecture that allows the benchmark agent to switch between:

- local LLM runtimes (for example, Ollama)
- frontier API LLM providers

This architecture is intentionally small so the project can improve benchmark performance quickly while preserving a clean path to higher-scoring provider and model choices.

## Core interface

Use a single provider-agnostic interface in agent code:

- `ModelClient.generate(messages, settings) -> ModelResponse`

Agent logic depends on this interface only.
Provider-specific SDK or transport code stays inside adapter implementations.

## Initial adapters

- `LocalOllamaClient` for local model runs
- `FrontierApiClient` for hosted API models

Both adapters must return the same normalized `ModelResponse` shape.

## Runtime selection via config

Select the active model provider through configuration (not code edits).

Suggested config shape:

```yaml
model:
  provider: local # local | api
  model: qwen2.5-coder:3b
  base_url: http://127.0.0.1:11434
  api_key_env: OPENAI_API_KEY
  timeout_seconds: 60
```

Guidelines:

- keep `provider` and `model` mandatory
- keep credentials out of Git and load from environment variables
- allow provider-specific optional fields while preserving a common top-level schema

## Design constraints for current contest phase

- keep the adapter boundary narrow and testable
- avoid provider-specific branching in core agent decision logic

## Done criteria for this architecture slice

- agent can run with `provider: local`
- agent can run with `provider: api`
- switching providers requires configuration change only
- run artifacts record which provider/model produced each result
