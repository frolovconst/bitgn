from __future__ import annotations

from .contracts import AgentAnswer, TrialHandle, TrialOutcome


class PlaceholderAgentLoop:
    """Temporary agent-loop stub.

    This class is intentionally simple so a real iterative tool-using loop can be
    introduced later without changing CLI/platform wiring.
    """

    def solve_trial(self, trial: TrialHandle) -> AgentAnswer:
        return AgentAnswer(
            message=(
                "Placeholder agent loop: benchmark connection is wired, "
                "but task-solving logic is not implemented yet."
            ),
            outcome=TrialOutcome.UNSUPPORTED,
            refs=[],
        )
