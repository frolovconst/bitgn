from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ToolExecution:
    content: str
    completed: bool = False
    completion_code: str | None = None
    answer: str | None = None
    grounding_refs: tuple[str, ...] = ()
    completed_steps_laconic: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskRunSummary:
    answer: str
    code: str
    grounding_refs: tuple[str, ...] = ()
    completed_steps_laconic: tuple[str, ...] = ()
    steps_taken: int = 0


class RuntimeExecutor(Protocol):
    def execute(self, command: object) -> ToolExecution:
        ...
