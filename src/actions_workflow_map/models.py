from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class StepModel:
    name: str | None = None
    uses: str | None = None
    run: str | None = None
    condition: str | None = None
    with_inputs: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MatrixModel:
    dimensions: dict[str, list[Any]] = field(default_factory=dict)
    includes: list[dict[str, Any]] = field(default_factory=list)
    excludes: list[dict[str, Any]] = field(default_factory=list)
    estimated_expansion: int | None = None
    has_unresolved_expressions: bool = False

    def to_legacy_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = dict(self.dimensions)
        if self.includes:
            result["include"] = self.includes
        if self.excludes:
            result["exclude"] = self.excludes
        return result


@dataclass(slots=True)
class ConcurrencyModel:
    group: str | None = None
    cancel_in_progress: bool | str | None = None
    scope: str = "workflow"
    owner: str = "workflow"


@dataclass(slots=True)
class JobModel:
    id: str
    name: str | None = None
    runs_on: Any = None
    needs: list[str] = field(default_factory=list)
    condition: str | None = None
    matrix: dict[str, Any] = field(default_factory=dict)
    matrix_details: MatrixModel | None = None
    permissions: dict[str, Any] | str | None = None
    effective_permissions: dict[str, Any] | str | None = None
    permission_source: str = "unspecified"
    environment: Any = None
    timeout_minutes: int | None = None
    concurrency: Any = None
    concurrency_details: ConcurrencyModel | None = None
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
    concurrency_details: ConcurrencyModel | None = None
    artifacts: list[ArtifactModel] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WorkflowReference:
    caller_workflow_path: str
    caller_job: str
    reference: str
    resolved_path: str | None = None
    target_workflow_path: str | None = None
    is_local: bool = False
    is_resolved: bool = False
    escapes_repository: bool = False


@dataclass(slots=True)
class RepositorySummary:
    workflow_count: int = 0
    parse_failure_count: int = 0
    job_count: int = 0
    dependency_count: int = 0
    matrix_job_count: int = 0
    estimated_matrix_executions: int = 0
    artifact_count: int = 0
    reusable_workflow_count: int = 0
    resolved_reusable_workflow_count: int = 0
    environment_count: int = 0
    concurrency_group_count: int = 0
    finding_count: int = 0


@dataclass(slots=True)
class RepositoryModel:
    root: Path
    workflows: list[WorkflowModel] = field(default_factory=list)
    reusable_workflow_references: list[WorkflowReference] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    summary: RepositorySummary = field(default_factory=RepositorySummary)

    def relative_path(self, path: str | Path) -> str:
        candidate = Path(path).resolve()
        try:
            return candidate.relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return candidate.name

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "0.2",
            "repository": {"root": "."},
            "summary": asdict(self.summary),
            "workflows": [workflow.to_dict() for workflow in self.workflows],
            "reusable_workflow_references": [
                asdict(reference) for reference in self.reusable_workflow_references
            ],
            "findings": [asdict(finding) for finding in self.findings],
        }
