from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class Message:
    role: Role
    content: str


@dataclass(frozen=True)
class ModelSettings:
    temperature: float = 0.0
    max_tokens: int | None = None
    timeout_seconds: float = 60.0


@dataclass(frozen=True)
class ModelResponse:
    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelClientConfig:
    provider: Literal["local", "openai"]
    model: str
    base_url: str
    api_key_env: str | None = None
    timeout_seconds: float = 60.0
