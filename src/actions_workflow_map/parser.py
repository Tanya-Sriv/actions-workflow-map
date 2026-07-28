from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.scanner import ScannerError

from .concurrency import parse_concurrency
from .errors import WorkflowParseError
from .matrix_analysis import parse_matrix
from .models import JobModel, StepModel, WorkflowModel
from .permissions import resolve_effective_permissions


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def parse_workflow(path: str | Path) -> WorkflowModel:
    source = Path(path)
    if not source.exists() or not source.is_file():
        raise WorkflowParseError(f"Workflow file not found: {source}")
    if source.suffix.lower() not in {".yml", ".yaml"}:
        raise WorkflowParseError("Input must be a .yml or .yaml workflow file")

    yaml = YAML(typ="safe")
    try:
        raw = yaml.load(source.read_text(encoding="utf-8"))
    except (OSError, ParserError, ScannerError) as exc:
        raise WorkflowParseError(f"Unable to parse YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise WorkflowParseError("Workflow root must be a YAML mapping")

    triggers = raw.get("on", raw.get(True))
    jobs_raw = raw.get("jobs")
    if not isinstance(jobs_raw, dict) or not jobs_raw:
        raise WorkflowParseError("Workflow must contain a non-empty jobs mapping")

    workflow_permissions = _plain(raw.get("permissions"))
    jobs: dict[str, JobModel] = {}
    unsupported: list[str] = []

    for job_id, value in jobs_raw.items():
        if not isinstance(value, dict):
            unsupported.append(f"jobs.{job_id}: expected mapping")
            continue

        steps: list[StepModel] = []
        for index, step in enumerate(value.get("steps", []) or []):
            if not isinstance(step, dict):
                unsupported.append(f"jobs.{job_id}.steps[{index}]: expected mapping")
                continue
            steps.append(
                StepModel(
                    name=step.get("name"),
                    uses=step.get("uses"),
                    run=step.get("run"),
                    condition=step.get("if"),
                    with_inputs=_plain(step.get("with", {}) or {}),
                )
            )

        strategy = value.get("strategy") or {}
        raw_matrix = strategy.get("matrix", {}) if isinstance(strategy, dict) else {}
        matrix_details = parse_matrix(_plain(raw_matrix))
        matrix = matrix_details.to_legacy_dict() if matrix_details else {}
        job_permissions = _plain(value.get("permissions"))
        effective_permissions, permission_source = resolve_effective_permissions(
            workflow_permissions,
            job_permissions,
        )

        jobs[str(job_id)] = JobModel(
            id=str(job_id),
            name=value.get("name"),
            runs_on=_plain(value.get("runs-on")),
            needs=_as_list(value.get("needs")),
            condition=value.get("if"),
            matrix=matrix,
            matrix_details=matrix_details,
            permissions=job_permissions,
            effective_permissions=effective_permissions,
            permission_source=permission_source,
            environment=_plain(value.get("environment")),
            timeout_minutes=value.get("timeout-minutes"),
            concurrency=_plain(value.get("concurrency")),
            concurrency_details=parse_concurrency(
                _plain(value.get("concurrency")),
                scope="job",
                owner=str(job_id),
            ),
            uses=value.get("uses"),
            steps=steps,
        )

    workflow_concurrency = _plain(raw.get("concurrency"))
    return WorkflowModel(
        name=raw.get("name"),
        source_path=str(source.resolve()),
        triggers=_plain(triggers),
        permissions=workflow_permissions,
        concurrency=workflow_concurrency,
        concurrency_details=parse_concurrency(
            workflow_concurrency,
            scope="workflow",
            owner=source.name,
        ),
        jobs=jobs,
        unsupported=unsupported,
    )
