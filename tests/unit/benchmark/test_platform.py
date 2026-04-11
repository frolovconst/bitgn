import pytest

from benchmark.bitgn.contracts import AgentAnswer, TrialOutcome, TrialSpec
from benchmark.bitgn.platform import BitgnBenchmarkPlatform


class _FakeStartPlaygroundResponse:
    def __init__(self) -> None:
        self.trial_id = "trial-123"
        self.harness_url = "https://vm.example"
        self.instruction = "do task"


class _FakeHarness:
    def __init__(self) -> None:
        self.start_playground_request = None
        self.get_benchmark_request = None
        self.start_run_request = None
        self.start_trial_requests = []
        self.submit_run_request = None

    def start_playground(self, request):
        self.start_playground_request = request
        return _FakeStartPlaygroundResponse()

    def get_benchmark(self, request):
        self.get_benchmark_request = request

        class _Task:
            def __init__(self, task_id: str) -> None:
                self.task_id = task_id

        class _Response:
            tasks = [_Task("t01"), _Task("t02"), _Task("t03")]

        return _Response()

    def start_run(self, request):
        self.start_run_request = request

        class _Response:
            run_id = "run-1"
            trial_ids = ["trial-a", "trial-b", "trial-c"]

        return _Response()

    def start_trial(self, request):
        self.start_trial_requests.append(request)

        trial_id = request["trial_id"]
        mapping = {
            "trial-a": ("t01", "inst-01", "https://vm/t01"),
            "trial-b": ("t02", "inst-02", "https://vm/t02"),
            "trial-c": ("t03", "inst-03", "https://vm/t03"),
        }
        task_id, instruction, harness_url = mapping[trial_id]

        class _Response:
            def __init__(self) -> None:
                self.trial_id = trial_id
                self.task_id = task_id
                self.instruction = instruction
                self.harness_url = harness_url

        return _Response()

    def submit_run(self, request):
        self.submit_run_request = request

    def end_trial(self, _request):
        class _Response:
            trial_id = "trial-123"
            score_detail = []

            def HasField(self, _name):
                return False

        return _Response()


def test_start_trial_uses_start_playground_by_default(monkeypatch):
    fake_harness = _FakeHarness()

    monkeypatch.setattr(
        "benchmark.bitgn.platform._create_harness_client",
        lambda _host: fake_harness,
    )
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_start_playground_request",
        lambda benchmark_id, task_id: {"benchmark_id": benchmark_id, "task_id": task_id},
    )

    platform = BitgnBenchmarkPlatform(benchmark_host="https://api.bitgn.com")

    trial = platform.start_trial(TrialSpec(benchmark_id="bitgn/pac1-dev", task_id="t01"))

    assert fake_harness.start_playground_request == {
        "benchmark_id": "bitgn/pac1-dev",
        "task_id": "t01",
    }
    assert trial.trial_id == "trial-123"
    assert trial.harness_url == "https://vm.example"


def test_run_mode_starts_run_and_resolves_requested_task(monkeypatch):
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_start_run_request",
        lambda benchmark_id, name, api_key: {
            "benchmark_id": benchmark_id,
            "name": name,
            "api_key": api_key,
        },
    )
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_start_trial_request",
        lambda trial_id: {"trial_id": trial_id},
    )

    fake_harness = _FakeHarness()
    monkeypatch.setattr(
        "benchmark.bitgn.platform._create_harness_client",
        lambda _host: fake_harness,
    )

    platform = BitgnBenchmarkPlatform(
        benchmark_host="https://api.bitgn.com",
        launch_mode="run",
        run_name="test-run",
        run_api_key="secret",
    )

    trial = platform.start_trial(TrialSpec(benchmark_id="bitgn/pac1-dev", task_id="t02"))

    assert fake_harness.start_run_request == {
        "benchmark_id": "bitgn/pac1-dev",
        "name": "test-run",
        "api_key": "secret",
    }
    assert fake_harness.start_trial_requests == [{"trial_id": "trial-a"}, {"trial_id": "trial-b"}]
    assert trial.trial_id == "trial-b"
    assert trial.harness_url == "https://vm/t02"


