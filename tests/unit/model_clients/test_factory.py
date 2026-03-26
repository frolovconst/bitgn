from model_clients import LocalOllamaClient, OpenAIModelClient, create_model_client
from model_clients.types import ModelClientConfig


def test_factory_returns_local_client():
    client = create_model_client(
        ModelClientConfig(
            provider="local",
            model="qwen2.5-coder:3b",
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
