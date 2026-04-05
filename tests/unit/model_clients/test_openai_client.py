import json
from unittest.mock import patch

import pytest

from model_clients.openai_client import OpenAIModelClient
from model_clients.types import Message, ModelSettings, ToolDefinition


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


def test_openai_generate_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_urlopen(req, timeout):
        assert req.full_url.endswith("/v1/chat/completions")
        assert req.headers["Authorization"] == "Bearer test-key"
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["model"] == "gpt-4.1-mini"
        assert payload["messages"][0]["role"] == "user"
        assert timeout == 60.0
        return _FakeResponse(
            {
                "model": "gpt-4.1-mini",
                "choices": [
                    {
                        "message": {"content": "hello from openai"},
                        "finish_reason": "stop",
                    }
                ],
            }
        )

    client = OpenAIModelClient(model="gpt-4.1-mini")

    with patch("model_clients.openai_client.request.urlopen", side_effect=fake_urlopen):
        response = client.generate([Message(role="user", content="hi")], ModelSettings(temperature=0.2, max_tokens=10))

    assert response.provider == "openai"
    assert response.content == "hello from openai"
    assert response.finish_reason == "stop"


def test_openai_missing_api_key_raises():
    client = OpenAIModelClient(model="gpt-4.1-mini", api_key_env="MISSING_KEY")
    with pytest.raises(ValueError, match="Missing API key"):
        client.generate([Message(role="user", content="hi")])


def test_openai_generate_forwards_tools(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_urlopen(req, timeout):
        _ = timeout
        payload = json.loads(req.data.decode("utf-8"))
        assert "tools" in payload
        assert payload["tools"][0]["function"]["name"] == "Context"
        assert payload["tools"][1]["function"]["name"] == "Search"
        assert payload["tools"][1]["function"]["parameters"]["type"] == "object"
        return _FakeResponse(
            {
                "model": "gpt-4.1-mini",
                "choices": [
                    {
                        "message": {"content": "ok"},
                        "finish_reason": "stop",
                    }
                ],
            }
        )

    client = OpenAIModelClient(model="gpt-4.1-mini")

    with patch("model_clients.openai_client.request.urlopen", side_effect=fake_urlopen):
        _ = client.generate(
            [Message(role="user", content="hi")],
            tools=[
                "Context",
                ToolDefinition(
                    name="Search",
                    description="Search repository files",
                    parameters={"type": "object", "properties": {"pattern": {"type": "string"}}},
                ),
            ],
        )
