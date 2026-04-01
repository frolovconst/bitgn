from benchmark.bitgn.protocol import ReportTaskCompletion
from benchmark.bitgn.runtime import _normalize_grounding_refs


def test_normalize_grounding_refs_strips_leading_slashes_and_dedupes():
    refs = _normalize_grounding_refs(["/AGENTS.MD", "HOME.MD", "/HOME.MD", " ", "///TASKS/TODO.MD"])

    assert refs == ("AGENTS.MD", "HOME.MD", "TASKS/TODO.MD")


def test_normalize_grounding_refs_are_used_for_completion_summary():
    command = ReportTaskCompletion(
        tool="report_completion",
        completed_steps_laconic=["Answered the question."],
        answer="TBD",
        grounding_refs=["/AGENTS.MD", "/HOME.MD"],
        code="completed",
    )

    refs = _normalize_grounding_refs(command.grounding_refs)

    assert refs == ("AGENTS.MD", "HOME.MD")
