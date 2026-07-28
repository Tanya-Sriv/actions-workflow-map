from pathlib import Path

from actions_workflow_map.repository_parser import parse_repository


def _write_workflow(path: Path, name: str) -> None:
    path.write_text(
        f"name: {name}\non:\n  workflow_dispatch:\njobs:\n  build:\n    runs-on: ubuntu-latest\n    timeout-minutes: 10\n    steps:\n      - run: echo ok\n",
        encoding="utf-8",
    )


def test_parses_multiple_workflows(tmp_path: Path) -> None:
    directory = tmp_path / ".github" / "workflows"
    directory.mkdir(parents=True)
    _write_workflow(directory / "a.yml", "A")
    _write_workflow(directory / "b.yaml", "B")
    repository = parse_repository(tmp_path)
    assert len(repository.workflows) == 2
    assert repository.summary.workflow_count == 2


def test_continues_after_malformed_workflow(tmp_path: Path) -> None:
    directory = tmp_path / ".github" / "workflows"
    directory.mkdir(parents=True)
    _write_workflow(directory / "valid.yml", "Valid")
    (directory / "bad.yml").write_text("jobs: [", encoding="utf-8")
    repository = parse_repository(tmp_path)
    assert len(repository.workflows) == 1
    assert any(finding.rule_id == "WF001" for finding in repository.findings)


def test_paths_are_sorted(tmp_path: Path) -> None:
    directory = tmp_path / ".github" / "workflows"
    directory.mkdir(parents=True)
    _write_workflow(directory / "z.yml", "Z")
    _write_workflow(directory / "a.yml", "A")
    repository = parse_repository(tmp_path)
    assert [Path(workflow.source_path).name for workflow in repository.workflows] == ["a.yml", "z.yml"]
