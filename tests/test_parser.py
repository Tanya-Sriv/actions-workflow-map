from pathlib import Path

import pytest

from actions_workflow_map.errors import WorkflowParseError
from actions_workflow_map.parser import parse_workflow

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_jobs_and_needs():
    model = parse_workflow(FIXTURES / "simple.yml")
    assert set(model.jobs) == {"build", "test"}
    assert model.jobs["test"].needs == ["build"]


def test_parse_triggers():
    model = parse_workflow(FIXTURES / "simple.yml")
    assert model.triggers == ["push", "pull_request"]


def test_parse_permissions():
    model = parse_workflow(FIXTURES / "simple.yml")
    assert model.permissions["contents"] == "read"


def test_reject_missing_jobs(tmp_path):
    path = tmp_path / "bad.yml"
    path.write_text("name: bad\n", encoding="utf-8")
    with pytest.raises(WorkflowParseError):
        parse_workflow(path)


def test_reject_wrong_extension(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_text("jobs: {}\n", encoding="utf-8")
    with pytest.raises(WorkflowParseError):
        parse_workflow(path)
