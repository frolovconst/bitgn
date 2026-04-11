from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkRunConfig:
    """Static configuration for one benchmark run invocation."""

    benchmark_host: str
    benchmark_id: str
    task_id: str | None
    all_tasks: bool
    allow_submit: bool
    agent_mode: str
    debug: bool
    trial_launch_mode: str
    model_provider: str
    model_name: str
    model_base_url: str
    model_api_key_env: str | None
    model_timeout_seconds: float
    bitgn_api_key_env: str = "BITGN_API_KEY"
    run_name: str | None = None


DEFAULT_BENCHMARK_HOST = "https://api.bitgn.com"
DEFAULT_BENCHMARK_ID = "bitgn/pac1-dev"
DEFAULT_MODEL_PROVIDER = "local"
DEFAULT_AGENT_MODE = "dumb"
DEFAULT_TRIAL_LAUNCH_MODE = "playground"
DEFAULT_LOCAL_MODEL = "qwen3.5:latest"
DEFAULT_LOCAL_MODEL_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_OPENAI_MODEL_BASE_URL = "https://api.openai.com"
DEFAULT_BITGN_API_KEY_ENV = "BITGN_API_KEY"
DEFAULT_RUN_NAME = "columbarium-trial-launch"


def env_default_benchmark_host() -> str:
    return os.getenv("BENCHMARK_HOST", DEFAULT_BENCHMARK_HOST)


def env_default_benchmark_id() -> str:
    return os.getenv("BENCHMARK_ID", DEFAULT_BENCHMARK_ID)


def default_model_name(provider: str) -> str:
    if provider == "openai":
        return DEFAULT_OPENAI_MODEL
    return DEFAULT_LOCAL_MODEL


def default_model_base_url(provider: str) -> str:
    if provider == "openai":
        return DEFAULT_OPENAI_MODEL_BASE_URL
    return DEFAULT_LOCAL_MODEL_BASE_URL


def env_default_run_name() -> str:
    return os.getenv("BITGN_RUN_NAME", DEFAULT_RUN_NAME)
