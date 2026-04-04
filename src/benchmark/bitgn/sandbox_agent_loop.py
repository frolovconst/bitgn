from __future__ import annotations

import json

from model_clients.base import ModelClient
from model_clients.types import Message, ModelSettings

from .common import RuntimeExecutor, TaskRunSummary
from .sandbox_protocol import ReportTaskCompletion, ReqOutline, ReqRead, parse_sandbox_agent_step

SYSTEM_PROMPT = """You are a benchmark agent operating inside the BitGN mini runtime.

Behaviors:
- Use only information found through tool outputs in this task. Do not answer from prior knowledge.
- Read discovered instruction files such as `AGENTS.MD` and `CLAUDE.MD` before answering.
- Use the available tools to inspect files, search text, and edit files when needed.
- Ground the final answer only with file paths that directly support the answer.
- Do not cite general instruction files unless they contain the answer or are the file that directed you to the answer.
- When the task is done, use `report_completion`.

Return JSON only.

Schema:
{
  "current_state": "short status",
  "plan_remaining_steps_brief": ["next step"],
  "task_completed": false,
  "function": {
    "tool": "outline|search|list|read|write|delete|report_completion",
    "...": "tool-specific fields"
  }
}

Tool fields:
- outline: {"tool":"outline","path":"/"}
- search: {"tool":"search","path":"/","pattern":"text","count":5}
- list: {"tool":"list","path":"/folder"}
- read: {"tool":"read","path":"file.txt"}
- write: {"tool":"write","path":"file.txt","content":"..."}
- delete: {"tool":"delete","path":"file.txt"}
- report_completion: {"tool":"report_completion","completed_steps_laconic":["..."],"answer":"...","grounding_refs":["..."],"code":"completed|failed"}

Do not wrap the JSON in commentary or markdown."""


def run_sandbox_task_loop(
    *,
    model_client: ModelClient,
    runtime: RuntimeExecutor,
    task_text: str,
    settings: ModelSettings,
    max_steps: int,
) -> TaskRunSummary:
    conversation = [
        Message(role="system", content=SYSTEM_PROMPT),
        Message(role="user", content=f"Task: {task_text}"),
    ]
    conversation.extend(_bootstrap_instruction_context(runtime))

    for step_index in range(max_steps):
        response = model_client.generate(conversation, settings)
        action = parse_sandbox_agent_step(response.content)

        conversation.append(Message(role="assistant", content=response.content))
        execution = runtime.execute(action.function)

        if execution.completed:
            return TaskRunSummary(
                answer=execution.answer or "",
                code=execution.completion_code or "completed",
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

    timeout_answer = "Unable to complete the task within the configured step limit."
    runtime.execute(
        ReportTaskCompletion(
            tool="report_completion",
            completed_steps_laconic=["Reached the configured step limit without completing the task."],
            answer=timeout_answer,
            grounding_refs=[],
            code="failed",
        )
    )
    return TaskRunSummary(
        answer=timeout_answer,
        code="failed",
        completed_steps_laconic=("Reached the configured step limit without completing the task.",),
        steps_taken=max_steps,
    )


def _bootstrap_instruction_context(runtime: RuntimeExecutor) -> list[Message]:
    messages: list[Message] = []
    outline_result = runtime.execute(ReqOutline(tool="outline", path="/"))
    messages.append(
        Message(
            role="user",
            content=f"Bootstrap tool output for root outline:\n{outline_result.content}",
        )
    )

    for path in _instruction_paths_from_outline(outline_result.content):
        read_result = runtime.execute(ReqRead(tool="read", path=path))
        messages.append(
            Message(
                role="user",
                content=f"Bootstrap tool output for read {path}:\n{read_result.content}",
            )
        )
    return messages


def _instruction_paths_from_outline(content: str) -> list[str]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return []

    files = payload.get("files")
    if not isinstance(files, list):
        return []

    paths: list[str] = []
    for entry in files:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not isinstance(path, str):
            continue
        file_name = path.rsplit("/", 1)[-1]
        if file_name in {"AGENTS.MD", "AGENTS.md", "CLAUDE.MD", "CLAUDE.md"}:
            paths.append(path)
    return paths
