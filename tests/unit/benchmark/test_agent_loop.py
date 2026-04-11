from benchmark.bitgn.agent_loop import DumbAgentLoop, PlaceholderAgentLoop, RiskidanticAgentLoop
from benchmark.bitgn.contracts import ToolCallTrace, TrialHandle, TrialOutcome


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


def test_riskidantic_agent_returns_denied_security():
    actions = []
    answer = RiskidanticAgentLoop(action_sink=actions.append).solve_trial(_trial())

    assert answer.outcome == TrialOutcome.DENIED_SECURITY
    assert answer.message == "Denied by security policy."
    assert answer.refs == []
    assert any(action.startswith("solve_trial:start") for action in actions)
    assert any("submit_outcome=OUTCOME_DENIED_SECURITY" in action for action in actions)
