from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random
from typing import Any

from model_clients.types import ToolDefinition

from .contracts import AgentAnswer, BenchmarkPlatform, ToolCallTrace, TrialHandle, TrialOutcome, TrialResult, TrialSpec
from .runtime_tools import (
    BENCHMARK_RUNTIME_SURFACE_BY_ID,
    RuntimeSurface,
    build_model_tool_definitions,
    call_runtime_tool,
    list_runtime_tool_names,
)


class TrialLaunchMode(str, Enum):
    PLAYGROUND = "playground"
    RUN = "run"


@dataclass
class _RunContext:
    run_id: str
    benchmark_id: str
    pending_trial_ids: list[str]
    submitted: bool = False


class BitgnBenchmarkPlatform(BenchmarkPlatform):
    """BitGN platform adapter.

    Supports both ad-hoc playground sessions and leaderboard runs.
    """

    def __init__(
        self,
        benchmark_host: str,
        launch_mode: str = TrialLaunchMode.PLAYGROUND.value,
        run_name: str | None = None,
        run_api_key: str | None = None,
    ) -> None:
        self._benchmark_host = benchmark_host
        self._launch_mode = TrialLaunchMode(launch_mode)
        self._run_name = run_name or "columbarium-trial-launch"
        self._run_api_key = run_api_key or ""
        self._harness = _create_harness_client(benchmark_host)
        self._trial_handles: dict[str, TrialHandle] = {}
        self._trial_ids_by_task_id: dict[str, str] = {}
        self._run_context: _RunContext | None = None

    def list_task_ids(self, benchmark_id: str) -> list[str]:
        response = self._harness.get_benchmark(_new_get_benchmark_request(benchmark_id=benchmark_id))
        return [task.task_id for task in response.tasks]

    def list_available_tools(self, benchmark_id: str) -> list[str]:
        return list_runtime_tool_names(benchmark_id)

    def list_runtime_tool_definitions(self, benchmark_id: str) -> list[ToolDefinition]:
        return build_model_tool_definitions(benchmark_id)

    def start_trial(self, spec: TrialSpec) -> TrialHandle:
        if self._launch_mode == TrialLaunchMode.PLAYGROUND:
            response = self._harness.start_playground(
                _new_start_playground_request(
                    benchmark_id=spec.benchmark_id,
                    task_id=spec.task_id,
                )
            )
            trial = TrialHandle(
                trial_id=response.trial_id,
                benchmark_id=spec.benchmark_id,
                harness_url=response.harness_url,
                instruction=response.instruction,
            )
            self._trial_handles[trial.trial_id] = trial
            return trial

        return self._start_run_trial(spec)

    def submit_answer(self, trial_id: str, answer: AgentAnswer) -> None:
        trial = self._trial_handles.get(trial_id)
        if trial is None:
            raise ValueError(f"Unknown trial id: {trial_id}")

        runtime_surface = _resolve_runtime_surface(trial.benchmark_id)
        if runtime_surface == RuntimeSurface.MINI:
            _submit_answer_mini(trial.harness_url, answer)
            return

        _submit_answer_pcm(trial.harness_url, answer)

    def call_random_tool(self, trial: TrialHandle) -> ToolCallTrace:
        runtime_surface = _resolve_runtime_surface(trial.benchmark_id)
        if runtime_surface == RuntimeSurface.MINI:
            tool_name = random.choice(["Outline", "List", "Search", "Read"])
            sample_args: dict[str, Any] = {
                "Outline": {"path": "/"},
                "List": {"path": "/"},
                "Search": {"path": "/", "pattern": ".", "count": 1},
                "Read": {"path": "/README.md"},
            }[tool_name]
            params, result = call_runtime_tool(trial, tool_name, sample_args)
            return ToolCallTrace(tool_name=tool_name, params=params, result=result)

        tool_name = random.choice(["Context", "List", "Tree", "Search", "Read", "Find"])
        sample_args = {
            "Context": {},
            "List": {"name": "/"},
            "Tree": {"root": "/", "level": 1},
            "Search": {"root": "/", "pattern": ".", "limit": 1},
            "Read": {"path": "/README.md"},
            "Find": {"root": "/", "name": "README", "type": "TYPE_FILES", "limit": 1},
        }[tool_name]
        params, result = call_runtime_tool(trial, tool_name, sample_args)
        return ToolCallTrace(tool_name=tool_name, params=params, result=result)

    def call_tool(self, trial: TrialHandle, tool_name: str, arguments: str | dict[str, Any] | None) -> ToolCallTrace:
        params, result = call_runtime_tool(trial, tool_name, arguments)
        return ToolCallTrace(tool_name=tool_name, params=params, result=result)

    def end_trial(self, trial_id: str) -> TrialResult:
        response = self._harness.end_trial(_new_end_trial_request(trial_id=trial_id))
        return TrialResult(
            trial_id=response.trial_id,
            score=_extract_optional_score(response),
            score_detail=list(response.score_detail),
        )

    def finalize_run(self, force: bool = False) -> None:
        if self._launch_mode != TrialLaunchMode.RUN:
            return

        if self._run_context is None or self._run_context.submitted:
            return

        self._harness.submit_run(
            _new_submit_run_request(
                run_id=self._run_context.run_id,
                force=force,
            )
        )
        self._run_context.submitted = True

    def _start_run_trial(self, spec: TrialSpec) -> TrialHandle:
        existing_trial_id = self._trial_ids_by_task_id.get(spec.task_id)
        if existing_trial_id is not None:
            return self._trial_handles[existing_trial_id]

        run = self._ensure_run(spec.benchmark_id)

        while run.pending_trial_ids:
            trial_id = run.pending_trial_ids.pop(0)
            response = self._harness.start_trial(_new_start_trial_request(trial_id=trial_id))
            trial = TrialHandle(
                trial_id=response.trial_id,
                benchmark_id=spec.benchmark_id,
                harness_url=response.harness_url,
                instruction=response.instruction,
            )
            self._trial_handles[trial.trial_id] = trial
            self._trial_ids_by_task_id[response.task_id] = trial.trial_id

            if response.task_id == spec.task_id:
                return trial

        raise ValueError(
            f"Task {spec.task_id!r} was not found in run for benchmark {spec.benchmark_id!r}."
        )

    def _ensure_run(self, benchmark_id: str) -> _RunContext:
        if self._run_context is not None:
            if self._run_context.benchmark_id != benchmark_id:
                raise ValueError(
                    "Run mode supports one benchmark per invocation. "
                    f"Current run benchmark={self._run_context.benchmark_id!r}, "
                    f"requested={benchmark_id!r}."
                )
            return self._run_context

        response = self._harness.start_run(
            _new_start_run_request(
                benchmark_id=benchmark_id,
                name=self._run_name,
                api_key=self._run_api_key,
            )
        )
        self._run_context = _RunContext(
            run_id=response.run_id,
            benchmark_id=benchmark_id,
            pending_trial_ids=list(response.trial_ids),
        )
        return self._run_context


