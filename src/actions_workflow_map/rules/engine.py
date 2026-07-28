from __future__ import annotations

import re
from typing import Any

from ..models import Finding, WorkflowModel

SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _permission_findings(scope: str, permissions: Any) -> list[Finding]:
    findings: list[Finding] = []
    if permissions == "write-all":
        findings.append(
            Finding(
                rule_id="WF201",
                severity="warning",
                title="Broad write permissions",
                evidence=f"{scope}.permissions = write-all",
                affected_node=scope,
                remediation="Grant only required write scopes.",
            )
        )
    elif isinstance(permissions, dict):
        writes = [str(key) for key, value in permissions.items() if str(value).lower() == "write"]
        if len(writes) >= 3:
            findings.append(
                Finding(
                    rule_id="WF201",
                    severity="warning",
                    title="Broad write permissions",
                    evidence=f"{scope}.permissions grants write to: {', '.join(writes)}",
                    affected_node=scope,
                    remediation="Reduce write scopes where feasible.",
                    limitation="Threshold-based review signal, not a complete security audit.",
                )
            )
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
            findings.append(
                Finding(
                    rule_id="WF401",
                    severity="warning",
                    title="No timeout configured",
                    evidence=f"jobs.{job.id} has no timeout-minutes",
                    affected_node=job.id,
                    remediation="Set timeout-minutes to bound stuck or unexpectedly long jobs.",
                )
            )

        references = [job.uses] if job.uses else []
        references.extend(step.uses for step in job.steps if step.uses)
        for ref in references:
            if ref is not None and _mutable_ref(ref):
                findings.append(
                    Finding(
                        rule_id="WF501",
                        severity="warning",
                        title="Mutable external action reference",
                        evidence=f"jobs.{job.id} uses {ref}",
                        affected_node=job.id,
                        remediation="Pin third-party actions to an immutable commit SHA.",
                        limitation="Local reusable workflows and docker:// references are excluded.",
                    )
                )

    for artifact in model.artifacts:
        if artifact.unresolved:
            continue
        if artifact.consumers and not artifact.producers:
            findings.append(
                Finding(
                    rule_id="WF301",
                    severity="warning",
                    title="Artifact consumer without visible producer",
                    evidence=(
                        f"Artifact '{artifact.name}' is downloaded by "
                        f"{', '.join(artifact.consumers)} but has no parsed producer."
                    ),
                    affected_node=artifact.consumers[0],
                    remediation=(
                        "Add or correct the upload step, or document that the artifact "
                        "comes from outside this workflow."
                    ),
                )
            )
        if artifact.producers and not artifact.consumers:
            findings.append(
                Finding(
                    rule_id="WF302",
                    severity="info",
                    title="Artifact producer without visible consumer",
                    evidence=(
                        f"Artifact '{artifact.name}' is uploaded by "
                        f"{', '.join(artifact.producers)} but not downloaded in this workflow."
                    ),
                    affected_node=artifact.producers[0],
                    remediation=(
                        "Confirm whether the artifact is intended for users, retention, "
                        "or another workflow."
                    ),
                )
            )
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
                                f"Job '{consumer}' downloads artifact '{artifact.name}' "
                                f"from producer(s) {sorted(producer_set)} but "
                                f"needs={sorted(declared)}."
                            ),
                            affected_node=consumer,
                            remediation=(
                                "Declare the producer job in needs when the consumer "
                                "depends on its artifact."
                            ),
                            limitation=(
                                "Static matching uses literal artifact names and direct needs only."
                            ),
                        )
                    )

    model.findings = sorted(
        findings,
        key=lambda finding: (
            finding.rule_id,
            finding.affected_node or "",
            finding.title,
        ),
    )
    return model.findings
