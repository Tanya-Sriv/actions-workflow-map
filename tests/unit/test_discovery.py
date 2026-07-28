from pathlib import Path

import pytest

from actions_workflow_map.discovery import (
    WorkflowDiscoveryError,
    discover_workflow_files,
)


def create_workflow_directory(repository: Path) -> Path:
    workflow_directory = repository / ".github" / "workflows"
    workflow_directory.mkdir(parents=True)
    return workflow_directory


def test_discovers_yml_and_yaml_files(tmp_path: Path) -> None:
    workflow_directory = create_workflow_directory(tmp_path)

    yml_file = workflow_directory / "ci.yml"
    yaml_file = workflow_directory / "release.yaml"

    yml_file.write_text("name: CI\n", encoding="utf-8")
    yaml_file.write_text("name: Release\n", encoding="utf-8")

    result = discover_workflow_files(tmp_path)

    assert result == sorted(
        [
            yml_file.resolve(),
            yaml_file.resolve(),
        ]
    )


def test_returns_sorted_paths(tmp_path: Path) -> None:
    workflow_directory = create_workflow_directory(tmp_path)

    second_file = workflow_directory / "z-release.yml"
    first_file = workflow_directory / "a-ci.yml"

    second_file.write_text("name: Release\n", encoding="utf-8")
    first_file.write_text("name: CI\n", encoding="utf-8")

    result = discover_workflow_files(tmp_path)

    assert result == [
        first_file.resolve(),
        second_file.resolve(),
    ]


def test_ignores_non_yaml_files(tmp_path: Path) -> None:
    workflow_directory = create_workflow_directory(tmp_path)

    workflow_file = workflow_directory / "ci.yml"
    ignored_file = workflow_directory / "README.md"
    ignored_json = workflow_directory / "metadata.json"

    workflow_file.write_text("name: CI\n", encoding="utf-8")
    ignored_file.write_text("# Workflows\n", encoding="utf-8")
    ignored_json.write_text("{}", encoding="utf-8")

    result = discover_workflow_files(tmp_path)

    assert result == [workflow_file.resolve()]


def test_returns_empty_list_when_workflow_directory_missing(
    tmp_path: Path,
) -> None:
    result = discover_workflow_files(tmp_path)

    assert result == []


def test_rejects_non_directory_repository_path(tmp_path: Path) -> None:
    repository_file = tmp_path / "repository.txt"
    repository_file.write_text("not a directory", encoding="utf-8")

    with pytest.raises(
        WorkflowDiscoveryError,
        match="Repository path is not a directory",
    ):
        discover_workflow_files(repository_file)


def test_rejects_missing_repository_path(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing-repository"

    with pytest.raises(
        WorkflowDiscoveryError,
        match="Path does not exist",
    ):
        discover_workflow_files(missing_path)