class PlaceholderBenchmarkPlatform(BenchmarkPlatform):
    """Mock benchmark platform for local plumbing and unit testing."""

    def __init__(self, benchmark_host: str) -> None:
        self._benchmark_host = benchmark_host

    def list_task_ids(self, benchmark_id: str) -> list[str]:
        _ = benchmark_id
        return ["t01"]

    def list_available_tools(self, benchmark_id: str) -> list[str]:
        return list_runtime_tool_names(benchmark_id)

    def call_random_tool(self, trial: TrialHandle) -> ToolCallTrace:
        _ = trial
        return ToolCallTrace(
            tool_name="Context",
            params='{"name": "/"}',
            result='{"placeholder": true}',
        )

    def start_trial(self, spec: TrialSpec) -> TrialHandle:
        trial_id = f"placeholder:{spec.benchmark_id}:{spec.task_id}"
        return TrialHandle(
            trial_id=trial_id,
            benchmark_id=spec.benchmark_id,
            harness_url=f"{self._benchmark_host}/mock-harness",
            instruction=(
                "Placeholder trial. No real benchmark call has been made yet. "
                "Implement BitGN API adapter next."
            ),
        )

    def submit_answer(self, trial_id: str, answer: AgentAnswer) -> None:
        _ = trial_id, answer

    def end_trial(self, trial_id: str) -> TrialResult:
        return TrialResult(
            trial_id=trial_id,
            score=None,
            score_detail=["Placeholder mode: no evaluation requested."],
        )

    def finalize_run(self, force: bool = False) -> None:
        _ = force


def _extract_optional_score(response: Any) -> float | None:
    if hasattr(response, "HasField"):
        if response.HasField("score"):
            return float(response.score)
        return None

    score = getattr(response, "score", None)
    if score is None:
        return None
    return float(score)


def _create_harness_client(benchmark_host: str):
    try:
        from bitgn.harness_connect import HarnessServiceClientSync
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "BitGN SDK is not installed. Install project dependencies with `uv sync` "
            "or run with `uv run bitgn-run ...`."
        ) from exc
    return HarnessServiceClientSync(benchmark_host)


def _create_pcm_runtime_client(harness_url: str):
    try:
        from bitgn.vm.pcm_connect import PcmRuntimeClientSync
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "BitGN SDK is not installed. Install project dependencies with `uv sync` "
            "or run with `uv run bitgn-run ...`."
        ) from exc
    return PcmRuntimeClientSync(harness_url)


