import json
from unittest.mock import patch

import pytest

from model_clients.ollama_client import LocalOllamaClient
from model_clients.types import Message, ToolDefinition


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


@pytest.mark.parametrize("model_name", ["qwen3.5:4b", "qwen3.5:9b"])
def test_ollama_generate_success(model_name: str):
    def fake_urlopen(req, timeout):
        assert req.full_url.endswith("/api/chat")
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["model"] == model_name
        assert payload["stream"] is False
        assert timeout == 60.0
        return _FakeResponse(
            {
                "model": model_name,
                "message": {"role": "assistant", "content": "hello from ollama"},
                "done_reason": "stop",
            }
        )

    client = LocalOllamaClient(model=model_name)

    with patch("model_clients.ollama_client.request.urlopen", side_effect=fake_urlopen):
        response = client.generate([Message(role="user", content="hello")])

    assert response.provider == "local"
    assert response.content == "hello from ollama"
    assert response.finish_reason == "stop"


def test_ollama_generate_passes_tools_and_parses_tool_calls():
    tools = [
        ToolDefinition(
            name="Search",
            description="Search files.",
            parameters={
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": ["pattern"],
                "additionalProperties": False,
            },
        )
    ]

    def fake_urlopen(req, timeout):
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["tools"][0]["function"]["name"] == "Search"
        assert timeout == 60.0
        return _FakeResponse(
            {
                "model": "qwen3.5:4b",
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_3",
                            "function": {"name": "Search", "arguments": {"pattern": "TODO"}},
                        }
                    ],
                },
                "done_reason": "tool_calls",
            }
        )

    client = LocalOllamaClient(model="qwen3.5:4b")

    with patch("model_clients.ollama_client.request.urlopen", side_effect=fake_urlopen):
        response = client.generate([Message(role="user", content="find todos")], tools=tools)

    assert response.content == ""
    assert response.finish_reason == "tool_calls"
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "Search"
    assert response.tool_calls[0].arguments == '{"pattern": "TODO"}'
