from __future__ import annotations

import json
from urllib import request

from .types import Message, ModelResponse, ModelSettings


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

    def generate(self, messages: list[Message], settings: ModelSettings | None = None) -> ModelResponse:
        settings = settings or ModelSettings(timeout_seconds=self._timeout_seconds)
        payload: dict[str, object] = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": settings.temperature},
        }
        if settings.max_tokens is not None:
            payload["options"]["num_predict"] = settings.max_tokens
        if _expects_json_response(messages):
            payload["format"] = "json"

        raw = _post_json(
            f"{self._base_url}/api/chat",
            payload=payload,
            timeout_seconds=settings.timeout_seconds,
        )
        return ModelResponse(
            content=raw["message"]["content"],
            model=raw.get("model", self._model),
            provider="local",
            finish_reason=raw.get("done_reason"),
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


def _expects_json_response(messages: list[Message]) -> bool:
    markers = (
        "return json only",
        "do not wrap the json",
        "respond with json",
        '"current_state"',
        '"function"',
        '"tool"',
    )
    for message in messages:
        content = message.content.lower()
        if any(marker in content for marker in markers):
            return True
    return False
