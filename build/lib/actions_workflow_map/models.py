from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


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
