from __future__ import annotations

from collections import defaultdict

from .concurrency import is_static_group
from .models import Finding, RepositoryModel
from .permissions import permission_expansions

DEFAULT_MATRIX_WARNING_THRESHOLD = 20


def _workflow_call_declared(triggers: object) -> bool:
    if isinstance(triggers, dict):
        return "workflow_call" in triggers
    if isinstance(triggers, list):
        return "workflow_call" in [str(item) for item in triggers]
    return str(triggers) == "workflow_call"


def _workflow_by_relative_path(repository: RepositoryModel) -> dict[str, object]:
    return {
        repository.relative_path(workflow.source_path): workflow
        for workflow in repository.workflows
    }


def run_repository_rules(repository: RepositoryModel) -> list[Finding]:
    findings = list(repository.findings)
    workflow_lookup = _workflow_by_relative_path(repository)

    for reference in repository.reusable_workflow_references:
        node = f"{reference.caller_workflow_path}::jobs.{reference.caller_job}"
        if reference.escapes_repository:
            findings.append(
                Finding(
                    rule_id="WF603",
                    severity="error",
                    title="Local reusable workflow escapes repository root",
                    evidence=f"{node} uses {reference.reference}",
                    affected_node=node,
                    remediation="Use a repository-local path under .github/workflows.",
                )
            )
            continue
        if reference.is_local and not reference.is_resolved:
            findings.append(
                Finding(
                    rule_id="WF601",
                    severity="warning",
                    title="Local reusable workflow not found",
                    evidence=f"{node} uses {reference.reference}",
                    affected_node=node,
                    remediation="Correct the local reusable-workflow path or add the target file.",
                )
            )
            continue
        if reference.is_local and reference.target_workflow_path:
            target = workflow_lookup.get(reference.target_workflow_path)
            if target is not None and not _workflow_call_declared(target.triggers):
                findings.append(
                    Finding(
                        rule_id="WF602",
                        severity="warning",
                        title="Referenced workflow lacks workflow_call",
                        evidence=(
                            f"{reference.target_workflow_path} is called by {node} "
                            "but does not declare workflow_call."
                        ),
                        affected_node=reference.target_workflow_path,
                        remediation="Declare workflow_call in the reusable workflow trigger configuration.",
                    )
                )

    static_groups: dict[str, list[tuple[str, bool | str | None]]] = defaultdict(list)
    for workflow in repository.workflows:
        workflow_path = repository.relative_path(workflow.source_path)
        if workflow.concurrency_details and is_static_group(workflow.concurrency_details.group):
            static_groups[workflow.concurrency_details.group or ""].append(
                (workflow_path, workflow.concurrency_details.cancel_in_progress)
            )
        for job in workflow.jobs.values():
            details = job.concurrency_details
            if details and is_static_group(details.group):
                static_groups[details.group or ""].append(
                    (f"{workflow_path}::jobs.{job.id}", details.cancel_in_progress)
                )

    for group, owners in sorted(static_groups.items()):
        workflow_names = {owner.split("::", 1)[0] for owner, _ in owners}
        if len(workflow_names) < 2:
            continue
        evidence = f"Concurrency group '{group}' is declared by: {', '.join(owner for owner, _ in owners)}"
        findings.append(
            Finding(
                rule_id="WF701",
                severity="warning",
                title="Concurrency group shared across workflows",
                evidence=evidence,
                affected_node=f"concurrency:{group}",
                remediation="Confirm that cross-workflow serialization is intentional.",
                limitation="Only exact static group strings are compared.",
            )
        )
        if any(cancel is True for _, cancel in owners):
            findings.append(
                Finding(
                    rule_id="WF702",
                    severity="warning",
                    title="Shared concurrency group enables cancellation",
                    evidence=evidence,
                    affected_node=f"concurrency:{group}",
                    remediation="Review whether one workflow may cancel another unexpectedly.",
                    limitation="This is a declared-configuration risk, not proof that cancellation occurs.",
                )
            )

    for workflow in repository.workflows:
        workflow_path = repository.relative_path(workflow.source_path)
        for job in workflow.jobs.values():
            details = job.matrix_details
            if (
                details
                and details.estimated_expansion is not None
                and details.estimated_expansion > DEFAULT_MATRIX_WARNING_THRESHOLD
            ):
                findings.append(
                    Finding(
                        rule_id="WF801",
                        severity="warning",
                        title="Large matrix expansion",
                        evidence=(
                            f"{workflow_path}::jobs.{job.id} has an estimated "
                            f"matrix expansion of {details.estimated_expansion}."
                        ),
                        affected_node=f"{workflow_path}::jobs.{job.id}",
                        remediation="Review whether every matrix combination is required.",
                    )
                )

            for scope, workflow_value, job_value in permission_expansions(
                workflow.permissions,
                job.permissions,
            ):
                findings.append(
                    Finding(
                        rule_id="WF901",
                        severity="warning",
                        title="Job permissions broaden workflow permissions",
                        evidence=(
                            f"{workflow_path}::jobs.{job.id} changes {scope} "
                            f"from {workflow_value} to {job_value}."
                        ),
                        affected_node=f"{workflow_path}::jobs.{job.id}",
                        remediation="Confirm the broader job-level permission is required.",
                    )
                )

    repository.findings = sorted(
        findings,
        key=lambda finding: (
            finding.rule_id,
            finding.affected_node or "",
            finding.title,
        ),
    )
    _populate_summary(repository, static_groups)
    return repository.findings


def _populate_summary(
    repository: RepositoryModel,
    static_groups: dict[str, list[tuple[str, bool | str | None]]],
) -> None:
    summary = repository.summary
    summary.workflow_count = len(repository.workflows)
    summary.parse_failure_count = sum(
        finding.rule_id == "WF001" for finding in repository.findings
    )
    summary.job_count = sum(len(workflow.jobs) for workflow in repository.workflows)
    summary.dependency_count = sum(
        len(job.needs)
        for workflow in repository.workflows
        for job in workflow.jobs.values()
    )
    matrix_details = [
        job.matrix_details
        for workflow in repository.workflows
        for job in workflow.jobs.values()
        if job.matrix_details is not None
    ]
    summary.matrix_job_count = len(matrix_details)
    summary.estimated_matrix_executions = sum(
        details.estimated_expansion or 0 for details in matrix_details
    )
    summary.artifact_count = sum(
        len(workflow.artifacts) for workflow in repository.workflows
    )
    summary.reusable_workflow_count = len(repository.reusable_workflow_references)
    summary.resolved_reusable_workflow_count = sum(
        reference.is_resolved for reference in repository.reusable_workflow_references
    )
    summary.environment_count = len(
        {
            str(job.environment)
            for workflow in repository.workflows
            for job in workflow.jobs.values()
            if job.environment is not None
        }
    )
    summary.concurrency_group_count = len(static_groups)
    summary.finding_count = len(repository.findings)
