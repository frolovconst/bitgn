from __future__ import annotations

import json
import shlex

from connectrpc.errors import ConnectError
from google.protobuf.json_format import MessageToDict

from bitgn.vm.pcm_connect import PcmRuntimeClientSync
from bitgn.vm.pcm_pb2 import (
    AnswerRequest,
    ContextRequest,
    DeleteRequest,
    FindRequest,
    ListRequest,
    MkDirRequest,
    MoveRequest,
    Outcome,
    ReadRequest,
    SearchRequest,
    TreeRequest,
    WriteRequest,
)

from .common import ToolExecution
from .pac1_protocol import (
    Pac1ToolCommand,
    ReportTaskCompletion,
    ReqContext,
    ReqDelete,
    ReqFind,
    ReqList,
    ReqMkDir,
    ReqMove,
    ReqRead,
    ReqSearch,
    ReqTree,
    ReqWrite,
)

OUTCOME_BY_NAME = {
    "OUTCOME_OK": Outcome.OUTCOME_OK,
    "OUTCOME_DENIED_SECURITY": Outcome.OUTCOME_DENIED_SECURITY,
    "OUTCOME_NONE_CLARIFICATION": Outcome.OUTCOME_NONE_CLARIFICATION,
    "OUTCOME_NONE_UNSUPPORTED": Outcome.OUTCOME_NONE_UNSUPPORTED,
    "OUTCOME_ERR_INTERNAL": Outcome.OUTCOME_ERR_INTERNAL,
}


class BitgnPcmRuntimeExecutor:
    def __init__(self, harness_url: str) -> None:
        self._vm = PcmRuntimeClientSync(harness_url)

    def execute(self, command: Pac1ToolCommand) -> ToolExecution:
        try:
            result = _dispatch(self._vm, command)
            if isinstance(command, ReportTaskCompletion):
                normalized_refs = _normalize_grounding_refs(command.grounding_refs)
                return ToolExecution(
                    content="{}",
                    completed=True,
                    completion_code=command.outcome,
                    answer=command.message,
                    grounding_refs=normalized_refs,
                    completed_steps_laconic=tuple(command.completed_steps_laconic),
                )
            return ToolExecution(content=_format_result(command, result))
        except ConnectError as exc:
            return ToolExecution(content=f"{exc.code}: {exc.message}")


def _dispatch(vm: PcmRuntimeClientSync, command: Pac1ToolCommand):
    if isinstance(command, ReqContext):
        return vm.context(ContextRequest())
    if isinstance(command, ReqTree):
        return vm.tree(TreeRequest(root=command.root, level=command.level))
    if isinstance(command, ReqFind):
        return vm.find(
            FindRequest(
                root=command.root,
                name=command.name,
                type={"all": 0, "files": 1, "dirs": 2}[command.kind],
                limit=command.limit,
            )
        )
    if isinstance(command, ReqSearch):
        return vm.search(SearchRequest(root=command.root, pattern=command.pattern, limit=command.limit))
    if isinstance(command, ReqList):
        return vm.list(ListRequest(name=command.path))
    if isinstance(command, ReqRead):
        return vm.read(
            ReadRequest(
                path=command.path,
                number=command.number,
                start_line=command.start_line,
                end_line=command.end_line,
            )
        )
    if isinstance(command, ReqWrite):
        return vm.write(
            WriteRequest(
                path=command.path,
                content=command.content,
                start_line=command.start_line,
                end_line=command.end_line,
            )
        )
    if isinstance(command, ReqDelete):
        return vm.delete(DeleteRequest(path=command.path))
    if isinstance(command, ReqMkDir):
        return vm.mk_dir(MkDirRequest(path=command.path))
    if isinstance(command, ReqMove):
        return vm.move(MoveRequest(from_name=command.from_name, to_name=command.to_name))
    if isinstance(command, ReportTaskCompletion):
        normalized_refs = _normalize_grounding_refs(command.grounding_refs)
        return vm.answer(
            AnswerRequest(
                message=command.message,
                outcome=OUTCOME_BY_NAME[command.outcome],
                refs=list(normalized_refs),
            )
        )
    raise ValueError(f"Unknown command: {command}")


def _format_result(command: Pac1ToolCommand, result) -> str:
    if result is None:
        return "{}"
    if isinstance(command, ReqTree):
        return _format_tree_response(command, result)
    if isinstance(command, ReqList):
        return _format_list_response(command, result)
    if isinstance(command, ReqRead):
        return _format_read_response(command, result)
    if isinstance(command, ReqSearch):
        return _format_search_response(command, result)
    return json.dumps(MessageToDict(result, preserving_proto_field_name=True), indent=2)


def _format_tree_entry(entry, prefix: str = "", is_last: bool = True) -> list[str]:
    branch = "└── " if is_last else "├── "
    lines = [f"{prefix}{branch}{entry.name}"]
    child_prefix = f"{prefix}{'    ' if is_last else '│   '}"
    children = list(entry.children)
    for idx, child in enumerate(children):
        lines.extend(_format_tree_entry(child, prefix=child_prefix, is_last=idx == len(children) - 1))
    return lines


def _render_command(command: str, body: str) -> str:
    return f"{command}\n{body}"


def _format_tree_response(command: ReqTree, result) -> str:
    root = result.root
    if not root.name:
        body = "."
    else:
        lines = [root.name]
        children = list(root.children)
        for idx, child in enumerate(children):
            lines.extend(_format_tree_entry(child, is_last=idx == len(children) - 1))
        body = "\n".join(lines)

    root_arg = command.root or "/"
    level_arg = f" -L {command.level}" if command.level > 0 else ""
    return _render_command(f"tree{level_arg} {root_arg}", body)


def _format_list_response(command: ReqList, result) -> str:
    body = "." if not result.entries else "\n".join(
        f"{entry.name}/" if entry.is_dir else entry.name for entry in result.entries
    )
    return _render_command(f"ls {command.path}", body)


def _format_read_response(command: ReqRead, result) -> str:
    if command.start_line > 0 or command.end_line > 0:
        start = command.start_line if command.start_line > 0 else 1
        end = command.end_line if command.end_line > 0 else "$"
        shell_command = f"sed -n '{start},{end}p' {command.path}"
    elif command.number:
        shell_command = f"cat -n {command.path}"
    else:
        shell_command = f"cat {command.path}"
    return _render_command(shell_command, result.content)


def _format_search_response(command: ReqSearch, result) -> str:
    root = shlex.quote(command.root or "/")
    pattern = shlex.quote(command.pattern)
    body = "\n".join(f"{match.path}:{match.line}:{match.line_text}" for match in result.matches)
    return _render_command(f"rg -n --no-heading -e {pattern} {root}", body)


def _normalize_grounding_refs(refs: list[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        candidate = ref.strip().lstrip("/")
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return tuple(normalized)
