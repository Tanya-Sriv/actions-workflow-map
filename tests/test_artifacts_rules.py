from pathlib import Path

from actions_workflow_map.artifact_flow import extract_artifacts
from actions_workflow_map.parser import parse_workflow
from actions_workflow_map.rules import run_rules

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    model = parse_workflow(FIXTURES / name)
    extract_artifacts(model)
    run_rules(model)
    return model


def test_artifact_matching():
    model = load("simple.yml")
    artifact = model.artifacts[0]
    assert artifact.producers == ["build"]
    assert artifact.consumers == ["test"]


def test_no_missing_dependency_when_needs_present():
    ids = {f.rule_id for f in load("simple.yml").findings}
    assert "WF101" not in ids


def test_missing_dependency_detected():
    ids = {f.rule_id for f in load("risky.yml").findings}
    assert "WF101" in ids


def test_broad_permissions_detected():
    ids = {f.rule_id for f in load("risky.yml").findings}
    assert "WF201" in ids


def test_missing_timeout_detected():
    findings = load("risky.yml").findings
    assert sum(f.rule_id == "WF401" for f in findings) == 2


def test_mutable_action_detected():
    evidence = [f.evidence for f in load("risky.yml").findings if f.rule_id == "WF501"]
    assert any("vendor/action@main" in value for value in evidence)


def test_standard_actions_tags_are_also_reported_mutable():
    ids = {f.rule_id for f in load("simple.yml").findings}
    assert "WF501" in ids
