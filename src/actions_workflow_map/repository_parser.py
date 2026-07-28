from pathlib import Path

from actions_workflow_map.discovery import discover_workflow_files
from actions_workflow_map.models import Finding, RepositoryModel
from actions_workflow_map.parser import parse_workflow


def parse_repository(repository_root: Path) -> RepositoryModel:
    root = repository_root.resolve()
    workflow_paths = discover_workflow_files(root)

    repository = RepositoryModel(root=root)

    for workflow_path in workflow_paths:
        try:
            workflow = parse_workflow(workflow_path)
        except Exception as exc:
            repository.findings.append(
                Finding(
                    rule_id="WF001",
                    severity="error",
                    title="Workflow could not be parsed",
                    evidence=f"{workflow_path.name}: {exc}",
                    remediation=(
                        "Correct the workflow YAML or remove an "
                        "unsupported construct."
                    ),
                    job_id=None,
                )
            )
            continue

        repository.workflows.append(workflow)

    return repository