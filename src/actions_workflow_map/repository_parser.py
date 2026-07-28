from __future__ import annotations

from pathlib import Path

from .artifact_flow import extract_artifacts
from .discovery import discover_workflow_files
from .errors import WorkflowMapError
from .models import Finding, RepositoryModel
from .parser import parse_workflow
from .repository_rules import run_repository_rules
from .reusable_workflows import resolve_reusable_workflows
from .rules import run_rules


def parse_repository(repository_root: Path) -> RepositoryModel:
    root = repository_root.resolve()
    repository = RepositoryModel(root=root)

    for workflow_path in discover_workflow_files(root):
        try:
            workflow = parse_workflow(workflow_path)
            extract_artifacts(workflow)
            run_rules(workflow)
        except WorkflowMapError as exc:
            repository.findings.append(
                Finding(
                    rule_id="WF001",
                    severity="error",
                    title="Workflow could not be parsed",
                    evidence=f"{workflow_path.name}: {exc}",
                    affected_node=workflow_path.name,
                    remediation="Correct the malformed or unsupported workflow YAML.",
                )
            )
            continue
        repository.workflows.append(workflow)

    resolve_reusable_workflows(repository)
    run_repository_rules(repository)
    return repository
