from __future__ import annotations

from model_clients.base import ModelClient
from model_clients.types import Message, ModelSettings

from .common import RuntimeExecutor, TaskRunSummary
from .pac1_protocol import ReportTaskCompletion, ReqContext, ReqRead, ReqTree, parse_pac1_agent_step

SYSTEM_PROMPT = """You are a pragmatic personal knowledge management assistant working inside the BitGN PCM runtime.

Behaviors:
- Use only information found through tool outputs in this task. Do not answer from prior knowledge.
- Keep edits small and targeted.
- Prefer reading instructions and current workspace context before making changes.
- Ground the final completion message with only the files that directly support the answer or change.
- If the task is blocked, unsupported, or unsafe, use `report_completion` with the most appropriate non-OK outcome.
- If the task is completed successfully, use `report_completion` with `OUTCOME_OK`.

Return JSON only.

Schema:
{
  "current_state": "short status",
  "plan_remaining_steps_brief": ["next step"],
  "task_completed": false,
  "function": {
    "tool": "context|tree|find|search|list|read|write|delete|mkdir|move|report_completion",
    "...": "tool-specific fields"
  }
}

Completion payload:
{"tool":"report_completion","completed_steps_laconic":["..."],"message":"...","grounding_refs":["..."],"outcome":"OUTCOME_OK|OUTCOME_DENIED_SECURITY|OUTCOME_NONE_CLARIFICATION|OUTCOME_NONE_UNSUPPORTED|OUTCOME_ERR_INTERNAL"}

Do not wrap the JSON in commentary or markdown."""


def run_pac1_task_loop(
    *,
    model_client: ModelClient,
    runtime: RuntimeExecutor,
    task_text: str,
    settings: ModelSettings,
    max_steps: int,
) -> TaskRunSummary:
    conversation = [Message(role="system", content=SYSTEM_PROMPT)]
    conversation.extend(_bootstrap_pcm_context(runtime))
    conversation.append(Message(role="user", content=f"Task: {task_text}"))

    for step_index in range(max_steps):
        response = model_client.generate(conversation, settings)
        action = parse_pac1_agent_step(response.content)

        conversation.append(Message(role="assistant", content=response.content))
        execution = runtime.execute(action.function)

        if execution.completed:
            return TaskRunSummary(
                answer=execution.answer or "",
                code=execution.completion_code or "OUTCOME_OK",
                grounding_refs=execution.grounding_refs,
                completed_steps_laconic=execution.completed_steps_laconic,
                steps_taken=step_index + 1,
            )

        tool_feedback = (
            f"Tool execution result for step {step_index + 1}:\n"
            f"- planned_step: {action.plan_remaining_steps_brief[0]}\n"
            f"- tool_output:\n{execution.content}"
        )
        conversation.append(Message(role="user", content=tool_feedback))

    timeout_message = "Unable to complete the task within the configured step limit."
    runtime.execute(
        ReportTaskCompletion(
            tool="report_completion",
            completed_steps_laconic=["Reached the configured step limit without completing the task."],
            message=timeout_message,
            grounding_refs=[],
            outcome="OUTCOME_ERR_INTERNAL",
        )
    )
    return TaskRunSummary(
        answer=timeout_message,
        code="OUTCOME_ERR_INTERNAL",
        completed_steps_laconic=("Reached the configured step limit without completing the task.",),
        steps_taken=max_steps,
    )


def _bootstrap_pcm_context(runtime: RuntimeExecutor) -> list[Message]:
    bootstrap_commands = [
        ReqTree(tool="tree", root="/", level=2),
        ReqRead(tool="read", path="AGENTS.md"),
        ReqRead(tool="read", path="AGENTS.MD"),
        ReqContext(tool="context"),
    ]
    messages: list[Message] = []
    for command in bootstrap_commands:
        result = runtime.execute(command)
        messages.append(Message(role="user", content=f"Bootstrap tool output:\n{result.content}"))
    return messages
