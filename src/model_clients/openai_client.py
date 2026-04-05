from __future__ import annotations

import json
import os
from dataclasses import asdict
from urllib import request

from .types import Message, ModelResponse, ModelSettings, ToolSpec


class OpenAIModelClient:
    """Minimal OpenAI Chat Completions adapter behind the model-client boundary."""

    def __init__(
        self,
        model: str,
        base_url: str = "https://api.openai.com",
        api_key_env: str = "OPENAI_API_KEY",
        timeout_seconds: float = 60.0,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._api_key_env = api_key_env
        self._timeout_seconds = timeout_seconds

    def _resolve_api_key(self) -> str:
        api_key = os.getenv(self._api_key_env)
        if not api_key:
            raise ValueError(f"Missing API key in environment variable: {self._api_key_env}")
        return api_key

    def generate(
        self,
        messages: list[Message],
        settings: ModelSettings | None = None,
        tools: list[ToolSpec] | None = None,
    ) -> ModelResponse:
        settings = settings or ModelSettings(timeout_seconds=self._timeout_seconds)
        payload: dict[str, object] = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": settings.temperature,
        }
        if settings.max_tokens is not None:
            payload["max_tokens"] = settings.max_tokens
        if tools:
            payload["tools"] = [_to_function_tool(tool) for tool in tools]

        raw = _post_json(
            f"{self._base_url}/v1/chat/completions",
            payload=payload,
            timeout_seconds=settings.timeout_seconds,
            headers={"Authorization": f"Bearer {self._resolve_api_key()}"},
        )
        first_choice = raw["choices"][0]
        message = first_choice.get("message", {})
        return ModelResponse(
            content=(message.get("content") or ""),
            model=raw.get("model", self._model),
            provider="openai",
            finish_reason=first_choice.get("finish_reason"),
            raw=raw,
        )


def _to_function_tool(tool: ToolSpec) -> dict[str, object]:
    if isinstance(tool, str):
        return {
            "type": "function",
            "function": {
                "name": tool,
                "description": f"Runtime tool {tool}",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        }
    return {"type": "function", "function": asdict(tool)}


def _post_json(url: str, payload: dict[str, object], timeout_seconds: float, headers: dict[str, str] | None = None) -> dict:
    req = request.Request(
        url,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
    )

    with request.urlopen(req, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))
