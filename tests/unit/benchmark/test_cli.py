import pytest

from benchmark.bitgn.cli import parse_config


def test_parse_config_defaults_to_local_qwen():
    config = parse_config(["--task-id", "t01"])

    assert config.task_id == "t01"
    assert config.all_tasks is False
    assert config.agent_mode == "llm"
    assert config.model_provider == "local"
    assert config.debug is False
    assert config.trial_launch_mode == "playground"
    assert config.model_name == "qwen3.5:4b"
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


def test_parse_config_trial_launch_mode():
    config = parse_config(["--task-id", "t01", "--trial-launch-mode", "run"])

    assert config.trial_launch_mode == "run"


def test_parse_config_agent_mode():
    config = parse_config(["--task-id", "t01", "--agent-mode", "placeholder"])

    assert config.agent_mode == "placeholder"


def test_parse_config_agent_mode_llm():
    config = parse_config(["--task-id", "t01", "--agent-mode", "llm"])

    assert config.agent_mode == "llm"


def test_parse_config_all_tasks_mode():
    config = parse_config(["--all-tasks"])

    assert config.all_tasks is True
    assert config.task_id is None


def test_parse_config_requires_task_selection():
    with pytest.raises(SystemExit, match="Either --task-id or --all-tasks must be provided"):
        parse_config([])


def test_parse_config_rejects_task_id_and_all_tasks_together():
    with pytest.raises(SystemExit, match="Use either --task-id or --all-tasks, not both"):
        parse_config(["--task-id", "t01", "--all-tasks"])
