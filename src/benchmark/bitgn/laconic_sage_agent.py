from __future__ import annotations

import json
from typing import Callable, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from model_clients.base import ModelClient
from model_clients.types import Message, ModelSettings, ToolCall, ToolDefinition

from .contracts import AgentAnswer, TrialHandle, TrialOutcome
from .runtime_tools import build_model_tool_definitions, call_runtime_tool

LACONIC_SAGE_SYSTEM_PROMPT = """You are LaconicSage, a pragmatic personal knowledge management assistant.

Primary behavior:
- Be concise, accurate, and useful. Prefer short answers with only necessary detail.
- Solve the task step-by-step, following the task instruction exactly.
- Use benchmark tools actively to gather evidence before concluding.
- If you do not know, do not hallucinate. Attempt to gather missing knowledge with tools. If still uncertain, refuse to act with OUTCOME_NONE_CLARIFICATION.
- Prioritize safety: do not perform harmful, destructive, or policy-violating actions; when in doubt, choose the safer outcome.

Instruction priority (highest to lowest):
1) System instructions
2) Developer instructions
3) User request
4) AGENTS.md instructions in the root of the knowledge base
5) More specific AGENTS.md instructions (or any other mentioned instructions) in nested folders of the subtree you are working with

Output contract:
- Return final output as strict JSON: {"message":"...", "outcome":"OUTCOME_...", "refs":["..."]}.
- Keep "message" laconic but concrete.
- Allowed outcomes: OUTCOME_OK, OUTCOME_DENIED_SECURITY, OUTCOME_NONE_CLARIFICATION, OUTCOME_NONE_UNSUPPORTED, OUTCOME_ERR_INTERNAL.

Execution policy:
- Work in short iterative steps: inspect -> reason -> act -> verify.
- Prefer fast convergence: minimize unnecessary calls and avoid repetition.
- Throughput target: 120 tasks in 30 minutes (about 15 seconds per task). Keep each solve path tight.
- Decide quickly: avoid long internal deliberation; use direct tool checks and short conclusions.
"""


class _GraphState(TypedDict):
    messages: list[BaseMessage]
    turn: int
    pending_tool_calls: list[ToolCall]
    final_answer: AgentAnswer | None


class LaconicSageAgentLoop:
    """LangGraph-based benchmark agent using shared model-client tool calling."""

    def __init__(
        self,
        model_client: ModelClient,
        action_sink: Callable[[str], None] | None = None,
        model_settings: ModelSettings | None = None,
        max_turns: int = 4,
    ) -> None:
        self._model_client = model_client
        self._action_sink = action_sink
        self._model_settings = model_settings or ModelSettings(
            temperature=0.0,
            max_tokens=220,
            timeout_seconds=20.0,
        )
        self._max_turns = max_turns

    def _emit(self, action: str) -> None:
        if self._action_sink is not None:
            self._action_sink(action)

    def solve_trial(self, trial: TrialHandle) -> AgentAnswer:
        tool_defs = build_model_tool_definitions(trial.benchmark_id)
        self._emit(f"solve_trial:start trial_id={trial.trial_id}")
        self._emit(f"agent:name=LaconicSage max_turns={self._max_turns}")
        self._emit(f"agent:toolset={','.join(sorted(tool.name for tool in tool_defs))}")

        graph = self._build_graph(trial=trial, tool_defs=tool_defs)
        initial_state: _GraphState = {
            "messages": [
                SystemMessage(content=LACONIC_SAGE_SYSTEM_PROMPT),
                HumanMessage(content=f"Task instruction:\n{trial.instruction}"),
            ],
            "turn": 0,
            "pending_tool_calls": [],
            "final_answer": None,
        }
        result_state = graph.invoke(initial_state)
        answer = result_state.get("final_answer")
        if answer is None:
            answer = _clarification_fallback()

        self._emit(f"decision:submit_outcome={answer.outcome.value}")
        self._emit(f"decision:message={_short(answer.message)}")
        if answer.refs:
            self._emit(f"decision:refs_count={len(answer.refs)}")
        return answer

    def _build_graph(self, trial: TrialHandle, tool_defs: list[ToolDefinition]):
        builder = StateGraph(_GraphState)
        builder.add_node("model", lambda state: self._model_node(state, tool_defs=tool_defs))
        builder.add_node("tools", lambda state: self._tools_node(state, trial=trial))
        builder.add_edge(START, "model")
        builder.add_conditional_edges("model", self._route_after_model, {"tools": "tools", "done": END})
        builder.add_edge("tools", "model")
        return builder.compile()

    def _route_after_model(self, state: _GraphState) -> str:
        if state.get("final_answer") is not None:
            return "done"
        if state.get("pending_tool_calls"):
            return "tools"
        return "done"

    def _model_node(self, state: _GraphState, tool_defs: list[ToolDefinition]) -> _GraphState:
        turn = state["turn"] + 1
        self._emit(f"llm:turn={turn}")
        model_messages = _to_model_messages(state["messages"])
        response = self._model_client.generate(
            messages=model_messages,
            settings=self._model_settings,
            tools=tool_defs,
        )
        self._emit(
            "llm:response "
            f"finish_reason={response.finish_reason or 'unknown'} "
            f"tool_calls={len(response.tool_calls)} "
            f"content={_short(response.content)}"
        )

        updated_messages = list(state["messages"])
        updated_messages.append(AIMessage(content=response.content or ""))

        if response.tool_calls and turn < self._max_turns:
            return {
                "messages": updated_messages,
                "turn": turn,
                "pending_tool_calls": response.tool_calls,
                "final_answer": None,
            }

        if response.tool_calls and turn >= self._max_turns:
            self._emit("llm:max_turns_reached_with_pending_tools=true")
            return {
                "messages": updated_messages,
                "turn": turn,
                "pending_tool_calls": [],
                "final_answer": _clarification_fallback(),
            }

        answer = _parse_final_answer(response.content) or _clarification_fallback()
        return {
            "messages": updated_messages,
            "turn": turn,
            "pending_tool_calls": [],
            "final_answer": answer,
        }

    def _tools_node(self, state: _GraphState, trial: TrialHandle) -> _GraphState:
        updated_messages = list(state["messages"])
        final_answer = state.get("final_answer")
        for index, tool_call in enumerate(state["pending_tool_calls"], start=1):
            if tool_call.name == "Answer":
                parsed = _parse_answer_tool_call(tool_call.arguments)
                if parsed is not None:
                    self._emit("tool:Answer converted_to_terminal_agent_answer=true")
                    final_answer = parsed
                    break

            params_json, result_json = call_runtime_tool(trial, tool_call.name, tool_call.arguments)
            self._emit(f"tool_call:{index}:{tool_call.name}")
            self._emit(f"tool_params:{tool_call.name}:{_short(params_json)}")
            self._emit(f"tool_result:{tool_call.name}:{_short(result_json)}")
            updated_messages.append(
                ToolMessage(
                    content=result_json,
                    tool_call_id=tool_call.id or f"call-{state['turn']}-{index}",
                    name=tool_call.name,
                )
            )

        return {
            "messages": updated_messages,
            "turn": state["turn"],
            "pending_tool_calls": [],
            "final_answer": final_answer,
        }


