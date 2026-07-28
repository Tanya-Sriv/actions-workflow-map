from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.scanner import ScannerError

from .errors import WorkflowParseError
from .models import JobModel, StepModel, WorkflowModel


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

    # YAML 1.1 parsers may coerce `on`; ruamel safe mode normally preserves it.
    triggers = raw.get("on", raw.get(True))
    jobs_raw = raw.get("jobs")
    if not isinstance(jobs_raw, dict) or not jobs_raw:
        raise WorkflowParseError("Workflow must contain a non-empty jobs mapping")

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
        matrix = strategy.get("matrix", {}) if isinstance(strategy, dict) else {}
        jobs[str(job_id)] = JobModel(
            id=str(job_id),
            name=value.get("name"),
            runs_on=_plain(value.get("runs-on")),
            needs=_as_list(value.get("needs")),
            condition=value.get("if"),
            matrix=_plain(matrix) if isinstance(matrix, dict) else {"unresolved": _plain(matrix)},
            permissions=_plain(value.get("permissions")),
            environment=_plain(value.get("environment")),
            timeout_minutes=value.get("timeout-minutes"),
            concurrency=_plain(value.get("concurrency")),
            uses=value.get("uses"),
            steps=steps,
        )

    return WorkflowModel(
        name=raw.get("name"),
        source_path=str(source),
        triggers=_plain(triggers),
        permissions=_plain(raw.get("permissions")),
        concurrency=_plain(raw.get("concurrency")),
        jobs=jobs,
        unsupported=unsupported,
    )
