from __future__ import annotations

import json
from urllib import request

from .types import Message, ModelResponse, ModelSettings, ToolCall, ToolDefinition


class LocalOllamaClient:
    """Minimal Ollama chat adapter behind the model-client boundary."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 60.0,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def generate(
        self,
        messages: list[Message],
        settings: ModelSettings | None = None,
        tools: list[ToolDefinition] | None = None,
    ) -> ModelResponse:
        settings = settings or ModelSettings(timeout_seconds=self._timeout_seconds)
        payload_messages = []
        for m in messages:
            item: dict[str, object] = {"role": m.role, "content": m.content}
            if m.name is not None:
                item["name"] = m.name
            if m.tool_call_id is not None:
                item["tool_call_id"] = m.tool_call_id
            payload_messages.append(item)

        payload: dict[str, object] = {
            "model": self._model,
            "messages": payload_messages,
            "stream": False,
            "options": {"temperature": settings.temperature},
        }
        if settings.max_tokens is not None:
            payload["options"]["num_predict"] = settings.max_tokens
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in tools
            ]

        raw = _post_json(
            f"{self._base_url}/api/chat",
            payload=payload,
            timeout_seconds=settings.timeout_seconds,
        )
        response_message = raw.get("message", {})
        tool_calls = []
        for call in response_message.get("tool_calls", []):
            function_payload = call.get("function", {})
            tool_calls.append(
                ToolCall(
                    id=call.get("id"),
                    name=function_payload.get("name", ""),
                    arguments=json.dumps(function_payload.get("arguments", {}), ensure_ascii=True),
                )
            )
        return ModelResponse(
            content=response_message.get("content", ""),
            model=raw.get("model", self._model),
            provider="local",
            finish_reason=raw.get("done_reason"),
            tool_calls=tool_calls,
            raw=raw,
        )


def _post_json(url: str, payload: dict[str, object], timeout_seconds: float) -> dict:
    req = request.Request(
        url,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with request.urlopen(req, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))
