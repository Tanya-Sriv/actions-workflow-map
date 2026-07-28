from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import ArtifactModel, WorkflowModel

UPLOAD = "actions/upload-artifact"
DOWNLOAD = "actions/download-artifact"


def _artifact_name(inputs: dict[str, Any], job_id: str, kind: str) -> tuple[str, bool]:
    value = inputs.get("name")
    if value is None:
        return (f"<default:{job_id}:{kind}>", True)
    text = str(value)
    return (text, "${{" in text)


def extract_artifacts(model: WorkflowModel) -> list[ArtifactModel]:
    rows: dict[str, ArtifactModel] = defaultdict(lambda: ArtifactModel(name=""))
    for job in model.jobs.values():
        for step in job.steps:
            ref = (step.uses or "").lower()
            if ref.startswith(UPLOAD):
                name, unresolved = _artifact_name(step.with_inputs, job.id, "upload")
                row = rows[name]
                row.name = name
                row.unresolved |= unresolved
                row.producers.append(job.id)
            elif ref.startswith(DOWNLOAD):
                name, unresolved = _artifact_name(step.with_inputs, job.id, "download")
                row = rows[name]
                row.name = name
                row.unresolved |= unresolved
                row.consumers.append(job.id)
    model.artifacts = sorted(rows.values(), key=lambda a: a.name)
    return model.artifacts
