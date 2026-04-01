from __future__ import annotations

import textwrap

from bitgn.harness_connect import HarnessServiceClientSync
from bitgn.harness_pb2 import (
    EndTrialRequest,
    EvalPolicy,
    GetBenchmarkRequest,
    StartPlaygroundRequest,
    StatusRequest,
)
from connectrpc.errors import ConnectError

from model_clients.factory import create_model_client

from .agent_loop import run_task_loop
from .config import BitgnRunConfig
from .runtime import BitgnMiniRuntimeExecutor

CLI_RED = "\x1B[31m"
CLI_GREEN = "\x1B[32m"
CLI_BLUE = "\x1B[34m"
CLI_CLR = "\x1B[0m"


def run_benchmark(config: BitgnRunConfig) -> int:
    model_client = create_model_client(config.model)
    scores: list[tuple[str, float]] = []
    exit_code = 0

    try:
        client = HarnessServiceClientSync(config.benchmark_host)
        print("Connecting to BitGN", client.status(StatusRequest()))
        benchmark = client.get_benchmark(GetBenchmarkRequest(benchmark_id=config.benchmark_id))
        print(
            f"{EvalPolicy.Name(benchmark.policy)} benchmark: {benchmark.benchmark_id} "
            f"with {len(benchmark.tasks)} tasks.\n{CLI_GREEN}{benchmark.description}{CLI_CLR}"
        )

        for task in benchmark.tasks:
            if config.task_ids and task.task_id not in config.task_ids:
                continue

            print("=" * 40)
            print(f"Starting Task: {task.task_id}")
            trial = client.start_playground(
                StartPlaygroundRequest(
                    benchmark_id=config.benchmark_id,
                    task_id=task.task_id,
                )
            )
            print("Task:", trial.instruction)

            try:
                summary = run_task_loop(
                    model_client=model_client,
                    runtime=BitgnMiniRuntimeExecutor(trial.harness_url),
                    task_text=trial.instruction,
                    settings=config.generation,
                    max_steps=config.max_steps,
                )

                print(f"{CLI_BLUE}AGENT ANSWER: {summary.answer}{CLI_CLR}")
                for ref in summary.grounding_refs:
                    print(f"- {CLI_BLUE}{ref}{CLI_CLR}")
            except Exception as exc:
                exit_code = 1
                print(f"{CLI_RED}Agent task failed: {exc}{CLI_CLR}")

            result = client.end_trial(EndTrialRequest(trial_id=trial.trial_id))
            if result.score >= 0:
                scores.append((task.task_id, result.score))
                style = CLI_GREEN if result.score == 1 else CLI_RED
                explain = textwrap.indent("\n".join(result.score_detail), "  ")
                print(f"\n{style}Score: {result.score:0.2f}\n{explain}\n{CLI_CLR}")

    except ConnectError as exc:
        print(f"{exc.code}: {exc.message}")
        return 1
    except KeyboardInterrupt:
        print(f"{CLI_RED}Interrupted{CLI_CLR}")
        return 130

    if scores:
        for task_id, score in scores:
            style = CLI_GREEN if score == 1 else CLI_RED
            print(f"{task_id}: {style}{score:0.2f}{CLI_CLR}")

        total = sum(score for _, score in scores) / len(scores) * 100.0
        print(f"FINAL: {total:0.2f}%")

    return exit_code
