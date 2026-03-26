import json
from unittest.mock import patch

from model_clients.ollama_client import LocalOllamaClient
from model_clients.types import Message


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


def test_ollama_generate_success():
    def fake_urlopen(req, timeout):
        assert req.full_url.endswith("/api/chat")
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["model"] == "qwen2.5-coder:3b"
        assert payload["stream"] is False
        assert timeout == 60.0
        return _FakeResponse(
            {
                "model": "qwen2.5-coder:3b",
                "message": {"role": "assistant", "content": "hello from ollama"},
                "done_reason": "stop",
            }
        )

    client = LocalOllamaClient(model="qwen2.5-coder:3b")

    with patch("model_clients.ollama_client.request.urlopen", side_effect=fake_urlopen):
        response = client.generate([Message(role="user", content="hello")])

    assert response.provider == "local"
    assert response.content == "hello from ollama"
    assert response.finish_reason == "stop"
