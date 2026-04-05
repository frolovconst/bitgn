from benchmark.bitgn.agent_loop import DumbAgentLoop, LlmToolAgentLoop, PlaceholderAgentLoop
from benchmark.bitgn.contracts import ToolCallTrace, TrialHandle, TrialOutcome
from model_clients.types import Message, ModelResponse, ModelSettings


def _trial() -> TrialHandle:
    return TrialHandle(
        trial_id="trial-123",
        benchmark_id="bitgn/pac1-dev",
        harness_url="https://vm.example",
        instruction="Solve task",
    )


def test_placeholder_agent_returns_unsupported():
    actions = []
    answer = PlaceholderAgentLoop(action_sink=actions.append).solve_trial(_trial())

    assert answer.outcome == TrialOutcome.UNSUPPORTED
    assert any(action.startswith("solve_trial:start") for action in actions)
    assert any("placeholder_outcome=OUTCOME_NONE_UNSUPPORTED" in action for action in actions)


def test_dumb_agent_returns_done_ok():
    slept = []
    actions = []
    agent = DumbAgentLoop(
        sleep_fn=lambda seconds: slept.append(seconds),
        uniform_fn=lambda low, high: 2.0,
        action_sink=actions.append,
    )
    answer = agent.solve_trial(_trial())

    assert answer.outcome == TrialOutcome.OK
    assert answer.message == "Done"
    assert answer.refs == []
    assert slept == [2.0]
    assert any(action.startswith("solve_trial:start") for action in actions)
    assert any(action.startswith("thinking_delay_seconds:") for action in actions)
    assert any("submit_done_outcome=OUTCOME_OK" in action for action in actions)


def test_dumb_agent_delay_bounds():
    captured = {}
    agent = DumbAgentLoop(
        sleep_fn=lambda seconds: captured.setdefault("seconds", seconds),
        uniform_fn=lambda low, high: (captured.setdefault("low", low), captured.setdefault("high", high), 1.5)[2],
    )

    _ = agent.solve_trial(_trial())

    assert captured["low"] == 1.0
    assert captured["high"] == 3.0
    assert captured["seconds"] == 1.5


def test_dumb_agent_calls_one_runtime_tool():
    calls = []
    actions = []
    agent = DumbAgentLoop(
        sleep_fn=lambda _seconds: None,
        uniform_fn=lambda _low, _high: 1.0,
        call_random_tool_fn=lambda trial: calls.append(trial.trial_id) or ToolCallTrace(
            tool_name="Context", params='{"root":"/"}', result='{"unix_time":"123"}'
        ),
        action_sink=actions.append,
    )

    _ = agent.solve_trial(_trial())

    assert calls == ["trial-123"]
    assert "runtime_tool_call:Context" in actions
    assert 'runtime_tool_params:{"root":"/"}' in actions
    assert 'runtime_tool_result:{"unix_time":"123"}' in actions


class _FakeModelClient:
    def __init__(self, responses: list[ModelResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def generate(self, messages: list[Message], settings: ModelSettings | None = None, tools=None) -> ModelResponse:
        self.calls.append(
            {
                "messages": list(messages),
                "settings": settings,
                "tools": tools,
            }
        )
        return self._responses.pop(0)


def test_llm_agent_executes_runtime_tool_then_completes():
    model_client = _FakeModelClient(
        responses=[
            ModelResponse(
                content="",
                model="qwen3.5:4b",
                provider="local",
                finish_reason="tool_calls",
                raw={
                    "message": {
                        "tool_calls": [
                            {"function": {"name": "Search", "arguments": '{"pattern":"TODO","root":"/","limit":1}'}}
                        ]
                    }
                },
            ),
            ModelResponse(
                content="",
                model="qwen3.5:4b",
                provider="local",
                finish_reason="tool_calls",
                raw={
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "report_completion",
                                    "arguments": '{"message":"Done","outcome":"OUTCOME_OK","refs":["/README.md"]}',
                                }
                            }
                        ]
                    }
                },
            ),
        ]
    )
    tool_calls = []
    actions = []

    def call_tool(_trial, tool_name, arguments):
        tool_calls.append((tool_name, arguments))
        return ToolCallTrace(
            tool_name=tool_name,
            params='{"pattern":"TODO","root":"/","limit":1}',
            result='{"matches":[]}',
        )

    agent = LlmToolAgentLoop(
        model_client=model_client,
        available_tools=["Search"],
        settings=ModelSettings(timeout_seconds=5.0),
        max_steps=5,
        action_sink=actions.append,
        call_tool_fn=call_tool,
    )

    answer = agent.solve_trial(_trial())

    assert answer.outcome == TrialOutcome.OK
    assert answer.message == "Done"
    assert answer.refs == ["/README.md"]
    assert tool_calls == [("Search", {"pattern": "TODO", "root": "/", "limit": 1})]
    assert any(action.startswith("llm_step:1:tool_call=Search") for action in actions)
    assert any(action.startswith("runtime_tool_call:Search") for action in actions)
    assert len(model_client.calls) == 2
    assert model_client.calls[0]["tools"] is not None


def test_llm_agent_returns_internal_error_on_unknown_tool():
    model_client = _FakeModelClient(
        responses=[
            ModelResponse(
                content='{"name":"UnknownTool","arguments":{}}',
                model="qwen3.5:4b",
                provider="local",
                finish_reason="stop",
                raw={},
            )
        ]
    )
    agent = LlmToolAgentLoop(
        model_client=model_client,
        available_tools=["Search"],
        max_steps=1,
        call_tool_fn=lambda _trial, _tool_name, _args: ToolCallTrace(tool_name="Search", params="{}", result="{}"),
    )

    answer = agent.solve_trial(_trial())

    assert answer.outcome == TrialOutcome.ERR_INTERNAL
    assert "unsupported tool" in answer.message.lower()
