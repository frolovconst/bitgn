from __future__ import annotations

from typing import Protocol

from .types import Message, ModelResponse, ModelSettings, ToolDefinition


class ModelClient(Protocol):
    def generate(
        self,
        messages: list[Message],
        settings: ModelSettings | None = None,
        tools: list[ToolDefinition] | None = None,
    ) -> ModelResponse:
        ...
