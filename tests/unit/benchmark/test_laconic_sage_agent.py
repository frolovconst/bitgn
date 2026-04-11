import pytest

pytest.importorskip("langgraph")
pytest.importorskip("langchain_core")

from benchmark.bitgn.contracts import TrialHandle, TrialOutcome
from benchmark.bitgn.laconic_sage_agent import LaconicSageAgentLoop
from model_clients.types import ModelResponse, ToolCall, ToolDefinition


class _StubModelClient:
    def __init__(self, responses):
        self._responses = list(responses)

    def generate(self, messages, settings=None, tools=None):
        if not self._responses:
            raise AssertionError("No more stubbed responses.")
        return self._responses.pop(0)


def _trial() -> TrialHandle:
    return TrialHandle(
        trial_id="trial-42",
        benchmark_id="bitgn/pac1-dev",
        harness_url="https://vm.example",
        instruction="Complete task with references.",
    )


def test_laconic_sage_parses_final_json_answer(monkeypatch):
    monkeypatch.setattr(
        "benchmark.bitgn.laconic_sage_agent.build_model_tool_definitions",
        lambda _benchmark_id: [],
    )
    agent = LaconicSageAgentLoop(
        model_client=_StubModelClient(
            [
                ModelResponse(
                    content='{"message":"Done","outcome":"OUTCOME_OK","refs":["/README.md"]}',
                    model="x",
                    provider="local",
                )
            ]
        )
    )

    answer = agent.solve_trial(_trial())

    assert answer.message == "Done"
    assert answer.outcome == TrialOutcome.OK
    assert answer.refs == ["/README.md"]


def test_laconic_sage_executes_tool_calls_and_logs(monkeypatch):
    tool_def = ToolDefinition(
        name="Search",
        description="Search files",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
    )
    monkeypatch.setattr(
        "benchmark.bitgn.laconic_sage_agent.build_model_tool_definitions",
        lambda _benchmark_id: [tool_def],
    )
    monkeypatch.setattr(
        "benchmark.bitgn.laconic_sage_agent.call_runtime_tool",
        lambda trial, tool_name, arguments: ('{"pattern":"TODO"}', '{"ok":true}'),
    )

    actions = []
    agent = LaconicSageAgentLoop(
        model_client=_StubModelClient(
            [
                ModelResponse(
                    content="",
                    model="x",
                    provider="local",
                    tool_calls=[ToolCall(id="call_1", name="Search", arguments='{"pattern":"TODO"}')],
                ),
                ModelResponse(
                    content='{"message":"No TODO left","outcome":"OUTCOME_OK","refs":[]}',
                    model="x",
                    provider="local",
                ),
            ]
        ),
        action_sink=actions.append,
    )

    answer = agent.solve_trial(_trial())

    assert answer.outcome == TrialOutcome.OK
    assert any("tool_call:1:Search" in action for action in actions)
    assert any("tool_result:Search" in action for action in actions)
