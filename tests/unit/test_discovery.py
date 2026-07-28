from pathlib import Path

import pytest

from actions_workflow_map.discovery import WorkflowDiscoveryError, discover_workflow_files


def _workflow_dir(root: Path) -> Path:
    path = root / ".github" / "workflows"
    path.mkdir(parents=True)
    return path


def test_discovers_yml_and_yaml_files(tmp_path: Path) -> None:
    directory = _workflow_dir(tmp_path)
    first = directory / "a.yml"
    second = directory / "b.yaml"
    first.write_text("name: A\n", encoding="utf-8")
    second.write_text("name: B\n", encoding="utf-8")
    assert discover_workflow_files(tmp_path) == [first.resolve(), second.resolve()]


def test_ignores_non_yaml_files(tmp_path: Path) -> None:
    directory = _workflow_dir(tmp_path)
    workflow = directory / "ci.yml"
    workflow.write_text("name: CI\n", encoding="utf-8")
    (directory / "README.md").write_text("ignore", encoding="utf-8")
    assert discover_workflow_files(tmp_path) == [workflow.resolve()]


def test_missing_workflow_directory_returns_empty(tmp_path: Path) -> None:
    assert discover_workflow_files(tmp_path) == []


def test_rejects_file_as_repository(tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(WorkflowDiscoveryError):
        discover_workflow_files(path)
