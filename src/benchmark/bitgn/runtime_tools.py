from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from model_clients.types import ToolDefinition

from .contracts import TrialHandle

_VALID_FIND_TYPES = {"TYPE_ALL", "TYPE_FILES", "TYPE_DIRS"}
_VALID_PCM_OUTCOMES = {
    "OUTCOME_OK",
    "OUTCOME_DENIED_SECURITY",
    "OUTCOME_NONE_CLARIFICATION",
    "OUTCOME_NONE_UNSUPPORTED",
    "OUTCOME_ERR_INTERNAL",
}

class RuntimeSurface(str, Enum):
    PCM = "pcm"
    MINI = "mini"


BENCHMARK_RUNTIME_SURFACE_BY_ID: dict[str, RuntimeSurface] = {
    "bitgn/pac1-dev": RuntimeSurface.PCM,
    "bitgn/sandbox": RuntimeSurface.MINI,
}


@dataclass(frozen=True)
class RuntimeToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class RuntimeTool:
    spec: RuntimeToolSpec
    validate: Callable[[dict[str, Any]], dict[str, Any]]
    invoke: Callable[[str, dict[str, Any]], Any]


class ToolValidationError(ValueError):
    def __init__(self, message: str, *, guidance: str) -> None:
        super().__init__(message)
        self.guidance = guidance


def list_runtime_tools(benchmark_id: str) -> list[RuntimeToolSpec]:
    surface = _resolve_runtime_surface(benchmark_id)
    return [tool.spec for tool in _tool_map_for_surface(surface).values()]


def list_runtime_tool_names(benchmark_id: str) -> list[str]:
    return [tool.name for tool in list_runtime_tools(benchmark_id)]


def build_model_tool_definitions(benchmark_id: str) -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name=tool.name,
            description=tool.description,
            parameters=tool.parameters,
        )
        for tool in list_runtime_tools(benchmark_id)
    ]