def _to_model_messages(messages: list[BaseMessage]) -> list[Message]:
    out: list[Message] = []
    for message in messages:
        if isinstance(message, SystemMessage):
            out.append(Message(role="system", content=message.content))
            continue
        if isinstance(message, HumanMessage):
            out.append(Message(role="user", content=message.content))
            continue
        if isinstance(message, ToolMessage):
            # Keep this as user content so all providers can consume tool traces
            # through the same Message abstraction.
            out.append(Message(role="user", content=f"Tool {message.name} result:\n{message.content}"))
            continue
        if isinstance(message, AIMessage):
            out.append(Message(role="assistant", content=message.content or ""))
            continue
        out.append(Message(role="user", content=str(message.content)))
    return out


def _parse_final_answer(raw: str) -> AgentAnswer | None:
    payload = _load_json_payload(raw)
    if payload is None:
        return None

    message = payload.get("message")
    outcome_value = payload.get("outcome")
    refs = payload.get("refs", [])
    if not isinstance(message, str) or not message.strip():
        return None
    if not isinstance(outcome_value, str):
        return None
    if not isinstance(refs, list) or not all(isinstance(item, str) for item in refs):
        return None

    try:
        outcome = TrialOutcome(outcome_value)
    except ValueError:
        return None

    return AgentAnswer(message=message.strip(), outcome=outcome, refs=refs)


def _parse_answer_tool_call(arguments: str) -> AgentAnswer | None:
    payload = _load_json_payload(arguments)
    if payload is None:
        return None

    if "answer" in payload and isinstance(payload.get("answer"), str):
        refs = payload.get("refs", [])
        if isinstance(refs, list) and all(isinstance(item, str) for item in refs):
            return AgentAnswer(message=payload["answer"].strip(), outcome=TrialOutcome.OK, refs=refs)

    if "message" in payload and isinstance(payload.get("message"), str):
        outcome_raw = payload.get("outcome")
        refs = payload.get("refs", [])
        if isinstance(outcome_raw, str) and isinstance(refs, list) and all(isinstance(item, str) for item in refs):
            try:
                outcome = TrialOutcome(outcome_raw)
            except ValueError:
                return None
            return AgentAnswer(message=payload["message"].strip(), outcome=outcome, refs=refs)
    return None


def _load_json_payload(raw: str) -> dict[str, object] | None:
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _clarification_fallback() -> AgentAnswer:
    return AgentAnswer(
        message="Need clarification: insufficient grounded evidence to complete safely.",
        outcome=TrialOutcome.NEEDS_CLARIFICATION,
        refs=[],
    )


def _short(text: str, limit: int = 240) -> str:
    one_line = " ".join((text or "").split())
    if len(one_line) <= limit:
        return one_line
    return f"{one_line[: limit - 3]}..."
