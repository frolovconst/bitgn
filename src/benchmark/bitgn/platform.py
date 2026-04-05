from __future__ import annotations

from .contracts import AgentAnswer, BenchmarkPlatform, TrialHandle, TrialResult, TrialSpec


class PlaceholderBenchmarkPlatform(BenchmarkPlatform):
    """Mock benchmark platform for plumbing and integration testing.

    Replace this class with the real BitGN API adapter while preserving the
    BenchmarkPlatform interface.
    """

    def __init__(self, benchmark_host: str) -> None:
        self._benchmark_host = benchmark_host

    def start_trial(self, spec: TrialSpec) -> TrialHandle:
        trial_id = f"placeholder:{spec.benchmark_id}:{spec.task_id}"
        return TrialHandle(
            trial_id=trial_id,
            harness_url=f"{self._benchmark_host}/mock-harness",
            instruction=(
                "Placeholder trial. No real benchmark call has been made yet. "
                "Implement BitGN API adapter next."
            ),
        )

    def submit_answer(self, trial_id: str, answer: AgentAnswer) -> None:
        _ = trial_id, answer

    def end_trial(self, trial_id: str) -> TrialResult:
        return TrialResult(
            trial_id=trial_id,
            score=None,
            score_detail=["Placeholder mode: no evaluation requested."],
        )
