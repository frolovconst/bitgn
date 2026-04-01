from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from model_clients.types import ModelClientConfig, ModelSettings


def _default_base_url(provider: str) -> str:
    if provider == "local":
        return "http://127.0.0.1:11434"
    if provider == "openai":
        return "https://api.openai.com"
    raise ValueError(f"Unsupported model provider: {provider}")


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


def _env_int(name: str, default: int | None) -> int | None:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class BitgnRunConfig:
    benchmark_host: str
    benchmark_id: str
    max_steps: int
    task_ids: tuple[str, ...]
    model: ModelClientConfig
    generation: ModelSettings

    @classmethod
    def from_env(cls, task_ids: list[str] | None = None) -> "BitgnRunConfig":
        provider_raw = os.getenv("BITGN_MODEL_PROVIDER", "openai")
        if provider_raw not in {"local", "openai"}:
            raise ValueError(f"Unsupported model provider: {provider_raw}")
        provider: Literal["local", "openai"] = provider_raw
        model_name = os.getenv("BITGN_MODEL")
        if not model_name:
            raise ValueError("Missing required environment variable: BITGN_MODEL")

        timeout_seconds = _env_float("BITGN_MODEL_TIMEOUT_SECONDS", 60.0)
        model_config = ModelClientConfig(
            provider=provider,
            model=model_name,
            base_url=os.getenv("BITGN_MODEL_BASE_URL", _default_base_url(provider)),
            api_key_env=os.getenv("BITGN_MODEL_API_KEY_ENV", "OPENAI_API_KEY"),
            timeout_seconds=timeout_seconds,
        )
        generation = ModelSettings(
            temperature=_env_float("BITGN_MODEL_TEMPERATURE", 0.0),
            max_tokens=_env_int("BITGN_MODEL_MAX_TOKENS", 2000),
            timeout_seconds=timeout_seconds,
        )
        return cls(
            benchmark_host=os.getenv("BENCHMARK_HOST", "https://api.bitgn.com"),
            benchmark_id=os.getenv("BITGN_BENCHMARK_ID", "bitgn/sandbox"),
            max_steps=int(os.getenv("BITGN_AGENT_MAX_STEPS", "30")),
            task_ids=tuple(task_ids or ()),
            model=model_config,
            generation=generation,
        )
