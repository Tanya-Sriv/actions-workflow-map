from __future__ import annotations

from typing import Any

from .models import ConcurrencyModel


def parse_concurrency(
    raw: Any,
    *,
    scope: str,
    owner: str,
) -> ConcurrencyModel | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        return ConcurrencyModel(group=raw, scope=scope, owner=owner)
    if isinstance(raw, dict):
        group = raw.get("group")
        return ConcurrencyModel(
            group=str(group) if group is not None else None,
            cancel_in_progress=raw.get("cancel-in-progress"),
            scope=scope,
            owner=owner,
        )
    return ConcurrencyModel(group=str(raw), scope=scope, owner=owner)


def is_static_group(group: str | None) -> bool:
    return bool(group) and "${{" not in group
