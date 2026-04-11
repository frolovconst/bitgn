from __future__ import annotations

import argparse
from dataclasses import replace
from math import isclose
from pathlib import Path
import random
import subprocess
from time import perf_counter
from typing import Sequence

from model_clients.factory import create_model_client
from model_clients.types import ModelClientConfig

from .agent_loop import DumbAgentLoop, PlaceholderAgentLoop, RiskidanticAgentLoop
from .config import (
    DEFAULT_AGENT_MODE,
    BenchmarkRunConfig,
    DEFAULT_BITGN_API_KEY_ENV,
    DEFAULT_MODEL_PROVIDER,
    DEFAULT_TRIAL_LAUNCH_MODE,
    default_model_base_url,
    default_model_name,
    env_default_run_name,
    env_default_benchmark_host,
    env_default_benchmark_id,
)
from .platform import BitgnBenchmarkPlatform, TrialLaunchMode
from .runner import BenchmarkRunService

ANSI_RESET = "\033[0m"
ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_GREEN = "\033[32m"
LOCAL_RUN_LOG_PATH = Path(".local/bitgn-runs.log")
RUN_NAME_PREFIX = "columbarium"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bitgn-run",
        description="Launch BitGN benchmark trials in playground or leaderboard run mode.",
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
        choices=["dumb", "placeholder", "riskidantic"],
        default=DEFAULT_AGENT_MODE,
        help="Agent implementation mode. Use dumb for connectivity checks and riskidantic to always deny.",
    )
    parser.add_argument(
        "--trial-launch-mode",
        choices=[TrialLaunchMode.PLAYGROUND.value, TrialLaunchMode.RUN.value],
        default=DEFAULT_TRIAL_LAUNCH_MODE,
        help="Trial launch strategy. `playground` runs ad-hoc trials, `run` creates a leaderboard run.",
    )
    parser.add_argument(
        "--bitgn-api-key-env",
        default=DEFAULT_BITGN_API_KEY_ENV,
        help="Environment variable name with BitGN API key for leaderboard run mode.",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Leaderboard run name used with --trial-launch-mode run. Auto-generated when omitted.",
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
    if args.trial_launch_mode == TrialLaunchMode.RUN.value and not args.allow_submit:
        raise SystemExit("Run mode requires --allow-submit so trials can be ended and submitted.")
    run_name = _resolve_run_name(args.run_name)
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
        bitgn_api_key_env=args.bitgn_api_key_env,
        run_name=run_name,
    )


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_config(argv)
    bitgn_api_key = _resolve_bitgn_api_key(config)
    run_started_at = perf_counter()
    task_results: list[tuple[str, float | None, float]] = []

    try:
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
            run_name=config.run_name,
            run_api_key=bitgn_api_key,
        )
        task_ids = [config.task_id] if config.task_id else platform.list_task_ids(config.benchmark_id)

        if not task_ids:
            print("No tasks returned by benchmark.")
            return 0

        _print_run_header(config, total_tasks=len(task_ids))

        if config.debug:
            _print_available_tools(config.benchmark_id, platform.list_available_tools(config.benchmark_id))

        try:
            for index, task_id in enumerate(task_ids, start=1):
                agent_actions: list[str] = []
                agent_loop = _create_agent_loop(config=config, platform=platform, agent_actions=agent_actions)
                service = BenchmarkRunService(platform=platform, agent_loop=agent_loop)

                task_config = replace(config, task_id=task_id, all_tasks=False)
                started_at = perf_counter()
                summary = service.run_once(task_config)
                elapsed_seconds = perf_counter() - started_at
                task_results.append((summary.task_id, summary.score, elapsed_seconds))
                _print_task_summary(
                    summary,
                    debug=config.debug,
                    index=index,
                    total=len(task_ids),
                    agent_actions=agent_actions,
                )
        finally:
            platform.finalize_run(force=(config.trial_launch_mode == TrialLaunchMode.RUN.value))

        _print_run_summary(task_results)
        return 0
    finally:
        _append_local_run_record(
            run_name=config.run_name or f"{RUN_NAME_PREFIX}-unknown",
            average_score=_compute_average_score(task_results),
            elapsed_seconds=perf_counter() - run_started_at,
            agent_mode=config.agent_mode,
        )


def _create_agent_loop(
    config: BenchmarkRunConfig,
    platform: BitgnBenchmarkPlatform,
    agent_actions: list[str],
):
    action_sink = agent_actions.append
    if config.agent_mode == "dumb":
        return DumbAgentLoop(
            call_random_tool_fn=platform.call_random_tool,
            action_sink=action_sink,
        )
    if config.agent_mode == "riskidantic":
        return RiskidanticAgentLoop(action_sink=action_sink)
    return PlaceholderAgentLoop(action_sink=action_sink)


def _print_task_summary(
    summary,
    debug: bool,
    index: int,
    total: int,
    agent_actions: list[str],
) -> None:
    divider = "=" * 72
    print()
    print(divider)
    print(f"TASK {index}/{total} | {summary.task_id}")
    print(divider)
    instruction_lines = (summary.instruction or "").splitlines() or ["(empty)"]
    task_lines = [
        f"task_id: {summary.task_id}",
        f"trial_id: {summary.trial_id}",
        f"submitted: {summary.submitted}",
        "instruction:",
        *[f"- {line}" for line in instruction_lines],
    ]
    action_lines = [f"- {action}" for action in agent_actions] or ["- (none)"]
    result_lines = [f"score: {_format_score(summary.score)}", "comments:"]
    score_lines = [f"- {line}" for line in summary.score_detail] or ["- (none)"]
    result_lines.extend(score_lines)
    if debug:
        result_lines.append("debug_detail:")
        result_lines.extend([f"- {line}" for line in summary.debug_detail] or ["- (none)"])

    _print_task_section("TASK DETAILS", task_lines)
    _print_task_section("SOLUTION LOG", action_lines)
    _print_task_section("RESULT", result_lines)


