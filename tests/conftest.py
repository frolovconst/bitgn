import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-local-model",
        action="store_true",
        default=False,
        help="run tests that make real requests to a local Ollama model",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-local-model"):
        return

    skip_local_model = pytest.mark.skip(
        reason="needs --run-local-model to make a real request to the local model"
    )
    for item in items:
        if "local_model" in item.keywords:
            item.add_marker(skip_local_model)
