from __future__ import annotations

from dataclasses import dataclass

from .config import BenchmarkRunConfig
from .contracts import AgentLoop, BenchmarkPlatform, TrialResult, TrialSpec


@dataclass(frozen=True)
class RunSummary:
    trial_id: str
    benchmark_id: str
    task_id: str
    submitted: bool
    score: float | None
    score_detail: list[str]


class BenchmarkRunService:
    """Coordinates platform lifecycle and agent loop execution."""

    def __init__(self, platform: BenchmarkPlatform, agent_loop: AgentLoop) -> None:
        self._platform = platform
        self._agent_loop = agent_loop

    def run_once(self, config: BenchmarkRunConfig) -> RunSummary:
        trial = self._platform.start_trial(
            TrialSpec(benchmark_id=config.benchmark_id, task_id=config.task_id)
        )
        answer = self._agent_loop.solve_trial(trial)

        if config.allow_submit:
            self._platform.submit_answer(trial.trial_id, answer)
            result = self._platform.end_trial(trial.trial_id)
            return _to_summary(config, result, submitted=True)

        return RunSummary(
            trial_id=trial.trial_id,
            benchmark_id=config.benchmark_id,
            task_id=config.task_id,
            submitted=False,
            score=None,
            score_detail=[
                "Submission disabled (--allow-submit not set).",
                f"Agent placeholder outcome: {answer.outcome.value}",
                f"Agent placeholder message: {answer.message}",
            ],
        )


def _to_summary(config: BenchmarkRunConfig, result: TrialResult, submitted: bool) -> RunSummary:
    return RunSummary(
        trial_id=result.trial_id,
        benchmark_id=config.benchmark_id,
        task_id=config.task_id,
        submitted=submitted,
        score=result.score,
        score_detail=result.score_detail,
    )
