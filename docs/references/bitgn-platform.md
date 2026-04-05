# BitGN Platform Reference

## Source

- URL: <https://bitgn.com/>
- Local vendored proto: [`../../proto/bitgn/`](../../proto/bitgn/)
- Upstream source copied from: `/Users/kofrolov/prj/expts/bitgn/sample-agents/proto/bitgn/`
- Last checked: 2026-04-05

## Working assumptions

- Agents interact with challenge environments via API.
- Platform provides deterministic scoring and feedback.
- Results are compared on a leaderboard.

## Benchmark runtime surfaces used in this repo

- `bitgn/pac1-dev` -> PCM runtime (`proto/bitgn/vm/pcm.proto`)
- `bitgn/sandbox` -> MINI runtime (`proto/bitgn/vm/mini.proto`)

Notes:

- The two runtimes have different tool surfaces and different answer request schemas.
- In current code, trial launch stays control-plane compatible (`StartPlayground`), and runtime selection is handled at answer-submission time by benchmark id.

Use round-specific docs for rule or API details.
