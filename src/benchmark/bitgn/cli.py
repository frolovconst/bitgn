from __future__ import annotations

import argparse
from typing import Sequence

from model_clients.factory import create_model_client
from model_clients.types import ModelClientConfig

from .agent_loop import PlaceholderAgentLoop
from .config import (
    BenchmarkRunConfig,
    DEFAULT_MODEL_PROVIDER,
    default_model_base_url,
    default_model_name,
    env_default_benchmark_host,
    env_default_benchmark_id,
)
from .platform import PlaceholderBenchmarkPlatform
from .runner import BenchmarkRunService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bitgn-run",
        description="Launch one benchmark trial run for the BitGN agent (placeholder mode).",
    )
    parser.add_argument("--benchmark-host", default=env_default_benchmark_host())
    parser.add_argument("--benchmark-id", default=env_default_benchmark_id())
    parser.add_argument("--task-id", required=True, help="Benchmark task id, for example: t01")
    parser.add_argument("--allow-submit", action="store_true", help="Submit answer and end trial")

    parser.add_argument(
        "--model-provider",
        choices=["local", "openai"],
        default=DEFAULT_MODEL_PROVIDER,
        help="Model provider behind the shared model-client boundary.",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Model id/name. Default depends on provider.",
    )
    parser.add_argument(
        "--model-base-url",
        default=None,
        help="Provider API base URL. Default depends on provider.",
    )
    parser.add_argument(
        "--model-api-key-env",
        default="OPENAI_API_KEY",
        help="Environment variable name with OpenAI API key.",
    )
    parser.add_argument(
        "--model-timeout-seconds",
        type=float,
        default=60.0,
        help="Per-request timeout for model API calls.",
    )
    return parser


def parse_config(argv: Sequence[str] | None = None) -> BenchmarkRunConfig:
    args = build_parser().parse_args(argv)
    provider = args.model_provider
    return BenchmarkRunConfig(
        benchmark_host=args.benchmark_host,
        benchmark_id=args.benchmark_id,
        task_id=args.task_id,
        allow_submit=args.allow_submit,
        model_provider=provider,
        model_name=args.model_name or default_model_name(provider),
        model_base_url=args.model_base_url or default_model_base_url(provider),
        model_api_key_env=(args.model_api_key_env if provider == "openai" else None),
        model_timeout_seconds=args.model_timeout_seconds,
    )


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_config(argv)

    # Construct and validate model client now so provider/model wiring stays
    # exercised even before agent loop logic is implemented.
    _ = create_model_client(
        ModelClientConfig(
            provider=config.model_provider,
            model=config.model_name,
            base_url=config.model_base_url,
            api_key_env=config.model_api_key_env,
            timeout_seconds=config.model_timeout_seconds,
        )
    )

    service = BenchmarkRunService(
        platform=PlaceholderBenchmarkPlatform(benchmark_host=config.benchmark_host),
        agent_loop=PlaceholderAgentLoop(),
    )
    summary = service.run_once(config)

    print(f"trial_id: {summary.trial_id}")
    print(f"benchmark_id: {summary.benchmark_id}")
    print(f"task_id: {summary.task_id}")
    print(f"submitted: {summary.submitted}")
    print(f"score: {summary.score}")
    print("score_detail:")
    for line in summary.score_detail:
        print(f"- {line}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
