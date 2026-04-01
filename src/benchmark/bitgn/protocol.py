from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, Field


class ReportTaskCompletion(BaseModel):
    tool: Literal["report_completion"]
    completed_steps_laconic: list[str]
    answer: str
    grounding_refs: list[str] = Field(default_factory=list)
    code: Literal["completed", "failed"]


class ReqOutline(BaseModel):
    tool: Literal["outline"]
    path: str = Field(..., description="folder path")


class ReqSearch(BaseModel):
    tool: Literal["search"]
    pattern: str
    count: int = Field(default=5, ge=1, le=10)
    path: str = "/"


class ReqList(BaseModel):
    tool: Literal["list"]
    path: str


class ReqRead(BaseModel):
    tool: Literal["read"]
    path: str


class ReqWrite(BaseModel):
    tool: Literal["write"]
    path: str
    content: str


class ReqDelete(BaseModel):
    tool: Literal["delete"]
    path: str


ToolCommand = Annotated[
    ReportTaskCompletion | ReqOutline | ReqSearch | ReqList | ReqRead | ReqWrite | ReqDelete,
    Field(discriminator="tool"),
]


class AgentStep(BaseModel):
    current_state: str
    plan_remaining_steps_brief: list[str] = Field(min_length=1, max_length=5)
    task_completed: bool
    function: ToolCommand


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
    def execute(self, command: ToolCommand) -> ToolExecution:
        ...


def parse_agent_step(content: str) -> AgentStep:
    candidate = _extract_json_object(content)
    payload = json.loads(candidate)
    _normalize_agent_step_payload(payload)
    return AgentStep.model_validate(payload)


def _normalize_agent_step_payload(payload: dict) -> None:
    plan = payload.get("plan_remaining_steps_brief")
    if not isinstance(plan, list) or not plan:
        tool_name = payload.get("function", {}).get("tool", "unknown")
        current_state = payload.get("current_state")
        fallback = f"Continue with tool '{tool_name}'"
        if isinstance(current_state, str) and current_state.strip():
            fallback = current_state.strip()
        payload["plan_remaining_steps_brief"] = [fallback]


def _extract_json_object(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response did not contain a JSON object")
    return stripped[start : end + 1]
