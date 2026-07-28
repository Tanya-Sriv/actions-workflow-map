from pathlib import Path

from actions_workflow_map.renderers import (
    render_repository_html,
    render_repository_json,
    render_repository_mermaid,
)
from actions_workflow_map.repository_parser import parse_repository


def test_repository_renderers_are_stable_and_portable() -> None:
    root = Path(__file__).parents[2] / "examples" / "repository-demo"
    repository = parse_repository(root)
    mermaid = render_repository_mermaid(repository)
    html = render_repository_html(repository, mermaid)
    report = render_repository_json(repository)
    assert "flowchart TD" in mermaid
    assert "Repository Analysis" in html
    assert '"schema_version": "0.2"' in report
    assert str(root.resolve()) not in report
