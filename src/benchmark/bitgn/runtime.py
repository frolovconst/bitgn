from __future__ import annotations

import json

from connectrpc.errors import ConnectError
from google.protobuf.json_format import MessageToDict

from bitgn.vm.mini_connect import MiniRuntimeClientSync
from bitgn.vm.mini_pb2 import (
    AnswerRequest,
    DeleteRequest,
    ListRequest,
    OutlineRequest,
    ReadRequest,
    SearchRequest,
    WriteRequest,
)

from .protocol import (
    ReportTaskCompletion,
    ReqDelete,
    ReqList,
    ReqOutline,
    ReqRead,
    ReqSearch,
    ReqWrite,
    RuntimeExecutor,
    ToolCommand,
    ToolExecution,
)


class BitgnMiniRuntimeExecutor(RuntimeExecutor):
    def __init__(self, harness_url: str) -> None:
        self._vm = MiniRuntimeClientSync(harness_url)

    def execute(self, command: ToolCommand) -> ToolExecution:
        try:
            if isinstance(command, ReqOutline):
                response = self._vm.outline(OutlineRequest(path=command.path))
                return ToolExecution(content=_proto_to_json(response))
            if isinstance(command, ReqSearch):
                response = self._vm.search(
                    SearchRequest(path=command.path, pattern=command.pattern, count=command.count)
                )
                return ToolExecution(content=_proto_to_json(response))
            if isinstance(command, ReqList):
                response = self._vm.list(ListRequest(path=command.path))
                return ToolExecution(content=_proto_to_json(response))
            if isinstance(command, ReqRead):
                response = self._vm.read(ReadRequest(path=command.path))
                return ToolExecution(content=_proto_to_json(response))
            if isinstance(command, ReqWrite):
                response = self._vm.write(WriteRequest(path=command.path, content=command.content))
                return ToolExecution(content=_proto_to_json(response))
            if isinstance(command, ReqDelete):
                response = self._vm.delete(DeleteRequest(path=command.path))
                return ToolExecution(content=_proto_to_json(response))
            if isinstance(command, ReportTaskCompletion):
                normalized_refs = _normalize_grounding_refs(command.grounding_refs)
                self._vm.answer(AnswerRequest(answer=command.answer, refs=list(normalized_refs)))
                return ToolExecution(
                    content="{}",
                    completed=True,
                    completion_code=command.code,
                    answer=command.answer,
                    grounding_refs=normalized_refs,
                    completed_steps_laconic=tuple(command.completed_steps_laconic),
                )
        except ConnectError as exc:
            return ToolExecution(content=f"{exc.code}: {exc.message}")

        raise ValueError(f"Unknown command: {command}")


def _proto_to_json(message: object) -> str:
    return json.dumps(
        MessageToDict(message, preserving_proto_field_name=True),
        indent=2,
        sort_keys=True,
    )


def _normalize_grounding_refs(refs: list[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        candidate = ref.strip()
        if not candidate:
            continue
        candidate = candidate.lstrip("/")
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return tuple(normalized)