def call_runtime_tool(trial: TrialHandle, tool_name: str, arguments: str | dict[str, Any] | None) -> tuple[str, str]:
    try:
        payload = _parse_arguments(arguments)
    except ToolValidationError as exc:
        return (
            json.dumps({}, ensure_ascii=True, sort_keys=True),
            json.dumps(
                {
                    "ok": False,
                    "error": "validation_error",
                    "message": str(exc),
                    "guidance": exc.guidance,
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        )
    tools = _tool_map_for_surface(_resolve_runtime_surface(trial.benchmark_id))
    tool = tools.get(tool_name)
    if tool is None:
        available = ", ".join(sorted(tools.keys()))
        return (
            json.dumps(payload, ensure_ascii=True, sort_keys=True),
            json.dumps(
                {
                    "ok": False,
                    "error": "unknown_tool",
                    "message": f"Unknown tool '{tool_name}'.",
                    "guidance": f"Use one of: {available}",
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        )

    try:
        validated = tool.validate(payload)
    except ToolValidationError as exc:
        return (
            json.dumps(payload, ensure_ascii=True, sort_keys=True),
            json.dumps(
                {
                    "ok": False,
                    "error": "validation_error",
                    "message": str(exc),
                    "guidance": exc.guidance,
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        )

    try:
        response = tool.invoke(trial.harness_url, validated)
    except Exception as exc:
        return (
            json.dumps(validated, ensure_ascii=True, sort_keys=True),
            json.dumps(
                {
                    "ok": False,
                    "error": "runtime_error",
                    "message": str(exc),
                    "guidance": "Revise arguments if needed and retry. If repeated, return OUTCOME_ERR_INTERNAL.",
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        )

    return (
        json.dumps(validated, ensure_ascii=True, sort_keys=True),
        json.dumps(_message_to_payload(response), ensure_ascii=True, sort_keys=True),
    )


def _parse_arguments(arguments: str | dict[str, Any] | None) -> dict[str, Any]:
    if arguments is None:
        return {}
    if isinstance(arguments, dict):
        return dict(arguments)
    if not arguments.strip():
        return {}
    try:
        parsed = json.loads(arguments)
    except json.JSONDecodeError as exc:
        raise ToolValidationError(
            f"Arguments must be valid JSON object: {exc}",
            guidance="Return a JSON object with valid keys/values for this tool and retry.",
        ) from exc
    if not isinstance(parsed, dict):
        raise ToolValidationError(
            "Arguments must decode to a JSON object.",
            guidance="Wrap arguments in a JSON object and retry.",
        )
    return parsed


def _tool_map_for_surface(surface: RuntimeSurface) -> dict[str, RuntimeTool]:
    if surface == RuntimeSurface.MINI:
        return _mini_tools()
    return _pcm_tools()


def _resolve_runtime_surface(benchmark_id: str) -> RuntimeSurface:
    return BENCHMARK_RUNTIME_SURFACE_BY_ID.get(benchmark_id, RuntimeSurface.PCM)


def _mini_tools() -> dict[str, RuntimeTool]:
    return {
        "Outline": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Outline",
                description=(
                    "Non-recursive tree view. For folder paths, returns child folders/files and "
                    "level-1 markdown headers for files. Parameter: path (string, '/' for workspace root)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File or folder path. Use '/' for workspace root.",
                        }
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {"path": _require_non_empty_str(a, "path")},
            invoke=lambda harness_url, a: _create_mini_runtime_client(harness_url).outline(
                _new_mini_outline_request(path=a["path"])
            ),
        ),
        "Search": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Search",
                description=(
                    "Regex search over workspace content. Parameters: path (string), pattern (POSIX regex string), "
                    "count (int, 1..10 snippets)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Search root path."},
                        "pattern": {"type": "string", "description": "POSIX regular expression."},
                        "count": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Maximum number of snippets to return.",
                        },
                    },
                    "required": ["path", "pattern", "count"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {
                "path": _require_non_empty_str(a, "path"),
                "pattern": _require_non_empty_str(a, "pattern"),
                "count": _require_int_in_range(a, "count", minimum=1, maximum=10),
            },
            invoke=lambda harness_url, a: _create_mini_runtime_client(harness_url).search(
                _new_mini_search_request(path=a["path"], pattern=a["pattern"], count=a["count"])
            ),
        ),
        "List": RuntimeTool(
            spec=RuntimeToolSpec(
                name="List",
                description=(
                    "List immediate folders/files at a path. Parameter: path (string)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Folder path to list."}
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {"path": _require_non_empty_str(a, "path")},
            invoke=lambda harness_url, a: _create_mini_runtime_client(harness_url).list(
                _new_mini_list_request(path=a["path"])
            ),
        ),
        "Read": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Read",
                description="Read full file content. Parameter: path (string file path).",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read."}
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {"path": _require_non_empty_str(a, "path")},
            invoke=lambda harness_url, a: _create_mini_runtime_client(harness_url).read(
                _new_mini_read_request(path=a["path"])
            ),
        ),
        "Write": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Write",
                description=(
                    "Write full file content. Parameters: path (string), content (string). "
                    "Note: JSON writes in directories with sibling _rules.txt may trigger schema validation."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to write."},
                        "content": {"type": "string", "description": "New file content."},
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {
                "path": _require_non_empty_str(a, "path"),
                "content": _require_str(a, "content"),
            },
            invoke=lambda harness_url, a: _create_mini_runtime_client(harness_url).write(
                _new_mini_write_request(path=a["path"], content=a["content"])
            ),
        ),
        "Delete": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Delete",
                description="Delete a file or folder path. Parameter: path (string).",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to delete."}
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {"path": _require_non_empty_str(a, "path")},
            invoke=lambda harness_url, a: _create_mini_runtime_client(harness_url).delete(
                _new_mini_delete_request(path=a["path"])
            ),
        ),
        "Answer": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Answer",
                description=(
                    "Submit terminal answer for a trial. Parameters: answer (string), refs (array of string references)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "description": "Final answer text to submit.",
                        },
                        "refs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Grounding references recorded verbatim.",
                        },
                    },
                    "required": ["answer"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {
                "answer": _require_non_empty_str(a, "answer"),
                "refs": _optional_str_list(a, "refs"),
            },
            invoke=lambda harness_url, a: _create_mini_runtime_client(harness_url).answer(
                _new_mini_answer_request(answer=a["answer"], refs=a["refs"])
            ),
        ),
    }


def _pcm_tools() -> dict[str, RuntimeTool]:
    return {
        "Read": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Read",
                description=(
                    "Read file content. Parameters: path (string), number (bool, optional line numbering), "
                    "start_line (int, 1-based inclusive, 0 means beginning), end_line (int, 1-based inclusive, 0 means end)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read."},
                        "number": {"type": "boolean", "description": "Prefix lines with source line numbers."},
                        "start_line": {"type": "integer", "minimum": 0},
                        "end_line": {"type": "integer", "minimum": 0},
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: _validate_pcm_line_range(
                {
                    "path": _require_non_empty_str(a, "path"),
                    "number": _optional_bool(a, "number", default=False),
                    "start_line": _optional_int(a, "start_line", default=0, minimum=0),
                    "end_line": _optional_int(a, "end_line", default=0, minimum=0),
                }
            ),
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).read(
                _new_pcm_read_request(
                    path=a["path"],
                    number=a["number"],
                    start_line=a["start_line"],
                    end_line=a["end_line"],
                )
            ),
        ),
        "Write": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Write",
                description=(
                    "Write file content. Parameters: path (string), content (string), start_line (int, optional), "
                    "end_line (int, optional). With both line values at 0, performs full overwrite."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to write."},
                        "content": {"type": "string", "description": "New content."},
                        "start_line": {"type": "integer", "minimum": 0},
                        "end_line": {"type": "integer", "minimum": 0},
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: _validate_pcm_line_range(
                {
                    "path": _require_non_empty_str(a, "path"),
                    "content": _require_str(a, "content"),
                    "start_line": _optional_int(a, "start_line", default=0, minimum=0),
                    "end_line": _optional_int(a, "end_line", default=0, minimum=0),
                }
            ),
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).write(
                _new_pcm_write_request(
                    path=a["path"],
                    content=a["content"],
                    start_line=a["start_line"],
                    end_line=a["end_line"],
                )
            ),
        ),
        "Delete": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Delete",
                description="Delete file or folder by path. Parameter: path (string).",
                parameters={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {"path": _require_non_empty_str(a, "path")},
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).delete(
                _new_pcm_delete_request(path=a["path"])
            ),
        ),
        "MkDir": RuntimeTool(
            spec=RuntimeToolSpec(
                name="MkDir",
                description="Create a directory path. Parameter: path (string).",
                parameters={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {"path": _require_non_empty_str(a, "path")},
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).mk_dir(
                _new_pcm_mkdir_request(path=a["path"])
            ),
        ),
        "Move": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Move",
                description=(
                    "Move or rename file/folder path. Parameters: from_name (string source path), "
                    "to_name (string destination path)."
                ),
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
            validate=lambda a: {
                "from_name": _require_non_empty_str(a, "from_name"),
                "to_name": _require_non_empty_str(a, "to_name"),
            },
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).move(
                _new_pcm_move_request(from_name=a["from_name"], to_name=a["to_name"])
            ),
        ),
        "List": RuntimeTool(
            spec=RuntimeToolSpec(
                name="List",
                description="List immediate entries under a path. Parameter: name (string path).",
                parameters={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {"name": _require_non_empty_str(a, "name")},
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).list(
                _new_pcm_list_request(name=a["name"])
            ),
        ),
        "Tree": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Tree",
                description=(
                    "Recursive tree view. Parameters: root (string path, empty means workspace root), "
                    "level (int depth, 0 means unlimited)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "root": {"type": "string"},
                        "level": {"type": "integer", "minimum": 0},
                    },
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {
                "root": _optional_str(a, "root", default=""),
                "level": _optional_int(a, "level", default=0, minimum=0),
            },
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).tree(
                _new_pcm_tree_request(root=a["root"], level=a["level"])
            ),
        ),
        "Find": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Find",
                description=(
                    "Find by filename under root. Parameters: root (string), name (string), type "
                    "('TYPE_ALL' | 'TYPE_FILES' | 'TYPE_DIRS', optional), limit (int >= 0, optional)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "root": {"type": "string"},
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": sorted(_VALID_FIND_TYPES)},
                        "limit": {"type": "integer", "minimum": 0},
                    },
                    "required": ["root", "name"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {
                "root": _require_str(a, "root"),
                "name": _require_non_empty_str(a, "name"),
                "type": _optional_enum(a, "type", default="TYPE_ALL", valid_values=_VALID_FIND_TYPES),
                "limit": _optional_int(a, "limit", default=0, minimum=0),
            },
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).find(
                _new_pcm_find_request(root=a["root"], name=a["name"], typ=a["type"], limit=a["limit"])
            ),
        ),
        "Search": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Search",
                description=(
                    "Regex search in files. Parameters: root (string, optional), pattern (string regex), "
                    "limit (int >= 0, 0 means no explicit limit)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "root": {"type": "string"},
                        "pattern": {"type": "string"},
                        "limit": {"type": "integer", "minimum": 0},
                    },
                    "required": ["pattern"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {
                "root": _optional_str(a, "root", default=""),
                "pattern": _require_non_empty_str(a, "pattern"),
                "limit": _optional_int(a, "limit", default=0, minimum=0),
            },
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).search(
                _new_pcm_search_request(root=a["root"], pattern=a["pattern"], limit=a["limit"])
            ),
        ),
        "Context": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Context",
                description="Get runtime context values such as current unix_time and RFC3339 time.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: _validate_empty_object(a),
            invoke=lambda harness_url, _a: _create_pcm_runtime_client(harness_url).context(
                _new_pcm_context_request()
            ),
        ),
        "Answer": RuntimeTool(
            spec=RuntimeToolSpec(
                name="Answer",
                description=(
                    "Submit terminal answer. Parameters: message (string), outcome (enum string), "
                    "refs (array of strings)."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "outcome": {"type": "string", "enum": sorted(_VALID_PCM_OUTCOMES)},
                        "refs": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["message", "outcome"],
                    "additionalProperties": False,
                },
            ),
            validate=lambda a: {
                "message": _require_non_empty_str(a, "message"),
                "outcome": _require_enum(a, "outcome", valid_values=_VALID_PCM_OUTCOMES),
                "refs": _optional_str_list(a, "refs"),
            },
            invoke=lambda harness_url, a: _create_pcm_runtime_client(harness_url).answer(
                _new_answer_request(message=a["message"], outcome=a["outcome"], refs=a["refs"])
            ),
        ),
    }


