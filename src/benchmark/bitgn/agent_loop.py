from __future__ import annotations

import random
import time
from typing import Callable

from .contracts import AgentAnswer, ToolCallTrace, TrialHandle, TrialOutcome


class PlaceholderAgentLoop:
    """Temporary agent-loop stub.

    This class is intentionally simple so a real iterative tool-using loop can be
    introduced later without changing CLI/platform wiring.
    """

    def __init__(self, action_sink: Callable[[str], None] | None = None) -> None:
        self._action_sink = action_sink

    def _emit(self, action: str) -> None:
        if self._action_sink is not None:
            self._action_sink(action)

    def solve_trial(self, trial: TrialHandle) -> AgentAnswer:
        self._emit(f"solve_trial:start trial_id={trial.trial_id}")
        self._emit("decision:placeholder_outcome=OUTCOME_NONE_UNSUPPORTED")
        return AgentAnswer(
            message=(
                "Placeholder agent loop: benchmark connection is wired, "
                "but task-solving logic is not implemented yet."
            ),
            outcome=TrialOutcome.UNSUPPORTED,
            refs=[],
        )


class DumbAgentLoop:
    """Minimal submission-only agent used for end-to-end platform connectivity checks.

    It does not perform any runtime tool actions and always returns a terminal
    "done" answer.
    """

    def __init__(
        self,
        sleep_fn: Callable[[float], None] = time.sleep,
        uniform_fn: Callable[[float, float], float] = random.uniform,
        call_random_tool_fn: Callable[[TrialHandle], ToolCallTrace] | None = None,
        action_sink: Callable[[str], None] | None = None,
    ) -> None:
        self._sleep = sleep_fn
        self._uniform = uniform_fn
        self._call_random_tool = call_random_tool_fn
        self._action_sink = action_sink

    def _emit(self, action: str) -> None:
        if self._action_sink is not None:
            self._action_sink(action)

    def solve_trial(self, trial: TrialHandle) -> AgentAnswer:
        self._emit(f"solve_trial:start trial_id={trial.trial_id}")
        if self._call_random_tool is not None:
            trace = self._call_random_tool(trial)
            self._emit(f"runtime_tool_call:{trace.tool_name}")
            self._emit(f"runtime_tool_params:{trace.params}")
            self._emit(f"runtime_tool_result:{trace.result}")
        # Mimic lightweight "thinking time" to make the run behavior look realistic.
        sleep_seconds = self._uniform(1.0, 3.0)
        self._emit(f"thinking_delay_seconds:{sleep_seconds:.3f}")
        self._sleep(sleep_seconds)
        self._emit("decision:submit_done_outcome=OUTCOME_OK")
        return AgentAnswer(
            message="Done",
            outcome=TrialOutcome.OK,
            refs=[],
        )
