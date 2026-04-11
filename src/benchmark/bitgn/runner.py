from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .config import BenchmarkRunConfig
from .contracts import AgentLoop, BenchmarkPlatform, TrialHandle, TrialResult, TrialSpec


@dataclass(frozen=True)
class RunSummary:
    trial_id: str
    benchmark_id: str
    task_id: str
    instruction: str
    submitted: bool
    score: float | None
    score_detail: list[str]
    debug_detail: list[str]


class BenchmarkRunService:
    """Coordinates platform lifecycle and agent loop execution."""

    def __init__(self, platform: BenchmarkPlatform, agent_loop: AgentLoop) -> None:
        self._platform = platform
        self._agent_loop = agent_loop

    def run_once(
        self,
        config: BenchmarkRunConfig,
        on_trial_started: Callable[[TrialHandle], None] | None = None,
    ) -> RunSummary:
        if config.task_id is None:
            raise ValueError("run_once requires a concrete task_id")
        debug_lines = _build_debug_lines(config)
        trial = self._platform.start_trial(
            TrialSpec(benchmark_id=config.benchmark_id, task_id=config.task_id)
        )
        if on_trial_started is not None:
            on_trial_started(trial)
        answer = self._agent_loop.solve_trial(trial)

        if config.allow_submit:
            self._platform.submit_answer(trial.trial_id, answer)
            result = self._platform.end_trial(trial.trial_id)
            return _to_summary(config, trial.instruction, result, submitted=True, debug_detail=debug_lines)

        return RunSummary(
            trial_id=trial.trial_id,
            benchmark_id=config.benchmark_id,
            task_id=config.task_id,
            instruction=trial.instruction,
            submitted=False,
            score=None,
            score_detail=[
                "Submission disabled (--allow-submit not set).",
                f"Agent placeholder outcome: {answer.outcome.value}",
                f"Agent placeholder message: {answer.message}",
            ],
            debug_detail=debug_lines,
        )


def _to_summary(
    config: BenchmarkRunConfig,
    instruction: str,
    result: TrialResult,
    submitted: bool,
    debug_detail: list[str],
) -> RunSummary:
    return RunSummary(
        trial_id=result.trial_id,
        benchmark_id=config.benchmark_id,
        task_id=config.task_id,
        instruction=instruction,
        submitted=submitted,
        score=result.score,
        score_detail=result.score_detail,
        debug_detail=debug_detail,
    )


def _build_debug_lines(config: BenchmarkRunConfig) -> list[str]:
    if not config.debug:
        return []
    return [
        "debug=true",
        f"provider={config.model_provider}",
        f"model={config.model_name}",
        f"model_base_url={config.model_base_url}",
        f"benchmark_host={config.benchmark_host}",
        f"benchmark_id={config.benchmark_id}",
        f"task_id={config.task_id or '<all-tasks>'}",
        f"all_tasks={config.all_tasks}",
        f"agent_mode={config.agent_mode}",
        f"trial_launch_mode={config.trial_launch_mode}",
        "llm_trace=not_implemented_yet",
    ]
