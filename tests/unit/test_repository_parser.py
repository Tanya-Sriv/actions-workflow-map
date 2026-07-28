from pathlib import Path

from actions_workflow_map.repository_parser import parse_repository


def create_workflow_directory(repository: Path) -> Path:
    workflow_directory = repository / ".github" / "workflows"
    workflow_directory.mkdir(parents=True)
    return workflow_directory


def write_valid_workflow(path: Path, name: str, job_id: str) -> None:
    path.write_text(
        f"""
name: {name}

on:
  workflow_dispatch:

jobs:
  {job_id}:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Run example
        run: echo "Hello"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_parses_multiple_workflows(tmp_path: Path) -> None:
    workflow_directory = create_workflow_directory(tmp_path)

    ci_path = workflow_directory / "ci.yml"
    release_path = workflow_directory / "release.yaml"

    write_valid_workflow(ci_path, "CI", "test")
    write_valid_workflow(release_path, "Release", "publish")

    repository = parse_repository(tmp_path)

    assert repository.root == tmp_path.resolve()
    assert len(repository.workflows) == 2
    assert repository.findings == []

    parsed_paths = [
        Path(workflow.source_path).resolve()
        for workflow in repository.workflows
    ]

    assert parsed_paths == [
        ci_path.resolve(),
        release_path.resolve(),
    ]


def test_returns_empty_repository_when_no_workflows_exist(
    tmp_path: Path,
) -> None:
    repository = parse_repository(tmp_path)

    assert repository.root == tmp_path.resolve()
    assert repository.workflows == []
    assert repository.findings == []


def test_continues_when_one_workflow_is_malformed(
    tmp_path: Path,
) -> None:
    workflow_directory = create_workflow_directory(tmp_path)

    valid_path = workflow_directory / "valid.yml"
    malformed_path = workflow_directory / "malformed.yml"

    write_valid_workflow(valid_path, "Valid Workflow", "build")

    malformed_path.write_text(
        """
name: Malformed Workflow

on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Broken step
        run: echo "missing closing bracket"
        env: [
""".strip()
        + "\n",
        encoding="utf-8",
    )

    repository = parse_repository(tmp_path)

    assert len(repository.workflows) == 1
    assert (
        Path(repository.workflows[0].source_path).resolve()
        == valid_path.resolve()
    )

    assert len(repository.findings) == 1

    finding = repository.findings[0]

    assert finding.rule_id == "WF001"
    assert "could not be parsed" in finding.title.lower()
    assert "malformed.yml" in finding.evidence.lower()


def test_parses_workflows_in_stable_sorted_order(
    tmp_path: Path,
) -> None:
    workflow_directory = create_workflow_directory(tmp_path)

    z_path = workflow_directory / "z-release.yml"
    a_path = workflow_directory / "a-ci.yml"
    m_path = workflow_directory / "m-test.yaml"

    write_valid_workflow(z_path, "Release", "release")
    write_valid_workflow(a_path, "CI", "build")
    write_valid_workflow(m_path, "Test", "test")

    repository = parse_repository(tmp_path)

    parsed_filenames = [
        Path(workflow.source_path).name
        for workflow in repository.workflows
    ]

    assert parsed_filenames == [
        "a-ci.yml",
        "m-test.yaml",
        "z-release.yml",
    ]