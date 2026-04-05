from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class TrialOutcome(str, Enum):
    OK = "OUTCOME_OK"
    DENIED_SECURITY = "OUTCOME_DENIED_SECURITY"
    NEEDS_CLARIFICATION = "OUTCOME_NONE_CLARIFICATION"
    UNSUPPORTED = "OUTCOME_NONE_UNSUPPORTED"
    ERR_INTERNAL = "OUTCOME_ERR_INTERNAL"


@dataclass(frozen=True)
class TrialSpec:
    benchmark_id: str
    task_id: str


@dataclass(frozen=True)
class TrialHandle:
    trial_id: str
    benchmark_id: str
    harness_url: str
    instruction: str


@dataclass(frozen=True)
class AgentAnswer:
    message: str
    outcome: TrialOutcome
    refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ToolCallTrace:
    tool_name: str
    params: str
    result: str


@dataclass(frozen=True)
class TrialResult:
    trial_id: str
    score: float | None
    score_detail: list[str] = field(default_factory=list)


class BenchmarkPlatform(Protocol):
    def list_task_ids(self, benchmark_id: str) -> list[str]:
        ...

    def list_available_tools(self, benchmark_id: str) -> list[str]:
        ...

    def call_random_tool(self, trial: TrialHandle) -> ToolCallTrace:
        ...

    def start_trial(self, spec: TrialSpec) -> TrialHandle:
        ...

    def submit_answer(self, trial_id: str, answer: AgentAnswer) -> None:
        ...

    def end_trial(self, trial_id: str) -> TrialResult:
        ...


class AgentLoop(Protocol):
    def solve_trial(self, trial: TrialHandle) -> AgentAnswer:
        ...