def _validate_pcm_line_range(payload: dict[str, Any]) -> dict[str, Any]:
    start = payload.get("start_line", 0)
    end = payload.get("end_line", 0)
    if start > 0 and end > 0 and end < start:
        raise ToolValidationError(
            "end_line must be greater than or equal to start_line when both are set.",
            guidance="Set end_line >= start_line, or set either bound to 0 for open range behavior.",
        )
    return payload


def _validate_empty_object(payload: dict[str, Any]) -> dict[str, Any]:
    if payload:
        keys = ", ".join(sorted(payload.keys()))
        raise ToolValidationError(
            f"This tool does not accept arguments. Received keys: {keys}",
            guidance="Call the tool with an empty JSON object {}.",
        )
    return {}


def _require_non_empty_str(payload: dict[str, Any], key: str) -> str:
    value = _require_str(payload, key)
    if not value.strip():
        raise ToolValidationError(
            f"Field '{key}' must be non-empty.",
            guidance=f"Provide a non-empty string for '{key}' and retry.",
        )
    return value


def _require_str(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ToolValidationError(
            f"Missing required field '{key}'.",
            guidance=f"Include '{key}' in the JSON arguments and retry.",
        )
    value = payload[key]
    if not isinstance(value, str):
        raise ToolValidationError(
            f"Field '{key}' must be a string.",
            guidance=f"Change '{key}' to a JSON string value and retry.",
        )
    return value


def _optional_str(payload: dict[str, Any], key: str, *, default: str) -> str:
    if key not in payload:
        return default
    value = payload[key]
    if not isinstance(value, str):
        raise ToolValidationError(
            f"Field '{key}' must be a string when provided.",
            guidance=f"Set '{key}' to a string or omit it.",
        )
    return value


def _optional_bool(payload: dict[str, Any], key: str, *, default: bool) -> bool:
    if key not in payload:
        return default
    value = payload[key]
    if not isinstance(value, bool):
        raise ToolValidationError(
            f"Field '{key}' must be a boolean.",
            guidance=f"Set '{key}' to true/false or omit it.",
        )
    return value


def _require_int_in_range(payload: dict[str, Any], key: str, *, minimum: int, maximum: int) -> int:
    value = _require_int(payload, key)
    if value < minimum or value > maximum:
        raise ToolValidationError(
            f"Field '{key}' must be between {minimum} and {maximum}.",
            guidance=f"Set '{key}' within [{minimum}, {maximum}] and retry.",
        )
    return value


def _require_int(payload: dict[str, Any], key: str) -> int:
    if key not in payload:
        raise ToolValidationError(
            f"Missing required field '{key}'.",
            guidance=f"Include '{key}' in the JSON arguments and retry.",
        )
    value = payload[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ToolValidationError(
            f"Field '{key}' must be an integer.",
            guidance=f"Set '{key}' to an integer JSON value and retry.",
        )
    return value


def _optional_int(
    payload: dict[str, Any],
    key: str,
    *,
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if key not in payload:
        return default
    value = payload[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ToolValidationError(
            f"Field '{key}' must be an integer when provided.",
            guidance=f"Set '{key}' to an integer or omit it.",
        )
    if minimum is not None and value < minimum:
        raise ToolValidationError(
            f"Field '{key}' must be >= {minimum}.",
            guidance=f"Increase '{key}' to at least {minimum} and retry.",
        )
    if maximum is not None and value > maximum:
        raise ToolValidationError(
            f"Field '{key}' must be <= {maximum}.",
            guidance=f"Decrease '{key}' to at most {maximum} and retry.",
        )
    return value


def _require_enum(payload: dict[str, Any], key: str, *, valid_values: set[str]) -> str:
    value = _require_str(payload, key)
    if value not in valid_values:
        allowed = ", ".join(sorted(valid_values))
        raise ToolValidationError(
            f"Field '{key}' has invalid value '{value}'.",
            guidance=f"Use one of: {allowed}",
        )
    return value


def _optional_enum(payload: dict[str, Any], key: str, *, default: str, valid_values: set[str]) -> str:
    if key not in payload:
        return default
    value = payload[key]
    if not isinstance(value, str):
        raise ToolValidationError(
            f"Field '{key}' must be a string when provided.",
            guidance=f"Set '{key}' to one of: {', '.join(sorted(valid_values))}",
        )
    if value not in valid_values:
        raise ToolValidationError(
            f"Field '{key}' has invalid value '{value}'.",
            guidance=f"Use one of: {', '.join(sorted(valid_values))}",
        )
    return value


def _optional_str_list(payload: dict[str, Any], key: str) -> list[str]:
    if key not in payload:
        return []
    value = payload[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ToolValidationError(
            f"Field '{key}' must be an array of strings.",
            guidance=f"Set '{key}' to an array like [\"path/file.md\"].",
        )
    return value


def _message_to_payload(message: Any) -> dict[str, Any]:
    try:
        from google.protobuf.json_format import MessageToDict

        return MessageToDict(message)
    except Exception:
        return {"raw": str(message)}


def _create_pcm_runtime_client(harness_url: str):
    from bitgn.vm.pcm_connect import PcmRuntimeClientSync

    return PcmRuntimeClientSync(harness_url)


def _create_mini_runtime_client(harness_url: str):
    from bitgn.vm.mini_connect import MiniRuntimeClientSync

    return MiniRuntimeClientSync(harness_url)


def _new_pcm_read_request(path: str, number: bool, start_line: int, end_line: int):
    from bitgn.vm.pcm_pb2 import ReadRequest

    return ReadRequest(path=path, number=number, start_line=start_line, end_line=end_line)


def _new_pcm_write_request(path: str, content: str, start_line: int, end_line: int):
    from bitgn.vm.pcm_pb2 import WriteRequest

    return WriteRequest(path=path, content=content, start_line=start_line, end_line=end_line)


def _new_pcm_delete_request(path: str):
    from bitgn.vm.pcm_pb2 import DeleteRequest

    return DeleteRequest(path=path)


def _new_pcm_mkdir_request(path: str):
    from bitgn.vm.pcm_pb2 import MkDirRequest

    return MkDirRequest(path=path)


def _new_pcm_move_request(from_name: str, to_name: str):
    from bitgn.vm.pcm_pb2 import MoveRequest

    return MoveRequest(from_name=from_name, to_name=to_name)


def _new_pcm_list_request(name: str):
    from bitgn.vm.pcm_pb2 import ListRequest

    return ListRequest(name=name)


def _new_pcm_tree_request(root: str, level: int):
    from bitgn.vm.pcm_pb2 import TreeRequest

    return TreeRequest(root=root, level=level)


def _new_pcm_find_request(root: str, name: str, typ: str, limit: int):
    from bitgn.vm.pcm_pb2 import FindRequest

    return FindRequest(root=root, name=name, type=getattr(FindRequest, typ), limit=limit)


def _new_pcm_search_request(root: str, pattern: str, limit: int):
    from bitgn.vm.pcm_pb2 import SearchRequest

    return SearchRequest(root=root, pattern=pattern, limit=limit)


def _new_pcm_context_request():
    from bitgn.vm.pcm_pb2 import ContextRequest

    return ContextRequest()


def _new_answer_request(message: str, outcome: str, refs: list[str]):
    from bitgn.vm.pcm_pb2 import AnswerRequest, Outcome

    return AnswerRequest(message=message, outcome=getattr(Outcome, outcome), refs=refs)


def _new_mini_outline_request(path: str):
    from bitgn.vm.mini_pb2 import OutlineRequest

    return OutlineRequest(path=path)


def _new_mini_list_request(path: str):
    from bitgn.vm.mini_pb2 import ListRequest

    return ListRequest(path=path)


def _new_mini_search_request(path: str, pattern: str, count: int):
    from bitgn.vm.mini_pb2 import SearchRequest

    return SearchRequest(path=path, pattern=pattern, count=count)


def _new_mini_read_request(path: str):
    from bitgn.vm.mini_pb2 import ReadRequest

    return ReadRequest(path=path)


def _new_mini_write_request(path: str, content: str):
    from bitgn.vm.mini_pb2 import WriteRequest

    return WriteRequest(path=path, content=content)


def _new_mini_delete_request(path: str):
    from bitgn.vm.mini_pb2 import DeleteRequest

    return DeleteRequest(path=path)


def _new_mini_answer_request(answer: str, refs: list[str]):
    from bitgn.vm.mini_pb2 import AnswerRequest

    return AnswerRequest(answer=answer, refs=refs)
