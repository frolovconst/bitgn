import os

import pytest

from model_clients.ollama_client import LocalOllamaClient
from model_clients.types import Message, ModelSettings


@pytest.mark.local_model
def test_ollama_generate_live_response():
    client = LocalOllamaClient(
        model=os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:3b"),
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        timeout_seconds=float(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "30")),
    )

    response = client.generate(
        [Message(role="user", content="Reply with exactly: local model ok")],
        ModelSettings(temperature=0.0, max_tokens=20, timeout_seconds=30.0),
    )

    assert response.provider == "local"
    assert response.model
    assert response.content.strip()
