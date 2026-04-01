from benchmark.bitgn.agent_loop import run_task_loop
from benchmark.bitgn.protocol import ReportTaskCompletion, ReqOutline, ReqRead, ToolExecution, ToolCommand
from model_clients.types import Message, ModelResponse, ModelSettings


class FakeModelClient:
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.calls: list[list[Message]] = []

    def generate(self, messages: list[Message], settings: ModelSettings | None = None) -> ModelResponse:
        self.calls.append(list(messages))
        return ModelResponse(
            content=self._responses.pop(0),
            model="fake-model",
            provider="fake",
        )


class FakeRuntime:
    def __init__(self) -> None:
        self.commands: list[ToolCommand] = []

    def execute(self, command: ToolCommand) -> ToolExecution:
        self.commands.append(command)
        if isinstance(command, ReqOutline):
            return ToolExecution(content='{"path":"/","files":[{"path":"AGENTS.MD"},{"path":"CLAUDE.MD"}]}')
        if isinstance(command, ReqRead):
            return ToolExecution(content=f'{{"path":"{command.path}","content":"instructions from {command.path}"}}')
        if isinstance(command, ReportTaskCompletion):
            return ToolExecution(
                content="{}",
                completed=True,
                completion_code=command.code,
                answer=command.answer,
                grounding_refs=tuple(command.grounding_refs),
                completed_steps_laconic=tuple(command.completed_steps_laconic),
            )
        raise AssertionError(f"Unexpected command: {command}")


def test_run_task_loop_completes_task():
    client = FakeModelClient(
        responses=[
            '{"current_state":"need discovery","plan_remaining_steps_brief":["Inspect root files"],'
            '"task_completed":false,"function":{"tool":"outline","path":"/"}}',
            '{"current_state":"done","plan_remaining_steps_brief":["Report answer"],'
            '"task_completed":true,"function":{"tool":"report_completion",'
            '"completed_steps_laconic":["Inspected the root outline."],"answer":"Not Ready",'
            '"grounding_refs":["AGENTS.MD"],"code":"completed"}}',
        ]
    )
    runtime = FakeRuntime()

    summary = run_task_loop(
        model_client=client,
        runtime=runtime,
        task_text="What should I say?",
        settings=ModelSettings(),
        max_steps=5,
    )

    assert summary.answer == "Not Ready"
    assert summary.code == "completed"
    assert summary.grounding_refs == ("AGENTS.MD",)
    assert len(runtime.commands) == 5
    assert isinstance(runtime.commands[0], ReqOutline)
    assert isinstance(runtime.commands[1], ReqRead)
    assert isinstance(runtime.commands[2], ReqRead)
    assert isinstance(runtime.commands[3], ReqOutline)
    assert isinstance(runtime.commands[4], ReportTaskCompletion)
    assert "Task: What should I say?" in client.calls[0][1].content
    assert "Bootstrap tool output for root outline" in client.calls[0][2].content
    assert "Bootstrap tool output for read AGENTS.MD" in client.calls[0][3].content
    assert "Bootstrap tool output for read CLAUDE.MD" in client.calls[0][4].content


def test_run_task_loop_tolerates_empty_plan_steps():
    client = FakeModelClient(
        responses=[
            '{"current_state":"simple arithmetic","plan_remaining_steps_brief":[],"task_completed":true,'
            '"function":{"tool":"report_completion","completed_steps_laconic":["Answered the arithmetic question."],'
            '"answer":"4","grounding_refs":[],"code":"completed"}}',
        ]
    )
    runtime = FakeRuntime()

    summary = run_task_loop(
        model_client=client,
        runtime=runtime,
        task_text="What is 2+2=?",
        settings=ModelSettings(),
        max_steps=5,
    )

    assert summary.answer == "4"
    assert summary.code == "completed"
    assert len(runtime.commands) == 4
    assert isinstance(runtime.commands[3], ReportTaskCompletion)
