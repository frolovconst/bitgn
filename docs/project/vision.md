# Vision

## Purpose

`columbarium` exists to develop an AI agent that performs as strongly as possible on BitGN benchmark challenges. The project is not just about running local models or experimenting with tooling. It is about turning those ingredients into a repeatable engineering loop that improves measurable benchmark outcomes.

BitGN provides API-connected challenge environments, deterministic scoring, and a public leaderboard. That makes the core project question concrete: what agent architecture, tool-use strategy, memory approach, and reliability discipline actually produce better scores under the benchmark's constraints? This repository is where we capture and refine those answers.

## Primary objective

Build an agent that can compete effectively on BitGN and climb as high as possible on the leaderboard.

## Desired outcomes

- A reproducible agent-development workflow that supports fast benchmark iteration.
- An agent architecture that improves benchmark outcomes rather than just looking sophisticated in isolation.
- A documented body of lessons about what helps or hurts score, reliability, and task completion on BitGN.

## Success signals

- The repository can reproduce agent runs and benchmark-facing workflows with minimal setup friction.
- The project tracks changes in benchmark score, task success patterns, and failure modes over time.
- The agent reaches progressively stronger positions on the BitGN leaderboard.

## Anti-goals

- Accumulating local LLM tooling that is not clearly connected to benchmark performance.
- Optimizing for impressive architecture or novelty without evidence that it improves benchmark results.

## Working philosophy

- Prefer measurable benchmark gains over aesthetic complexity.
- Treat every infrastructure addition as support for the evaluation loop.
- Capture durable learnings so future agent work starts from evidence, not folklore.
