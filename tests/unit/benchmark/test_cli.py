import pytest
from benchmark.bitgn.runner import RunSummary

from benchmark.bitgn.cli import (
    _append_local_run_record,
    _compute_average_score,
    _format_score,
    _print_task_summary,
    parse_config,
)


def test_parse_config_defaults_to_local_qwen():
    config = parse_config(["--task-id", "t01"])

    assert config.task_id == "t01"
    assert config.all_tasks is False
    assert config.agent_mode == "dumb"
    assert config.model_provider == "local"
    assert config.debug is False
    assert config.trial_launch_mode == "playground"
    assert config.model_name == "qwen3.5:latest"
    assert config.model_base_url == "http://127.0.0.1:11434"
    assert config.model_api_key_env is None
    assert config.bitgn_api_key_env == "BITGN_API_KEY"
    assert config.run_name.startswith("columbarium-")
    assert len(config.run_name) > len("columbarium-")


def test_parse_config_openai_defaults_and_key_env():
    config = parse_config(["--task-id", "t01", "--model-provider", "openai"])

    assert config.model_provider == "openai"
    assert config.model_name == "gpt-4.1-mini"
    assert config.model_base_url == "https://api.openai.com"
    assert config.model_api_key_env == "OPENAI_API_KEY"


def test_parse_config_run_name_from_env(monkeypatch):
    monkeypatch.setenv("BITGN_RUN_NAME", "columbarium-envname")
    config = parse_config(["--task-id", "t01"])
    assert config.run_name == "columbarium-envname"


def test_parse_config_run_name_flag_overrides_env(monkeypatch):
    monkeypatch.setenv("BITGN_RUN_NAME", "columbarium-envname")
    config = parse_config(["--task-id", "t01", "--run-name", "columbarium-cli"])
    assert config.run_name == "columbarium-cli"


def test_parse_config_debug_flag():
    config = parse_config(["--task-id", "t01", "--debug"])

    assert config.debug is True


def test_parse_config_trial_launch_mode():
    config = parse_config(["--task-id", "t01", "--trial-launch-mode", "run", "--allow-submit"])

    assert config.trial_launch_mode == "run"


def test_parse_config_run_mode_requires_allow_submit():
    with pytest.raises(SystemExit, match="Run mode requires --allow-submit"):
        parse_config(["--task-id", "t01", "--trial-launch-mode", "run"])


def test_parse_config_agent_mode():
    config = parse_config(["--task-id", "t01", "--agent-mode", "placeholder"])

    assert config.agent_mode == "placeholder"


def test_parse_config_agent_mode_riskidantic():
    config = parse_config(["--task-id", "t01", "--agent-mode", "riskidantic"])

    assert config.agent_mode == "riskidantic"


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


def test_format_score_colors_by_bucket():
    assert "\033[31m" in _format_score(0.0)
    assert "\033[33m" in _format_score(0.5)
    assert "\033[32m" in _format_score(1.0)
    assert _format_score(None) == "None"


def test_compute_average_score_ignores_missing_scores():
    average = _compute_average_score(
        [
            ("t01", 1.0, 1.2),
            ("t02", None, 0.5),
            ("t03", 0.0, 2.1),
        ]
    )
    assert average == 0.5


def test_compute_average_score_none_when_all_missing():
    assert _compute_average_score([("t01", None, 0.1), ("t02", None, 0.2)]) is None


def test_task_summary_has_three_sections(capsys):
    summary = RunSummary(
        trial_id="trial-1",
        benchmark_id="bitgn/pac1-dev",
        task_id="t01",
        instruction="Do the thing",
        submitted=False,
        score=None,
        score_detail=["line one"],
        debug_detail=["debug line"],
    )

    _print_task_summary(
        summary=summary,
        debug=False,
        index=1,
        total=1,
        agent_actions=["solve_trial:start trial_id=trial-1"],
    )
    out = capsys.readouterr().out

    assert "TASK DETAILS" in out
    assert "SOLUTION LOG" in out
    assert "RESULT" in out
    assert out.count("TASK DETAILS") == 1
    assert out.count("SOLUTION LOG") == 1
    assert out.count("RESULT") == 1


def test_append_local_run_record_writes_required_fields(tmp_path, monkeypatch):
    log_path = tmp_path / "runs.log"
    monkeypatch.setattr("benchmark.bitgn.cli.LOCAL_RUN_LOG_PATH", log_path)
    monkeypatch.setattr("benchmark.bitgn.cli._resolve_commit_sha", lambda: "abc123def456")

    _append_local_run_record(
        run_name="columbarium-calm-curie",
        average_score=0.75,
        elapsed_seconds=12.3,
        agent_mode="dumb",
    )

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    line = lines[0]
    assert "run_name=columbarium-calm-curie" in line
    assert "average_score=0.750000" in line
    assert "commit_sha=abc123def456" in line
    assert "time_seconds=12.300" in line
    assert "agent_mode=dumb" in line
