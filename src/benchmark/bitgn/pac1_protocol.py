from __future__ import annotations

import json
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ReportTaskCompletion(BaseModel):
    tool: Literal["report_completion"]
    completed_steps_laconic: list[str]
    message: str
    grounding_refs: list[str] = Field(default_factory=list)
    outcome: Literal[
        "OUTCOME_OK",
        "OUTCOME_DENIED_SECURITY",
        "OUTCOME_NONE_CLARIFICATION",
        "OUTCOME_NONE_UNSUPPORTED",
        "OUTCOME_ERR_INTERNAL",
    ]


class ReqContext(BaseModel):
    tool: Literal["context"]


class ReqTree(BaseModel):
    tool: Literal["tree"]
    level: int = Field(default=2, ge=0)
    root: str = "/"


class ReqFind(BaseModel):
    tool: Literal["find"]
    name: str
    root: str = "/"
    kind: Literal["all", "files", "dirs"] = "all"
    limit: int = Field(default=10, ge=1, le=20)


class ReqSearch(BaseModel):
    tool: Literal["search"]
    pattern: str
    limit: int = Field(default=10, ge=1, le=20)
    root: str = "/"


class ReqList(BaseModel):
    tool: Literal["list"]
    path: str = "/"


class ReqRead(BaseModel):
    tool: Literal["read"]
    path: str
    number: bool = False
    start_line: int = Field(default=0, ge=0)
    end_line: int = Field(default=0, ge=0)


class ReqWrite(BaseModel):
    tool: Literal["write"]
    path: str
    content: str
    start_line: int = Field(default=0, ge=0)
    end_line: int = Field(default=0, ge=0)


class ReqDelete(BaseModel):
    tool: Literal["delete"]
    path: str


class ReqMkDir(BaseModel):
    tool: Literal["mkdir"]
    path: str


class ReqMove(BaseModel):
    tool: Literal["move"]
    from_name: str
    to_name: str


Pac1ToolCommand = Annotated[
    ReportTaskCompletion
    | ReqContext
    | ReqTree
    | ReqFind
    | ReqSearch
    | ReqList
    | ReqRead
    | ReqWrite
    | ReqDelete
    | ReqMkDir
    | ReqMove,
    Field(discriminator="tool"),
]


class Pac1AgentStep(BaseModel):
    current_state: str
    plan_remaining_steps_brief: list[str] = Field(min_length=1, max_length=5)
    task_completed: bool
    function: Pac1ToolCommand


def parse_pac1_agent_step(content: str) -> Pac1AgentStep:
    candidate = _extract_json_object(content)
    payload = json.loads(candidate)
    _normalize_agent_step_payload(payload)
    return Pac1AgentStep.model_validate(payload)


def _normalize_agent_step_payload(payload: dict) -> None:
    current_state = payload.get("current_state")
    if not isinstance(current_state, str) or not current_state.strip():
        payload["current_state"] = "Continue with the next best PAC1 tool action."

    _promote_top_level_tool_payload(payload)

    function_payload = payload.get("function")
    if not isinstance(function_payload, dict):
        payload["function"] = {
            "tool": "report_completion",
            "completed_steps_laconic": ["Could not parse a concrete tool call from the model output."],
            "message": "Model response omitted the PAC1 function payload.",
            "grounding_refs": [],
            "outcome": "OUTCOME_ERR_INTERNAL",
        }
        function_payload = payload["function"]

    _normalize_function_payload(function_payload)

    task_completed = payload.get("task_completed")
    if not isinstance(task_completed, bool):
        payload["task_completed"] = function_payload.get("tool") == "report_completion"

    plan = payload.get("plan_remaining_steps_brief")
    if not isinstance(plan, list) or not plan:
        tool_name = function_payload.get("tool", "unknown")
        fallback = f"Continue with tool '{tool_name}'"
        if isinstance(payload["current_state"], str) and payload["current_state"].strip():
            fallback = payload["current_state"].strip()
        payload["plan_remaining_steps_brief"] = [fallback]


