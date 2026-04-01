# BitGN Benchmark Runner

## Purpose

Describe the benchmark-facing execution path that connects Columbarium's agent
code to the BitGN API and scoring flow.

## Summary

The repository now includes a minimal BitGN runner under `src/benchmark/bitgn/`
that reproduces the core behavior of the sibling `sample-agents` project while
remaining inside Columbarium's architecture constraints.

## Key architectural choices

- benchmark execution code lives under `src/benchmark/bitgn/`
- model generation goes through `src/model_clients/` only
- BitGN harness and mini-runtime clients are isolated in the benchmark package
- runtime configuration is environment-backed rather than hard-coded in agent logic
- operator entry goes through the versioned script `scripts/run-bitgn-sandbox`

## Main flow

1. load benchmark and model configuration
2. create a provider-agnostic model client
3. fetch benchmark metadata from the BitGN harness
4. start a trial for each selected task
5. run the task loop against the BitGN mini runtime until completion or step limit
6. end the trial and print scores

## Important boundaries

- `src/benchmark/bitgn/agent_loop.py`: task-solving loop and agent prompt
- `src/benchmark/bitgn/runtime.py`: BitGN mini-runtime dispatch adapter
- `src/benchmark/bitgn/runner.py`: benchmark and trial orchestration
- `src/model_clients/`: provider-specific model transport

## Why this shape matters

This keeps the first benchmark-facing implementation small and runnable without
collapsing the repository back into a flat sample script.
