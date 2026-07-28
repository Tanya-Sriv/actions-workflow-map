from __future__ import annotations

from pathlib import Path

from .models import RepositoryModel, WorkflowReference


def is_local_workflow_reference(reference: str) -> bool:
    return reference.startswith("./")


def resolve_reusable_workflows(repository: RepositoryModel) -> list[WorkflowReference]:
    root = repository.root.resolve()
    workflows_by_path = {
        Path(workflow.source_path).resolve(): workflow for workflow in repository.workflows
    }
    references: list[WorkflowReference] = []

    for workflow in repository.workflows:
        caller_path = repository.relative_path(workflow.source_path)
        for job in workflow.jobs.values():
            reference = job.uses
            if not reference:
                continue

            if not is_local_workflow_reference(reference):
                references.append(
                    WorkflowReference(
                        caller_workflow_path=caller_path,
                        caller_job=job.id,
                        reference=reference,
                        is_local=False,
                    )
                )
                continue

            candidate = (root / reference.removeprefix("./")).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                references.append(
                    WorkflowReference(
                        caller_workflow_path=caller_path,
                        caller_job=job.id,
                        reference=reference,
                        resolved_path=str(candidate),
                        is_local=True,
                        escapes_repository=True,
                    )
                )
                continue

            target = workflows_by_path.get(candidate)
            references.append(
                WorkflowReference(
                    caller_workflow_path=caller_path,
                    caller_job=job.id,
                    reference=reference,
                    resolved_path=repository.relative_path(candidate),
                    target_workflow_path=(
                        repository.relative_path(target.source_path) if target else None
                    ),
                    is_local=True,
                    is_resolved=target is not None,
                )
            )

    repository.reusable_workflow_references = sorted(
        references,
        key=lambda item: (
            item.caller_workflow_path,
            item.caller_job,
            item.reference,
        ),
    )
    return repository.reusable_workflow_references
