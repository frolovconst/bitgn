import json

from benchmark.bitgn.contracts import TrialHandle
from benchmark.bitgn.runtime_tools import (
    build_model_tool_definitions,
    call_runtime_tool,
    list_runtime_tool_names,
)


def test_runtime_tool_name_coverage_for_surfaces():
    assert set(list_runtime_tool_names("bitgn/pac1-dev")) == {
        "Read",
        "Write",
        "Delete",
        "MkDir",
        "Move",
        "List",
        "Tree",
        "Find",
        "Search",
        "Context",
        "Answer",
    }
    assert set(list_runtime_tool_names("bitgn/sandbox")) == {
        "Outline",
        "Search",
        "List",
        "Read",
        "Write",
        "Delete",
        "Answer",
    }


def test_runtime_tool_definitions_include_schema_and_description():
    tools = {tool.name: tool for tool in build_model_tool_definitions("bitgn/pac1-dev")}
    search = tools["Search"]
    assert "Regex" in search.description
    assert search.parameters["type"] == "object"
    assert "pattern" in search.parameters["properties"]


def test_validation_errors_are_returned_with_guidance():
    trial = TrialHandle(
        trial_id="trial-1",
        benchmark_id="bitgn/pac1-dev",
        harness_url="https://vm.example",
        instruction="",
    )

    params, result = call_runtime_tool(trial, "Search", {"root": "/"})

    assert json.loads(params) == {"root": "/"}
    payload = json.loads(result)
    assert payload["ok"] is False
    assert payload["error"] == "validation_error"
    assert "guidance" in payload


def test_runtime_tool_executes_context(monkeypatch):
    trial = TrialHandle(
        trial_id="trial-1",
        benchmark_id="bitgn/pac1-dev",
        harness_url="https://vm.example",
        instruction="",
    )

    class _FakeRuntime:
        def context(self, request):
            assert request == {"request": "context"}
            return {"unix_time": "123"}

    monkeypatch.setattr(
        "benchmark.bitgn.runtime_tools._create_pcm_runtime_client",
        lambda _url: _FakeRuntime(),
    )
    monkeypatch.setattr(
        "benchmark.bitgn.runtime_tools._new_pcm_context_request",
        lambda: {"request": "context"},
    )
    monkeypatch.setattr(
        "benchmark.bitgn.runtime_tools._message_to_payload",
        lambda response: response,
    )

    params, result = call_runtime_tool(trial, "Context", {})

    assert json.loads(params) == {}
    assert json.loads(result) == {"unix_time": "123"}
