from pathlib import Path

from actions_workflow_map.repository_parser import parse_repository


def test_repository_demo_rules() -> None:
    root = Path(__file__).parents[2] / "examples" / "repository-demo"
    repository = parse_repository(root)
    rule_ids = {finding.rule_id for finding in repository.findings}
    assert "WF701" in rule_ids
    assert "WF702" in rule_ids
    assert "WF901" in rule_ids
    assert repository.summary.resolved_reusable_workflow_count == 1
