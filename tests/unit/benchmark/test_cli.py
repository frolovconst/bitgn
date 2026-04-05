from benchmark.bitgn.cli import parse_config


def test_parse_config_defaults_to_local_qwen():
    config = parse_config(["--task-id", "t01"])

    assert config.task_id == "t01"
    assert config.model_provider == "local"
    assert config.debug is False
    assert config.model_name == "qwen3.5:latest"
    assert config.model_base_url == "http://127.0.0.1:11434"
    assert config.model_api_key_env is None


def test_parse_config_openai_defaults_and_key_env():
    config = parse_config(["--task-id", "t01", "--model-provider", "openai"])

    assert config.model_provider == "openai"
    assert config.model_name == "gpt-4.1-mini"
    assert config.model_base_url == "https://api.openai.com"
    assert config.model_api_key_env == "OPENAI_API_KEY"


def test_parse_config_debug_flag():
    config = parse_config(["--task-id", "t01", "--debug"])

    assert config.debug is True