def _normalize_function_payload(function_payload: dict) -> None:
    tool = function_payload.get("tool")
    if not isinstance(tool, str):
        function_payload["tool"] = "report_completion"
        tool = "report_completion"

    if "file" in function_payload and "path" not in function_payload:
        function_payload["path"] = function_payload.pop("file")

    if tool == "report_completion":
        completed_steps = function_payload.get("completed_steps_laconic")
        if not isinstance(completed_steps, list) or not completed_steps:
            message = function_payload.get("message")
            answer = function_payload.get("answer")
            fallback_step = "Report the final task status."
            if isinstance(message, str) and message.strip():
                fallback_step = message.strip()
            elif isinstance(answer, str) and answer.strip():
                fallback_step = answer.strip()
            function_payload["completed_steps_laconic"] = [fallback_step]

        message = function_payload.get("message")
        if not isinstance(message, str) or not message.strip():
            answer = function_payload.get("answer")
            if isinstance(answer, str) and answer.strip():
                function_payload["message"] = answer.strip()
            else:
                function_payload["message"] = "Task completed without a detailed message."

        refs = function_payload.get("grounding_refs")
        if not isinstance(refs, list):
            function_payload["grounding_refs"] = []

        outcome = function_payload.get("outcome")
        if not isinstance(outcome, str) or not outcome.strip():
            function_payload["outcome"] = "OUTCOME_OK"
        return

    if tool in {"read", "list", "delete", "mkdir"}:
        path = function_payload.get("path")
        if not isinstance(path, str) or not path.strip():
            function_payload["path"] = "/"
        return

    if tool == "write":
        path = function_payload.get("path")
        if not isinstance(path, str) or not path.strip():
            function_payload["path"] = "/tmp/pac1_write.txt"
        content = function_payload.get("content")
        if not isinstance(content, str):
            function_payload["content"] = ""
        return

    if tool == "move":
        from_name = function_payload.get("from_name")
        if not isinstance(from_name, str) or not from_name.strip():
            function_payload["from_name"] = "/"
        to_name = function_payload.get("to_name")
        if not isinstance(to_name, str) or not to_name.strip():
            function_payload["to_name"] = "/"
        return

    if tool == "find":
        name = function_payload.get("name")
        if not isinstance(name, str) or not name.strip():
            function_payload["name"] = "*"
        root = function_payload.get("root")
        if not isinstance(root, str) or not root.strip():
            function_payload["root"] = "/"
        return

    if tool == "search":
        pattern = function_payload.get("pattern")
        if not isinstance(pattern, str) or not pattern.strip():
            function_payload["pattern"] = "."
        root = function_payload.get("root")
        if not isinstance(root, str) or not root.strip():
            function_payload["root"] = "/"


def _promote_top_level_tool_payload(payload: dict) -> None:
    function_payload = payload.get("function")
    if isinstance(function_payload, dict):
        return

    promoted = _extract_embedded_tool_payload(payload)
    if promoted is None:
        return

    reserved_keys = {"current_state", "plan_remaining_steps_brief", "task_completed", "function"}
    for key, value in list(payload.items()):
        if key in reserved_keys or key == "tool":
            continue
        if key in {"action", "tool_call", "function_call", "call"} and isinstance(value, dict):
            continue
        promoted[key] = value
        payload.pop(key)
    payload["function"] = promoted


def _extract_embedded_tool_payload(payload: dict) -> dict | None:
    tool = payload.get("tool")
    if isinstance(tool, str) and tool.strip():
        return {"tool": tool}

    for candidate_key in ("action", "tool_call", "function_call", "call"):
        candidate = payload.get(candidate_key)
        if isinstance(candidate, dict):
            nested_tool = candidate.get("tool") or candidate.get("name")
            if isinstance(nested_tool, str) and nested_tool.strip():
                promoted = dict(candidate)
                if "tool" not in promoted:
                    promoted["tool"] = nested_tool
                return promoted
    return None


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
