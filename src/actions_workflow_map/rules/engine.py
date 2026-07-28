from __future__ import annotations

import re
from typing import Any

from ..models import Finding, WorkflowModel

SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _permission_findings(scope: str, permissions: Any) -> list[Finding]:
    findings: list[Finding] = []
    if permissions == "write-all":
        findings.append(Finding("WF201", "warning", "Broad write permissions", f"{scope}.permissions = write-all", scope, "Grant only required write scopes."))
    elif isinstance(permissions, dict):
        writes = [key for key, value in permissions.items() if str(value).lower() == "write"]
        if len(writes) >= 3:
            findings.append(Finding("WF201", "warning", "Broad write permissions", f"{scope}.permissions grants write to: {', '.join(writes)}", scope, "Reduce write scopes where feasible.", "Threshold-based review signal, not a complete security audit."))
    return findings


def _mutable_ref(ref: str) -> bool:
    if ref.startswith(("./", "docker://")):
        return False
    if "@" not in ref:
        return True
    revision = ref.rsplit("@", 1)[1]
    return not bool(SHA_RE.fullmatch(revision))


def run_rules(model: WorkflowModel) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_permission_findings("workflow", model.permissions))

    for job in model.jobs.values():
        findings.extend(_permission_findings(f"jobs.{job.id}", job.permissions))
        if job.timeout_minutes is None:
            findings.append(Finding("WF401", "warning", "No timeout configured", f"jobs.{job.id} has no timeout-minutes", job.id, "Set timeout-minutes to bound stuck or unexpectedly long jobs."))

        references = [job.uses] if job.uses else []
        references.extend(step.uses for step in job.steps if step.uses)
        for ref in references:
            assert ref is not None
            if _mutable_ref(ref):
                findings.append(Finding(
                    rule_id="WF501",
                    severity="warning",
                    title="Mutable external action reference",
                    evidence=f"jobs.{job.id} uses {ref}",
                    job_id=job.id,
                    remediation=(
                        "Pin third-party actions to an immutable commit SHA."
                    ),
                ))

    for artifact in model.artifacts:
        if artifact.unresolved:
            continue
        if artifact.consumers and not artifact.producers:
            findings.append(Finding("WF301", "warning", "Artifact consumer without visible producer", f"Artifact '{artifact.name}' is downloaded by {', '.join(artifact.consumers)} but has no parsed producer.", artifact.consumers[0], "Add or correct the upload step, or document that the artifact comes from outside this workflow."))
        if artifact.producers and not artifact.consumers:
            findings.append(Finding("WF302", "info", "Artifact producer without visible consumer", f"Artifact '{artifact.name}' is uploaded by {', '.join(artifact.producers)} but not downloaded in this workflow.", artifact.producers[0], "Confirm whether the artifact is intended for users, retention, or another workflow."))
        if artifact.producers and artifact.consumers:
            for consumer in artifact.consumers:
                declared = set(model.jobs[consumer].needs)
                producer_set = set(artifact.producers)
                if declared.isdisjoint(producer_set):
                    findings.append(
                        Finding(
                            rule_id="WF101",
                            severity="warning",
                            title="Missing declared dependency",
                            evidence=(
                                f"Job '{consumer}' downloads artifact "
                                f"'{artifact.name}' from producer(s) "
                                f"{sorted(producer_set)} but "
                                f"needs={sorted(declared)}."
                            ),
                            job_id=consumer,
                            remediation=(
                                "Declare the producer job in needs when the "
                                "consumer depends on its artifact."
                            ),
                        )
                    )
    model.findings = findings
    return findings
