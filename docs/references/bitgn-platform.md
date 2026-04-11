# BitGN Platform Reference

## Source

- URL: <https://bitgn.com/>
- Local vendored proto: [`../../proto/bitgn/`](../../proto/bitgn/)
- Upstream source copied from: `/Users/kofrolov/prj/expts/bitgn/sample-agents/proto/bitgn/`
- Sample agents repository location: `/Users/kofrolov/prj/expts/bitgn/sample-agents`
- Last checked: 2026-04-11

## Observed benchmark API shape (as of 2026-04-11)

The benchmark-facing API used by this project currently has three relevant parts:

1. `harness`
2. `vm.mini`
3. `vm.pcm`

Practical interpretation for this repository:

- `harness` is the control-plane entrypoint for connecting to the platform and running sets of tasks.
- `vm.mini` and `vm.pcm` are distinct task surfaces with different tool capabilities.
- `vm.mini` is used for sandbox-style/debug runs.
- `vm.pcm` is used for leaderboard-scored runs.
- Agents are expected to solve tasks from both MINI and PCM using each runtime's available tools.

## Working assumptions

- Agents interact with challenge environments via API.
- Platform provides deterministic scoring and feedback.
- Results are compared on a leaderboard.

## Benchmark runtime surfaces used in this repo

- `bitgn/pac1-dev` -> PCM runtime (`proto/bitgn/vm/pcm.proto`)
- `bitgn/sandbox` -> MINI runtime (`proto/bitgn/vm/mini.proto`)

Notes:

- The two runtimes have different tool surfaces and different answer request schemas.
- In current code, `trial-launch-mode playground` uses `StartPlayground`.
- In current code, `trial-launch-mode run` uses `StartRun -> StartTrial -> EndTrial -> SubmitRun(force=true)`.
- Runtime selection is handled at answer-submission time by benchmark id.

## Implemented runtime API calls (as of 2026-04-11)

Implementation source:

- Runtime wrappers, descriptions, and validators: `src/benchmark/bitgn/runtime_tools.py`
- Platform exposure/helpers: `src/benchmark/bitgn/platform.py`

`bitgn/pac1-dev` (PCM) implemented calls:

- `Read`
- `Write`
- `Delete`
- `MkDir`
- `Move`
- `List`
- `Tree`
- `Find`
- `Search`
- `Context`
- `Answer`

`bitgn/sandbox` (MINI) implemented calls:

- `Outline`
- `Search`
- `List`
- `Read`
- `Write`
- `Delete`
- `Answer`

Validation behavior:

- Every runtime tool has an input validator.
- Validation failures return a structured tool result with:
  - `error=validation_error`
  - a concrete failure message
  - actionable `guidance` for revise-and-retry flow by the LLM caller

Use round-specific docs for rule or API details.
