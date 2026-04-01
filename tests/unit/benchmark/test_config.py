import pytest

from benchmark.bitgn.config import BitgnRunConfig


def test_config_from_env_defaults(monkeypatch):
    monkeypatch.setenv("BITGN_MODEL", "gpt-4.1-mini")

    config = BitgnRunConfig.from_env()

    assert config.benchmark_kind == "sandbox"
    assert config.benchmark_host == "https://api.bitgn.com"
    assert config.benchmark_id == "bitgn/sandbox"
    assert config.model.provider == "openai"
    assert config.model.base_url == "https://api.openai.com"
    assert config.generation.max_tokens == 2000


def test_config_from_env_local_provider(monkeypatch):
    monkeypatch.setenv("BITGN_MODEL", "qwen2.5-coder:3b")
    monkeypatch.setenv("BITGN_MODEL_PROVIDER", "local")

    config = BitgnRunConfig.from_env(task_ids=["t01"])

    assert config.model.provider == "local"
    assert config.model.base_url == "http://127.0.0.1:11434"
    assert config.task_ids == ("t01",)


def test_config_from_env_pac1_defaults(monkeypatch):
    monkeypatch.setenv("BITGN_MODEL", "gpt-4.1-mini")
    monkeypatch.setenv("BITGN_BENCHMARK_KIND", "pac1")

    config = BitgnRunConfig.from_env(task_ids=["task-1"])

    assert config.benchmark_kind == "pac1"
    assert config.benchmark_id == "bitgn/pac1-dev"
    assert config.task_ids == ("task-1",)


def test_config_requires_model(monkeypatch):
    monkeypatch.delenv("BITGN_MODEL", raising=False)

    with pytest.raises(ValueError, match="BITGN_MODEL"):
        BitgnRunConfig.from_env()
