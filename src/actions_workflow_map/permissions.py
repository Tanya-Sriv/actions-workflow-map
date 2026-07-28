from __future__ import annotations

from typing import Any

PermissionValue = dict[str, Any] | str | None


def resolve_effective_permissions(
    workflow_permissions: PermissionValue,
    job_permissions: PermissionValue,
) -> tuple[PermissionValue, str]:
    if job_permissions is not None:
        return job_permissions, "job"
    if workflow_permissions is not None:
        return workflow_permissions, "workflow"
    return None, "unspecified"


def normalize_permission_level(value: Any) -> int | None:
    levels = {"none": 0, "read": 1, "write": 2}
    return levels.get(str(value).lower())


def permission_expansions(
    workflow_permissions: PermissionValue,
    job_permissions: PermissionValue,
) -> list[tuple[str, str, str]]:
    if not isinstance(workflow_permissions, dict) or not isinstance(job_permissions, dict):
        return []
    expansions: list[tuple[str, str, str]] = []
    for scope, job_value in job_permissions.items():
        workflow_value = workflow_permissions.get(scope, "none")
        workflow_level = normalize_permission_level(workflow_value)
        job_level = normalize_permission_level(job_value)
        if workflow_level is not None and job_level is not None and job_level > workflow_level:
            expansions.append((str(scope), str(workflow_value), str(job_value)))
    return expansions
