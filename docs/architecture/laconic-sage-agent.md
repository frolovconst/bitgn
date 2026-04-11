# LaconicSage Agent

`LaconicSage` is the LangGraph-based benchmark agent mode used for real tool-calling runs.

## Purpose

- Replace placeholder behavior with an iterative, benchmark-aware loop.
- Reuse the shared model-client boundary (`model_clients`) across providers.
- Keep outputs concise while preserving grounded behavior.

## Runtime flow

1. Build runtime tool definitions from `runtime_tools` for the active benchmark id.
2. Start a LangGraph state machine with system prompt + task instruction.
3. Call the selected model through `ModelClient.generate(..., tools=...)`.
4. If tool calls are requested, execute them through `call_runtime_tool(...)` and feed results back into the loop.
5. Parse a strict JSON terminal answer into `AgentAnswer`.
6. If evidence is insufficient, return `OUTCOME_NONE_CLARIFICATION`.

## Safety and quality constraints

- Prompt enforces instruction precedence, including root and nested `AGENTS.md` rules.
- Prompt instructs no hallucination and clarification fallback when uncertain.
- Safety is explicit priority: uncertain or risky actions should downgrade to safe outcomes.
- Turn count is capped (`max_turns=4`) for bounded latency and throughput.
- Generation budget is capped (`max_tokens=220`, timeout up to 20s) to keep decisions fast.

## Logging

During each trial, agent actions are appended to the run "SOLUTION LOG" stream:

- trial start
- model turn count and response shape
- tool calls, arguments, and tool results
- terminal outcome and final message

This log is intended to support fast benchmark debugging and score iteration.
