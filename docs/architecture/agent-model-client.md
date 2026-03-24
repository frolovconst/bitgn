# Agent Model Client Architecture

## Purpose

Define a minimal, extensible architecture that allows the benchmark agent to switch between:

- local LLM runtimes (Ollama)
- OpenAI API-hosted models

This architecture is intentionally small so the project can improve benchmark performance quickly while preserving a clean path to provider and model changes.

## Core interface

Use a single provider-agnostic interface in agent code:

- `ModelClient.generate(messages, settings) -> ModelResponse`

Agent logic depends on this interface only.
Provider-specific transport code stays inside adapter implementations.

## Implemented adapters (v1)

- `LocalOllamaClient` in `src/model_clients/ollama_client.py`
- `OpenAIModelClient` in `src/model_clients/openai_client.py`

Both adapters return a normalized `ModelResponse` shape from `src/model_clients/types.py`.

A small factory in `src/model_clients/factory.py` selects the adapter from config.

## Runtime selection via config

Current config shape:

```python
ModelClientConfig(
  provider="local",   # local | openai
  model="qwen2.5-coder:3b",
  base_url="http://127.0.0.1:11434",
  api_key_env="OPENAI_API_KEY",  # openai only
  timeout_seconds=60.0,
)
```

Guidelines:

- keep `provider` and `model` mandatory
- keep credentials out of Git and load from environment variables
- allow provider-specific optional fields while preserving a common top-level schema

## Design constraints for current contest phase

- keep the adapter boundary narrow and testable
- avoid provider-specific branching in core agent decision logic
- prioritize fast unit tests by mocking transport rather than launching model servers

## Done criteria for this architecture slice

- agent can run with `provider: local`
- agent can run with `provider: openai`
- switching providers requires configuration change only
- tests validate request/response normalization behavior without external network dependencies
