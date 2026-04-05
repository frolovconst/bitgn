from dataclasses import replace

from benchmark.bitgn.agent_loop import PlaceholderAgentLoop
from benchmark.bitgn.config import BenchmarkRunConfig
from benchmark.bitgn.platform import PlaceholderBenchmarkPlatform
from benchmark.bitgn.runner import BenchmarkRunService


def _config(allow_submit: bool, debug: bool = False) -> BenchmarkRunConfig:
    return BenchmarkRunConfig(
        benchmark_host="https://api.bitgn.com",
        benchmark_id="bitgn/pac1-dev",
        task_id="t01",
        all_tasks=False,
        allow_submit=allow_submit,
        agent_mode="placeholder",
        debug=debug,
        trial_launch_mode="playground",
        model_provider="local",
        model_name="qwen3.5:latest",
        model_base_url="http://127.0.0.1:11434",
        model_api_key_env=None,
        model_timeout_seconds=60.0,
    )


def test_run_once_without_submit_returns_placeholder_details():
    service = BenchmarkRunService(
        platform=PlaceholderBenchmarkPlatform("https://api.bitgn.com"),
        agent_loop=PlaceholderAgentLoop(),
    )

    summary = service.run_once(_config(allow_submit=False))

    assert summary.submitted is False
    assert summary.score is None
    assert any("Submission disabled" in line for line in summary.score_detail)
    assert summary.debug_detail == []


def test_run_once_with_submit_flows_through_placeholder_platform():
    service = BenchmarkRunService(
        platform=PlaceholderBenchmarkPlatform("https://api.bitgn.com"),
        agent_loop=PlaceholderAgentLoop(),
    )

    summary = service.run_once(_config(allow_submit=True))

    assert summary.submitted is True
    assert summary.score is None
    assert summary.trial_id.startswith("placeholder:")


def test_run_once_with_debug_includes_diagnostics():
    service = BenchmarkRunService(
        platform=PlaceholderBenchmarkPlatform("https://api.bitgn.com"),
        agent_loop=PlaceholderAgentLoop(),
    )

    summary = service.run_once(_config(allow_submit=False, debug=True))

    assert any("debug=true" == line for line in summary.debug_detail)
    assert any(line.startswith("provider=local") for line in summary.debug_detail)


def test_run_once_requires_concrete_task_id():
    service = BenchmarkRunService(
        platform=PlaceholderBenchmarkPlatform("https://api.bitgn.com"),
        agent_loop=PlaceholderAgentLoop(),
    )
    config = replace(_config(allow_submit=False), task_id=None, all_tasks=True)

    try:
        service.run_once(config)
        assert False, "Expected ValueError when task_id is missing"
    except ValueError as exc:
        assert "run_once requires a concrete task_id" in str(exc)
