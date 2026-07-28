import json
from pathlib import Path

from actions_workflow_map.artifact_flow import extract_artifacts
from actions_workflow_map.parser import parse_workflow
from actions_workflow_map.renderers import render_html, render_json, render_mermaid
from actions_workflow_map.rules import run_rules

FIXTURE = Path(__file__).parent / "fixtures" / "simple.yml"


def model():
    value = parse_workflow(FIXTURE)
    extract_artifacts(value)
    run_rules(value)
    return value


def test_mermaid_contains_jobs_and_edge():
    text = render_mermaid(model())
    assert "build -->|needs| test" in text
    assert "artifact: package" in text


def test_json_is_valid_and_stable_shape():
    data = json.loads(render_json(model()))
    assert data["name"] == "Simple CI"
    assert "jobs" in data and "findings" in data


def test_html_contains_boundary_and_mermaid():
    value = model()
    html = render_html(value, render_mermaid(value))
    assert "does not simulate all runtime behavior" in html
    assert "mermaid" in html
