from benchmark.bitgn.pac1_protocol import parse_pac1_agent_step


def test_parse_pac1_agent_step_infers_task_completion_for_report_completion():
    step = parse_pac1_agent_step(
        '{"current_state":"Search complete","plan_remaining_steps_brief":["report completion"],'
        '"function":{"tool":"report_completion","completed_steps_laconic":["Found the thread."],'
        '"message":"Discarded the thread.","grounding_refs":["02_distill/threads/foo.md"]}}'
    )

    assert step.task_completed is True
    assert step.function.tool == "report_completion"
    assert step.function.outcome == "OUTCOME_OK"


def test_parse_pac1_agent_step_accepts_read_file_alias():
    step = parse_pac1_agent_step(
        '{"current_state":"Read inbox note","plan_remaining_steps_brief":["inspect note"],'
        '"task_completed":false,"function":{"tool":"read","file":"00_inbox/task.md"}}'
    )

    assert step.task_completed is False
    assert step.function.tool == "read"
    assert step.function.path == "00_inbox/task.md"


def test_parse_pac1_agent_step_backfills_missing_write_content():
    step = parse_pac1_agent_step(
        '{"current_state":"Drafting Maya digest","plan_remaining_steps_brief":["write digest"],'
        '"task_completed":false,"function":{"tool":"write","path":"/tmp/maya_digest.md"}}'
    )

    assert step.function.tool == "write"
    assert step.function.path == "/tmp/maya_digest.md"
    assert step.function.content == ""


def test_parse_pac1_agent_step_synthesizes_fallback_function_when_missing():
    step = parse_pac1_agent_step('{"current_state":"Need a valid action","plan_remaining_steps_brief":["recover"]}')

    assert step.task_completed is True
    assert step.function.tool == "report_completion"
    assert step.function.outcome == "OUTCOME_ERR_INTERNAL"
    assert "omitted" in step.function.message.lower()


def test_parse_pac1_agent_step_promotes_top_level_tool_payload():
    step = parse_pac1_agent_step(
        '{"current_state":"Inspect thread","plan_remaining_steps_brief":["read thread"],'
        '"task_completed":false,"tool":"read","file":"02_distill/threads/thread.md"}'
    )

    assert step.task_completed is False
    assert step.function.tool == "read"
    assert step.function.path == "02_distill/threads/thread.md"


def test_parse_pac1_agent_step_promotes_nested_action_payload():
    step = parse_pac1_agent_step(
        '{"current_state":"Discard the thread","plan_remaining_steps_brief":["delete thread"],'
        '"task_completed":false,"action":{"name":"delete","file":"02_distill/threads/thread.md"}}'
    )

    assert step.task_completed is False
    assert step.function.tool == "delete"
    assert step.function.path == "02_distill/threads/thread.md"