def _create_mini_runtime_client(harness_url: str):
    try:
        from bitgn.vm.mini_connect import MiniRuntimeClientSync
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "BitGN SDK is not installed. Install project dependencies with `uv sync` "
            "or run with `uv run bitgn-run ...`."
        ) from exc
    return MiniRuntimeClientSync(harness_url)


def _new_start_playground_request(benchmark_id: str, task_id: str):
    from bitgn.harness_pb2 import StartPlaygroundRequest

    return StartPlaygroundRequest(benchmark_id=benchmark_id, task_id=task_id)


def _new_get_benchmark_request(benchmark_id: str):
    from bitgn.harness_pb2 import GetBenchmarkRequest

    return GetBenchmarkRequest(benchmark_id=benchmark_id)


def _new_end_trial_request(trial_id: str):
    from bitgn.harness_pb2 import EndTrialRequest

    return EndTrialRequest(trial_id=trial_id)


def _new_start_run_request(benchmark_id: str, name: str, api_key: str):
    from bitgn.harness_pb2 import StartRunRequest

    return StartRunRequest(benchmark_id=benchmark_id, name=name, api_key=api_key)


def _new_start_trial_request(trial_id: str):
    from bitgn.harness_pb2 import StartTrialRequest

    return StartTrialRequest(trial_id=trial_id)


def _new_submit_run_request(run_id: str, force: bool):
    from bitgn.harness_pb2 import SubmitRunRequest

    return SubmitRunRequest(run_id=run_id, force=force)


def _new_answer_request(message: str, outcome: int, refs: list[str]):
    from bitgn.vm.pcm_pb2 import AnswerRequest

    return AnswerRequest(message=message, outcome=outcome, refs=refs)


def _new_mini_answer_request(answer: str, refs: list[str]):
    from bitgn.vm.mini_pb2 import AnswerRequest

    return AnswerRequest(answer=answer, refs=refs)


def _new_pcm_context_request():
    from bitgn.vm.pcm_pb2 import ContextRequest

    return ContextRequest()


def _new_pcm_list_request(name: str):
    from bitgn.vm.pcm_pb2 import ListRequest

    return ListRequest(name=name)


def _new_pcm_tree_request(root: str, level: int):
    from bitgn.vm.pcm_pb2 import TreeRequest

    return TreeRequest(root=root, level=level)


def _new_pcm_search_request(root: str, pattern: str, limit: int):
    from bitgn.vm.pcm_pb2 import SearchRequest

    return SearchRequest(root=root, pattern=pattern, limit=limit)


def _new_mini_outline_request(path: str):
    from bitgn.vm.mini_pb2 import OutlineRequest

    return OutlineRequest(path=path)


def _new_mini_list_request(path: str):
    from bitgn.vm.mini_pb2 import ListRequest

    return ListRequest(path=path)


def _new_mini_search_request(path: str, pattern: str, count: int):
    from bitgn.vm.mini_pb2 import SearchRequest

    return SearchRequest(path=path, pattern=pattern, count=count)


def _map_outcome(outcome: TrialOutcome) -> int:
    from bitgn.vm.pcm_pb2 import Outcome

    mapping: dict[TrialOutcome, int] = {
        TrialOutcome.OK: Outcome.OUTCOME_OK,
        TrialOutcome.DENIED_SECURITY: Outcome.OUTCOME_DENIED_SECURITY,
        TrialOutcome.NEEDS_CLARIFICATION: Outcome.OUTCOME_NONE_CLARIFICATION,
        TrialOutcome.UNSUPPORTED: Outcome.OUTCOME_NONE_UNSUPPORTED,
        TrialOutcome.ERR_INTERNAL: Outcome.OUTCOME_ERR_INTERNAL,
    }
    return mapping[outcome]


def _resolve_runtime_surface(benchmark_id: str) -> RuntimeSurface:
    return BENCHMARK_RUNTIME_SURFACE_BY_ID.get(benchmark_id, RuntimeSurface.PCM)


def _submit_answer_pcm(harness_url: str, answer: AgentAnswer) -> None:
    runtime = _create_pcm_runtime_client(harness_url)
    runtime.answer(
        _new_answer_request(
            message=answer.message,
            outcome=_map_outcome(answer.outcome),
            refs=answer.refs,
        )
    )


def _submit_answer_mini(harness_url: str, answer: AgentAnswer) -> None:
    runtime = _create_mini_runtime_client(harness_url)
    runtime.answer(
        _new_mini_answer_request(
            answer=answer.message,
            refs=answer.refs,
        )
    )

