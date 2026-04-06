import pytest

from model_clients import LocalOllamaClient, OpenAIModelClient, create_model_client
from model_clients.types import ModelClientConfig


@pytest.mark.parametrize("model_name", ["qwen3.5:4b", "qwen3.5:9b"])
def test_factory_returns_local_client(model_name: str):
    client = create_model_client(
        ModelClientConfig(
            provider="local",
            model=model_name,
            base_url="http://127.0.0.1:11434",
        )
    )
    assert isinstance(client, LocalOllamaClient)


def test_factory_returns_openai_client():
    client = create_model_client(
        ModelClientConfig(
            provider="openai",
            model="gpt-4.1-mini",
            base_url="https://api.openai.com",
            api_key_env="OPENAI_API_KEY",
        )
    )
    assert isinstance(client, OpenAIModelClient)
