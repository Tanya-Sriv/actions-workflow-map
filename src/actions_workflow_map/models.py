from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from pathlib import Path


@dataclass(slots=True)
class StepModel:
    name: str | None = None
    uses: str | None = None
    run: str | None = None
    condition: str | None = None
    with_inputs: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobModel:
    id: str
    name: str | None = None
    runs_on: Any = None
    needs: list[str] = field(default_factory=list)
    condition: str | None = None
    matrix: dict[str, Any] = field(default_factory=dict)
    permissions: dict[str, Any] | str | None = None
    environment: Any = None
    timeout_minutes: int | None = None
    concurrency: Any = None
    uses: str | None = None
    steps: list[StepModel] = field(default_factory=list)


@dataclass(slots=True)
class ArtifactModel:
    name: str
    producers: list[str] = field(default_factory=list)
    consumers: list[str] = field(default_factory=list)
    unresolved: bool = False


@dataclass(slots=True)
class Finding:
    rule_id: str
    severity: str
    title: str
    evidence: str
    affected_node: str | None = None
    remediation: str | None = None
    limitation: str | None = None


@dataclass(slots=True)
class WorkflowModel:
    name: str | None
    source_path: str
    triggers: Any
    permissions: dict[str, Any] | str | None
    concurrency: Any
    jobs: dict[str, JobModel]
    artifacts: list[ArtifactModel] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
        
@dataclass
class WorkflowReference:
    caller_workflow: str
    caller_job: str
    reference: str
    resolved_path: Path | None
    target_workflow: str | None
    is_local: bool
    is_resolved: bool


@dataclass
class RepositorySummary:
    workflow_count: int = 0
    job_count: int = 0
    dependency_count: int = 0
    matrix_job_count: int = 0
    estimated_matrix_executions: int = 0
    artifact_count: int = 0
    reusable_workflow_count: int = 0
    environment_count: int = 0
    concurrency_group_count: int = 0
    finding_count: int = 0


@dataclass
class RepositoryModel:
    root: Path
    workflows: list["WorkflowModel"] = field(default_factory=list)
    reusable_workflow_references: list[WorkflowReference] = field(
        default_factory=list
    )
    findings: list["Finding"] = field(default_factory=list)
    summary: RepositorySummary = field(default_factory=RepositorySummary)