def test_run_mode_finalize_submits_run_once(monkeypatch):
    fake_harness = _FakeHarness()
    monkeypatch.setattr(
        "benchmark.bitgn.platform._create_harness_client",
        lambda _host: fake_harness,
    )
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_start_run_request",
        lambda benchmark_id, name, api_key: {
            "benchmark_id": benchmark_id,
            "name": name,
            "api_key": api_key,
        },
    )
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_start_trial_request",
        lambda trial_id: {"trial_id": trial_id},
    )
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_submit_run_request",
        lambda run_id, force: {"run_id": run_id, "force": force},
    )

    platform = BitgnBenchmarkPlatform(
        benchmark_host="https://api.bitgn.com",
        launch_mode="run",
    )
    _ = platform.start_trial(TrialSpec(benchmark_id="bitgn/pac1-dev", task_id="t01"))
    platform.finalize_run(force=True)
    platform.finalize_run(force=True)

    assert fake_harness.submit_run_request == {"run_id": "run-1", "force": True}


def test_list_task_ids_uses_get_benchmark(monkeypatch):
    fake_harness = _FakeHarness()
    monkeypatch.setattr(
        "benchmark.bitgn.platform._create_harness_client",
        lambda _host: fake_harness,
    )
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_get_benchmark_request",
        lambda benchmark_id: {"benchmark_id": benchmark_id},
    )

    platform = BitgnBenchmarkPlatform(benchmark_host="https://api.bitgn.com")
    task_ids = platform.list_task_ids("bitgn/pac1-dev")

    assert fake_harness.get_benchmark_request == {"benchmark_id": "bitgn/pac1-dev"}
    assert task_ids == ["t01", "t02", "t03"]


def test_submit_answer_uses_pcm_for_pac1_benchmark(monkeypatch):
    fake_harness = _FakeHarness()
    fake_runtime_calls = {}

    class _FakePcmRuntime:
        def answer(self, request):
            fake_runtime_calls["request"] = request

    monkeypatch.setattr("benchmark.bitgn.platform._create_harness_client", lambda _host: fake_harness)
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_start_playground_request",
        lambda benchmark_id, task_id: {"benchmark_id": benchmark_id, "task_id": task_id},
    )
    monkeypatch.setattr("benchmark.bitgn.platform._create_pcm_runtime_client", lambda _url: _FakePcmRuntime())
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_answer_request",
        lambda message, outcome, refs: {"message": message, "outcome": outcome, "refs": refs},
    )

    platform = BitgnBenchmarkPlatform(benchmark_host="https://api.bitgn.com")
    trial = platform.start_trial(TrialSpec(benchmark_id="bitgn/pac1-dev", task_id="t01"))
    platform.submit_answer(
        trial.trial_id,
        AgentAnswer(message="Done", outcome=TrialOutcome.OK, refs=["README.md"]),
    )

    assert fake_runtime_calls["request"]["message"] == "Done"
    assert fake_runtime_calls["request"]["refs"] == ["README.md"]


def test_submit_answer_uses_mini_for_sandbox_benchmark(monkeypatch):
    fake_harness = _FakeHarness()
    fake_runtime_calls = {}

    class _FakeMiniRuntime:
        def answer(self, request):
            fake_runtime_calls["request"] = request

    monkeypatch.setattr("benchmark.bitgn.platform._create_harness_client", lambda _host: fake_harness)
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_start_playground_request",
        lambda benchmark_id, task_id: {"benchmark_id": benchmark_id, "task_id": task_id},
    )
    monkeypatch.setattr("benchmark.bitgn.platform._create_mini_runtime_client", lambda _url: _FakeMiniRuntime())
    monkeypatch.setattr(
        "benchmark.bitgn.platform._new_mini_answer_request",
        lambda answer, refs: {"answer": answer, "refs": refs},
    )

    platform = BitgnBenchmarkPlatform(benchmark_host="https://api.bitgn.com")
    trial = platform.start_trial(TrialSpec(benchmark_id="bitgn/sandbox", task_id="t01"))
    platform.submit_answer(
        trial.trial_id,
        AgentAnswer(message="Done", outcome=TrialOutcome.OK, refs=["/tmp/file.txt"]),
    )

    assert fake_runtime_calls["request"] == {"answer": "Done", "refs": ["/tmp/file.txt"]}