def _print_task_section(title: str, lines: list[str]) -> None:
    divider = "-" * 72
    print(title)
    print(divider)
    for line in lines:
        print(line)
    print(divider)


def _print_available_tools(benchmark_id: str, tools: list[str]) -> None:
    divider = "=" * 72
    print()
    print(divider)
    print(f"Available runtime tools | benchmark={benchmark_id}")
    print(divider)
    for tool in tools:
        print(f"- {tool}")


def _print_run_header(config: BenchmarkRunConfig, total_tasks: int) -> None:
    divider = "=" * 72
    print(divider)
    print("RUN INFO")
    print(divider)
    print(f"benchmark_host: {config.benchmark_host}")
    print(f"benchmark_id: {config.benchmark_id}")
    print(f"task_scope: {'all' if config.all_tasks else config.task_id}")
    print(f"total_tasks: {total_tasks}")
    print(f"allow_submit: {config.allow_submit}")
    print(f"agent_mode: {config.agent_mode}")
    print(f"trial_launch_mode: {config.trial_launch_mode}")
    if config.trial_launch_mode == TrialLaunchMode.RUN.value:
        print(f"run_name: {config.run_name}")
        print(f"bitgn_api_key_env: {config.bitgn_api_key_env}")
    print(f"model_provider: {config.model_provider}")
    print(f"model_name: {config.model_name}")
    print(f"model_base_url: {config.model_base_url}")
    print("=" * 72)


def _format_score(score: float | None) -> str:
    if score is None:
        return "None"

    score_text = str(score)
    if isclose(score, 0.0, abs_tol=1e-9):
        return f"{ANSI_RED}{score_text}{ANSI_RESET}"
    if 0.0 < score < 1.0:
        return f"{ANSI_YELLOW}{score_text}{ANSI_RESET}"
    if isclose(score, 1.0, abs_tol=1e-9):
        return f"{ANSI_GREEN}{score_text}{ANSI_RESET}"
    return score_text


def _resolve_bitgn_api_key(config: BenchmarkRunConfig) -> str | None:
    if config.trial_launch_mode != TrialLaunchMode.RUN.value:
        return None

    import os

    key = os.getenv(config.bitgn_api_key_env, "").strip()
    if not key:
        raise SystemExit(
            f"Run mode requires a BitGN API key in env var {config.bitgn_api_key_env!r}."
        )
    return key


def _compute_average_score(task_results: list[tuple[str, float | None, float]]) -> float | None:
    scored_values = [score for _, score, _ in task_results if score is not None]
    if not scored_values:
        return None
    return sum(scored_values) / len(scored_values)


def _print_run_summary(task_results: list[tuple[str, float | None, float]]) -> None:
    divider = "=" * 72
    print()
    print(divider)
    print("RUN SUMMARY")
    print(divider)
    average_score = _compute_average_score(task_results)
    print(f"average_score: {_format_score(average_score)}")
    print()
    print("task_id | score | time_seconds")
    print("-" * 72)
    for task_id, score, elapsed_seconds in task_results:
        print(f"{task_id} | {_format_score(score)} | {elapsed_seconds:.3f}")


def _resolve_run_name(cli_run_name: str | None) -> str:
    if cli_run_name is not None:
        run_name = cli_run_name.strip()
        if run_name:
            return run_name

    env_run_name = env_default_run_name()
    if env_run_name:
        return env_run_name
    return _generate_default_run_name()


def _generate_default_run_name() -> str:
    # Docker-style pattern: short adjective + surname-like token.
    adjectives = (
        "agile",
        "calm",
        "dandy",
        "eager",
        "keen",
        "lucky",
        "merry",
        "noble",
        "proud",
        "swift",
    )
    names = (
        "bohr",
        "curie",
        "fermi",
        "lovel",
        "raman",
        "turing",
        "wu",
    )
    rng = random.SystemRandom()
    clause = f"{rng.choice(adjectives)}-{rng.choice(names)}"
    return f"{RUN_NAME_PREFIX}-{clause}"


def _append_local_run_record(
    run_name: str,
    average_score: float | None,
    elapsed_seconds: float,
    agent_mode: str,
) -> None:
    LOCAL_RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    average_score_text = "None" if average_score is None else f"{average_score:.6f}"
    commit_sha = _resolve_commit_sha()
    with LOCAL_RUN_LOG_PATH.open("a", encoding="utf-8") as run_log:
        run_log.write(
            "\t".join(
                [
                    f"run_name={run_name}",
                    f"average_score={average_score_text}",
                    f"commit_sha={commit_sha}",
                    f"time_seconds={elapsed_seconds:.3f}",
                    f"agent_mode={agent_mode}",
                ]
            )
        )
        run_log.write("\n")


def _resolve_commit_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        sha = result.stdout.strip()
        return sha or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
