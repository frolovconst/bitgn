from __future__ import annotations

from .ollama_client import LocalOllamaClient
from .openai_client import OpenAIModelClient
from .types import ModelClientConfig


def create_model_client(config: ModelClientConfig):
    if config.provider == "local":
        return LocalOllamaClient(
            model=config.model,
            base_url=config.base_url,
            timeout_seconds=config.timeout_seconds,
        )

    if config.provider == "openai":
        return OpenAIModelClient(
            model=config.model,
            base_url=config.base_url,
            api_key_env=config.api_key_env or "OPENAI_API_KEY",
            timeout_seconds=config.timeout_seconds,
        )

    raise ValueError(f"Unsupported model provider: {config.provider}")
