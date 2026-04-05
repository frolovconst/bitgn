from __future__ import annotations

import json
import random
import time
from typing import Any, Callable

from model_clients.base import ModelClient
from model_clients.types import Message, ModelSettings, ToolDefinition

from .platform import BENCHMARK_RUNTIME_SURFACE_BY_ID, RuntimeSurface
from .contracts import AgentAnswer, ToolCallTrace, TrialHandle, TrialOutcome

_REPORT_COMPLETION_TOOL = ToolDefinition(
    name="report_completion",
    description="Use when the task is finished or blocked to return the final benchmark answer.",
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "outcome": {
                "type": "string",
                "enum": [
                    TrialOutcome.OK.value,
                    TrialOutcome.DENIED_SECURITY.value,
                    TrialOutcome.NEEDS_CLARIFICATION.value,
                    TrialOutcome.UNSUPPORTED.value,
                    TrialOutcome.ERR_INTERNAL.value,
                ],
            },
            "refs": {"type": "array", "items": {"type": "string"}},
            "completed_steps_laconic": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["message", "outcome", "refs"],
        "additionalProperties": False,
    },
)

_TOOL_SCHEMAS: dict[str, ToolDefinition] = {
    "Context": ToolDefinition(
        name="Context",
        description="Get runtime context metadata for the current trial workspace.",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
    ),
    "Tree": ToolDefinition(
        name="Tree",
        description="List files and directories recursively from a root path.",
        parameters={
            "type": "object",
            "properties": {
                "root": {"type": "string"},
                "level": {"type": "integer", "minimum": 0},
            },
            "additionalProperties": False,
        },
    ),
    "Find": ToolDefinition(
        name="Find",
        description="Find files/directories by name under a root.",
        parameters={
            "type": "object",
            "properties": {
                "root": {"type": "string"},
                "name": {"type": "string"},
                "kind": {"type": "string", "enum": ["all", "files", "dirs"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    ),
    "Search": ToolDefinition(
        name="Search",
        description="Search file content by regex pattern under a root/path.",
        parameters={
            "type": "object",
            "properties": {
                "root": {"type": "string"},
                "path": {"type": "string"},
                "pattern": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "count": {"type": "integer", "minimum": 1, "maximum": 200},
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
    ),
    "List": ToolDefinition(
        name="List",
        description="List direct children in a directory.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "name": {"type": "string"},
            },
            "additionalProperties": False,
        },
    ),
    "Read": ToolDefinition(
        name="Read",
        description="Read file content, optionally using line ranges.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "number": {"type": "boolean"},
                "start_line": {"type": "integer", "minimum": 0},
                "end_line": {"type": "integer", "minimum": 0},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    "Write": ToolDefinition(
        name="Write",
        description="Write content to a file (full overwrite or line range).",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "start_line": {"type": "integer", "minimum": 0},
                "end_line": {"type": "integer", "minimum": 0},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    ),
    "Delete": ToolDefinition(
        name="Delete",
        description="Delete a file or directory path.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    "MkDir": ToolDefinition(
        name="MkDir",
        description="Create a directory path.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    "Move": ToolDefinition(
        name="Move",
        description="Move or rename a file/directory.",
        parameters={
            "type": "object",
            "properties": {
                "from_name": {"type": "string"},
                "to_name": {"type": "string"},
            },
            "required": ["from_name", "to_name"],
            "additionalProperties": False,
        },
    ),
    "Outline": ToolDefinition(
        name="Outline",
        description="Return the mini-runtime outline for a path.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "additionalProperties": False,
        },
    ),
}

_SYSTEM_PROMPT = (
    "You are a pragmatic benchmark task-solving assistant.\n"
    "Use runtime tools to inspect/edit files and keep changes minimal.\n"
    "Call exactly one tool each step.\n"
    "When done or blocked, call report_completion.\n"
    "In report_completion always include:\n"
    "- message: concise final answer\n"
    "- outcome: one of the provided outcome enums\n"
    "- refs: array of exact file paths (case-sensitive) that grounded the answer; use [] only if no file grounded it."
)


class PlaceholderAgentLoop:
    """Temporary agent-loop stub.

    This class is intentionally simple so a real iterative tool-using loop can be
    introduced later without changing CLI/platform wiring.
    """

    def __init__(self, action_sink: Callable[[str], None] | None = None) -> None:
        self._action_sink = action_sink

    def _emit(self, action: str) -> None:
        if self._action_sink is not None:
            self._action_sink(action)

    def solve_trial(self, trial: TrialHandle) -> AgentAnswer:
        self._emit(f"solve_trial:start trial_id={trial.trial_id}")
        self._emit("decision:placeholder_outcome=OUTCOME_NONE_UNSUPPORTED")
        return AgentAnswer(
            message=(
                "Placeholder agent loop: benchmark connection is wired, "
                "but task-solving logic is not implemented yet."
            ),
            outcome=TrialOutcome.UNSUPPORTED,
            refs=[],
        )


class DumbAgentLoop:
    """Minimal submission-only agent used for end-to-end platform connectivity checks.

    It does not perform any runtime tool actions and always returns a terminal
    "done" answer.
    """

    def __init__(
        self,
        sleep_fn: Callable[[float], None] = time.sleep,
        uniform_fn: Callable[[float, float], float] = random.uniform,
        call_random_tool_fn: Callable[[TrialHandle], ToolCallTrace] | None = None,
        action_sink: Callable[[str], None] | None = None,
    ) -> None:
        self._sleep = sleep_fn
        self._uniform = uniform_fn
        self._call_random_tool = call_random_tool_fn
        self._action_sink = action_sink

    def _emit(self, action: str) -> None:
        if self._action_sink is not None:
            self._action_sink(action)

    def solve_trial(self, trial: TrialHandle) -> AgentAnswer:
        self._emit(f"solve_trial:start trial_id={trial.trial_id}")
        if self._call_random_tool is not None:
            trace = self._call_random_tool(trial)
            self._emit(f"runtime_tool_call:{trace.tool_name}")
            self._emit(f"runtime_tool_params:{trace.params}")
            self._emit(f"runtime_tool_result:{trace.result}")
        # Mimic lightweight "thinking time" to make the run behavior look realistic.
        sleep_seconds = self._uniform(1.0, 3.0)
        self._emit(f"thinking_delay_seconds:{sleep_seconds:.3f}")
        self._sleep(sleep_seconds)
        self._emit("decision:submit_done_outcome=OUTCOME_OK")
        return AgentAnswer(
            message="Done",
            outcome=TrialOutcome.OK,
            refs=[],
        )


class LlmToolAgentLoop:
    """Iterative tool-using agent loop backed by ModelClient tool-calling."""

    def __init__(
        self,
        model_client: ModelClient,
        available_tools: list[str],
        settings: ModelSettings | None = None,
        max_steps: int = 30,
        action_sink: Callable[[str], None] | None = None,
        call_tool_fn: Callable[[TrialHandle, str, dict[str, Any]], ToolCallTrace] | None = None,
    ) -> None:
        self._model_client = model_client
        self._available_tools = [tool for tool in available_tools if tool != "Answer"]
        self._settings = settings or ModelSettings()
        self._max_steps = max_steps
        self._action_sink = action_sink
        self._call_tool = call_tool_fn or _call_runtime_tool

    def _emit(self, action: str) -> None:
        if self._action_sink is not None:
            self._action_sink(action)

    def solve_trial(self, trial: TrialHandle) -> AgentAnswer:
        self._emit(f"solve_trial:start trial_id={trial.trial_id}")
        tools = _build_tool_list(self._available_tools)
        messages: list[Message] = [Message(role="system", content=_SYSTEM_PROMPT)]

        for bootstrap_name, bootstrap_args in _bootstrap_calls(self._available_tools):
            trace = self._safe_call_tool(trial, bootstrap_name, bootstrap_args)
            if trace is None:
                return AgentAnswer(
                    message=f"Failed to run bootstrap tool {bootstrap_name}.",
                    outcome=TrialOutcome.ERR_INTERNAL,
                    refs=[],
                )
            messages.append(Message(role="user", content=_format_tool_observation(trace)))

        messages.append(
            Message(
                role="user",
                content=(
                    "Task instruction follows. Solve it by using runtime tools.\n"
                    f"{trial.instruction}"
                ),
            )
        )

        for step in range(1, self._max_steps + 1):
            response = self._model_client.generate(messages=messages, settings=self._settings, tools=tools)
            content = response.content.strip()
            if content:
                messages.append(Message(role="assistant", content=content))
            self._emit(f"llm_step:{step}:finish_reason={response.finish_reason or 'unknown'}")
            self._emit(f"llm_step:{step}:output={_truncate_for_log(content or '<empty>')}")

            call = _extract_tool_call(response.raw, content)
            if call is None:
                correction = (
                    "No tool call detected. Call one tool from the provided list, "
                    "or call report_completion."
                )
                messages.append(Message(role="user", content=correction))
                self._emit(f"llm_step:{step}:missing_tool_call")
                continue

            tool_name, arguments = call
            self._emit(f"llm_step:{step}:tool_call={tool_name}")
            if tool_name == _REPORT_COMPLETION_TOOL.name:
                if not isinstance(arguments.get("refs"), list):
                    messages.append(
                        Message(
                            role="user",
                            content=(
                                "Invalid report_completion: `refs` must be present and must be an array "
                                "of exact case-sensitive file paths (or [] when none). "
                                "Call report_completion again."
                            ),
                        )
                    )
                    self._emit(f"llm_step:{step}:invalid_report_completion_missing_refs")
                    continue
                return _to_agent_answer(arguments)

            if tool_name not in self._available_tools:
                self._emit(f"llm_step:{step}:unsupported_tool={tool_name}")
                return AgentAnswer(
                    message=f"Model requested unsupported tool: {tool_name}",
                    outcome=TrialOutcome.ERR_INTERNAL,
                    refs=[],
                )

            trace = self._safe_call_tool(trial, tool_name, arguments)
            if trace is None:
                return AgentAnswer(
                    message=f"Runtime tool call failed: {tool_name}",
                    outcome=TrialOutcome.ERR_INTERNAL,
                    refs=[],
                )
            messages.append(Message(role="user", content=_format_tool_observation(trace)))

        return AgentAnswer(
            message=f"Reached step limit ({self._max_steps}) before completion.",
            outcome=TrialOutcome.UNSUPPORTED,
            refs=[],
        )

    def _safe_call_tool(
        self,
        trial: TrialHandle,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolCallTrace | None:
        try:
            trace = self._call_tool(trial, tool_name, arguments)
            self._emit(f"runtime_tool_call:{trace.tool_name}")
            self._emit(f"runtime_tool_params:{trace.params}")
            self._emit(f"runtime_tool_result:{trace.result}")
            return trace
        except Exception as exc:
            self._emit(f"runtime_tool_error:{tool_name}:{exc}")
            return None


def _build_tool_list(available_tools: list[str]) -> list[ToolDefinition]:
    result: list[ToolDefinition] = []
    for tool_name in available_tools:
        schema = _TOOL_SCHEMAS.get(tool_name)
        if schema is not None:
            result.append(schema)
    result.append(_REPORT_COMPLETION_TOOL)
    return result


def _bootstrap_calls(available_tools: list[str]) -> list[tuple[str, dict[str, Any]]]:
    result: list[tuple[str, dict[str, Any]]] = []
    for name, args in (
        ("Tree", {"root": "/", "level": 2}),
        ("Read", {"path": "AGENTS.md"}),
        ("Context", {}),
        ("Outline", {"path": "/"}),
        ("List", {"path": "/"}),
    ):
        if name in available_tools:
            result.append((name, args))
    return result


def _extract_tool_call(raw: dict[str, Any], content: str) -> tuple[str, dict[str, Any]] | None:
    call = _extract_tool_call_from_raw(raw)
    if call is not None:
        return call
    if not content:
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if "function" in payload and isinstance(payload["function"], dict):
        function_payload = payload["function"]
        return _normalize_call(function_payload.get("name"), function_payload.get("arguments"))
    return _normalize_call(payload.get("name"), payload.get("arguments"))


def _extract_tool_call_from_raw(raw: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    candidates = []
    choice_message = (((raw.get("choices") or [{}])[0]).get("message") or {})
    if isinstance(choice_message, dict):
        candidates.extend(choice_message.get("tool_calls") or [])
    root_message = raw.get("message") or {}
    if isinstance(root_message, dict):
        candidates.extend(root_message.get("tool_calls") or [])

    for item in candidates:
        function_payload = item.get("function") if isinstance(item, dict) else None
        if isinstance(function_payload, dict):
            normalized = _normalize_call(function_payload.get("name"), function_payload.get("arguments"))
            if normalized is not None:
                return normalized
    return None


def _normalize_call(name: Any, arguments: Any) -> tuple[str, dict[str, Any]] | None:
    if not isinstance(name, str) or not name:
        return None
    if arguments is None:
        return name, {}
    if isinstance(arguments, dict):
        return name, arguments
    if isinstance(arguments, str):
        try:
            decoded = json.loads(arguments)
        except json.JSONDecodeError:
            return None
        if isinstance(decoded, dict):
            return name, decoded
    return None


def _to_agent_answer(arguments: dict[str, Any]) -> AgentAnswer:
    message = str(arguments.get("message", "Completed"))
    refs = arguments.get("refs", [])
    if not isinstance(refs, list):
        refs = []
    outcome_raw = str(arguments.get("outcome", TrialOutcome.OK.value))
    try:
        outcome = TrialOutcome(outcome_raw)
    except ValueError:
        outcome = TrialOutcome.ERR_INTERNAL
        message = f"Invalid completion outcome from model: {outcome_raw}"
        refs = []
    return AgentAnswer(message=message, outcome=outcome, refs=[str(ref) for ref in refs])


def _format_tool_observation(trace: ToolCallTrace) -> str:
    return (
        f"Tool {trace.tool_name} executed.\n"
        f"params={trace.params}\n"
        f"result={trace.result}"
    )


def _call_runtime_tool(trial: TrialHandle, tool_name: str, arguments: dict[str, Any]) -> ToolCallTrace:
    runtime_surface = BENCHMARK_RUNTIME_SURFACE_BY_ID.get(trial.benchmark_id, RuntimeSurface.PCM)
    if runtime_surface == RuntimeSurface.MINI:
        return _call_runtime_tool_mini(trial.harness_url, tool_name, arguments)
    return _call_runtime_tool_pcm(trial.harness_url, tool_name, arguments)


def _call_runtime_tool_pcm(harness_url: str, tool_name: str, arguments: dict[str, Any]) -> ToolCallTrace:
    from bitgn.vm.pcm_connect import PcmRuntimeClientSync
    from bitgn.vm.pcm_pb2 import (
        ContextRequest,
        DeleteRequest,
        FindRequest,
        ListRequest,
        MkDirRequest,
        MoveRequest,
        ReadRequest,
        SearchRequest,
        TreeRequest,
        WriteRequest,
    )

    runtime = PcmRuntimeClientSync(harness_url)
    if tool_name == "Context":
        response = runtime.context(ContextRequest())
    elif tool_name == "Tree":
        response = runtime.tree(
            TreeRequest(
                root=str(arguments.get("root", "/")),
                level=int(arguments.get("level", 2)),
            )
        )
    elif tool_name == "Find":
        kind = str(arguments.get("kind", "all"))
        type_by_kind = {"all": 0, "files": 1, "dirs": 2}
        response = runtime.find(
            FindRequest(
                root=str(arguments.get("root", "/")),
                name=str(arguments.get("name", "")),
                type=type_by_kind.get(kind, 0),
                limit=int(arguments.get("limit", 10)),
            )
        )
    elif tool_name == "Search":
        response = runtime.search(
            SearchRequest(
                root=str(arguments.get("root", "/")),
                pattern=str(arguments.get("pattern", "")),
                limit=int(arguments.get("limit", 10)),
            )
        )
    elif tool_name == "List":
        path = str(arguments.get("path", arguments.get("name", "/")))
        response = runtime.list(ListRequest(name=path))
    elif tool_name == "Read":
        response = runtime.read(
            ReadRequest(
                path=str(arguments.get("path", "")),
                number=bool(arguments.get("number", False)),
                start_line=int(arguments.get("start_line", 0)),
                end_line=int(arguments.get("end_line", 0)),
            )
        )
    elif tool_name == "Write":
        response = runtime.write(
            WriteRequest(
                path=str(arguments.get("path", "")),
                content=str(arguments.get("content", "")),
                start_line=int(arguments.get("start_line", 0)),
                end_line=int(arguments.get("end_line", 0)),
            )
        )
    elif tool_name == "Delete":
        response = runtime.delete(DeleteRequest(path=str(arguments.get("path", ""))))
    elif tool_name == "MkDir":
        response = runtime.mk_dir(MkDirRequest(path=str(arguments.get("path", ""))))
    elif tool_name == "Move":
        response = runtime.move(
            MoveRequest(
                from_name=str(arguments.get("from_name", "")),
                to_name=str(arguments.get("to_name", "")),
            )
        )
    else:
        raise ValueError(f"Unsupported PCM tool: {tool_name}")

    return ToolCallTrace(
        tool_name=tool_name,
        params=json.dumps(arguments, ensure_ascii=True, sort_keys=True),
        result=_format_response_payload(response),
    )


def _call_runtime_tool_mini(harness_url: str, tool_name: str, arguments: dict[str, Any]) -> ToolCallTrace:
    from bitgn.vm.mini_connect import MiniRuntimeClientSync
    from bitgn.vm.mini_pb2 import DeleteRequest, ListRequest, OutlineRequest, ReadRequest, SearchRequest, WriteRequest

    runtime = MiniRuntimeClientSync(harness_url)
    if tool_name == "Outline":
        response = runtime.outline(OutlineRequest(path=str(arguments.get("path", "/"))))
    elif tool_name == "List":
        response = runtime.list(ListRequest(path=str(arguments.get("path", "/"))))
    elif tool_name == "Search":
        response = runtime.search(
            SearchRequest(
                path=str(arguments.get("path", "/")),
                pattern=str(arguments.get("pattern", "")),
                count=int(arguments.get("count", arguments.get("limit", 10))),
            )
        )
    elif tool_name == "Read":
        response = runtime.read(ReadRequest(path=str(arguments.get("path", ""))))
    elif tool_name == "Write":
        response = runtime.write(
            WriteRequest(
                path=str(arguments.get("path", "")),
                content=str(arguments.get("content", "")),
            )
        )
    elif tool_name == "Delete":
        response = runtime.delete(DeleteRequest(path=str(arguments.get("path", ""))))
    else:
        raise ValueError(f"Unsupported MINI tool: {tool_name}")

    return ToolCallTrace(
        tool_name=tool_name,
        params=json.dumps(arguments, ensure_ascii=True, sort_keys=True),
        result=_format_response_payload(response),
    )


def _format_response_payload(response: Any) -> str:
    try:
        from google.protobuf.json_format import MessageToDict

        payload = MessageToDict(response)
        return json.dumps(payload, ensure_ascii=True, sort_keys=True)
    except Exception:
        return str(response)


def _truncate_for_log(value: str, max_chars: int = 400) -> str:
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars]}...(truncated)"
