from __future__ import annotations

import argparse
from dataclasses import replace
from typing import Sequence

from model_clients.factory import create_model_client
from model_clients.types import ModelClientConfig

from .agent_loop import DumbAgentLoop, PlaceholderAgentLoop
from .config import (
    DEFAULT_AGENT_MODE,
    BenchmarkRunConfig,
    DEFAULT_MODEL_PROVIDER,
    DEFAULT_TRIAL_LAUNCH_MODE,
    default_model_base_url,
    default_model_name,
    env_default_benchmark_host,
    env_default_benchmark_id,
)
from .platform import BitgnBenchmarkPlatform, TrialLaunchMode
from .runner import BenchmarkRunService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bitgn-run",
        description="Launch one BitGN benchmark trial run (playground-first, placeholder agent logic).",
    )
    parser.add_argument("--benchmark-host", default=env_default_benchmark_host())
    parser.add_argument("--benchmark-id", default=env_default_benchmark_id())
    parser.add_argument("--task-id", default=None, help="Benchmark task id, for example: t01")
    parser.add_argument(
        "--all-tasks",
        action="store_true",
        help="Run the full benchmark task list from GetBenchmark.",
    )
    parser.add_argument("--allow-submit", action="store_true", help="Submit answer and end trial")
    parser.add_argument(
        "--agent-mode",
        choices=["dumb", "placeholder"],
        default=DEFAULT_AGENT_MODE,
        help="Agent implementation mode. Use dumb for end-to-end connectivity checks.",
    )
    parser.add_argument(
        "--trial-launch-mode",
        choices=[TrialLaunchMode.PLAYGROUND.value, TrialLaunchMode.RUN.value],
        default=DEFAULT_TRIAL_LAUNCH_MODE,
        help="Trial launch strategy. Use playground by default; run mode is a future stub.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debug output. Reserved for future full LLM traces.",
    )

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
    if not args.all_tasks and not args.task_id:
        raise SystemExit("Either --task-id or --all-tasks must be provided.")
    if args.all_tasks and args.task_id:
        raise SystemExit("Use either --task-id or --all-tasks, not both.")
    provider = args.model_provider
    return BenchmarkRunConfig(
        benchmark_host=args.benchmark_host,
        benchmark_id=args.benchmark_id,
        task_id=args.task_id,
        all_tasks=args.all_tasks,
        allow_submit=args.allow_submit,
        agent_mode=args.agent_mode,
        debug=args.debug,
        trial_launch_mode=args.trial_launch_mode,
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

    platform = BitgnBenchmarkPlatform(
        benchmark_host=config.benchmark_host,
        launch_mode=config.trial_launch_mode,
    )
    task_ids = [config.task_id] if config.task_id else platform.list_task_ids(config.benchmark_id)

    if not task_ids:
        print("No tasks returned by benchmark.")
        return 0

    if config.debug:
        _print_available_tools(config.benchmark_id, platform.list_available_tools(config.benchmark_id))

    for index, task_id in enumerate(task_ids, start=1):
        agent_actions: list[str] = []
        agent_loop = _create_agent_loop(config=config, platform=platform, agent_actions=agent_actions)
        service = BenchmarkRunService(platform=platform, agent_loop=agent_loop)

        task_config = replace(config, task_id=task_id, all_tasks=False)
        summary = service.run_once(task_config)
        _print_task_summary(
            summary,
            debug=config.debug,
            index=index,
            total=len(task_ids),
            agent_actions=agent_actions,
        )

    return 0


def _create_agent_loop(
    config: BenchmarkRunConfig,
    platform: BitgnBenchmarkPlatform,
    agent_actions: list[str],
):
    action_sink = agent_actions.append if config.debug else None
    if config.agent_mode == "dumb":
        return DumbAgentLoop(
            call_random_tool_fn=platform.call_random_tool,
            action_sink=action_sink,
        )
    return PlaceholderAgentLoop(action_sink=action_sink)


def _print_task_summary(
    summary,
    debug: bool,
    index: int,
    total: int,
    agent_actions: list[str],
) -> None:
    divider = "=" * 72
    print(divider)
    print(f"Task {index}/{total} | {summary.task_id}")
    print(divider)
    print(f"trial_id: {summary.trial_id}")
    print(f"benchmark_id: {summary.benchmark_id}")
    print(f"task_id: {summary.task_id}")
    print(f"submitted: {summary.submitted}")
    print(f"score: {summary.score}")
    print("score_detail:")
    for line in summary.score_detail:
        print(f"- {line}")
    if debug:
        print("debug_detail:")
        for line in summary.debug_detail:
            print(f"- {line}")
        print("agent_actions:")
        if agent_actions:
            for action in agent_actions:
                print(f"- {action}")
        else:
            print("- (none)")


def _print_available_tools(benchmark_id: str, tools: list[str]) -> None:
    divider = "=" * 72
    print(divider)
    print(f"Available runtime tools | benchmark={benchmark_id}")
    print(divider)
    for tool in tools:
        print(f"- {tool}")


if __name__ == "__main__":
    raise SystemExit(main())
