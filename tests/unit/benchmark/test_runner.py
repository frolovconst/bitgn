from benchmark.bitgn.agent_loop import PlaceholderAgentLoop
from benchmark.bitgn.config import BenchmarkRunConfig
from benchmark.bitgn.platform import PlaceholderBenchmarkPlatform
from benchmark.bitgn.runner import BenchmarkRunService


def _config(allow_submit: bool) -> BenchmarkRunConfig:
    return BenchmarkRunConfig(
        benchmark_host="https://api.bitgn.com",
        benchmark_id="bitgn/pac1-dev",
        task_id="t01",
        allow_submit=allow_submit,
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


def test_run_once_with_submit_flows_through_placeholder_platform():
    service = BenchmarkRunService(
        platform=PlaceholderBenchmarkPlatform("https://api.bitgn.com"),
        agent_loop=PlaceholderAgentLoop(),
    )

    summary = service.run_once(_config(allow_submit=True))

    assert summary.submitted is True
    assert summary.score is None
    assert summary.trial_id.startswith("placeholder:")
