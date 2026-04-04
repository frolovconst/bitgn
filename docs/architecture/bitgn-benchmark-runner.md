# BitGN Benchmark Runner

## Purpose

Describe the benchmark-facing execution paths that connect Columbarium's agent
code to the BitGN API and scoring flow.

## Summary

The repository now includes BitGN runners under `src/benchmark/bitgn/` that
reproduce the core behavior of the sibling `sample-agents` project while
remaining inside Columbarium's architecture constraints.

## Key architectural choices

- benchmark execution code lives under `src/benchmark/bitgn/`
- model generation goes through `src/model_clients/` only
- BitGN harness, mini-runtime, and PCM-runtime clients are isolated in the benchmark package
- runtime configuration is environment-backed rather than hard-coded in agent logic
- operator entry goes through versioned scripts such as `scripts/run-bitgn-sandbox` and `scripts/run-bitgn-pac1`

## Main flow

1. load benchmark and model configuration
2. create a provider-agnostic model client
3. fetch benchmark metadata from the BitGN harness
4. start a trial for each selected task
5. run the task loop against the benchmark-specific BitGN runtime until completion or step limit
6. end the trial and print scores

## Important boundaries

- `src/benchmark/bitgn/sandbox_agent_loop.py`: mini-runtime sandbox task loop
- `src/benchmark/bitgn/sandbox_runtime.py`: BitGN mini-runtime dispatch adapter
- `src/benchmark/bitgn/pac1_agent_loop.py`: PCM-runtime PAC1 task loop
- `src/benchmark/bitgn/pac1_runtime.py`: BitGN PCM-runtime dispatch adapter
- `src/benchmark/bitgn/runner.py`: benchmark and trial orchestration
- `src/model_clients/`: provider-specific model transport

## Why this shape matters

This keeps the first benchmark-facing implementation small and runnable without
collapsing the repository back into a flat sample script.
